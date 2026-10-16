from falkordb import FalkorDB

# Connect to our local FalkorDB server
db = FalkorDB(host="localhost", port=6379)

graph = db.select_graph("aidtrace")

result = graph.query(
    "RETURN 'AidTrace connected to FalkorDB!' AS message"
)

print(result.result_set)