
from graph_explorer import get_graph_evidence


def test_graph_evidence_contains_real_nodes():
    data = get_graph_evidence()

    assert data["node_count"] > 0
    assert data["node_count"] == len(data["nodes"])


def test_graph_evidence_relationship_count_is_correct():
    data = get_graph_evidence()

    assert data["relationship_count"] == len(data["relationships"])


def test_relationships_reference_returned_nodes():
    data = get_graph_evidence()

    node_ids = {node["id"] for node in data["nodes"]}

    for relationship in data["relationships"]:
        assert relationship["source"] in node_ids
        assert relationship["target"] in node_ids
