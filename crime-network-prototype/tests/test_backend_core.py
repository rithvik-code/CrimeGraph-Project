from backend.services.graph import CaseGraph
from backend.services.neo4j_service import _cypher_relation_name


def test_graph_loads_structured_case_and_reports_stats():
    graph = CaseGraph()
    graph.load_cases([{
        "case_id": "case-1",
        "person": "Alice Example",
        "phone": "+1 555 0100",
        "connected_to": "Bob Example",
        "relation_note": "payment transfer",
    }])

    stats = graph.stats()
    assert stats["persons_identified"] == 2
    assert stats["phones_traced"] == 1
    assert stats["total_relations"] == 2
    assert any(edge["priority"] == "high" for edge in graph.all_edges_summary())


def test_relationship_names_are_safe_cypher_tokens():
    assert _cypher_relation_name("financial link") == "FINANCIAL_LINK"
    assert _cypher_relation_name("x` MATCH (n) DETACH DELETE n") == "X_MATCH_N_DETACH_DELETE_N"
    assert "`" not in _cypher_relation_name("unsafe`value")
