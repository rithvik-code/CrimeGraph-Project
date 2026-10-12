"""
CrimeGraph AI — FastAPI Routes

Endpoints:
  GET  /api/stats          — Dashboard statistics
  GET  /api/graph-data     — Cytoscape.js graph elements
  GET  /api/geo-data       — Geocoded graph data for map view
  GET  /api/connections    — Edge summary with confidence scores
  GET  /api/anomalies      — Detected anomalies
  GET  /api/node/{id}      — Node details
  GET  /api/path           — Shortest path between two nodes
  GET  /api/neo4j-stats    — Advanced Neo4j graph statistics
  POST /api/extract        — Extract entities from text
  POST /api/upload-text    — Extract from pasted text
  POST /api/upload-file    — Extract from uploaded file
  POST /api/load-cases     — Load structured case records
  POST /api/reset          — Reset graph to initial state
"""

import io
import csv
import json
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.config import MAX_UPLOAD_BYTES, MAX_TEXT_CHARS
from backend.services.graph import CaseGraph
from backend.services.ner import extract_entities, extract_relations
from backend.services.entity_resolution import deduplicate_all
from backend.services.geocoding import geocode_all_locations, get_map_bounds

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# ── Global graph instance (starts empty — user provides data) ──
graph = CaseGraph()


# ── Helper: persist to PostgreSQL + Neo4j ────────────────

async def _persist_extraction(entities: dict, relations: list, label: str):
    """Save extraction to PostgreSQL and sync to Neo4j."""
    # 1. Save to PostgreSQL
    try:
        from backend.services.db_service import (
            upsert_entities_batch, upsert_relations_batch,
            add_cooccurrence_links
        )
        from backend.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            await upsert_entities_batch(session, entities, source_label=label)
            await upsert_relations_batch(session, relations, source_label=label)
            await add_cooccurrence_links(session, entities, source_label=label)
            await session.commit()
        logger.info(f"Persisted extraction '{label}' to PostgreSQL")
    except Exception as e:
        logger.warning(f"PostgreSQL persist failed: {e}")

    # 2. Sync to Neo4j
    try:
        from backend.services.neo4j_service import sync_graph_to_neo4j
        await sync_graph_to_neo4j(graph)
        logger.info("Synced graph to Neo4j")
    except Exception as e:
        logger.warning(f"Neo4j sync failed: {e}")


# ── Dashboard ─────────────────────────────────────────────
@router.get("/stats")
async def get_stats():
    # Try PostgreSQL first for accuracy
    try:
        from backend.services.db_service import get_db_stats
        from backend.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            db_stats = await get_db_stats(session)
            if db_stats["total_entities"] > 0:
                return db_stats
    except Exception:
        pass
    return graph.stats()


# ── Graph ─────────────────────────────────────────────────
@router.get("/graph-data")
async def get_graph_data():
    return graph.to_cytoscape_json()


@router.get("/geo-data")
async def get_geo_data():
    """Return graph data with geocoded coordinates for map view."""
    cytoscape = graph.to_cytoscape_json()

    location_names = [
        n["data"]["id"]
        for n in cytoscape
        if n.get("data", {}).get("nodeType") == "location"
    ]

    geocoded = geocode_all_locations(location_names)
    bounds = get_map_bounds(geocoded)

    adj = _build_adjacency(cytoscape)
    geo_nodes = []
    for item in cytoscape:
        if "source" in item.get("data", {}):
            geo_nodes.append(item)
        else:
            node = item.copy()
            node_id = node["data"]["id"]
            node_type = node["data"].get("nodeType", "person")

            if node_type == "location" and node_id in geocoded:
                coords = geocoded[node_id]
                node["data"]["lat"] = coords["lat"]
                node["data"]["lng"] = coords["lng"]
                node["data"]["geocoded"] = True

            elif node_type != "location":
                parent_loc = _find_nearest_location(node_id, cytoscape, geocoded, adj)
                if parent_loc:
                    coords = geocoded[parent_loc]
                    import hashlib
                    h = int(hashlib.md5(node_id.encode()).hexdigest()[:8], 16)
                    offset_lat = ((h % 100) - 50) * 0.008
                    offset_lng = (((h >> 8) % 100) - 50) * 0.008
                    node["data"]["lat"] = coords["lat"] + offset_lat
                    node["data"]["lng"] = coords["lng"] + offset_lng
                    node["data"]["geocoded"] = True

            geo_nodes.append(node)

    return {
        "elements": geo_nodes,
        "bounds": bounds,
        "geocoded_locations": {k: v for k, v in geocoded.items()},
    }


def _build_adjacency(cytoscape: list) -> dict:
    adj = {}
    for item in cytoscape:
        data = item.get("data", {})
        if "source" not in data:
            continue
        src, tgt = data["source"], data["target"]
        adj.setdefault(src, set()).add(tgt)
        adj.setdefault(tgt, set()).add(src)
    return adj


def _find_nearest_location(node_id: str, cytoscape: list, geocoded: dict, adj: dict = None) -> str:
    if adj is None:
        adj = _build_adjacency(cytoscape)

    type_lookup = {
        item["data"]["id"]: item["data"].get("nodeType")
        for item in cytoscape
        if "source" not in item.get("data", {})
    }

    for neighbor in adj.get(node_id, set()):
        if type_lookup.get(neighbor) == "location" and neighbor in geocoded:
            return neighbor

    for neighbor in adj.get(node_id, set()):
        for hop2 in adj.get(neighbor, set()):
            if hop2 == node_id:
                continue
            if type_lookup.get(hop2) == "location" and hop2 in geocoded:
                return hop2

    return None


@router.get("/connections")
async def get_connections():
    return graph.edges_summary()


@router.get("/all-edges")
async def get_all_edges():
    """Return ALL edges with types and confidence for analytics charts."""
    return graph.all_edges_summary()


@router.get("/anomalies")
async def get_anomalies():
    return graph.detect_anomalies()


@router.get("/node/{node_id}")
async def get_node_details(node_id: str):
    details = graph.get_node_details(node_id)
    if not details:
        raise HTTPException(status_code=404, detail="Node not found")
    return details


@router.get("/path")
async def get_path(source: str, target: str):
    # Try Neo4j first for advanced graph queries
    try:
        from backend.services.neo4j_service import neo4j_shortest_path
        path = await neo4j_shortest_path(source, target)
        if path:
            return {"path": path, "found": True, "source": "neo4j"}
    except Exception:
        pass
    # Fall back to NetworkX
    path = graph.get_shortest_path(source, target)
    return {"path": path, "found": len(path) > 0, "source": "networkx"}


@router.get("/neo4j-stats")
async def get_neo4j_stats():
    """Advanced graph statistics from Neo4j GDS."""
    try:
        from backend.services.neo4j_service import neo4j_advanced_stats
        return await neo4j_advanced_stats()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {str(e)[:100]}")


# ── Extraction ────────────────────────────────────────────
@router.post("/extract")
async def extract_from_text_endpoint(text: str = Form(...), source_name: str = Form("manual")):
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")
    if len(text) > MAX_TEXT_CHARS:
        raise HTTPException(status_code=413, detail=f"Text exceeds the {MAX_TEXT_CHARS:,}-character limit")

    entities = extract_entities(text)
    entities = deduplicate_all(entities)
    relations = extract_relations(text, entities)

    label = f"extract-{abs(hash(text)) % 100000}"
    graph.load_extraction(entities, relations, source_label=label)

    # Persist to databases
    await _persist_extraction(entities, relations, label)

    anomalies = graph.detect_anomalies()

    return {
        "extraction_id": label,
        "entities": entities,
        "relations": relations,
        "anomalies": anomalies,
        "stats": graph.stats(),
    }


@router.post("/upload-text")
async def upload_text_endpoint(data: dict):
    text = data.get("text", "")
    source_name = data.get("source_name", "pasted_text")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")
    if not isinstance(text, str):
        raise HTTPException(status_code=422, detail="text must be a string")
    if len(text) > MAX_TEXT_CHARS:
        raise HTTPException(status_code=413, detail=f"Text exceeds the {MAX_TEXT_CHARS:,}-character limit")

    entities = extract_entities(text)
    entities = deduplicate_all(entities)
    relations = extract_relations(text, entities)

    label = f"paste-{abs(hash(text)) % 100000}"
    graph.load_extraction(entities, relations, source_label=label)

    # Persist to databases
    await _persist_extraction(entities, relations, label)

    anomalies = graph.detect_anomalies()

    return {
        "success": True,
        "results": [{
            "type": "narrative",
            "label": source_name,
            "entities": entities,
            "relations": relations,
        }],
        "anomalies": anomalies,
        "stats": graph.stats(),
    }


@router.post("/upload-file")
async def upload_file_endpoint(file: UploadFile = File(...)):
    filename = (file.filename or "unknown").lower()
    results = []

    try:
        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit")

        if filename.endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            cases = data if isinstance(data, list) else [data]
            graph.load_cases(cases)
            results.append({"type": "structured", "count": len(cases), "label": filename})

            # Persist structured cases
            label = f"file-{filename}"
            await _persist_extraction(
                {"people": [c.get("person", "") for c in cases if c.get("person")],
                 "phones": list(set(c.get("phone", "") for c in cases if c.get("phone"))),
                 "locations": list(set(c.get("location", "") for c in cases if c.get("location"))),
                 "vehicles": list(set(c.get("vehicle", "") for c in cases if c.get("vehicle"))),
                 "financial": list(set(filter(None,
                     [c.get("financial_from", "") for c in cases] +
                     [c.get("financial_to", "") for c in cases])))},
                [],
                label,
            )

        elif filename.endswith(".csv"):
            stream = io.StringIO(content.decode("utf-8"))
            reader = csv.DictReader(stream)
            cases = []
            for i, row in enumerate(reader):
                case = {
                    "case_id": row.get("case_id", f"upload-{i+1}"),
                    "person": row.get("person", ""),
                    "phone": row.get("phone", None),
                    "location": row.get("location", None),
                    "vehicle": row.get("vehicle", None),
                    "connected_to": row.get("connected_to", None),
                    "relation_note": row.get("relation_note", ""),
                    "financial_from": row.get("financial_from", None),
                    "financial_to": row.get("financial_to", None),
                }
                if case["person"]:
                    cases.append(case)
            graph.load_cases(cases)
            results.append({"type": "structured", "count": len(cases), "label": filename})

        elif filename.endswith((".txt", ".md", ".log")):
            text = content.decode("utf-8")
            entities = extract_entities(text)
            entities = deduplicate_all(entities)
            relations = extract_relations(text, entities)

            label = f"file-{filename}"
            graph.load_extraction(entities, relations, source_label=label)

            # Persist narrative extraction
            await _persist_extraction(entities, relations, label)

            results.append({
                "type": "narrative",
                "label": filename,
                "entities": entities,
                "relations": relations,
            })

        else:
            raise HTTPException(status_code=415, detail="Unsupported file type. Use .json, .csv, .txt, .md, or .log")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("File upload processing failed")
        raise HTTPException(status_code=400, detail="Unable to process the uploaded file")

    anomalies = graph.detect_anomalies()

    return {
        "success": True,
        "results": results,
        "anomalies": anomalies,
        "stats": graph.stats(),
    }


@router.post("/load-cases")
async def load_cases(data: dict):
    cases = data.get("cases", [])
    if not cases:
        raise HTTPException(status_code=400, detail="No cases provided")

    graph.load_cases(cases)

    # Persist
    label = "structured-load"
    entities = {
        "people": list(set(c.get("person", "") for c in cases if c.get("person"))),
        "phones": list(set(c.get("phone", "") for c in cases if c.get("phone"))),
        "locations": list(set(c.get("location", "") for c in cases if c.get("location"))),
        "vehicles": list(set(c.get("vehicle", "") for c in cases if c.get("vehicle"))),
        "financial": list(set(filter(None,
            [c.get("financial_from", "") for c in cases] +
            [c.get("financial_to", "") for c in cases]))),
    }
    await _persist_extraction(entities, [], label)

    return {
        "success": True,
        "loaded": len(cases),
        "stats": graph.stats(),
    }


@router.post("/reset")
async def reset_graph():
    global graph
    graph = CaseGraph()

    # Clear PostgreSQL and Neo4j
    try:
        from backend.services.db_service import reset_db
        from backend.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await reset_db(session)
        logger.info("PostgreSQL data cleared")
    except Exception as e:
        logger.warning(f"PostgreSQL reset failed: {e}")

    try:
        from backend.database import get_neo4j
        driver = get_neo4j()
        async with driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
        logger.info("Neo4j data cleared")
    except Exception as e:
        logger.warning(f"Neo4j reset failed: {e}")

    return {"status": "reset", "stats": graph.stats()}
