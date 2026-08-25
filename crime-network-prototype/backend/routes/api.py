"""
CrimeGraph AI — FastAPI Routes

Endpoints:
  GET  /api/stats          — Dashboard statistics
  GET  /api/graph-data     — Cytoscape.js graph elements
  GET  /api/connections    — Edge summary with confidence scores
  GET  /api/anomalies      — Detected anomalies
  GET  /api/node/{id}      — Node details
  GET  /api/path           — Shortest path between two nodes
  POST /api/extract        — Extract entities from text
  POST /api/upload-text    — Extract from pasted text
  POST /api/upload-file    — Extract from uploaded file
  POST /api/load-cases     — Load structured case records
  POST /api/reset          — Reset graph to initial state
"""

import io
import csv
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.services.graph import CaseGraph
from backend.services.ner import extract_entities, extract_relations
from backend.services.entity_resolution import deduplicate_all

router = APIRouter(prefix="/api")

# ── Global graph instance (starts empty — user provides data) ──
graph = CaseGraph()


# ── Dashboard ─────────────────────────────────────────────
@router.get("/stats")
async def get_stats():
    return graph.stats()


# ── Graph ─────────────────────────────────────────────────
@router.get("/graph-data")
async def get_graph_data():
    return graph.to_cytoscape_json()


@router.get("/connections")
async def get_connections():
    return graph.edges_summary()


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
    path = graph.get_shortest_path(source, target)
    return {"path": path, "found": len(path) > 0}


# ── Extraction ────────────────────────────────────────────
@router.post("/extract")
async def extract_from_text_endpoint(text: str = Form(...), source_name: str = Form("manual")):
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")
    
    # Extract entities
    entities = extract_entities(text)
    
    # Deduplicate
    entities = deduplicate_all(entities)
    
    # Extract relations
    relations = extract_relations(text, entities)
    
    # Load into graph
    label = f"extract-{abs(hash(text)) % 100000}"
    graph.load_extraction(entities, relations, source_label=label)
    
    # Detect anomalies
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
    
    entities = extract_entities(text)
    entities = deduplicate_all(entities)
    relations = extract_relations(text, entities)
    
    label = f"paste-{abs(hash(text)) % 100000}"
    graph.load_extraction(entities, relations, source_label=label)
    
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
        
        if filename.endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            cases = data if isinstance(data, list) else [data]
            graph.load_cases(cases)
            results.append({"type": "structured", "count": len(cases), "label": filename})
        
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
        
        else:
            # Plain text — run through NER
            text = content.decode("utf-8")
            entities = extract_entities(text)
            entities = deduplicate_all(entities)
            relations = extract_relations(text, entities)
            
            label = f"file-{filename}"
            graph.load_extraction(entities, relations, source_label=label)
            results.append({
                "type": "narrative",
                "label": filename,
                "entities": entities,
                "relations": relations,
            })
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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
    return {
        "success": True,
        "loaded": len(cases),
        "stats": graph.stats(),
    }


@router.post("/reset")
async def reset_graph():
    global graph
    graph = CaseGraph()
    return {"status": "reset", "stats": graph.stats()}
