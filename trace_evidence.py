from falkordb import FalkorDB

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
    r.item AS item,
    d.reported_quantity AS reported,
    rec.confirmed_quantity AS confirmed,
    d.reported_quantity - rec.confirmed_quantity AS gap,
    route.name AS route,
    route.status AS route_status,
    incident.description AS incident,
    w.name AS warehouse,
    s.quantity AS stock_quantity
"""

result = graph.query(query)

for row in result.result_set:
    (
        community, item, reported, confirmed, gap,
        route, route_status, incident, warehouse, stock
    ) = row

    print("\n=== AidTrace Evidence Trace ===")
    print(f"Community: {community}")
    print(f"Item: {item}")
    print(f"Reported delivery: {reported}")
    print(f"Receipt-confirmed quantity: {confirmed}")
    print(f"Unconfirmed quantity: {gap}")

    print("\n--- Related evidence ---")
    print(f"Route: {route or 'No route found'}")
    print(f"Route status: {route_status or 'Unknown'}")
    print(f"Incident: {incident or 'No incident found'}")
    print(f"Warehouse: {warehouse or 'No warehouse found'}")
    print(f"Recorded stock: {stock if stock is not None else 'Unknown'}")

    print("\n--- Investigation assessment ---")
    if route_status == "Disrupted":
        print(
            "A simulated route disruption is recorded. "
            "Investigate whether it affected this delivery."
        )
    else:
        print("No disrupted route is confirmed in the connected evidence.")

    if stock is not None and stock > 0:
        print(
            "Potential stock is recorded. Verify its allocation "
            "and delivery feasibility."
        )

    print(
        "The discrepancy remains unresolved until further "
        "evidence is checked."
    )