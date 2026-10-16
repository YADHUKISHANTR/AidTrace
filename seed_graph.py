
from falkordb import FalkorDB

db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("aidtrace")

# --------------------------------------------------
# SCENARIO 1: Wayanad, Kerala
# Original investigation case.
# --------------------------------------------------

graph.query("""
MERGE (c:Community {name: 'Wayanad'})
SET c.location = 'Wayanad, Kerala',
    c.scenario_id = 'wayanad'

MERGE (r:ReliefRequest {id: 'REQ-001'})
SET r.item = 'Water kits',
    r.quantity = 120,
    r.status = 'Open',
    r.scenario_id = 'wayanad'

MERGE (d:Delivery {id: 'DEL-001'})
SET d.reported_quantity = 120,
    d.status = 'Reported delivered',
    d.scenario_id = 'wayanad'

MERGE (rec:Receipt {id: 'REC-001'})
SET rec.confirmed_quantity = 70,
    rec.status = 'Partial confirmation',
    rec.scenario_id = 'wayanad'

MERGE (c)-[:HAS_REQUEST]->(r)
MERGE (r)-[:FULFILLED_BY]->(d)
MERGE (d)-[:HAS_RECEIPT]->(rec)
""")

# --------------------------------------------------
# Wayanad supporting evidence
# Synthetic demonstration records only.
# --------------------------------------------------

graph.query("""
MERGE (route:Route {id: 'ROUTE-001'})
SET route.name = 'Relief delivery route',
    route.status = 'Disrupted',
    route.scenario_id = 'wayanad',
    route.synthetic_demo = true

MERGE (incident:Incident {id: 'INCIDENT-001'})
SET incident.description = 'Possible delivery delay requiring verification',
    incident.status = 'Unverified lead',
    incident.scenario_id = 'wayanad',
    incident.synthetic_demo = true

MERGE (warehouse:Warehouse {id: 'WAREHOUSE-WAYANAD-001'})
SET warehouse.name = 'Wayanad Relief Warehouse',
    warehouse.scenario_id = 'wayanad',
    warehouse.synthetic_demo = true

MERGE (supply:Supply {id: 'SUPPLY-WAYANAD-001'})
SET supply.item = 'Water kits',
    supply.quantity = 20,
    supply.scenario_id = 'wayanad',
    supply.synthetic_demo = true

MERGE (warehouse)-[:STORES]->(supply)
""")

# --------------------------------------------------
# Wayanad cross-centre discrepancy demonstration
# Synthetic data only.
# --------------------------------------------------

graph.query("""
MERGE (centreA:Community {name: 'Centre A'})
SET centreA.location = 'Synthetic demo location A',
    centreA.scenario_id = 'wayanad'

MERGE (requestA:ReliefRequest {id: 'REQ-A-001'})
SET requestA.item = 'Water kits',
    requestA.quantity = 100,
    requestA.status = 'Open',
    requestA.synthetic_demo = true,
    requestA.scenario_id = 'wayanad'

MERGE (deliveryA:Delivery {id: 'DEL-A-001'})
SET deliveryA.reported_quantity = 140,
    deliveryA.status = 'Reported delivered',
    deliveryA.synthetic_demo = true,
    deliveryA.scenario_id = 'wayanad'

MERGE (receiptA:Receipt {id: 'REC-A-001'})
SET receiptA.confirmed_quantity = 140,
    receiptA.status = 'Confirmed in synthetic demo',
    receiptA.synthetic_demo = true,
    receiptA.scenario_id = 'wayanad'

MERGE (centreA)-[:HAS_REQUEST]->(requestA)
MERGE (requestA)-[:FULFILLED_BY]->(deliveryA)
MERGE (deliveryA)-[:HAS_RECEIPT]->(receiptA)

MERGE (centreB:Community {name: 'Centre B'})
SET centreB.location = 'Synthetic demo location B',
    centreB.scenario_id = 'wayanad'

MERGE (requestB:ReliefRequest {id: 'REQ-B-001'})
SET requestB.item = 'Water kits',
    requestB.quantity = 100,
    requestB.status = 'Open',
    requestB.synthetic_demo = true,
    requestB.scenario_id = 'wayanad'

MERGE (deliveryB:Delivery {id: 'DEL-B-001'})
SET deliveryB.reported_quantity = 60,
    deliveryB.status = 'Reported delivered',
    deliveryB.synthetic_demo = true,
    deliveryB.scenario_id = 'wayanad'

MERGE (receiptB:Receipt {id: 'REC-B-001'})
SET receiptB.confirmed_quantity = 60,
    receiptB.status = 'Confirmed in synthetic demo',
    receiptB.synthetic_demo = true,
    receiptB.scenario_id = 'wayanad'

MERGE (centreB)-[:HAS_REQUEST]->(requestB)
MERGE (requestB)-[:FULFILLED_BY]->(deliveryB)
MERGE (deliveryB)-[:HAS_RECEIPT]->(receiptB)
""")

# --------------------------------------------------
# SCENARIO 2: Assam river flooding
# Synthetic demonstration data only.
# --------------------------------------------------

graph.query("""
MERGE (c:Community {name: 'Assam Community A'})
SET c.location = 'Synthetic demo location, Assam',
    c.scenario_id = 'assam',
    c.synthetic_demo = true

MERGE (r:ReliefRequest {id: 'ASSAM-REQ-001'})
SET r.item = 'Emergency food packs',
    r.quantity = 200,
    r.status = 'Open',
    r.scenario_id = 'assam',
    r.synthetic_demo = true

MERGE (d:Delivery {id: 'ASSAM-DEL-001'})
SET d.reported_quantity = 200,
    d.status = 'Reported delivered',
    d.scenario_id = 'assam',
    d.synthetic_demo = true

MERGE (rec:Receipt {id: 'ASSAM-REC-001'})
SET rec.confirmed_quantity = 150,
    rec.status = 'Partial confirmation',
    rec.scenario_id = 'assam',
    rec.synthetic_demo = true

MERGE (warehouse:Warehouse {id: 'WAREHOUSE-ASSAM-001'})
SET warehouse.name = 'Assam Relief Warehouse',
    warehouse.scenario_id = 'assam',
    warehouse.synthetic_demo = true

MERGE (supply:Supply {id: 'SUPPLY-ASSAM-001'})
SET supply.item = 'Emergency food packs',
    supply.quantity = 40,
    supply.scenario_id = 'assam',
    supply.synthetic_demo = true

MERGE (c)-[:HAS_REQUEST]->(r)
MERGE (r)-[:FULFILLED_BY]->(d)
MERGE (d)-[:HAS_RECEIPT]->(rec)
MERGE (warehouse)-[:STORES]->(supply)
""")

print("AidTrace graph seeded successfully.")
print("Wayanad scenario seeded.")
print("Synthetic Wayanad cross-centre records added.")
print("Synthetic Assam scenario seeded.")

# --------------------------------------------------
# VERIFY COMMUNITIES AND REQUESTS
# --------------------------------------------------

result = graph.query("""
MATCH (c:Community)-[:HAS_REQUEST]->(r:ReliefRequest)
RETURN c.name AS centre,
       r.id AS request_id,
       r.item AS item,
       r.quantity AS requested_quantity,
       c.scenario_id AS community_scenario,
       r.scenario_id AS request_scenario
ORDER BY community_scenario, centre
""")

for row in result.result_set:
    print(row)

# --------------------------------------------------
# VERIFY SUPPORTING RECORDS
# --------------------------------------------------

result = graph.query("""
MATCH (n)
WHERE n:Route OR n:Incident OR n:Warehouse OR n:Supply
RETURN labels(n) AS node_type,
       coalesce(n.name, n.id, n.description, n.item) AS record,
       n.scenario_id AS scenario_id
ORDER BY scenario_id, node_type
""")

for row in result.result_set:
    print(row)
