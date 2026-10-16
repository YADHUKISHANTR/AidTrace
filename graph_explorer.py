
from falkordb import FalkorDB


def get_graph_evidence():

    #retrive real node and relationships from the adtrace falkoredb graph 
    # #this fuction reads graph data and not modify it
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("aidtrace")

    node_query = """
    MATCH (n)
    RETURN
        id(n) AS internal_id,
        labels(n) AS labels,
        properties(n) AS properties
    """

    node_result = graph.query(node_query)

    nodes = []
    node_ids = set()

    for row in node_result.result_set:
        internal_id, labels, properties = row
        node_id = str(internal_id)
        node_ids.add(node_id)

        nodes.append({
            "id": node_id,
            "labels": labels or [],
            "properties": properties or {}
        })

    relationship_query = """
    MATCH (source)-[r]->(target)
    RETURN
        id(source) AS source_id,
        type(r) AS relationship_type,
        properties(r) AS relationship_properties,
        id(target) AS target_id
    """

    relationship_result = graph.query(relationship_query)

    relationships = []

    for row in relationship_result.result_set:
        source_id, relationship_type, properties, target_id = row

        relationships.append({
            "source": str(source_id),
            "type": relationship_type,
            "properties": properties or {},
            "target": str(target_id)
        })

    return {
        "nodes": nodes,
        "relationships": relationships,
        "node_count": len(nodes),
        "relationship_count": len(relationships)
    }
