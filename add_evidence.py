from falkordb import FalkorDB

db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("aidtrace")

#  stock information
graph.query("""
MERGE (w:Warehouse {id: 'WH-001'})
SET w.name = 'Kalpetta Relief Supply Warehouse',
    w.item = 'Water kits',
    w.available_quantity = 20

MERGE (s:Supply {id: 'SUP-001'})
SET s.item = 'Water kits',
    s.quantity = 20

MERGE (w)-[:STORES]->(s)
""")

# Add a route and a synthetic incident report
graph.query("""
MERGE (route:Route {id: 'ROUTE-001'})
SET route.name = 'Thamarassery Ghat Road',
    route.status = 'Disrupted'

MERGE (incident:IncidentReport {id: 'INC-001'})
SET incident.description =
    'SIMULATED DEMO: temporary disruption on Thamarassery Ghat Road',
    incident.status = 'Simulated'

MERGE (incident)-[:AFFECTS]->(route)

MERGE (d:Delivery {id: 'DEL-001'})
MERGE (d)-[:TRANSPORTED_VIA]->(route)
""")

print("Additional simulated Kerala evidence added to AidTrace.")