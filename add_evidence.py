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
# Stock information — Wayanad demonstration scenario
graph.query("""
MERGE (w:Warehouse {id: 'WH-001'})
SET w.name = 'Kalpetta Relief Supply Warehouse',
    w.item = 'Water kits',
    w.available_quantity = 20,
    w.scenario_id = 'wayanad'

MERGE (s:Supply {id: 'SUP-001'})
SET s.item = 'Water kits',
    s.quantity = 20,
    s.scenario_id = 'wayanad'

MERGE (w)-[:STORES]->(s)
""")

print("Additional simulated Kerala evidence added to AidTrace.")