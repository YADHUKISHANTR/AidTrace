from falkordb import FalkorDB

# Connect to our local FalkorDB server
db = FalkorDB(host="localhost", port=6379)

# Select the graph that AidTrace will use
graph = db.select_graph("aidtrace")

# Run a simple test query
result = graph.query(
    "RETURN 'AidTrace connected to FalkorDB!' AS message"
)

print(result.result_set)