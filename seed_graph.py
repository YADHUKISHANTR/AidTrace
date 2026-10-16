
from falkordb import FalkorDB

# Connect to the local database
db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("aidtrace")

# Create the community
graph.query("""
MERGE (c:Community {name: 'Greenfield'})
SET c.location = 'Demo Region'

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

print("AidTrace demo graph created successfully!")

# Check what was stored
result = graph.query("""
MATCH (n)
RETURN labels(n) AS type, n
""")

for row in result.result_set:
    print(row)
