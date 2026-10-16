from falkordb import FalkorDB

db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("aidtrace")

graph.query("""
MATCH (c:Community)-[:HAS_REQUEST]->(
    r:ReliefRequest {id: 'REQ-001'}
)
SET c.name = 'Wayanad',
    c.location = 'Wayanad, Kerala'

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

print("AidTrace Wayanad demo graph created successfully!")

result = graph.query("""
MATCH (n)
RETURN labels(n) AS type, n
""")

for row in result.result_set:
    print(row)