"""
Graph Builder Service

Maintains an in-memory NetworkX graph.
Supports: persons, vehicles, phones, locations, financial accounts.
Outputs Cytoscape.js format for React frontend.
"""

import networkx as nx
from typing import Optional
from .anomaly import detect_anomalies


class CaseGraph:
    def __init__(self):
        self.g = nx.Graph()
    
    # ── Node helpers ──────────────────────────────────────
    def _ensure_node(self, name: str, node_type: str, **kwargs):
        if not self.g.has_node(name):
            self.g.add_node(name, type=node_type, **kwargs)
        else:
            # Merge metadata
            for k, v in kwargs.items():
                if k not in self.g.nodes[name]:
                    self.g.nodes[name][k] = v
    
    def add_person(self, name: str, **kwargs):
        self._ensure_node(name, "person", **kwargs)
    
    def add_phone(self, phone: str, **kwargs):
        self._ensure_node(phone, "phone", **kwargs)
    
    def add_location(self, loc: str, **kwargs):
        self._ensure_node(loc, "location", **kwargs)
    
    def add_vehicle(self, vehicle: str, **kwargs):
        self._ensure_node(vehicle, "vehicle", **kwargs)
    
    def add_financial(self, account: str, **kwargs):
        self._ensure_node(account, "financial", **kwargs)
    
    # ── Edge helper ───────────────────────────────────────
    def link(self, a: str, b: str, relation: str, source: str = "",
             case_id: str = None, priority: str = "supporting", confidence: float = 0.5):
        if not self.g.has_edge(a, b):
            self.g.add_edge(a, b, relations=set(), sources=[], case_ids=set(),
                          priority="supporting", evidence=[])
        data = self.g.edges[a, b]
        data["relations"].add(relation)
        if source:
            data["sources"].append(source)
            data["evidence"].append(source[:200])
        if case_id:
            data["case_ids"].add(case_id)
        # Upgrade priority if needed
        if priority == "high":
            data["priority"] = "high"
        # Update confidence
        if confidence > data.get("confidence", 0):
            data["confidence"] = confidence
    
    # ── Load structured cases ─────────────────────────────
    def load_cases(self, cases: list[dict]):
        for case in cases:
            person = case.get("person", "")
            if not person:
                continue
            self.add_person(person)
            
            if case.get("phone"):
                self.add_phone(case["phone"])
                self.link(person, case["phone"], "has_phone", case_id=case.get("case_id", ""))
            
            if case.get("location"):
                self.add_location(case["location"])
                self.link(person, case["location"], "present_at", case_id=case.get("case_id", ""))
            
            if case.get("vehicle"):
                self.add_vehicle(case["vehicle"])
                self.link(person, case["vehicle"], "owns", case_id=case.get("case_id", ""))
            
            if case.get("financial_from"):
                self.add_financial(case["financial_from"])
                self.link(person, case["financial_from"], "owns_account", case_id=case.get("case_id", ""))
            
            if case.get("financial_to"):
                self.add_financial(case["financial_to"])
                self.link(person, case["financial_to"], "receives_funds", case_id=case.get("case_id", ""))
            
            if case.get("connected_to"):
                other = case["connected_to"]
                self.add_person(other)
                note = case.get("relation_note", "").lower()
                if any(w in note for w in ("payment", "transfer", "fund")):
                    rel, priority = "financial_link", "high"
                elif any(w in note for w in ("contact", "call", "phone")):
                    rel, priority = "communication", "high"
                elif any(w in note for w in ("lent", "vehicle")):
                    rel, priority = "vehicle_link", "supporting"
                else:
                    rel, priority = "linked", "supporting"
                self.link(person, other, rel, case_id=case.get("case_id", ""), priority=priority)
    
    # ── Load NER extraction ───────────────────────────────
    def load_extraction(self, entities: dict, relations: list, source_label: str = ""):
        for p in entities.get("people", []):
            self.add_person(p)
        for ph in entities.get("phones", []):
            self.add_phone(ph)
        for loc in entities.get("locations", []):
            self.add_location(loc)
        for v in entities.get("vehicles", []):
            self.add_vehicle(v)
        for fin in entities.get("financial", []):
            self.add_financial(fin)
        
        for rel in relations:
            src = rel.get("source", "")
            tgt = rel.get("target", "")
            if src and tgt:
                self.add_person(src)
                self.add_person(tgt)
                self.link(src, tgt, rel.get("relation_type", "linked"),
                         source=rel.get("evidence", ""),
                         case_id=source_label,
                         priority=rel.get("priority", "supporting"))
        
        # Co-occurrence links
        for p in entities.get("people", []):
            for loc in entities.get("locations", []):
                self.link(p, loc, "located_at", case_id=source_label)
            for ph in entities.get("phones", []):
                self.link(p, ph, "has_phone", case_id=source_label)
            for v in entities.get("vehicles", []):
                self.link(p, v, "associated_vehicle", case_id=source_label)
            for fin in entities.get("financial", []):
                self.link(p, fin, "associated_financial", case_id=source_label)
    
    # ── Analysis ──────────────────────────────────────────
    def person_pairs(self):
        return [
            (a, b)
            for a, b in self.g.edges()
            if self.g.nodes[a].get("type") == "person" and self.g.nodes[b].get("type") == "person"
        ]
    
    def shared_neighbors(self, a: str, b: str):
        na = set(self.g.neighbors(a)) - {b}
        nb = set(self.g.neighbors(b)) - {a}
        return na & nb
    
    def confidence_score(self, a: str, b: str):
        """Explainable confidence score."""
        if not self.g.has_edge(a, b):
            return 0, []
        
        shared = self.shared_neighbors(a, b)
        edge_data = self.g.edges[a, b]
        rels = edge_data.get("relations", set())
        
        score = 40 if len(rels) > 0 else 0
        breakdown = []
        
        if len(rels) > 0:
            breakdown.append(("Direct link recorded", 40))
        
        for s in shared:
            t = self.g.nodes[s].get("type", "unknown")
            score += 20
            breakdown.append((f"Shared {t}: {s}", 20))
        
        # Bonus for high-priority relations
        if any("financial" in r or "communication" in r for r in rels):
            score += 10
            breakdown.append(("High-priority relation type", 10))
        
        return min(score, 98), breakdown
    
    def get_shortest_path(self, source: str, target: str) -> list:
        """Find shortest path between two entities."""
        try:
            path = nx.shortest_path(self.g, source, target)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def detect_anomalies(self) -> list[dict]:
        """Run anomaly detection on current graph."""
        return detect_anomalies(self.g)
    
    # ── Output ────────────────────────────────────────────
    def to_cytoscape_json(self) -> list:
        """Output Cytoscape.js-compatible elements array."""
        color_map = {
            "person": "#e63946",
            "phone": "#457b9d",
            "location": "#2a9d8f",
            "vehicle": "#f4a261",
            "financial": "#e9c46a",
        }
        shape_map = {
            "person": "ellipse",
            "phone": "round-rectangle",
            "location": "rectangle",
            "vehicle": "diamond",
            "financial": "round-hexagon",
        }
        icon_map = {
            "person": "👤",
            "phone": "📱",
            "location": "📍",
            "vehicle": "🚗",
            "financial": "💰",
        }
        
        nodes = []
        for n, d in self.g.nodes(data=True):
            ntype = d.get("type", "person")
            nodes.append({
                "data": {
                    "id": n,
                    "label": n,
                    "nodeType": ntype,
                    "icon": icon_map.get(ntype, ""),
                    "color": color_map.get(ntype, "#999"),
                    "shape": shape_map.get(ntype, "ellipse"),
                },
                "classes": ntype,
            })
        
        edges = []
        for a, b, d in self.g.edges(data=True):
            rels = sorted(d.get("relations", []))
            priority = d.get("priority", "supporting")
            score, _ = self.confidence_score(a, b)
            edges.append({
                "data": {
                    "source": a,
                    "target": b,
                    "label": ", ".join(rels),
                    "priority": priority,
                    "relations": rels,
                    "confidence": score,
                },
                "classes": priority,
            })
        
        return nodes + edges
    
    def stats(self) -> dict:
        """Return current graph statistics."""
        people = [n for n, d in self.g.nodes(data=True) if d.get("type") == "person"]
        vehicles = [n for n, d in self.g.nodes(data=True) if d.get("type") == "vehicle"]
        locations = [n for n, d in self.g.nodes(data=True) if d.get("type") == "location"]
        phones = [n for n, d in self.g.nodes(data=True) if d.get("type") == "phone"]
        financials = [n for n, d in self.g.nodes(data=True) if d.get("type") == "financial"]
        
        case_ids = set()
        for _, _, d in self.g.edges(data=True):
            case_ids |= d.get("case_ids", set())
        
        summary = self.edges_summary()
        high_risk = [e for e in summary if e["high_risk"]]
        
        return {
            "total_cases": len(case_ids),
            "persons_identified": len(people),
            "vehicles_tracked": len(vehicles),
            "locations_mapped": len(locations),
            "phones_traced": len(phones),
            "financial_links": len(financials),
            "total_entities": self.g.number_of_nodes(),
            "total_relations": self.g.number_of_edges(),
            "connections": len(summary),
            "high_risk_connections": len(high_risk),
        }
    
    def edges_summary(self) -> list:
        result = []
        for a, b in self.person_pairs():
            data = self.g.edges[a, b]
            score, breakdown = self.confidence_score(a, b)
            result.append({
                "source": a,
                "target": b,
                "relations": sorted(data.get("relations", [])),
                "confidence": score,
                "breakdown": breakdown,
                "high_risk": score >= 80,
            })
        return result
    
    def get_node_details(self, node_id: str) -> dict:
        """Get detailed info about a specific node."""
        if not self.g.has_node(node_id):
            return {}
        
        data = self.g.nodes[node_id]
        neighbors = []
        for neighbor in self.g.neighbors(node_id):
            edge_data = self.g.edges[node_id, neighbor]
            neighbors.append({
                "name": neighbor,
                "type": self.g.nodes[neighbor].get("type", "unknown"),
                "relations": sorted(edge_data.get("relations", [])),
                "confidence": self.confidence_score(node_id, neighbor)[0],
            })
        
        return {
            "id": node_id,
            "name": node_id,
            "type": data.get("type", "unknown"),
            "metadata": {k: v for k, v in data.items() if k != "type"},
            "neighbors": sorted(neighbors, key=lambda x: x["confidence"], reverse=True),
            "degree": self.g.degree(node_id),
        }
