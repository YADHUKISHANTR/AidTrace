
from falkordb import FalkorDB


ALLOWED_SCENARIOS = {"wayanad", "assam"}


def get_graph_evidence(scenario_id="wayanad"):
    """
    Retrieve nodes and relationships for one AidTrace scenario.
    This function reads graph data and does not modify it.
    """

    if not isinstance(scenario_id, str):
        raise ValueError("Invalid scenario ID.")

    scenario_id = scenario_id.strip().lower()

    if scenario_id not in ALLOWED_SCENARIOS:
        raise ValueError("Invalid scenario ID.")

    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("aidtrace")

    node_query = """
    MATCH (n)
    WHERE n.scenario_id = $scenario_id
    RETURN
        id(n) AS internal_id,
        labels(n) AS labels,
        properties(n) AS properties
    """

    node_result = graph.query(
        node_query,
        {"scenario_id": scenario_id}
    )

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
    WHERE source.scenario_id = $scenario_id
      AND target.scenario_id = $scenario_id
    RETURN
        id(source) AS source_id,
        type(r) AS relationship_type,
        properties(r) AS relationship_properties,
        id(target) AS target_id
    """

    relationship_result = graph.query(
        relationship_query,
        {"scenario_id": scenario_id}
    )

    relationships = []

    for row in relationship_result.result_set:
        source_id, relationship_type, properties, target_id = row

        source_id = str(source_id)
        target_id = str(target_id)

        # Keep only connections between nodes returned for this scenario.
        if source_id not in node_ids or target_id not in node_ids:
            continue

        relationships.append({
            "source": source_id,
            "type": relationship_type,
            "properties": properties or {},
            "target": target_id
        })

    return {
        "scenario_id": scenario_id,
        "nodes": nodes,
        "relationships": relationships,
        "node_count": len(nodes),
        "relationship_count": len(relationships)
    }
