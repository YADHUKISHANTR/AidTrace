
from falkordb import FalkorDB
import json

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
    w.name AS warehouse,
    s.quantity AS stock
"""

result = graph.query(query)

if not result.result_set:
    print("No matching investigation found.")
    raise SystemExit(0)

row = result.result_set[0]

(
    community, request_id, item, requested, delivery_id,
    reported, confirmed, route, route_status, incident,
    warehouse, stock
) = row

gap = reported - confirmed

# Build the report from graph evidence.
report = {
    "case_id": request_id,
    "community": community,
    "item": item,
    "requested_quantity": requested,
    "reported_delivered": reported,
    "receipt_confirmed": confirmed,
    "unconfirmed_quantity": gap,
    "status": "Needs human review",
    "evidence": [
        {
            "type": "delivery_record",
            "reference": delivery_id,
            "reported_quantity": reported
        },
        {
            "type": "receipt",
            "confirmed_quantity": confirmed
        }
    ],
    "leads_to_investigate": [],
    "recommended_actions": []
}

if route:
    report["evidence"].append({
        "type": "route",
        "name": route,
        "status": route_status
    })

if incident:
    report["evidence"].append({
        "type": "incident_report",
        "description": incident
    })

if route_status == "Disrupted":
    report["leads_to_investigate"].append(
        "Check whether the route disruption affected this delivery."
    )

if stock is not None and stock > 0:
    report["leads_to_investigate"].append(
        f"Verify whether {stock} recorded kits at {warehouse} "
        "are available and unallocated."
    )

report["recommended_actions"] = [
    "Request or locate additional receipt and handover evidence.",
    "Ask the delivery organisation to reconcile the reported quantity.",
    "Check route and dispatch records before drawing conclusions."
]

print(json.dumps(report, indent=2))
