from falkordb import FalkorDB


def get_investigation():
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("aidtrace")

    query = """
    MATCH (c:Community)-[:HAS_REQUEST]->(r:ReliefRequest)
          -[:FULFILLED_BY]->(d:Delivery)
          -[:HAS_RECEIPT]->(rec:Receipt)

    OPTIONAL MATCH (d)-[:TRANSPORTED_VIA]->(route:Route)
    OPTIONAL MATCH (incident:IncidentReport)-[:AFFECTS]->(route)

    OPTIONAL MATCH (w:Warehouse)-[:STORES]->(s:Supply)
    WHERE s.item = r.item

    RETURN
        c.name AS community,
        r.id AS request_id,
        r.item AS item,
        r.quantity AS requested,
        d.id AS delivery_id,
        d.reported_quantity AS reported,
        rec.confirmed_quantity AS confirmed,
        route.name AS route,
        route.status AS route_status,
        incident.description AS incident,
        incident.status AS incident_status,
        w.name AS warehouse,
        s.quantity AS stock
    """

    result = graph.query(query)

    if not result.result_set:
        return None

    row = result.result_set[0]

    (
        community,
        request_id,
        item,
        requested,
        delivery_id,
        reported,
        confirmed,
        route,
        route_status,
        incident,
        incident_status,
        warehouse,
        stock
    ) = row

    gap = (
        max(reported - confirmed, 0)
        if reported is not None and confirmed is not None
        else None
    )

    incident_is_simulated = bool(
        incident and "SIMULATED" in incident.upper()
    ) or (
        incident_status is not None
        and "simulated" in str(incident_status).lower()
    )

    evidence = [
        {
            "type": "relief_request",
            "reference": request_id,
            "community": community,
            "item": item,
            "requested_quantity": requested
        },
        {
            "type": "delivery_record",
            "reference": delivery_id,
            "reported_quantity": reported,
            "quantity_is_reported_not_independently_verified": True
        },
        {
            "type": "receipt",
            "confirmed_quantity": confirmed
        }
    ]

    if route:
        evidence.append({
            "type": "transport_route",
            "name": route,
            "recorded_status": route_status
        })

    if incident:
        evidence.append({
            "type": "incident_report",
            "description": incident,
            "recorded_status": incident_status,
            "simulated_demo_evidence": incident_is_simulated,
            "causal_link_verified": False
        })

    if warehouse or stock is not None:
        evidence.append({
            "type": "warehouse_stock",
            "warehouse": warehouse,
            "item": item,
            "recorded_quantity": stock,
            "physical_stock_verified": False
        })

    leads = []

    if gap is not None and gap > 0:
        leads.append({
            "title": "Unconfirmed delivery quantity",
            "finding": (
                f"{gap} {item} remain unconfirmed by the available receipt."
            ),
            "status": "Unresolved",
            "next_step": (
                "Request additional receipts or handover records."
            )
        })

    if route_status == "Disrupted":
        leads.append({
            "title": "Transport route requires review",
            "finding": (
                f"The recorded status of {route} is Disrupted. "
                "Its effect on this delivery has not been established."
            ),
            "status": "Unverified",
            "next_step": (
                "Verify the route status and compare delivery timestamps "
                "with independently sourced transport records."
            )
        })

    if stock is not None and stock > 0:
        leads.append({
            "title": "Recorded warehouse stock",
            "finding": (
                f"{stock} {item} are recorded at {warehouse}; "
                "physical availability is unverified."
            ),
            "status": "Unverified",
            "next_step": (
                "Verify current physical stock, allocation, and availability."
            )
        })

    recommended_actions = [
        "Request additional receipt or handover evidence.",
        "Ask the delivery organisation to reconcile the reported quantity.",
        "Review original delivery records and timestamps."
    ]

    if route_status == "Disrupted":
        recommended_actions.append(
            "Verify the route status and its relevance using independent "
            "records; do not assume it caused the discrepancy."
        )

    if stock is not None and stock > 0:
        recommended_actions.append(
            f"Verify the availability and allocation of the {stock} "
            f"recorded kits at {warehouse}."
        )

  

    cross_centre_query = """
    MATCH (c:Community)-[:HAS_REQUEST]->(r:ReliefRequest)
          -[:FULFILLED_BY]->(d:Delivery)
          -[:HAS_RECEIPT]->(rec:Receipt)

    RETURN
        c.name AS centre,
        c.location AS location,
        r.id AS request_id,
        r.item AS item,
        r.quantity AS requested,
        d.id AS delivery_id,
        d.reported_quantity AS reported,
        rec.confirmed_quantity AS confirmed
    ORDER BY c.name, r.id
    """

    cross_centre_result = graph.query(cross_centre_query)

    cross_centre_findings = []
    cross_centre_actions = []


    records_by_item = {}

    for record in cross_centre_result.result_set:
        (
            centre,
            location,
            centre_request_id,
            centre_item,
            centre_requested,
            centre_delivery_id,
            centre_reported,
            centre_confirmed
        ) = record

        if not centre_item or centre_requested is None:
            continue

        records_by_item.setdefault(centre_item, []).append({
            "centre": centre,
            "location": location,
            "request_id": centre_request_id,
            "item": centre_item,
            "requested": centre_requested,
            "delivery_id": centre_delivery_id,
            "reported": centre_reported,
            "confirmed": centre_confirmed
        })

    for compared_item, centre_records in records_by_item.items():
        if len(centre_records) < 2:
            continue

     

        for centre_record in centre_records:
            centre_name = centre_record["centre"]
            centre_requested = centre_record["requested"]
            centre_confirmed = centre_record["confirmed"]
            centre_reported = centre_record["reported"]

            if centre_confirmed is None:
                cross_centre_findings.append({
                    "title": "Cross-centre evidence incomplete",
                    "centre": centre_name,
                    "item": compared_item,
                    "request_id": centre_record["request_id"],
                    "finding": (
                        f"{centre_name} has no receipt-confirmed quantity "
                        f"for {compared_item} in the available records."
                    ),
                    "status": "Unverified",
                    "next_step": (
                        "Obtain and verify receipt or handover records "
                        "before comparing quantities."
                    )
                })
                continue

            variance = centre_confirmed - centre_requested

            if variance > 0:
                cross_centre_findings.append({
                    "title": "Confirmed quantity exceeds request",
                    "centre": centre_name,
                    "item": compared_item,
                    "request_id": centre_record["request_id"],
                    "requested_quantity": centre_requested,
                    "reported_quantity": centre_reported,
                    "confirmed_quantity": centre_confirmed,
                    "variance": variance,
                    "finding": (
                        f"{centre_name} has {variance} more {compared_item} "
                        "receipt-confirmed than its recorded request."
                    ),
                    "status": "Requires verification",
                    "next_step": (
                        "Check request amendments, duplicate records, "
                        "additional allocations, and current physical stock."
                    )
                })

            elif variance < 0:
                shortfall = abs(variance)

                cross_centre_findings.append({
                    "title": "Confirmed quantity below request",
                    "centre": centre_name,
                    "item": compared_item,
                    "request_id": centre_record["request_id"],
                    "requested_quantity": centre_requested,
                    "reported_quantity": centre_reported,
                    "confirmed_quantity": centre_confirmed,
                    "variance": variance,
                    "finding": (
                        f"{centre_name} has {shortfall} fewer "
                        f"{compared_item} receipt-confirmed than requested."
                    ),
                    "status": "Requires verification",
                    "next_step": (
                        "Verify outstanding deliveries, receipts, "
                        "allocations, and unmet demand."
                    )
                })

            if (
                centre_reported is not None
                and centre_confirmed is not None
                and centre_reported > centre_confirmed
            ):
                delivery_gap = centre_reported - centre_confirmed

                cross_centre_findings.append({
                    "title": "Reported delivery exceeds confirmed receipt",
                    "centre": centre_name,
                    "item": compared_item,
                    "request_id": centre_record["request_id"],
                    "reported_quantity": centre_reported,
                    "confirmed_quantity": centre_confirmed,
                    "variance": delivery_gap,
                    "finding": (
                        f"{delivery_gap} {compared_item} reported delivered "
                        f"to {centre_name} are not confirmed by its receipt."
                    ),
                    "status": "Unresolved",
                    "next_step": (
                        "Request additional receipts or handover records."
                    )
                })



        demo_centre_names = {"Centre A", "Centre B"}

        demo_centre_records = [
            record for record in centre_records
            if record["centre"] in demo_centre_names
        ]

        above_request = [
            record for record in demo_centre_records
            if record["confirmed"] is not None
            and record["confirmed"] > record["requested"]
        ]

        below_request = [
            record for record in demo_centre_records
            if record["confirmed"] is not None
            and record["confirmed"] < record["requested"]
        ]

        if above_request and below_request:
            for higher in above_request:
                for lower in below_request:
                    cross_centre_findings.append({
                        "title": "Potential cross-centre allocation imbalance",
                        "item": compared_item,
                        "centres": [
                            higher["centre"],
                            lower["centre"]
                        ],
                        "finding": (
                            f"{higher['centre']} has a confirmed quantity "
                            "above its recorded request, while "
                            f"{lower['centre']} has a confirmed quantity "
                            "below its recorded request."
                        ),
                        "status": "Investigation lead only",
                        "next_step": (
                            "Verify current stock, outstanding obligations, "
                            "request amendments, and transfer authority at "
                            "both centres. Do not assume the excess is "
                            "available or transferable."
                        )
                    })

                    cross_centre_actions.append(
                        f"Verify the records and current availability of "
                        f"{compared_item} at {higher['centre']} and "
                        f"{lower['centre']} before considering any "
                        "reallocation."
                    )

    if cross_centre_findings:
        cross_centre_actions.extend([
            "Reconcile each centre's original request, delivery record, "
            "and receipt independently.",
            "Check for amended requests, duplicate records, and outstanding "
            "deliveries before concluding that an imbalance exists."
        ])

 

    return {
        "case_id": request_id,
        "community": community,
        "request_id": request_id,
        "item": item,
        "requested": requested,
        "requested_quantity": requested,
        "delivery_id": delivery_id,
        "reported": reported,
        "reported_delivered": reported,
        "confirmed": confirmed,
        "receipt_confirmed": confirmed,
        "gap": gap,
        "unconfirmed_quantity": gap,
        "route": route,
        "route_status": route_status,
        "incident": incident,
        "incident_status": incident_status,
        "incident_is_simulated": incident_is_simulated,
        "warehouse": warehouse,
        "stock": stock,
        "status": "Needs human review",
        "assessment": (
            "An evidence gap is not proof of loss, theft, or non-delivery. "
            "Reported quantities and physical stock require verification."
        ),
        "evidence": evidence,
        "leads": leads,
        "leads_to_investigate": leads,
        "recommended_actions": recommended_actions,
        "cross_centre_findings": cross_centre_findings,
        "cross_centre_actions": cross_centre_actions,
        "ai_generated": False
    }