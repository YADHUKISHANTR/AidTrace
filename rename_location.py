
from falkordb import FalkorDB

db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("aidtrace")

# Rename the existing community without creating a duplicate.
graph.query("""
MATCH (c:Community)-[:HAS_REQUEST]->(r:ReliefRequest {id: 'REQ-001'})
SET c.name = 'Wayanad',
    c.location = 'Wayanad, Kerala'
""")

# Update the existing route and warehouse records.
graph.query("""
MATCH (route:Route {id: 'ROUTE-001'})
SET route.name = 'Thamarassery Ghat Road'
""")

graph.query("""
MATCH (w:Warehouse {id: 'WH-001'})
SET w.name = 'Kalpetta Relief Supply Warehouse'
""")

# Mark the incident clearly as simulated demo data.
graph.query("""
MATCH (incident:IncidentReport {id: 'INC-001'})
SET incident.description =
    'SIMULATED DEMO: temporary disruption on Thamarassery Ghat Road',
    incident.status = 'Simulated'
""")

# Verify the changes.
result = graph.query("""
MATCH (c:Community)-[:HAS_REQUEST]->(r:ReliefRequest {id: 'REQ-001'})
OPTIONAL MATCH (d:Delivery {id: 'DEL-001'})-[:TRANSPORTED_VIA]->(route:Route)
OPTIONAL MATCH (w:Warehouse {id: 'WH-001'})
RETURN c.name, c.location, route.name, w.name
""")

for row in result.result_set:
    print("Community:", row[0])
    print("Location:", row[1])
    print("Road:", row[2])
    print("Warehouse:", row[3])
