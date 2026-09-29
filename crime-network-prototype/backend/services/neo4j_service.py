"""
Neo4j Service — Graph database persistence and advanced graph queries.

Handles syncing the NetworkX graph to Neo4j, and running graph algorithms
like shortest path, community detection, and centrality analysis.
"""

import logging
from typing import Optional
from backend.database import get_neo4j

logger = logging.getLogger(__name__)


async def init_neo4j_constraints():
    """Create unique constraints and indexes in Neo4j."""
    driver = get_neo4j()
    async with driver.session() as session:
        # Create constraints for all entity types
        for label in ["Person", "Phone", "Location", "Vehicle", "Financial",
                       "Email", "Date", "IPAddress", "Address"]:
            try:
                await session.run(
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.name IS UNIQUE"
                )
            except Exception as e:
                logger.warning(f"Constraint creation for {label}: {e}")

        # Create indexes for faster lookups
        try:
            await session.run("CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.name)")
            await session.run("CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.entity_type)")
        except Exception as e:
            logger.warning(f"Index creation: {e}")

    logger.info("Neo4j constraints and indexes initialized")


# ── Label Mapping ───────────────────────────────────────

_TYPE_TO_LABEL = {
    "person": "Person",
    "phone": "Phone",
    "location": "Location",
    "vehicle": "Vehicle",
    "financial": "Financial",
    "email": "Email",
    "date": "Date",
    "ip_address": "IPAddress",
    "address": "Address",
}


# ── Sync NetworkX → Neo4j ───────────────────────────────

async def sync_graph_to_neo4j(graph):
    """Sync the entire NetworkX graph to Neo4j."""
    driver = get_neo4j()
    async with driver.session() as session:
        # Clear existing data
        await session.run("MATCH (n) DETACH DELETE n")

        # Create all nodes
        for node_id, data in graph.g.nodes(data=True):
            ntype = data.get("type", "person")
            label = _TYPE_TO_LABEL.get(ntype, "Entity")
            await session.run(
                f"MERGE (n:{label} {{name: $name}}) SET n.entity_type = $etype",
                name=node_id, etype=ntype,
            )

        # Create all edges
        for a, b, data in graph.g.edges(data=True):
            rels = sorted(data.get("relations", []))
            priority = data.get("priority", "supporting")
            for rel_type in rels:
                safe_rel = rel_type.upper().replace(" ", "_")
                await session.run(
                    f"MATCH (a {{name: $src}}), (b {{name: $tgt}}) "
                    f"MERGE (a)-[r:{safe_rel}]->(b) "
                    f"SET r.priority = $priority, r.relation_type = $rtype",
                    src=a, tgt=b, priority=priority, rtype=rel_type,
                )

    logger.info(f"Synced {graph.g.number_of_nodes()} nodes, {graph.g.number_of_edges()} edges to Neo4j")


# ── Sync Neo4j → NetworkX ──────────────────────────────

async def sync_neo4j_to_graph(graph):
    """Load graph data from Neo4j back into NetworkX (for recovery)."""
    driver = get_neo4j()
    async with driver.session() as session:
        # Load nodes
        result = await session.run("MATCH (n) RETURN n.name AS name, n.entity_type AS etype")
        node_count = 0
        async for record in result:
            name = record["name"]
            etype = record["etype"] or "person"
            graph._ensure_node(name, etype)
            node_count += 1

        # Load edges
        result = await session.run(
            "MATCH (a)-[r]->(b) WHERE a.name IS NOT NULL AND b.name IS NOT NULL "
            "RETURN a.name AS src, b.name AS tgt, r.relation_type AS rtype, r.priority AS priority"
        )
        edge_count = 0
        async for record in result:
            graph.link(
                record["src"], record["tgt"],
                record["rtype"] or "linked",
                priority=record["priority"] or "supporting",
            )
            edge_count += 1

    logger.info(f"Loaded {node_count} nodes, {edge_count} edges from Neo4j")
    return node_count, edge_count


# ── Advanced Graph Queries ──────────────────────────────

async def neo4j_shortest_path(source: str, target: str) -> list:
    """Find shortest path between two entities using Neo4j."""
    driver = get_neo4j()
    async with driver.session() as session:
        result = await session.run(
            "MATCH path = shortestPath((a {name: $src})-[*]-(b {name: $tgt})) "
            "RETURN [n IN nodes(path) | n.name] AS path_nodes, "
            "length(path) AS hops",
            src=source, tgt=target,
        )
        record = await result.single()
        if record:
            return record["path_nodes"]
    return []


async def neo4j_find_communities() -> list[list[str]]:
    """Find communities (clusters) in the graph using connected components."""
    driver = get_neo4j()
    async with driver.session() as session:
        result = await session.run(
            "CALL gds.dfs.stream({nodeProjection: '*', relationshipProjection: '*'}) "
            "YIELD nodeId, componentId "
            "RETURN gds.util.asNode(nodeId).name AS name, componentId "
            "ORDER BY componentId"
        )
        communities = {}
        async for record in result:
            cid = record["componentId"]
            name = record["name"]
            if cid not in communities:
                communities[cid] = []
            communities[cid].append(name)
        return list(communities.values())


async def neo4j_centrality() -> list[dict]:
    """Calculate betweenness centrality for all nodes."""
    driver = get_neo4j()
    async with driver.session() as session:
        result = await session.run(
            "CALL gds.betweenness.stream({nodeProjection: '*', relationshipProjection: '*'}) "
            "YIELD nodeId, score "
            "RETURN gds.util.asNode(nodeId).name AS name, score "
            "ORDER BY score DESC LIMIT 20"
        )
        return [{"name": r["name"], "centrality": round(r["score"], 4)} async for r in result]


async def neo4j_node_details(node_name: str) -> dict:
    """Get detailed info about a node from Neo4j."""
    driver = get_neo4j()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (n {name: $name})-[r]-(m) "
            "RETURN m.name AS neighbor, type(r) AS rel_type, r.priority AS priority "
            "ORDER BY r.priority DESC",
            name=node_name,
        )
        neighbors = []
        async for record in result:
            neighbors.append({
                "name": record["neighbor"],
                "relation": record["rel_type"],
                "priority": record["priority"],
            })

        # Get node type
        type_result = await session.run(
            "MATCH (n {name: $name}) RETURN labels(n)[0] AS label, n.entity_type AS etype",
            name=node_name,
        )
        type_record = await type_result.single()

    return {
        "name": node_name,
        "type": type_record["etype"] if type_record else "unknown",
        "neo4j_label": type_record["label"] if type_record else "Entity",
        "neighbors": neighbors,
        "degree": len(neighbors),
    }


async def neo4j_advanced_stats() -> dict:
    """Get advanced graph statistics from Neo4j."""
    driver = get_neo4j()
    stats = {}
    async with driver.session() as session:
        # Node count
        result = await session.run("MATCH (n) RETURN count(n) AS count")
        record = await result.single()
        stats["total_nodes"] = record["count"]

        # Edge count
        result = await session.run("MATCH ()-[r]->() RETURN count(r) AS count")
        record = await result.single()
        stats["total_edges"] = record["count"]

        # Density
        result = await session.run(
            "MATCH (n) WITH count(n) AS nodeCount "
            "MATCH ()-[r]->() WITH count(r) AS edgeCount, nodeCount "
            "RETURN CASE WHEN nodeCount > 1 "
            "THEN toFloat(edgeCount) / (nodeCount * (nodeCount - 1)) "
            "ELSE 0 END AS density"
        )
        record = await result.single()
        stats["density"] = round(record["density"], 4) if record else 0

        # Connected components
        try:
            result = await session.run(
                "CALL gds.dfs.stream({nodeProjection: '*', relationshipProjection: '*'}) "
                "YIELD componentId "
                "RETURN count(DISTINCT componentId) AS components"
            )
            record = await result.single()
            stats["connected_components"] = record["components"] if record else 1
        except Exception:
            stats["connected_components"] = 1

        # Average degree
        result = await session.run(
            "MATCH (n) OPTIONAL MATCH (n)-[r]-() "
            "RETURN avg(count(r)) AS avgDegree"
        )

    return stats
