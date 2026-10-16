
from falkordb import FalkorDB


def build_action_plans(
    request_id,
    delivery_id,
    receipt_id,
    item,
    gap,
    warehouse,
    stock,
    route,
    route_status,
    incident_is_simulated,
    evidence,
):
    """Build traceable investigation actions without assuming wrongdoing."""

    action_plans = []

    def add_action(
        action_id,
        title,
        priority,
        reason,
        evidence_references,
        verification_steps,
    ):
        action_plans.append({
            "id": action_id,
            "title": title,
            "priority": priority,
            "status": "Pending human review",
            "reason": reason,
            "evidence_references": evidence_references,
            "verification_steps": verification_steps,
            "requires_human_review": True,
            "automatically_authorized": False,
        })

    if gap is not None and gap > 0:
        add_action(
            action_id="ACT-001",
            title="Reconcile the unconfirmed delivery quantity",
            priority="High",
            reason=(
                f"{gap} {item} are reported as delivered but are not "
                "confirmed by the available receipt."
            ),
            evidence_references=[
                ref for ref in [request_id, delivery_id, receipt_id]
                if ref
            ],
            verification_steps=[
                "Request additional receipts and handover records.",
                "Review original delivery documents and timestamps.",
                "Obtain recipient confirmation where available.",
                "Record the reconciliation outcome and supporting evidence.",
            ],
        )

    if warehouse and stock is not None and stock > 0:
        add_action(
            action_id="ACT-002",
            title="Verify recorded warehouse stock",
            priority="High",
            reason=(
                f"{stock} {item} are recorded at {warehouse}, "
                "but physical availability has not been verified."
            ),
            evidence_references=[
                entry.get("reference")
                for entry in evidence
                if entry.get("type") == "warehouse_stock"
                and entry.get("reference")
            ],
            verification_steps=[
                "Locate the original warehouse stock record and record its ID.",
                "Confirm the physical quantity currently on hand.",
                "Check item condition and storage location.",
                "Review existing commitments and pending allocations.",
                "Verify transport feasibility and transfer authority "
                "before considering any allocation.",
            ],
        )

    if route and route_status == "Disrupted":
        add_action(
            action_id="ACT-003",
            title="Verify the reported transport disruption",
            priority="Medium",
            reason=(
                f"The graph records {route} as Disrupted. "
                "Its effect on the delivery discrepancy is unverified."
            ),
            evidence_references=[
                entry.get("reference")
                for entry in evidence
                if entry.get("type") == "incident_report"
                and entry.get("reference")
            ],
            verification_steps=[
                "Verify the route status using independent records.",
                "Compare the disruption period with delivery timestamps.",
                "Do not attribute the discrepancy to the route without "
                "supporting evidence.",
            ],
        )

    if incident_is_simulated:
        action_plans.append({
            "id": "ACT-004",
            "title": "Keep simulated incident evidence separate",
            "priority": "Low",
            "status": "Pending human review",
            "reason": (
                "The linked incident is marked as simulated demonstration "
                "evidence and cannot establish a real-world cause."
            ),
            "evidence_references": [
                entry.get("reference")
                for entry in evidence
                if entry.get("type") == "incident_report"
                and entry.get("reference")
            ],
            "verification_steps": [
                "Retain the simulation label in reports and the interface.",
                "Do not use the simulated incident as proof of causation.",
                "Obtain independently verified incident records if needed.",
            ],
            "requires_human_review": True,
            "automatically_authorized": False,
        })

    return action_plans


def get_resource_matches(graph, scenario_id="wayanad"):
    """
    Find potential matches between recorded unmet demand and recorded
    warehouse stock within the selected scenario.

    Requests remain visible even when delivery or receipt records are
    missing. Missing receipt evidence is treated as zero confirmed
    quantity for shortfall calculation, not as proof that nothing arrived.

    Matches are independent investigation leads, not allocations.
    The same recorded stock may appear as a candidate for multiple
    centres, so potential matches must not be added together.
    """

    demand_query = """
    
            MATCH (c:Community)-[:HAS_REQUEST]->(r:ReliefRequest)
            WHERE c.scenario_id = $scenario_id
            AND r.scenario_id = $scenario_id

            OPTIONAL MATCH (r)-[:FULFILLED_BY]->(d:Delivery)
            WHERE d.scenario_id = $scenario_id

            OPTIONAL MATCH (d)-[:HAS_RECEIPT]->(rec:Receipt)
            WHERE rec.scenario_id = $scenario_id

            RETURN
                c.name AS centre,
                r.id AS request_id,
                r.item AS item,
                r.quantity AS requested,
                rec.confirmed_quantity AS confirmed
            ORDER BY centre, request_id

    """

    # Warehouse and supply nodes will need scenario_id properties
    # before this query can safely return scenario-specific stock.
    stock_query = """
    MATCH (w:Warehouse)-[:STORES]->(s:Supply)
    WHERE w.scenario_id = $scenario_id
      AND s.scenario_id = $scenario_id
    RETURN
        w.name AS warehouse,
        s.item AS item,
        s.quantity AS recorded_quantity
    ORDER BY w.name, s.item
    """

   
    demand_result = graph.query(
        demand_query,
        {"scenario_id": scenario_id},
    )
    stock_result = graph.query(
        stock_query,
        {"scenario_id": scenario_id},
    )
   

    demands_by_item = {}

    for row in demand_result.result_set:
        centre, request_id, item, requested, confirmed = row

        if not item or requested is None:
            continue

        receipt_evidence_available = confirmed is not None
        confirmed_quantity = confirmed if confirmed is not None else 0
        shortfall = max(requested - confirmed_quantity, 0)

        if shortfall <= 0:
            continue

        demands_by_item.setdefault(item, []).append({
            "centre": centre,
            "request_id": request_id,
            "requested_quantity": requested,
            "receipt_confirmed_quantity": confirmed_quantity,
            "receipt_evidence_available": receipt_evidence_available,
            "recorded_shortfall": shortfall,
        })

    stock_by_item = {}

    for row in stock_result.result_set:
        warehouse, item, recorded_quantity = row

        if (
            not item
            or recorded_quantity is None
            or recorded_quantity <= 0
        ):
            continue

        stock_by_item.setdefault(item, []).append({
            "warehouse": warehouse,
            "recorded_quantity": recorded_quantity,
        })

    matches = []
    unmatched_demand = []

    for item, demands in demands_by_item.items():
        supplies = stock_by_item.get(item, [])

        for demand in demands:
            remaining_need = demand["recorded_shortfall"]
            candidate_warehouses = []
            potential_match_quantity = 0

            # Assess each demand independently. Stock is not reserved.
            for supply in supplies:
                if remaining_need <= 0:
                    break

                quantity = min(
                    remaining_need,
                    supply["recorded_quantity"],
                )

                candidate_warehouses.append({
                    "warehouse": supply["warehouse"],
                    "recorded_stock_quantity": supply["recorded_quantity"],
                    "potential_match_quantity": quantity,
                    "physical_stock_verified": False,
                    "transfer_authorized": False,
                    "shared_stock_pool": True,
                    "match_is_additive": False,
                })

                potential_match_quantity += quantity
                remaining_need -= quantity

            if candidate_warehouses:
                matches.append({
                    "centre": demand["centre"],
                    "request_id": demand["request_id"],
                    "item": item,
                    "recorded_shortfall": demand["recorded_shortfall"],
                    "potential_match_quantity": potential_match_quantity,
                    "remaining_unmatched_quantity": remaining_need,
                    "candidate_warehouses": candidate_warehouses,
                    "match_is_additive": False,
                    "status": "Potential match — requires verification",
                    "evidence": {
                        "request_reference": demand["request_id"],
                        "receipt_confirmed_quantity":
                            demand["receipt_confirmed_quantity"],
                        "receipt_evidence_available":
                            demand["receipt_evidence_available"],
                        "warehouse_stock_is_recorded_not_verified": True,
                        "same_stock_may_match_multiple_centres": True,
                    },
                    "next_step": (
                        "Verify receipt records and outstanding deliveries. "
                        "Verify physical stock, existing commitments, item "
                        "condition, location, transport feasibility, and "
                        "transfer authority. Compare competing demands "
                        "before deciding whether any allocation is possible."
                    ),
                })

            if remaining_need > 0:
                unmatched_demand.append({
                    "centre": demand["centre"],
                    "request_id": demand["request_id"],
                    "item": item,
                    "unmatched_quantity": remaining_need,
                    "status": (
                        "No additional recorded matching stock found; "
                        "candidate stock may cover part of the shortfall"
                        if candidate_warehouses
                        else "No recorded matching stock found"
                    ),
                })

    return {
        "resource_matches": matches,
        "unmatched_demand": unmatched_demand,
        "resource_matching_note": (
            "Matches are potential leads based on recorded stock, not "
            "confirmed available resources. Recorded quantities may be "
            "outdated, duplicated, committed elsewhere, or physically "
            "unavailable. The same stock may appear as a candidate for "
            "multiple centres, so matches must not be summed across "
            "centres or treated as allocations. Missing receipt evidence "
            "does not prove non-delivery. Verify warehouse records, "
            "physical stock, existing commitments, and transfer authority "
            "before making allocation decisions."
        ),
    }


def get_investigation(scenario_id="wayanad"):
    """Investigate records belonging to one selected scenario."""

    allowed_scenarios = {"wayanad", "assam"}

    if scenario_id not in allowed_scenarios:
        raise ValueError(f"Unsupported scenario: {scenario_id}")

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

    WITH c, r, d, rec, route, incident, w, s
    WHERE c.scenario_id = $scenario_id
      AND r.scenario_id = $scenario_id
      AND d.scenario_id = $scenario_id
      AND rec.scenario_id = $scenario_id

    RETURN
        c.name AS community,
        r.id AS request_id,
        r.item AS item,
        r.quantity AS requested,
        d.id AS delivery_id,
        d.reported_quantity AS reported,
        rec.id AS receipt_id,
        rec.confirmed_quantity AS confirmed,
        route.name AS route,
        route.status AS route_status,
        incident.description AS incident,
        incident.status AS incident_status,
        w.name AS warehouse,
        s.quantity AS stock
    """

    result = graph.query(query, {"scenario_id": scenario_id})

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
        receipt_id,
        confirmed,
        route,
        route_status,
        incident,
        incident_status,
        warehouse,
        stock,
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
            "requested_quantity": requested,
        },
        {
            "type": "delivery_record",
            "reference": delivery_id,
            "reported_quantity": reported,
            "quantity_is_reported_not_independently_verified": True,
        },
        {
            "type": "receipt",
            "reference": receipt_id,
            "confirmed_quantity": confirmed,
        },
    ]

    if route:
        evidence.append({
            "type": "transport_route",
            "name": route,
            "recorded_status": route_status,
        })

    if incident:
        evidence.append({
            "type": "incident_report",
            "description": incident,
            "recorded_status": incident_status,
            "simulated_demo_evidence": incident_is_simulated,
            "causal_link_verified": False,
        })

    if warehouse or stock is not None:
        evidence.append({
            "type": "warehouse_stock",
            "reference": None,
            "warehouse": warehouse,
            "item": item,
            "recorded_quantity": stock,
            "physical_stock_verified": False,
            "source_record_reference_available": False,
            "verification_required": True,
        })

    leads = []

    if gap is not None and gap > 0:
        leads.append({
            "title": "Unconfirmed delivery quantity",
            "finding": (
                f"{gap} {item} remain unconfirmed by the available receipt."
            ),
            "status": "Unresolved",
            "next_step": "Request additional receipts or handover records.",
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
            ),
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
            ),
        })

    recommended_actions = [
        "Request additional receipt or handover evidence.",
        "Ask the delivery organisation to reconcile the reported quantity.",
        "Review original delivery records and timestamps.",
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

    WITH c, r, d, rec
    WHERE c.scenario_id = $scenario_id
      AND r.scenario_id = $scenario_id
      AND d.scenario_id = $scenario_id
      AND rec.scenario_id = $scenario_id

    RETURN
        c.name AS centre,
        c.location AS location,
        r.id AS request_id,
        r.item AS item,
        r.quantity AS requested,
        d.id AS delivery_id,
        d.reported_quantity AS reported,
        rec.confirmed_quantity AS confirmed
    ORDER BY centre, request_id
    """

    cross_centre_result = graph.query(
        cross_centre_query,
        {"scenario_id": scenario_id},
    )

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
            centre_confirmed,
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
            "confirmed": centre_confirmed,
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
                    ),
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
                    ),
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
                    ),
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
                    ),
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
                            lower["centre"],
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
                        ),
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
            "deliveries before concluding that an imbalance exists.",
        ])

    resource_matching = get_resource_matches(graph, scenario_id)

    action_plans = build_action_plans(
        request_id=request_id,
        delivery_id=delivery_id,
        receipt_id=receipt_id,
        item=item,
        gap=gap,
        warehouse=warehouse,
        stock=stock,
        route=route,
        route_status=route_status,
        incident_is_simulated=incident_is_simulated,
        evidence=evidence,
    )

    return {
        "scenario_id": scenario_id,
        "case_id": request_id,
        "community": community,
        "request_id": request_id,
        "item": item,
        "requested": requested,
        "requested_quantity": requested,
        "delivery_id": delivery_id,
        "reported": reported,
        "reported_delivered": reported,
        "receipt_id": receipt_id,
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
        "action_plans": action_plans,
        "cross_centre_findings": cross_centre_findings,
        "cross_centre_actions": cross_centre_actions,
        "resource_matches": resource_matching["resource_matches"],
        "unmatched_demand": resource_matching["unmatched_demand"],
        "resource_matching_note": resource_matching["resource_matching_note"],
        "ai_generated": False,
    }
