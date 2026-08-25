"""
NER Service — Hybrid approach:
  - spaCy for person names, locations, organizations
  - Regex for phone numbers, vehicles, financial accounts
  - Custom rules for domain-specific patterns
"""

import re
import spacy

# Load spaCy English model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
    nlp = spacy.load("en_core_web_sm")

# ── Regex Patterns ────────────────────────────────────────
PHONE_REGEX = re.compile(r'\b\d{10}\b')
ACCOUNT_REGEX = re.compile(r'Bank\s+Account\s+([A-Z])', re.IGNORECASE)

VEHICLE_DESCRIPTIONS = [
    r'white\s+van', r'black\s+SUV', r'blue\s+sedan', r'red\s+car',
    r'blue\s+hatchback', r'white\s+sedan', r'black\s+car', r'red\s+sedan',
    r'silver\s+SUV', r'green\s+truck', r'white\s+hatchback', r'red\s+truck',
    r'motorcycle', r'scooter', r'auto\s+rickshaw', r'truck', r'van',
]
VEHICLE_PATTERN = re.compile(
    r'(?:a\s+|the\s+)?(' + '|'.join(VEHICLE_DESCRIPTIONS) + r')\b',
    re.IGNORECASE
)

# ── Stopwords for name detection ──────────────────────────
STOPWORDS = {
    "the", "officer", "police", "later", "case", "phone", "location",
    "according", "investigator", "during", "cctv", "bank", "one",
    "second", "third", "first", "incident", "suspect", "financial",
    "additionally", "conclusion", "operation", "shadow", "link",
    "intelligence", "analysis", "criminal", "evidence", "network",
    "summary", "registry", "trail", "vehicle", "call", "report",
    "september", "august", "january", "february", "march", "april",
    "may", "june", "july", "october", "november", "december",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "also", "was", "were", "had", "has", "have", "who", "which",
    "that", "this", "these", "those", "where", "when", "how",
    "industrial", "spare", "parts", "electronic", "devices",
    "approximately", "valued", "declared", "contained", "intercepted",
    "shipment", "cargo", "counterfeit", "intelligent",
}


def extract_entities(text: str) -> dict:
    """
    Extract all entity types from unstructured text.
    Returns dict with keys: people, locations, phones, vehicles, financial
    """
    doc = nlp(text)
    
    people = set()
    locations = set()
    organizations = set()
    
    # ── spaCy NER ─────────────────────────────────────────
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            if _is_valid_person_name(name):
                people.add(name)
        elif ent.label_ in ("GPE", "LOC", "FAC"):
            locations.add(ent.text.strip())
        elif ent.label_ == "ORG":
            organizations.add(ent.text.strip())
    
    # ── Regex-based extraction ─────────────────────────────
    phones = list(set(PHONE_REGEX.findall(text)))
    
    vehicles = []
    for match in VEHICLE_PATTERN.finditer(text):
        v = match.group(1).strip().title()
        if v not in vehicles:
            vehicles.append(v)
    
    financial = []
    for match in ACCOUNT_REGEX.finditer(text):
        acc = f"Bank Account {match.group(1)}"
        if acc not in financial:
            financial.append(acc)
    
    # Also detect standalone financial patterns
    for match in re.finditer(r'(?:account|transfer|fund)s?\s+(?:number|from|to)?\s*([A-Z]\d*)', text, re.IGNORECASE):
        acc = match.group(0).strip().title()
        if acc not in financial and len(acc) > 3:
            financial.append(acc)
    
    return {
        "people": sorted(people),
        "locations": sorted(locations),
        "phones": phones,
        "vehicles": vehicles,
        "financial": financial,
        "organizations": sorted(organizations),
    }


def extract_relations(text: str, entities: dict) -> list:
    """
    Extract relationships between entities from text.
    Returns list of (source, target, relation_type, evidence_sentence)
    """
    relations = []
    doc = nlp(text)
    
    # Relationship verb patterns
    verb_patterns = {
        "transferred": "financial_transfer",
        "transfer": "financial_transfer",
        "contacted": "communication",
        "called": "communication",
        "messaged": "communication",
        "met": "meeting",
        "visited": "visited",
        "lent": "vehicle_lending",
        "owned": "ownership",
        "owns": "ownership",
        "registered": "registration",
        "received": "financial_transfer",
        "detected": "detection",
        "arranged": "logistics",
        "accessed": "access",
    }
    
    all_people = entities.get("people", [])
    
    for sent in doc.sents:
        sent_text = sent.text.lower()
        
        # Find which people appear in this sentence
        people_in_sent = [p for p in all_people if p.lower() in sent_text]
        
        if len(people_in_sent) < 2:
            continue
        
        # Determine relation type
        rel_type = "linked"
        for verb, label in verb_patterns.items():
            if verb in sent_text:
                rel_type = label
                break
        
        # Link first two people found
        if len(people_in_sent) >= 2:
            relations.append({
                "source": people_in_sent[0],
                "target": people_in_sent[1],
                "relation_type": rel_type,
                "evidence": sent.text.strip(),
                "priority": "high" if rel_type in ("financial_transfer", "communication") else "supporting",
            })
    
    return relations


def _is_valid_person_name(name: str) -> bool:
    """Filter out false-positive person names."""
    words = name.split()
    
    # Must be 1-3 words
    if len(words) > 3 or len(words) < 1:
        return False
    
    # First word must not be a stopword
    if words[0].lower() in STOPWORDS:
        return False
    
    # Must start with uppercase
    if not name[0].isupper():
        return False
    
    # Skip if all words are stopwords
    if all(w.lower() in STOPWORDS for w in words):
        return False
    
    # Skip vehicle descriptions
    vehicle_words = {"van", "suv", "sedan", "hatchback", "truck", "motorcycle", "car", "bike"}
    if any(w.lower() in vehicle_words for w in words):
        return False
    
    # Skip if too short (single char)
    if len(name) < 2:
        return False
    
    return True
