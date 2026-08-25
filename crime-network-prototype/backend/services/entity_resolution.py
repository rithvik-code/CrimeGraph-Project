"""
Entity Resolution Service

Identifies and merges duplicate entities across multiple case reports.
Uses string similarity (Jaro-Winkler) + attribute matching.
"""

from difflib import SequenceMatcher
from typing import Optional


def jaro_winkler(s1: str, s2: str) -> float:
    """Compute Jaro-Winkler similarity between two strings."""
    # Use SequenceMatcher as a lightweight alternative
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def resolve_persons(persons_list: list[dict], threshold: float = 0.82) -> list[dict]:
    """
    Given a list of person entities {name, source_case_id, ...},
    merge duplicates and return deduplicated list.
    
    Merging rules:
    - Names with similarity > threshold are merged
    - Keep the version with the most attributes
    - Track all source cases
    """
    if not persons_list:
        return []
    
    # Sort by name length (prefer longer/fuller names)
    sorted_persons = sorted(persons_list, key=lambda p: len(p.get("name", "")), reverse=True)
    
    clusters = []  # list of lists (clusters of duplicates)
    
    for person in sorted_persons:
        name = person.get("name", "").strip()
        if not name:
            continue
        
        merged = False
        for cluster in clusters:
            # Compare against the "representative" (first in cluster)
            rep_name = cluster[0]["name"]
            similarity = jaro_winkler(name, rep_name)
            
            if similarity >= threshold:
                # Check for substring match too (e.g., "Pradeep" in "Pradeep Menon")
                if name.lower() in rep_name.lower() or rep_name.lower() in name.lower():
                    cluster.append(person)
                    merged = True
                    break
                elif similarity >= threshold:
                    cluster.append(person)
                    merged = True
                    break
        
        if not merged:
            clusters.append([person])
    
    # Build merged results
    merged_persons = []
    for cluster in clusters:
        # Pick the longest name as canonical
        canonical = max(cluster, key=lambda p: len(p.get("name", "")))
        all_sources = list(set(p.get("source_case_id", "") for p in cluster if p.get("source_case_id")))
        
        merged_persons.append({
            "name": canonical["name"],
            "source_cases": all_sources,
            "merged_from": [p["name"] for p in cluster if p["name"] != canonical["name"]],
            "confidence": min(1.0, 0.8 + 0.2 * len(cluster)),  # Higher confidence with more sources
        })
    
    return merged_persons


def resolve_vehicles(vehicles_list: list[dict], threshold: float = 0.85) -> list[dict]:
    """Deduplicate vehicles using string similarity."""
    if not vehicles_list:
        return []
    
    clusters = []
    sorted_vehicles = sorted(vehicles_list, key=lambda v: len(v.get("name", "")), reverse=True)
    
    for vehicle in sorted_vehicles:
        name = vehicle.get("name", "").strip()
        if not name:
            continue
        
        merged = False
        for cluster in clusters:
            rep_name = cluster[0]["name"]
            if jaro_winkler(name, rep_name) >= threshold or name.lower() in rep_name.lower():
                cluster.append(vehicle)
                merged = True
                break
        
        if not merged:
            clusters.append([vehicle])
    
    return [
        {
            "name": max(c, key=lambda v: len(v.get("name", "")))["name"],
            "merged_from": [v["name"] for v in c if v["name"] != max(c, key=lambda v: len(v.get("name", "")))["name"]],
        }
        for c in clusters
    ]


def resolve_locations(locations_list: list[dict], threshold: float = 0.80) -> list[dict]:
    """Deduplicate locations, preferring specific over general."""
    if not locations_list:
        return []
    
    clusters = []
    # Sort by specificity (more words = more specific)
    sorted_locs = sorted(locations_list, key=lambda l: len(l.get("name", "").split()), reverse=True)
    
    for loc in sorted_locs:
        name = loc.get("name", "").strip()
        if not name:
            continue
        
        merged = False
        for cluster in clusters:
            rep_name = cluster[0]["name"]
            # Check if one is a substring of the other (e.g., "Chennai" in "Chennai Port")
            if jaro_winkler(name, rep_name) >= threshold:
                cluster.append(loc)
                merged = True
                break
        
        if not merged:
            clusters.append([loc])
    
    return [
        {
            "name": c[0]["name"],  # Most specific
            "merged_from": [l["name"] for l in c[1:]],
        }
        for c in clusters
    ]


def deduplicate_all(entities: dict) -> dict:
    """Run entity resolution on all entity types."""
    people = [{"name": p} for p in entities.get("people", [])]
    vehicles = [{"name": v} for v in entities.get("vehicles", [])]
    locations = [{"name": l} for l in entities.get("locations", [])]
    
    resolved_people = resolve_persons(people)
    resolved_vehicles = resolve_vehicles(vehicles)
    resolved_locations = resolve_locations(locations)
    
    return {
        "people": [p["name"] for p in resolved_people],
        "people_with_sources": resolved_people,
        "vehicles": [v["name"] for v in resolved_vehicles],
        "locations": [l["name"] for l in resolved_locations],
        "phones": entities.get("phones", []),  # Phones are already unique
        "financial": entities.get("financial", []),
        "organizations": entities.get("organizations", []),
    }
