
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
        community, request_id, item, requested, delivery_id,
        reported, confirmed, route, route_status, incident,
        incident_status, warehouse, stock
    ) = row

    # Keep missing quantities from causing a calculation error.
    gap = (
        max(reported - confirmed, 0)
        if reported is not None and confirmed is not None
        else None
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
            "reported_quantity": reported
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
            "simulated_demo_evidence": (
                "SIMULATED" in incident.upper()
                or incident_status == "Simulated"
            )
        })

    if warehouse or stock is not None:
        evidence.append({
            "type": "warehouse_stock",
            "warehouse": warehouse,
            "item": item,
            "recorded_quantity": stock
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
            "finding": f"The recorded status of {route} is Disrupted.",
            "status": "Unverified",
            "next_step": (
                "Compare dispatch times, route records, and handover evidence."
            )
        })

    if stock is not None and stock > 0:
        leads.append({
            "title": "Recorded warehouse stock",
            "finding": (
                f"{stock} {item} are recorded at {warehouse}."
            ),
            "status": "Unverified",
            "next_step": (
                "Verify current stock, allocation, and availability."
            )
        })

    recommended_actions = [
        "Request additional receipt or handover evidence.",
        "Ask the delivery organisation to reconcile the reported quantity.",
        "Review dispatch records and delivery timestamps."
    ]

    if route_status == "Disrupted":
        recommended_actions.append(
            "Check whether the simulated route disruption affected this delivery."
        )

    if stock is not None and stock > 0:
        recommended_actions.append(
            f"Verify the availability and allocation of the {stock} "
            f"recorded kits at {warehouse}."
        )

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
        "warehouse": warehouse,
        "stock": stock,
        "status": "Needs human review",
        "assessment": (
            "An evidence gap is not proof of loss, theft, or non-delivery. "
            "Findings require verification."
        ),
        "evidence": evidence,
        "leads": leads,
        "leads_to_investigate": leads,
        "recommended_actions": recommended_actions,
        "ai_generated": False
    }
