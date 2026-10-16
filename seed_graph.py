
from falkordb import FalkorDB

db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("aidtrace")

# --------------------------------------------------
# EXISTING CASE: Wayanad
# Keep the original request, delivery, and receipt.
# --------------------------------------------------

graph.query("""
MERGE (c:Community {name: 'Wayanad'})
SET c.location = 'Wayanad, Kerala'

MERGE (r:ReliefRequest {id: 'REQ-001'})
SET r.item = 'Water kits',
    r.quantity = 120,
    r.status = 'Open'

MERGE (d:Delivery {id: 'DEL-001'})
SET d.reported_quantity = 120,
    d.status = 'Reported delivered'

MERGE (rec:Receipt {id: 'REC-001'})
SET rec.confirmed_quantity = 70,
    rec.status = 'Partial confirmation'

MERGE (c)-[:HAS_REQUEST]->(r)
MERGE (r)-[:FULFILLED_BY]->(d)
MERGE (d)-[:HAS_RECEIPT]->(rec)
""")

# --------------------------------------------------
# NEW FEATURE: Cross-centre discrepancy detection
# Synthetic demonstration data only.
# --------------------------------------------------

graph.query("""
MERGE (centreA:Community {name: 'Centre A'})
SET centreA.location = 'Synthetic demo location A'

MERGE (requestA:ReliefRequest {id: 'REQ-A-001'})
SET requestA.item = 'Water kits',
    requestA.quantity = 100,
    requestA.status = 'Open',
    requestA.synthetic_demo = true

MERGE (deliveryA:Delivery {id: 'DEL-A-001'})
SET deliveryA.reported_quantity = 140,
    deliveryA.status = 'Reported delivered',
    deliveryA.synthetic_demo = true

MERGE (receiptA:Receipt {id: 'REC-A-001'})
SET receiptA.confirmed_quantity = 140,
    receiptA.status = 'Confirmed in synthetic demo',
    receiptA.synthetic_demo = true

MERGE (centreA)-[:HAS_REQUEST]->(requestA)
MERGE (requestA)-[:FULFILLED_BY]->(deliveryA)
MERGE (deliveryA)-[:HAS_RECEIPT]->(receiptA)

MERGE (centreB:Community {name: 'Centre B'})
SET centreB.location = 'Synthetic demo location B'

MERGE (requestB:ReliefRequest {id: 'REQ-B-001'})
SET requestB.item = 'Water kits',
    requestB.quantity = 100,
    requestB.status = 'Open',
    requestB.synthetic_demo = true

MERGE (deliveryB:Delivery {id: 'DEL-B-001'})
SET deliveryB.reported_quantity = 60,
    deliveryB.status = 'Reported delivered',
    deliveryB.synthetic_demo = true

MERGE (receiptB:Receipt {id: 'REC-B-001'})
SET receiptB.confirmed_quantity = 60,
    receiptB.status = 'Confirmed in synthetic demo',
    receiptB.synthetic_demo = true

MERGE (centreB)-[:HAS_REQUEST]->(requestB)
MERGE (requestB)-[:FULFILLED_BY]->(deliveryB)
MERGE (deliveryB)-[:HAS_RECEIPT]->(receiptB)
""")

print("AidTrace graph seeded successfully.")
print("Existing Wayanad case preserved.")
print("Synthetic cross-centre demo records added.")

# Show all communities and their requests.
result = graph.query("""
MATCH (c:Community)-[:HAS_REQUEST]->(r:ReliefRequest)
RETURN c.name AS centre,
       r.id AS request_id,
       r.item AS item,
       r.quantity AS requested_quantity
ORDER BY centre
""")

for row in result.result_set:
    print(row)
