"""
CrimeGraph AI — Investigator Productivity Suite Routes

Endpoints:
  GET    /api/timeline              — Timeline events
  POST   /api/notes                 — Add annotation note
  GET    /api/notes                 — Get notes (optional entity_id filter)
  DELETE /api/notes/{id}            — Delete note
  GET    /api/search?q=             — Fuzzy search across entities
  GET    /api/entity/{id}/profile   — Full entity profile
  GET    /api/risk-scores           — Risk scores for all persons
  POST   /api/generate-report       — Generate investigation report
  POST   /api/compare-cases         — Compare multiple extractions
  POST   /api/watchlist             — Add to watchlist
  GET    /api/watchlist             — Get watchlist
  DELETE /api/watchlist/{id}        — Remove from watchlist
  GET    /api/check-watchlist       — Check entities against watchlist
"""

import json
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


# ── Timeline ──────────────────────────────────────────────
@router.get("/timeline")
async def get_timeline():
    """Return all timeline events from the graph, sorted by date."""
    from backend.routes.api import graph
    events = []
    seen_dates = set()
    
    for node_id, data in graph.g.nodes(data=True):
        ntype = data.get("type", "unknown")
        # Extract dates connected to this node
        for neighbor in graph.g.neighbors(node_id):
            ndata = graph.g.nodes[neighbor]
            if ndata.get("type") == "date":
                date_str = neighbor
                edge_data = graph.g.edges[node_id, neighbor]
                rels = list(edge_data.get("relations", []))
                events.append({
                    "id": f"{node_id}-{date_str}",
                    "entity": node_id,
                    "entity_type": ntype,
                    "date": date_str,
                    "event_type": "mention",
                    "description": f"{node_id} — associated with date {date_str}",
                    "relations": rels,
                    "group": ntype,
                })
                seen_dates.add(date_str)
        
        # Also check if the node itself is a date
        if ntype == "date":
            # Find what entities reference this date
            connected_entities = []
            for neighbor in graph.g.neighbors(node_id):
                ndata2 = graph.g.nodes[neighbor]
                if ndata2.get("type") != "location":
                    connected_entities.append(neighbor)
            if connected_entities:
                events.append({
                    "id": f"date-{node_id}",
                    "entity": node_id,
                    "entity_type": "date",
                    "date": node_id,
                    "event_type": "event",
                    "description": f"Event on {node_id}: {', '.join(connected_entities[:5])}",
                    "relations": [],
                    "group": "date",
                })
    
    # Sort by date string (works for ISO format)
    events.sort(key=lambda e: e.get("date", ""))
    return events


# ── Notes & Annotations ───────────────────────────────────
@router.post("/notes")
async def add_note(data: dict):
    """Add an investigation note to an entity."""
    entity_id = data.get("entity_id", "")
    content = data.get("content", "")
    author = data.get("author", "Analyst")
    tag = data.get("tag", "general")
    entity_type = data.get("entity_type", "unknown")
    
    if not entity_id or not content:
        raise HTTPException(status_code=400, detail="entity_id and content required")
    
    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("INSERT INTO notes (entity_id, entity_type, author, content, tag) VALUES (:eid, :etype, :author, :content, :tag) RETURNING id, created_at"),
                {"eid": entity_id, "etype": entity_type, "author": author, "content": content, "tag": tag}
            )
            row = result.fetchone()
            await session.commit()
            return {"id": row[0], "created_at": str(row[1]), "entity_id": entity_id, "content": content, "author": author, "tag": tag}
    except Exception as e:
        logger.warning(f"Note insert failed: {e}")
        return {"id": -1, "entity_id": entity_id, "content": content, "author": author, "tag": tag, "note": "stored in-memory only"}


@router.get("/notes")
async def get_notes(entity_id: str = None):
    """Get investigation notes, optionally filtered by entity."""
    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            if entity_id:
                result = await session.execute(
                    text("SELECT id, entity_id, entity_type, author, content, tag, created_at FROM notes WHERE entity_id = :eid ORDER BY created_at DESC"),
                    {"eid": entity_id}
                )
            else:
                result = await session.execute(
                    text("SELECT id, entity_id, entity_type, author, content, tag, created_at FROM notes ORDER BY created_at DESC")
                )
            rows = result.fetchall()
            return [{"id": r[0], "entity_id": r[1], "entity_type": r[2], "author": r[3], "content": r[4], "tag": r[5], "created_at": str(r[6])} for r in rows]
    except Exception as e:
        logger.warning(f"Notes query failed: {e}")
        return []


@router.delete("/notes/{note_id}")
async def delete_note(note_id: int):
    """Delete an investigation note."""
    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM notes WHERE id = :id"), {"id": note_id})
            await session.commit()
        return {"status": "deleted", "id": note_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Smart Search ──────────────────────────────────────────
@router.get("/search")
async def search_entities(q: str = "", limit: int = 20):
    """Fuzzy search across all entities in the graph."""
    from backend.routes.api import graph
    from difflib import SequenceMatcher
    
    if not q.strip():
        return []
    
    q_lower = q.lower().strip()
    results = []
    
    for node_id, data in graph.g.nodes(data=True):
        ntype = data.get("type", "unknown")
        # Calculate similarity
        name_lower = node_id.lower()
        
        # Exact match gets highest score
        if q_lower == name_lower:
            score = 1.0
        elif q_lower in name_lower or name_lower in q_lower:
            score = 0.85
        else:
            score = SequenceMatcher(None, q_lower, name_lower).ratio()
        
        if score > 0.3:
            degree = graph.g.degree(node_id)
            results.append({
                "id": node_id,
                "type": ntype,
                "score": round(score, 3),
                "degree": degree,
                "color": {"person": "#ef4444", "phone": "#3b82f6", "location": "#10b981", "vehicle": "#f59e0b", "financial": "#a78bfa", "email": "#06b6d4", "date": "#f472b6", "ip_address": "#fb923c", "address": "#84cc16"}.get(ntype, "#999"),
            })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


# ── Entity Profile ────────────────────────────────────────
@router.get("/entity/{entity_id}/profile")
async def get_entity_profile(entity_id: str):
    """Get full profile for an entity: connections, notes, risk, timeline."""
    from backend.routes.api import graph
    from urllib.parse import unquote
    entity_id = unquote(entity_id)
    
    if not graph.g.has_node(entity_id):
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    
    data = graph.g.nodes[entity_id]
    ntype = data.get('type', 'unknown')
    
    connections = {}
    for neighbor in graph.g.neighbors(entity_id):
        ndata = graph.g.neighbors
        ndata2 = graph.g.nodes[neighbor]
        ntype_n = ndata2.get('type', 'unknown')
        edge_data = graph.g.edges[entity_id, neighbor]
        rels = list(edge_data.get('relations', []))
        score, breakdown = graph.confidence_score(entity_id, neighbor)
        if ntype_n not in connections:
            connections[ntype_n] = []
        connections[ntype_n].append({'name': neighbor, 'relations': rels, 'confidence': score, 'priority': edge_data.get('priority', 'supporting')})
    for k in connections:
        connections[k].sort(key=lambda x: x['confidence'], reverse=True)
    
    notes = []
    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import text as sqltext
        async with AsyncSessionLocal() as session:
            result = await session.execute(sqltext('SELECT id, author, content, tag, created_at FROM notes WHERE entity_id = :eid ORDER BY created_at DESC'), {'eid': entity_id})
            notes = [{'id': r[0], 'author': r[1], 'content': r[2], 'tag': r[3], 'created_at': str(r[4])} for r in result.fetchall()]
    except Exception:
        pass
    
    timeline = [neighbor for neighbor in graph.g.neighbors(entity_id) if graph.g.nodes[neighbor].get('type') == 'date']
    timeline.sort()
    
    return {
        'id': entity_id, 'type': ntype,
        'metadata': {k: v for k, v in data.items() if k != 'type'},
        'degree': graph.g.degree(entity_id),
        'connections': connections,
        'connection_count': sum(len(v) for v in connections.values()),
        'notes': notes, 'note_count': len(notes),
        'timeline': timeline, 'on_watchlist': False,
    }


# -- Risk Scoring
@router.get("/risk-scores")
async def get_risk_scores():
    import networkx as nx
    from backend.routes.api import graph
    person_nodes = [n for n, d in graph.g.nodes(data=True) if d.get("type") == "person"]
    if not person_nodes: return []
    try: centrality = nx.betweenness_centrality(graph.g)
    except: centrality = {n: 0 for n in graph.g.nodes()}
    financial_nodes = {n for n, d in graph.g.nodes(data=True) if d.get("type") == "financial"}
    location_nodes = {n for n, d in graph.g.nodes(data=True) if d.get("type") == "location"}
    scores = []
    for person in person_nodes:
        degree = graph.g.degree(person)
        cent = centrality.get(person, 0)
        fin_count = sum(1 for n in graph.g.neighbors(person) if n in financial_nodes)
        loc_neighbors = set(graph.g.neighbors(person)) & location_nodes
        shared_loc_count = sum(1 for loc in loc_neighbors if sum(1 for n2 in graph.g.neighbors(loc) if graph.g.nodes[n2].get("type") == "person") >= 2)
        from backend.services.anomaly import detect_anomalies
        anomalies = detect_anomalies(graph.g)
        anomaly_count = sum(1 for a in anomalies if person in a.get("entities_involved", []))
        max_degree = max(graph.g.degree(n) for n in person_nodes) if person_nodes else 1
        max_cent = max(centrality.get(n, 0) for n in person_nodes) if person_nodes else 0.01
        degree_score = (degree / max(max_degree, 1)) * 25
        cent_score = (cent / max(max_cent, 0.01)) * 25
        fin_score = min(fin_count * 10, 25)
        loc_score = min(shared_loc_count * 8, 15)
        anomaly_score = min(anomaly_count * 10, 10)
        raw_score = degree_score + cent_score + fin_score + loc_score + anomaly_score
        risk_score = min(100, max(0, round(raw_score)))
        level = "critical" if risk_score >= 80 else "high" if risk_score >= 60 else "medium" if risk_score >= 30 else "low"
        scores.append({"entity": person, "risk_score": risk_score, "level": level, "breakdown": {"connectivity": round(degree_score, 1), "centrality": round(cent_score, 1), "financial_access": round(fin_score, 1), "location_convergence": round(loc_score, 1), "anomaly_involvement": round(anomaly_score, 1)}, "metrics": {"degree": degree, "centrality": round(cent, 3), "financial_accounts": fin_count, "shared_locations": shared_loc_count, "anomalies": anomaly_count}})
    scores.sort(key=lambda x: x["risk_score"], reverse=True)
    return scores

# -- Report Export
@router.post("/generate-report")
async def generate_report(data: dict):
    """Generate a comprehensive professional investigation report as HTML."""
    from backend.routes.api import graph
    import networkx as nx

    title = data.get("title", "CrimeGraph AI Investigation Report")
    now_str = datetime.now().strftime("%B %d, %Y at %H:%M")
    stats = graph.stats()

    nodes = [(nid, nd.get("type", "unknown")) for nid, nd in graph.g.nodes(data=True)]
    edges_list = [(a, b, list(ed.get("relations", [])), ed.get("priority", "supporting"), ed.get("confidence", 0.8))
                  for a, b, ed in graph.g.edges(data=True)]

    # Risk scores
    risk_scores = []
    person_nodes = [n for n, d in graph.g.nodes(data=True) if d.get("type") == "person"]
    try:
        centrality = nx.betweenness_centrality(graph.g)
    except Exception:
        centrality = {n: 0 for n in graph.g.nodes()}
    financial_nodes = {n for n, d in graph.g.nodes(data=True) if d.get("type") == "financial"}
    location_nodes = {n for n, d in graph.g.nodes(data=True) if d.get("type") == "location"}
    for person in person_nodes:
        degree = graph.g.degree(person)
        cent = centrality.get(person, 0)
        fin_count = sum(1 for n in graph.g.neighbors(person) if n in financial_nodes)
        loc_neighbors = set(graph.g.neighbors(person)) & location_nodes
        shared_loc = sum(1 for loc in loc_neighbors if sum(1 for n2 in graph.g.neighbors(loc) if graph.g.nodes[n2].get("type") == "person") >= 2)
        try:
            from backend.services.anomaly import detect_anomalies
            anom_list = detect_anomalies(graph.g)
            anomaly_count = sum(1 for a in anom_list if person in a.get("entities_involved", []))
        except Exception:
            anomaly_count = 0
        max_degree = max(graph.g.degree(n) for n in person_nodes) if person_nodes else 1
        max_cent = max(centrality.get(n, 0) for n in person_nodes) if person_nodes else 0.01
        raw = (degree / max(max_degree, 1)) * 25 + (cent / max(max_cent, 0.01)) * 25 + min(fin_count * 10, 25) + min(shared_loc * 8, 15) + min(anomaly_count * 10, 10)
        score = min(100, max(0, round(raw)))
        level = "CRITICAL" if score >= 80 else "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW"
        risk_scores.append({"entity": person, "score": score, "level": level, "degree": degree, "centrality": round(cent, 3), "financial": fin_count, "shared_locations": shared_loc, "anomalies": anomaly_count})
    risk_scores.sort(key=lambda x: x["score"], reverse=True)

    # Timeline
    timeline_events = []
    for nid, nd in graph.g.nodes(data=True):
        if nd.get("type") == "date":
            connected = [nb for nb in graph.g.neighbors(nid) if graph.g.nodes[nb].get("type") != "location"]
            if connected:
                timeline_events.append({"date": nid, "entities": connected[:5], "description": "Event involving " + ", ".join(connected[:3])})
    timeline_events.sort(key=lambda e: e["date"])

    # Notes
    notes = []
    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import text as sqltext
        async with AsyncSessionLocal() as session:
            result = await session.execute(sqltext("SELECT entity_id, entity_type, author, content, tag, created_at FROM notes ORDER BY created_at DESC LIMIT 50"))
            notes = [{"entity": r[0], "type": r[1], "author": r[2], "content": r[3], "tag": r[4], "date": str(r[5])} for r in result.fetchall()]
    except Exception:
        pass

    try:
        anomalies = graph.detect_anomalies()
    except Exception:
        anomalies = []

    entity_groups = {}
    for nid, ntype in nodes:
        entity_groups.setdefault(ntype, []).append(nid)

    tc = {"person": "#ff3355", "phone": "#3b82f6", "location": "#00ff88", "vehicle": "#ffb800", "financial": "#a855f7", "email": "#00f0ff", "date": "#f472b6", "ip_address": "#fb923c", "address": "#84cc16"}
    tl = {"person": "Persons", "phone": "Phones", "location": "Locations", "vehicle": "Vehicles", "financial": "Financial", "email": "Emails", "date": "Dates", "ip_address": "IP Addresses", "address": "Addresses"}

    # Build entity tables
    entity_sections = []
    for etype in ["person", "location", "vehicle", "phone", "financial", "email", "date", "ip_address", "address"]:
        elist = entity_groups.get(etype, [])
        if not elist:
            continue
        color = tc.get(etype, "#999")
        label = tl.get(etype, etype.title())
        rows_html = ""
        for ename in sorted(elist):
            deg = graph.g.degree(ename)
            neighbors = list(graph.g.neighbors(ename))
            ntypes = {}
            for nb in neighbors:
                nbtype = graph.g.nodes[nb].get("type", "unknown")
                ntypes.setdefault(nbtype, []).append(nb)
            conn_parts = []
            for k, v in ntypes.items():
                conn_parts.append(str(len(v)) + " " + tl.get(k, k))
            conn_summary = ", ".join(conn_parts)
            rows_html += '<tr><td style="font-weight:600">' + ename + '</td><td>' + str(deg) + '</td><td style="font-size:12px;color:#8b95b0">' + conn_summary + '</td></tr>\n'
        entity_sections.append('<div class="entity-section"><h3><span class="type-dot" style="background:' + color + '"></span>' + label + " (" + str(len(elist)) + ')</h3><table><thead><tr><th>Name</th><th>Connections</th><th>Connected To</th></tr></thead><tbody>' + rows_html + "</tbody></table></div>")
    entity_tables_html = "\n".join(entity_sections)

    # Relationship table
    rel_rows = ""
    for src, tgt, rels, priority, conf in edges_list[:300]:
        conf_pct = round(conf * 100)
        conf_color = "#00ff88" if conf_pct >= 80 else "#ffb800" if conf_pct >= 50 else "#ff3355"
        rel_rows += '<tr><td>' + src + '</td><td>' + tgt + '</td><td>' + ", ".join(rels) + '</td><td><span class="priority-badge ' + priority + '">' + priority + '</span></td><td><div class="conf-bar"><div class="conf-fill" style="width:' + str(conf_pct) + "%;background:" + conf_color + '"></div><span>' + str(conf_pct) + '%</span></div></td></tr>\n'

    # Risk table
    risk_rows = ""
    for r in risk_scores:
        lc = r["level"].lower()
        risk_rows += '<tr><td style="font-weight:600">' + r["entity"] + '</td><td><span class="risk-badge ' + lc + '">' + r["level"] + '</span></td><td class="score-num">' + str(r["score"]) + "</td><td>" + str(r["degree"]) + "</td><td>" + str(r["centrality"]) + "</td><td>" + str(r["financial"]) + "</td><td>" + str(r["shared_locations"]) + "</td><td>" + str(r["anomalies"]) + "</td></tr>\n"

    # Timeline HTML
    timeline_html = ""
    for evt in timeline_events[:30]:
        entities_html = "".join('<span class="entity-chip">' + e + "</span>" for e in evt["entities"])
        timeline_html += '<div class="timeline-item"><div class="timeline-date">' + evt["date"] + '</div><div class="timeline-desc">' + evt["description"] + '</div><div class="timeline-entities">' + entities_html + "</div></div>\n"

    # Notes HTML
    notes_html = ""
    for note in notes[:20]:
        tag_class = note.get("tag", "general")
        notes_html += '<div class="note-item"><div class="note-header"><span class="note-entity">' + note["entity"] + '</span><span class="note-tag ' + tag_class + '">' + tag_class + '</span><span class="note-author">' + note["author"] + '</span><span class="note-date">' + note["date"][:10] + '</span></div><div class="note-content">' + note["content"] + "</div></div>\n"

    # Anomalies HTML
    anomaly_html = ""
    for a in anomalies[:15]:
        sev = a.get("severity", "medium")
        ent_chips = " ".join('<span class="entity-chip">' + e + "</span>" for e in a.get("entities_involved", [])[:5])
        anomaly_html += '<div class="anomaly-item ' + sev + '"><div class="anomaly-severity">' + sev.upper() + '</div><div class="anomaly-type">' + a.get("type", "").replace("_", " ").title() + '</div><div class="anomaly-desc">' + a.get("description", "") + '</div><div class="anomaly-entities">' + ent_chips + "</div></div>\n"

    # Type summary
    type_summary = ""
    for etype in ["person", "location", "vehicle", "phone", "financial", "email", "date", "ip_address", "address"]:
        count = len(entity_groups.get(etype, []))
        if count > 0:
            color = tc.get(etype, "#999")
            label = tl.get(etype, etype.title())
            type_summary += '<div class="summary-stat"><div class="summary-num" style="color:' + color + '">' + str(count) + '</div><div class="summary-label">' + label + "</div></div>"

    high_risk_count = sum(1 for r in risk_scores if r["level"] in ("CRITICAL", "HIGH"))

    # Build conditional sections
    risk_section = ""
    if risk_scores:
        risk_section = '<div class="section"><div class="section-title"><span class="icon">&#9888;</span> Risk Assessment</div><table><thead><tr><th>Person</th><th>Level</th><th>Score</th><th>Connections</th><th>Centrality</th><th>Financial</th><th>Shared Loc</th><th>Anomalies</th></tr></thead><tbody>' + risk_rows + "</tbody></table></div>"

    rel_section = ""
    if rel_rows:
        rel_section = '<div class="section"><div class="section-title"><span class="icon">&#128279;</span> Network Relationships</div><table><thead><tr><th>Source</th><th>Target</th><th>Relations</th><th>Priority</th><th>Confidence</th></tr></thead><tbody>' + rel_rows + "</tbody></table></div>"

    tl_section = ""
    if timeline_html:
        tl_section = '<div class="section"><div class="section-title"><span class="icon">&#128197;</span> Timeline</div>' + timeline_html + "</div>"

    anom_section = ""
    if anomaly_html:
        anom_section = '<div class="section"><div class="section-title"><span class="icon">&#128680;</span> Anomaly Alerts</div>' + anomaly_html + "</div>"

    notes_section = ""
    if notes_html:
        notes_section = '<div class="section"><div class="section-title"><span class="icon">&#128221;</span> Investigation Notes</div>' + notes_html + "</div>"

    # Assemble the full HTML
    css = open("backend/routes/_report_css.txt", "r", encoding="utf-8").read()
    body_parts = [
        '<div class="report-header"><div class="badge">CLASSIFIED - INVESTIGATION REPORT</div><h1>' + title + '</h1><div class="subtitle">AI-Powered Criminal Network Analysis</div><div class="date">Generated: ' + now_str + ' | CrimeGraph AI v3.0</div></div>',
        '<div class="section"><div class="section-title"><span class="icon">&#128202;</span> Executive Summary</div><div class="summary-grid">' + type_summary + '</div><div class="findings"><div class="finding-card"><h4>Total Entities</h4><div class="big-num" style="color:#00f0ff">' + str(stats.get("total_entities", 0)) + '</div><div class="desc">Across ' + str(len(entity_groups)) + ' entity types</div></div><div class="finding-card"><h4>Relationships</h4><div class="big-num" style="color:#a855f7">' + str(stats.get("total_relations", 0)) + '</div><div class="desc">Connections mapped in the network</div></div><div class="finding-card"><h4>Risk Assessment</h4><div class="big-num" style="color:#ff3355">' + str(high_risk_count) + '</div><div class="desc">High/Critical risk individuals</div></div><div class="finding-card"><h4>Anomalies Detected</h4><div class="big-num" style="color:#ffb800">' + str(len(anomalies)) + '</div><div class="desc">Suspicious patterns identified</div></div></div></div>',
        risk_section,
        '<div class="section"><div class="section-title"><span class="icon">&#128269;</span> Extracted Entities</div>' + entity_tables_html + '</div>',
        rel_section,
        tl_section,
        anom_section,
        notes_section,
        '<div class="report-footer"><div class="brand">CRIME GRAPH AI</div><p>AI-powered criminal network analysis platform</p><p style="margin-top:8px">FastAPI + React + spaCy NER + Neo4j GDS + PostgreSQL + Cytoscape.js</p><p style="margin-top:4px">Report generated on ' + now_str + '</p></div>',
    ]
    body_html = "\n".join(body_parts)

    html = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + title + '</title><style>' + css + '</style></head><body><div class="page">' + body_html + '</div></body></html>'

    return {"html": html, "title": title, "generated_at": now_str}

# -- Case Comparison
@router.post("/compare-cases")
async def compare_cases(data: dict):
    reports = data.get("reports", [])
    if len(reports) < 2:
        raise HTTPException(status_code=400, detail="At least 2 reports required")
    from backend.services.ner import extract_entities
    from backend.services.entity_resolution import deduplicate_all
    extractions = []
    for i, report in enumerate(reports):
        text_val = report.get("text", "")
        label = report.get("label", f"Report {i+1}")
        entities = extract_entities(text_val)
        entities = deduplicate_all(entities)
        extractions.append({"label": label, "entities": entities})
    all_entity_sets = {}
    for ext in extractions:
        for etype, elist in ext["entities"].items():
            if etype in ("people_with_sources",):
                continue
            for e in elist:
                if isinstance(e, str):
                    if e not in all_entity_sets:
                        all_entity_sets[e] = {"type": etype, "found_in": []}
                    all_entity_sets[e]["found_in"].append(ext["label"])
    shared = {k: v for k, v in all_entity_sets.items() if len(v["found_in"]) >= 2}
    matrix = []
    for i, ext1 in enumerate(extractions):
        row = {"report": ext1["label"], "entity_count": sum(len(v) for k, v in ext1["entities"].items() if k != "people_with_sources" and isinstance(v, list)), "shared_with": []}
        for j, ext2 in enumerate(extractions):
            if i != j:
                set1, set2 = set(), set()
                for k, v in ext1["entities"].items():
                    if k != "people_with_sources" and isinstance(v, list): set1.update(v)
                for k, v in ext2["entities"].items():
                    if k != "people_with_sources" and isinstance(v, list): set2.update(v)
                overlap = set1 & set2
                if overlap:
                    row["shared_with"].append({"report": ext2["label"], "shared_count": len(overlap), "shared_entities": list(overlap)[:10]})
        matrix.append(row)
    return {"extractions": [{"label": e["label"], "entities": {k: v for k, v in e["entities"].items() if k != "people_with_sources" and isinstance(v, list)}} for e in extractions], "shared_entities": [{"name": k, "type": v["type"], "found_in": v["found_in"]} for k, v in shared.items()], "comparison_matrix": matrix, "total_shared": len(shared)}

# -- Watchlist
@router.post("/watchlist")
async def add_to_watchlist(data: dict):
    name = data.get("name", "")
    entity_type = data.get("entity_type", "person")
    metadata = data.get("metadata", {})
    source = data.get("source", "manual")
    if not name: raise HTTPException(status_code=400, detail="name required")
    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import text as sqltext
        async with AsyncSessionLocal() as session:
            await session.execute(sqltext("INSERT INTO watchlist (name, entity_type, metadata, source) VALUES (:name, :etype, :meta, :src) ON CONFLICT (name, entity_type) DO UPDATE SET metadata = :meta, source = :src"), {"name": name, "etype": entity_type, "meta": json.dumps(metadata), "src": source})
            await session.commit()
        return {"status": "added", "name": name, "entity_type": entity_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/watchlist")
async def get_watchlist():
    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import text as sqltext
        async with AsyncSessionLocal() as session:
            result = await session.execute(sqltext("SELECT id, name, entity_type, metadata, added_at, source FROM watchlist ORDER BY added_at DESC"))
            rows = result.fetchall()
            return [{"id": r[0], "name": r[1], "entity_type": r[2], "metadata": json.loads(r[3]) if r[3] else {}, "added_at": str(r[4]), "source": r[5]} for r in rows]
    except: return []

@router.delete("/watchlist/{item_id}")
async def remove_from_watchlist(item_id: int):
    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import text as sqltext
        async with AsyncSessionLocal() as session:
            await session.execute(sqltext("DELETE FROM watchlist WHERE id = :id"), {"id": item_id})
            await session.commit()
        return {"status": "removed", "id": item_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-watchlist")
async def check_watchlist():
    from backend.routes.api import graph
    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import text as sqltext
        async with AsyncSessionLocal() as session:
            result = await session.execute(sqltext("SELECT name, entity_type FROM watchlist"))
            wl_entries = result.fetchall()
    except: return {"matches": [], "total_watchlist": 0}
    matches = []
    graph_entities = {nid: nd.get("type", "unknown") for nid, nd in graph.g.nodes(data=True)}
    for wl_name, wl_type in wl_entries:
        for nid, ntype in graph_entities.items():
            if nid.lower() == wl_name.lower() and (wl_type == ntype or wl_type == "any"):
                matches.append({"watchlist_entry": wl_name, "entity_type": wl_type, "matched_graph_entity": nid, "graph_entity_type": ntype})
    return {"matches": matches, "total_watchlist": len(wl_entries), "total_matches": len(matches)}
