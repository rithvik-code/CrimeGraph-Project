"""
Anomaly Detection Service

Detects suspicious patterns in the entity-relationship graph:
  1. Hub anomalies — entities connected to an unusually high number of others
  2. Financial anomalies — circular money flows, rapid transfers
  3. Communication anomalies — frequent contacts between suspects
  4. Location anomalies — multiple suspects at same location
  5. Vehicle anomalies — shared vehicle access patterns
"""

import networkx as nx
from typing import Optional


def detect_anomalies(G: nx.Graph) -> list[dict]:
    """
    Run all anomaly detection algorithms on the graph.
    Returns list of anomaly dicts with type, description, entities, severity.
    """
    anomalies = []
    anomalies.extend(_detect_hubs(G))
    anomalies.extend(_detect_financial_chains(G))
    anomalies.extend(_detect_communication_clusters(G))
    anomalies.extend(_detect_location_convergence(G))
    anomalies.extend(_detect_vehicle_sharing(G))
    anomalies.extend(_detect_centrality_anomalies(G))
    return anomalies


def _detect_hubs(G: nx.Graph) -> list[dict]:
    """Detect entities connected to unusually many others (potential kingpins)."""
    anomalies = []
    person_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "person"]
    
    if not person_nodes:
        return anomalies
    
    degrees = {n: G.degree(n) for n in person_nodes}
    avg_degree = sum(degrees.values()) / len(degrees) if degrees else 0
    threshold = max(avg_degree * 1.8, 3)
    
    for node, degree in degrees.items():
        if degree >= threshold and degree > 3:
            neighbors = list(G.neighbors(node))
            anomalies.append({
                "anomaly_type": "hub_suspect",
                "description": f"{node} is connected to {degree} entities — unusually high connectivity suggests a central role in the network.",
                "entities_involved": [node] + neighbors[:5],
                "severity": "high" if degree >= threshold * 1.5 else "medium",
                "metric": {"degree": degree, "threshold": round(threshold, 1)},
            })
    
    return anomalies


def _detect_financial_chains(G: nx.Graph) -> list[dict]:
    """Detect circular financial flows or chains of transfers."""
    anomalies = []
    
    # Find financial subgraph
    financial_nodes = {n for n, d in G.nodes(data=True) if d.get("type") == "financial"}
    person_nodes = {n for n, d in G.nodes(data=True) if d.get("type") == "person"}
    
    # Check for people connected to multiple financial accounts
    for person in person_nodes:
        fin_neighbors = [n for n in G.neighbors(person) if n in financial_nodes]
        if len(fin_neighbors) >= 3:
            anomalies.append({
                "anomaly_type": "financial_hub",
                "description": f"{person} has access to {len(fin_neighbors)} financial accounts — potential money laundering.",
                "entities_involved": [person] + fin_neighbors,
                "severity": "high",
                "metric": {"account_count": len(fin_neighbors)},
            })
    
    # Check for circular transfers (person A -> person B -> person A via financial)
    for p1 in person_nodes:
        for p2 in person_nodes:
            if p1 >= p2:
                continue
            if G.has_edge(p1, p2):
                edge_data = G.edges[p1, p2]
                rels = edge_data.get("relations", set())
                if any("financial" in r for r in rels):
                    # Check if there's a return path
                    shared_financial = set(G.neighbors(p1)) & set(G.neighbors(p2)) & financial_nodes
                    if shared_financial:
                        anomalies.append({
                            "anomaly_type": "circular_finance",
                            "description": f"Mutual financial connection between {p1} and {p2} through shared accounts.",
                            "entities_involved": [p1, p2] + list(shared_financial),
                            "severity": "high",
                            "metric": {"shared_accounts": len(shared_financial)},
                        })
    
    return anomalies


def _detect_communication_clusters(G: nx.Graph) -> list[dict]:
    """Detect dense communication clusters."""
    anomalies = []
    
    # Find communication edges
    comm_edges = [
        (u, v) for u, v, d in G.edges(data=True)
        if any("communication" in r or "contact" in r for r in d.get("relations", set()))
    ]
    
    if len(comm_edges) >= 3:
        # Check if these form a clique
        comm_graph = nx.Graph()
        comm_graph.add_edges_from(comm_edges)
        
        cliques = list(nx.find_cliques(comm_graph))
        for clique in cliques:
            if len(clique) >= 3:
                anomalies.append({
                    "anomaly_type": "communication_cluster",
                    "description": f"Dense communication cluster: {', '.join(clique)} — all frequently communicating.",
                    "entities_involved": list(clique),
                    "severity": "medium",
                    "metric": {"cluster_size": len(clique)},
                })
    
    return anomalies


def _detect_location_convergence(G: nx.Graph) -> list[dict]:
    """Detect locations visited by multiple suspects."""
    anomalies = []
    
    location_nodes = {n for n, d in G.nodes(data=True) if d.get("type") == "location"}
    person_nodes = {n for n, d in G.nodes(data=True) if d.get("type") == "person"}
    
    for loc in location_nodes:
        visitors = [
            n for n in G.neighbors(loc)
            if n in person_nodes
        ]
        if len(visitors) >= 3:
            anomalies.append({
                "anomaly_type": "location_convergence",
                "description": f"{len(visitors)} suspects at {loc}: {', '.join(visitors)} — coordinated activity.",
                "entities_involved": [loc] + visitors,
                "severity": "high" if len(visitors) >= 4 else "medium",
                "metric": {"visitor_count": len(visitors)},
            })
    
    return anomalies


def _detect_vehicle_sharing(G: nx.Graph) -> list[dict]:
    """Detect multiple people using the same vehicle."""
    anomalies = []
    
    vehicle_nodes = {n for n, d in G.nodes(data=True) if d.get("type") == "vehicle"}
    person_nodes = {n for n, d in G.nodes(data=True) if d.get("type") == "person"}
    
    for vehicle in vehicle_nodes:
        users = [
            n for n in G.neighbors(vehicle)
            if n in person_nodes
        ]
        if len(users) >= 2:
            anomalies.append({
                "anomaly_type": "shared_vehicle",
                "description": f"Vehicle '{vehicle}' shared by: {', '.join(users)} — possible coordinated transport.",
                "entities_involved": [vehicle] + users,
                "severity": "medium",
                "metric": {"user_count": len(users)},
            })
    
    return anomalies


def _detect_centrality_anomalies(G: nx.Graph) -> list[dict]:
    """Detect nodes with high betweenness centrality (bridge nodes)."""
    anomalies = []
    person_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "person"]
    
    if len(person_nodes) < 3:
        return anomalies
    
    try:
        centrality = nx.betweenness_centrality(G)
    except Exception:
        return anomalies
    
    # Find person nodes with high centrality
    person_centrality = {n: centrality.get(n, 0) for n in person_nodes}
    if not person_centrality:
        return anomalies
    
    avg_centrality = sum(person_centrality.values()) / len(person_centrality)
    
    for node, cent in person_centrality.items():
        if cent > avg_centrality * 2 and cent > 0.1:
            anomalies.append({
                "anomaly_type": "bridge_node",
                "description": f"{node} has high betweenness centrality ({cent:.2f}) — acts as a bridge between network segments.",
                "entities_involved": [node],
                "severity": "medium",
                "metric": {"centrality": round(cent, 3)},
            })
    
    return anomalies
