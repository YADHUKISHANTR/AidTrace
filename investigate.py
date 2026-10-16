
from falkordb import FalkorDB

# Connect to AidTrace's graph
db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("aidtrace")

# Follow the evidence chain and calculate the discrepancy
query = """
MATCH (c:Community)-[:HAS_REQUEST]->(r:ReliefRequest)
      -[:FULFILLED_BY]->(d:Delivery)
      -[:HAS_RECEIPT]->(rec:Receipt)

RETURN
    c.name AS community,
    r.item AS item,
    r.quantity AS requested,
    d.reported_quantity AS reported_delivered,
    rec.confirmed_quantity AS confirmed,
    d.reported_quantity - rec.confirmed_quantity
        AS unconfirmed_quantity
"""

result = graph.query(query)

# Display the investigation result
for row in result.result_set:
    community, item, requested, reported, confirmed, unconfirmed = row

    print("\n--- AidTrace Investigation ---")
    print(f"Community: {community}")
    print(f"Item: {item}")
    print(f"Quantity requested: {requested}")
    print(f"Quantity reported delivered: {reported}")
    print(f"Quantity confirmed by receipt: {confirmed}")
    print(f"Quantity not yet confirmed: {unconfirmed}")
