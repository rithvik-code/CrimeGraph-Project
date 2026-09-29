"""
NER Service — Enterprise-grade with robust false-positive filtering.

  - spaCy for person names, locations, organizations
  - Regex for phone numbers, vehicles, financial accounts, emails, dates, IPs, addresses
  - Massive blacklist to prevent tech platforms, generic nouns, and non-entities from being detected
  - Contextual validation: names must appear in name-like contexts
  - International city coverage for proper geocoding
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
PHONE_REGEX = re.compile(r'\b(\d{10})\b')
ACCOUNT_REGEX = re.compile(r'Bank\s+Account\s+([A-Z])', re.IGNORECASE)

# Email pattern
EMAIL_REGEX = re.compile(
    r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
)

# Date patterns (multiple formats)
DATE_PATTERNS = [
    re.compile(r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b'),
    re.compile(r'\b(\d{1,2}/\d{1,2}/\d{4})\b'),
    re.compile(r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b', re.IGNORECASE),
    re.compile(r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE),
    re.compile(r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\b', re.IGNORECASE),
    re.compile(r'\b(\d{1,2}[-.]\d{1,2}[-.]\d{4})\b'),
    re.compile(r'\b((?:last|this|next)\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|week|month|year))\b', re.IGNORECASE),
    re.compile(r'\b(\d{1,2}\s+(?:days?|weeks?|months?|years?)\s+ago)\b', re.IGNORECASE),
]

# IP address patterns
IPV4_REGEX = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
)
IPV6_REGEX = re.compile(
    r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
)

# Physical address patterns
ADDRESS_US_REGEX = re.compile(
    r'\b\d{1,6}\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,4}'
    r'(?:\s+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln'
    r'|Court|Ct|Place|Pl|Way|Circle|Cir|Terrace|Ter|Highway|Hwy|Parkway|Pkwy'
    r'|Trail|Trl|Loop|Row))'
    r'(?:\s*,?\s+[A-Z][a-zA-Z\s]+,?\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?)?',
    re.IGNORECASE
)
ADDRESS_INDIA_REGEX = re.compile(
    r'\b(?:No\.?\s*)?\d{1,5}(?:/\d{1,5})?\s*,?\s*'
    r'[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3}'
    r'(?:\s+(?:Road|Rd|Street|St|Avenue|Ave|Lane|Ln|Nagar|Marg|Path|Cross|Layout|Colony|Extension))'
    r'(?:\s*,?\s*[A-Z][a-zA-Z\s]+)?'
    r'(?:\s*[-\u2013]\s*\d{6})?',
    re.IGNORECASE
)
ADDRESS_GENERIC_REGEX = re.compile(
    r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3}\s+'
    r'(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln'
    r'|Nagar|Marg|Path|Cross|Layout|Colony|Extension'
    r'|Highway|Hwy|Parkway|Pkwy|Bypass)\b',
    re.IGNORECASE
)

VEHICLE_DESCRIPTIONS = [
    r'white\s+van', r'black\s+SUV', r'blue\s+sedan', r'red\s+car',
    r'blue\s+hatchback', r'white\s+sedan', r'black\s+car', r'red\s+sedan',
    r'silver\s+SUV', r'green\s+truck', r'white\s+hatchback', r'red\s+truck',
    r'motorcycle', r'scooter', r'auto\s+rickshaw', r'truck', r'van',
    r'silver\s+sedan', r'grey\s+SUV', r'yellow\s+taxi', r'black\s+van',
    r'white\s+truck', r'blue\s+car', r'red\s+van', r'green\s+car',
]
VEHICLE_PATTERN = re.compile(
    r'(?:a\s+|the\s+)?(' + '|'.join(VEHICLE_DESCRIPTIONS) + r')\b',
    re.IGNORECASE
)

# ══════════════════════════════════════════════════════════
#  COMPREHENSIVE ENTITY BLACKLISTS
# ══════════════════════════════════════════════════════════

# --- MASTER entity blacklist: words that should NEVER be any entity type ---
# Used across all entity validators
_UNIVERSAL_BLACKLIST = {
    # Tech platforms / social media
    "instagram", "facebook", "twitter", "tiktok", "whatsapp", "telegram",
    "linkedin", "youtube", "snapchat", "reddit", "pinterest", "tumblr",
    "discord", "signal", "line", "wechat", "qq", "vine",
    "netflix", "spotify", "hulu", "disney", "amazon", "ebay", "shopify",
    "uber", "lyft", "airbnb", "zoom", "skype", "teams", "slack",
    "google", "bing", "yahoo", "baidu", "duckduckgo", "brave",
    "apple", "microsoft", "samsung", "huawei", "xiaomi",
    # Tech/platform concepts
    "app", "application", "website", "webpage", "browser", "search engine",
    "social media", "social network", "messaging app", "chat app",
    "video platform", "streaming", "podcast", "blog", "vlog",
    "online platform", "digital platform", "virtual platform",
    "dark web", "deep web", "darknet", "clearnet",
    "forum", "channel", "group chat", "server",
    # Diplomatic / institutional terms that look like locations
    "consulate", "embassy", "high commission", "legation",
    "consulate general", "consular", "diplomatic",
    # Generic nouns spaCy mislabels
    "node", "nodes", "edge", "edges", "graph", "vertices", "vertex",
    "relationship", "relationships", "entity", "entities",
    "person", "persons", "people", "individual", "individuals",
    "suspect", "suspects", "witness", "witnesses", "victim", "victims",
    "vehicle", "vehicles", "car", "van", "truck", "sedan",
    "location", "locations", "place", "places", "site", "sites",
    "phone", "phones", "call", "calls", "number", "numbers",
    "financial", "account", "accounts", "bank", "transaction", "transactions",
    "connection", "connections", "link", "links",
    "report", "reports", "case", "cases", "incident", "incidents",
    "evidence", "analysis", "intelligence", "operation", "network",
    "summary", "overview", "background", "findings", "conclusion",
    "investigation", "surveillance", "monitoring", "tracking",
    "document", "documents", "record", "records", "file", "files",
    "statement", "testimony", "warrant", "subpoena",
    "crime", "crimes", "criminal", "criminals", "offence", "offences",
    "theft", "fraud", "scam", "smuggling", "trafficking",
    "arrest", "arrests", "detention", "custody",
    "police", "officer", "officers", "detective", "detectives",
    "inspector", "constable", "constables",
    "agency", "agencies", "department", "departments",
    # Financial / crypto
    "bitcoin", "ethereum", "crypto", "blockchain", "wallet", "token",
    "defi", "nft", "mining", "halving", "bull", "bear", "satoshi",
    "key", "keys", "lessons", "takeaways", "insights", "trends",
    "market", "trading", "portfolio", "exchange", "coin", "altcoin",
    "smart contract", "gas fee", "transaction fee",
    "binance", "coinbase", "kraken", "bitfinex", "poloniex",
    # General concepts / technology
    "data", "information", "technology", "system", "platform",
    "security", "privacy", "encryption", "firewall", "server",
    "database", "algorithm", "protocol", "interface",
    "communication", "surveillance", "monitoring", "tracking",
    "digital", "cyber", "online", "virtual", "cloud",
    "social", "media", "networking",
    "money", "cash", "funds", "payment", "payments",
    "transfer", "transfers", "receipt", "receipts",
    "transport", "logistics", "supply", "delivery",
    "cargo", "shipment", "freight", "consignment",
    # Document / section headers
    "case", "report", "summary", "incident", "conclusion", "analysis",
    "intelligence", "evidence", "network", "operation", "overview",
    "background", "findings", "recommendations", "executive", "abstract",
    "introduction", "methodology", "results", "discussion", "appendix",
    "registry", "trail", "call", "log", "record", "file", "document",
    "statement", "testimony", "affidavit", "warrant", "subpoena",
    # Time/date
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "january", "february", "march",
    "april", "may", "june", "july", "august", "september",
    "october", "november", "december",
    "morning", "afternoon", "evening", "night", "today",
    "yesterday", "tomorrow",
    # Verbs / grammar
    "was", "were", "had", "has", "have", "been", "being",
    "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "must",
    "who", "which", "that", "this", "these", "those",
    "where", "when", "how", "what", "why",
    "also", "then", "than", "after", "before", "during",
    "according", "approximately", "declared", "contained",
    "intercepted", "detected", "recovered", "seized", "confiscated",
    # Colors
    "white", "black", "blue", "red", "green", "silver", "grey",
    "yellow", "orange", "purple", "brown", "golden",
    # Entity-type terms
    "email", "e-mail", "date", "timestamp", "ip", "ipv4", "ipv6",
    "address", "street", "avenue", "boulevard", "road",
    "url", "domain", "hostname",
    "ip address", "physical address", "mailing address",
    # Crime terms
    "murder", "murders", "attack", "assault", "kill", "killer",
    "ciphers", "cipher", "cipher text",
    "jurisdictional", "fragmentation",
    "zodiac", "challenge", "challenges",
    "chapter", "section", "page", "paragraph", "heading",
    "window", "turnout",
    "subscription", "device", "gadget", "equipment",
    "application", "software", "program", "tool", "utility",
    "service", "service provider",
}

# ── Name Validation ────────────────────────────────────────
NAME_PATTERN = re.compile(r'^[A-Z][a-z]+(?: [A-Z][a-z]+){1,2}$')


def _is_blacklisted(word: str) -> bool:
    """Check if a word or phrase is in any blacklist."""
    w = word.lower().strip()
    if w in _UNIVERSAL_BLACKLIST:
        return True
    # Check individual words
    for part in w.split():
        if part in _UNIVERSAL_BLACKLIST:
            return True
    return False


def _is_valid_person_name(name: str, full_text: str = "") -> bool:
    """Multi-layer validation to filter out false-positive person names."""
    words = name.split()

    # Layer 1: Basic structural checks
    if len(words) > 3 or len(words) < 2:
        return False
    if len(name) < 4:
        return False
    if not NAME_PATTERN.match(name):
        return False

    # Layer 2: Universal blacklist
    name_lower = name.lower()
    if name_lower in _UNIVERSAL_BLACKLIST:
        return False
    for word in words:
        if word.lower() in _UNIVERSAL_BLACKLIST:
            return False

    # Layer 3: Pattern-based rejection for compound terms
    reject_patterns = [
        r'(?i)^(bitcoin|crypto|blockchain|key|lesson|takeaway|google|facebook|instagram)',
        r'(?i)(key\s+lesson|key\s+takeaway|key\s+insight)',
        r'(?i)(social\s+media|digital\s+platform|online\s+system)',
        r'(?i)(smart\s+contract|gas\s+fee|transaction\s+fee)',
        r'(?i)(executive\s+summary|case\s+summary)',
        r'(?i)(financial\s+crime|cyber\s+crime|organized\s+crime)',
        r'(?i)(ip\s+address|email|physical\s+address|mailing)',
        r'(?i)(google\s+maps|google\s+earth|google\s+drive)',
        r'(?i)(dark\s+web|deep\s+web|darknet)',
        r'(?i)(online\s+platform|social\s+network|messaging)',
    ]
    for pattern in reject_patterns:
        if re.search(pattern, name):
            return False

    # Layer 4: Context-based validation
    if full_text:
        context_patterns = [
            rf'\b{re.escape(name)}\b.*?(?:was|were|had|has|is|are|did|does|will|would|could|should)',
            rf'(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+{re.escape(name)}',
            rf'(?:officer|detective|inspector|constable)\s+{re.escape(name)}',
            rf'{re.escape(name)}\s+(?:was|were|had|has|is|are|did|does|received|sent|contacted|called|met|visited|owned|registered|accessed|facilitated|coordinated|transferred|paid|lent|borrowed|supplied|provided|arranged|involved|linked|connected|associated|identified|named|known|reported|confirmed|alleged|accused|arrested|detained|questioned|interviewed|observed|spotted|located|found|recovered|seized|confiscated|intercepted|detected|monitored|tracked|surveilled|followed|pursued|chased)',
            rf'(?:identified|named|known|identified as|known as|accused|charged|arrested|suspected)\s+{re.escape(name)}',
        ]
        has_context = any(re.search(p, full_text, re.IGNORECASE) for p in context_patterns)

        if not has_context:
            common_surnames = [
                r'(?i)\b(Sharma|Patel|Singh|Kumar|Gupta|Reddy|Nair|Menon|Das|Shah|Mehta|Verma|Joshi|Iyer|Mishra|Choudhary|Tiwari|Pandey|Srivastava|Rao|Chowdhury|Banerjee|Mukherjee|Ghosh|Sen|Bose|Dutta|Barua|Phukan|Kalita|Saikia|Borah|Khan|Ali|Sheikh|Hussain|Ahmad|Ahmed|Prasad|Shukla|Sinha|Tripathi|Jha|Pandit|Kapoor|Malhotra|Chopra|Khanna|Bhattacharya)\b',
                r'(?i)\b(Smith|Johnson|Williams|Brown|Jones|Davis|Miller|Wilson|Moore|Taylor|Anderson|Thomas|Jackson|White|Harris|Martin|Thompson|Garcia|Martinez|Robinson|Clark|Rodriguez|Lewis|Lee|Walker|Hall|Allen|Young|King|Wright|Scott|Green|Baker|Adams|Nelson|Hill|Campbell|Mitchell|Roberts|Carter|Phillips|Evans|Turner|Torres|Parker|Collins|Edwards|Stewart|Flores|Morris|Nguyen|Murphy|Rivera|Cook|Rogers|Morgan|Peterson|Cooper|Reed|Bailey|Bell|Gomez|Kelly|Howard|Ward|Cox|Diaz|Richardson|Wood|Watson|Brooks|Bennett|Gray|James|Reyes|Cruz|Hughes|Price|Myers|Long|Foster|Sanders|Ross|Morales|Powell|Sullivan|Russell|Ortiz|Jenkins|Gutierrez|Perry|Butler|Barnes|Fisher|Henderson|Coleman|Simmons|Jordan|Reynolds|Hamilton|Graham|Kim|Gonzalez|Alexander|Ramos|Wallace|Griffin|West|Cole|Hayes|Chavez|Gibson|Bryant|Ellis|Stevens|Murray|Ford|Marshall|Owens|Harrison|Fernandez|Wells|Webb|Simpson|Tucker|Porter|Hunter|Hicks|Crawford|Henry|Boyd|Mason|Morales|Kennedy|Warren|Dixon|Reeves|Burns|Gordon|Shaw|Holmes|Rice|Robertson|Hunt|Black|Daniels|Palmer|Mills|Grant|Cunningham|Williamson|Webber|Cameron|Meyer|Moreno|Vance|Chen|Wang|Liu|Zhang|Yang|Huang|Zhao|Tanaka|Suzuki|Watanabe|Nakamura|Kim|Park|Lee|Choi)\b',
            ]
            has_common_surname = any(re.search(p, name) for p in common_surnames)
            if not has_common_surname:
                return False

    # Layer 5: Character checks
    if any(c.isdigit() for c in name):
        return False
    if len(name) > 30:
        return False

    return True


def _is_valid_location(loc: str) -> bool:
    """Validate that a detected location is genuine."""
    loc_lower = loc.strip().lower()

    if len(loc) < 3:
        return False

    # Universal blacklist check
    if _is_blacklisted(loc):
        return False

    words = loc.split()
    for word in words:
        if word.lower() in _UNIVERSAL_BLACKLIST:
            return False

    # Additional location-specific false positives
    non_location_words = {
        "window", "street", "turnout", "road", "across", "the",
        "murder", "murders", "attack", "ciphers", "zodiac",
        "challenge", "challenges", "fragmentation", "jurisdictional",
        "chapter", "section", "page", "paragraph", "heading",
        "consulate", "embassy", "high commission", "diplomatic",
        "consular", "legation",
        "forum", "channel", "exchange", "subscription", "device",
        "application", "software", "program", "tool",
        "service", "provider", "platform", "system",
    }
    if any(w in loc_lower for w in non_location_words):
        return False

    return True


def _is_valid_organization(org: str) -> bool:
    """Validate that a detected organization is genuine."""
    if len(org) < 3:
        return False

    # Universal blacklist check
    if _is_blacklisted(org):
        return False

    org_lower = org.lower().strip()
    if org_lower in _UNIVERSAL_BLACKLIST:
        return False
    for word in org.split():
        if word.lower().strip(':*-,().!?') in _UNIVERSAL_BLACKLIST:
            return False

    # Reject if any word is purely special chars or mixed alpha-special
    for word in org.split():
        clean = re.sub(r'[^a-zA-Z]', '', word)
        if len(clean) < 2:
            return False

    # Reject all-caps unless it's a known acronym (FBI, CIA, etc.)
    known_acronyms = {"FBI", "CIA", "NSA", "DEA", "ATF", "ICE", "DHS", "DOJ",
                      "INTERPOL", "Europol", "NATO", "UN", "EU", "FEMA",
                      "IRS", "SEC", "CFTC", "FINRA", "SOCOM", "CENTCOM"}
    if org.isupper() and len(org) > 4 and org not in known_acronyms:
        return False

    return True


# ══════════════════════════════════════════════════════════
#  ENTITY EXTRACTION
# ══════════════════════════════════════════════════════════

# Known cities that spaCy may mislabel
KNOWN_CITIES = {
    # India
    "mumbai", "delhi", "chennai", "bangalore", "bengaluru", "kolkata",
    "hyderabad", "pune", "ahmedabad", "jaipur", "lucknow", "kanpur",
    "nagpur", "indore", "bhopal", "patna", "surat", "coimbatore",
    "kochi", "thiruvananthapuram", "trivandrum", "madurai", "mysore",
    "mysuru", "chandigarh", "amritsar", "jodhpur", "guwahati",
    "bhubaneswar", "raipur", "ranchi", "dehradun", "shimla", "goa",
    "panaji", "chengalpattu", "vellore", "salem", "tiruchirappalli",
    "trichy", "erode", "tirunelveli", "ooty", "kodaikanal",
    "navi mumbai", "thane", "nashik", "aurangabad", "kolhapur", "solapur",
    "mangalore", "mangaluru", "hubli", "belgaum", "belagavi",
    "calicut", "kozhikode", "thrissur", "kollam",
    "howrah", "darjeeling", "siliguri",
    "warangal", "nizamabad",
    "rajkot", "jamnagar", "gandhinagar",
    "agra", "varanasi", "noida", "ghaziabad", "meerut",
    "allahabad", "prayagraj",
    "gwalior", "jabalpur", "ujjain",
    "ludhiana", "jalandhar", "patiala",
    "gurgaon", "gurugram", "faridabad", "panipat",
    "cuttack", "puri",
    "jamshedpur", "dhanbad", "bokaro",
    "bilaspur", "durg",
    "haridwar", "rishikesh", "nainital",
    # International
    "london", "new york", "dubai", "singapore", "tokyo",
    "shanghai", "hong kong", "sydney", "toronto", "berlin",
    "paris", "moscow", "bangkok", "kuala lumpur",
    "johannesburg", "nairobi", "cairo", "istanbul",
    "sao paulo", "mexico city", "los angeles", "san francisco",
    "chicago", "miami", "washington", "washington dc",
    "boston", "seattle", "denver", "atlanta", "dallas", "houston",
    "philadelphia", "phoenix", "detroit", "minneapolis", "nashville",
    "las vegas", "orlando", "portland", "austin", "san diego",
    "honolulu", "anchorage",
    "rome", "madrid", "barcelona", "amsterdam", "brussels", "vienna",
    "zurich", "geneva", "stockholm", "oslo", "copenhagen", "helsinki",
    "dublin", "lisbon", "athens", "warsaw", "prague", "budapest",
    "bucharest", "sofia", "zagreb", "belgrade", "kyiv", "kiev",
    "taipei", "seoul", "beijing", "guangzhou", "shenzhen",
    "mumbai", "delhi", "chennai", "bangalore",
    "reykjavik", "lima", "bogota", "buenos aires", "santiago",
    "caracas", "quito", "montevideo", "medellin",
    "casablanca", "tunis", "algiers", "lagos", "accra", "addis ababa",
    "dar es salaam", "kampala", "kigali", "lilongwe",
    "manila", "jakarta", "hanoi", "ho chi minh", "phnom penh",
    "yangon", "vientiane", "colombo", "kathmandu", "dhaka",
    "karachi", "lahore", "islamabad", "rawalpindi",
    "tel aviv", "jerusalem", "doha", "riyadh", "jeddah",
    "abu dhabi", "muscat", "manama", "kuwait city", "amman",
    "beirut", "baghdad", "tehran", "damascus",
}

INDIAN_SURNAMES = {
    "sharma", "patel", "singh", "kumar", "gupta", "reddy", "nair",
    "menon", "das", "shah", "mehta", "verma", "joshi", "iyer",
    "mishra", "choudhary", "tiwari", "pandey", "srivastava", "rao",
    "chowdhury", "banerjee", "mukherjee", "ghosh", "sen", "bose",
    "dutta", "barua", "phukan", "kalita", "saikia", "borah",
    "khan", "ali", "sheikh", "hussain", "ahmad", "ahmed",
    "prasad", "shukla", "sinha", "tripathi", "jha", "pandit",
    "kapoor", "malhotra", "chopra", "khanna", "bhattacharya",
}


def extract_entities(text: str) -> dict:
    """
    Extract all entity types from unstructured text.
    Returns dict with keys: people, locations, phones, vehicles, financial,
    organizations, emails, dates, ip_addresses, addresses
    """
    doc = nlp(text)

    people = set()
    locations = set()
    organizations = set()

    # ── spaCy NER ─────────────────────────────────────────
    for ent in doc.ents:
        raw_text = ent.text.strip()

        # Skip if on universal blacklist
        if _is_blacklisted(raw_text):
            continue

        if ent.label_ == "PERSON":
            # Check if it's actually a known city (spaCy sometimes mislabels)
            if raw_text.lower() in KNOWN_CITIES:
                locations.add(raw_text)
                continue
            if _is_valid_person_name(raw_text, text):
                people.add(raw_text)

        elif ent.label_ in ("GPE", "LOC", "FAC"):
            if _is_valid_location(raw_text):
                locations.add(raw_text)

        elif ent.label_ == "ORG":
            # Check if it's actually a known city
            if raw_text.lower() in KNOWN_CITIES:
                locations.add(raw_text)
                continue
            # Check if it's a person with Indian surname in ORG label
            name_parts = raw_text.split()
            if len(name_parts) == 2 and name_parts[1].lower() in INDIAN_SURNAMES:
                if _is_valid_person_name(raw_text, text):
                    people.add(raw_text)
                    continue
            if _is_valid_organization(raw_text):
                organizations.add(raw_text)

    # ── Regex-based extraction ─────────────────────────────

    # Phone numbers
    phones = list(set(PHONE_REGEX.findall(text)))

    # Vehicles
    vehicles = []
    for match in VEHICLE_PATTERN.finditer(text):
        v = match.group(1).strip()
        words = v.split()
        fixed = []
        for w in words:
            if w.upper() in ('SUV', 'CEO', 'FIR', 'ATM', 'GPS', 'SIM'):
                fixed.append(w.upper())
            elif w.lower() in ('van', 'car', 'truck', 'sedan', 'hatchback', 'motorcycle', 'scooter', 'rickshaw', 'bike'):
                fixed.append(w.lower())
            else:
                fixed.append(w.title())
        v = ' '.join(fixed)
        if v not in vehicles:
            vehicles.append(v)

    # Financial accounts
    financial = []
    for match in re.finditer(r'\bBank\s+Account\s+([A-Z])\b', text, re.IGNORECASE):
        acc = f"Bank Account {match.group(1)}"
        if acc not in financial:
            financial.append(acc)

    # Email addresses
    emails = list(set(EMAIL_REGEX.findall(text)))

    # Dates
    dates = []
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            date_str = match.group(1).strip()
            if len(date_str) >= 4 and date_str not in dates:
                dates.append(date_str)

    # IP addresses
    ip_addresses = list(set(IPV4_REGEX.findall(text) + IPV6_REGEX.findall(text)))

    # Physical addresses
    addresses = []
    for pattern in [ADDRESS_US_REGEX, ADDRESS_INDIA_REGEX, ADDRESS_GENERIC_REGEX]:
        for match in pattern.finditer(text):
            addr = match.group(0).strip()
            if len(addr) >= 8 and addr not in addresses:
                if not VEHICLE_PATTERN.match(addr):
                    addresses.append(addr)

    return {
        "people": sorted(people),
        "locations": sorted(locations),
        "phones": phones,
        "vehicles": vehicles,
        "financial": financial,
        "organizations": sorted(organizations),
        "emails": emails,
        "dates": dates,
        "ip_addresses": ip_addresses,
        "addresses": addresses,
    }


def extract_relations(text: str, entities: dict) -> list:
    """
    Extract relationships between entities from text.
    Returns list of dicts with source, target, relation_type, evidence, priority
    """
    relations = []
    doc = nlp(text)

    verb_patterns = {
        "transferred": "financial_transfer",
        "transfer": "financial_transfer",
        "sent": "financial_transfer",
        "paid": "financial_transfer",
        "contacted": "communication",
        "called": "communication",
        "messaged": "communication",
        "texted": "communication",
        "emailed": "communication",
        "met": "meeting",
        "visited": "visited",
        "lent": "vehicle_lending",
        "borrowed": "vehicle_lending",
        "owned": "ownership",
        "owns": "ownership",
        "registered": "registration",
        "received": "financial_transfer",
        "detected": "detection",
        "arranged": "logistics",
        "accessed": "access",
        "supplied": "supply",
        "provided": "supply",
        "facilitated": "facilitation",
        "coordinated": "coordination",
        "involved": "involvement",
        "linked": "linked",
        "connected": "linked",
        "associated": "linked",
    }

    all_people = entities.get("people", [])

    for sent in doc.sents:
        sent_text = sent.text.lower()
        people_in_sent = [p for p in all_people if p.lower() in sent_text]

        if len(people_in_sent) < 2:
            continue

        rel_type = "linked"
        for verb, label in verb_patterns.items():
            if verb in sent_text:
                rel_type = label
                break

        for i in range(len(people_in_sent)):
            for j in range(i + 1, len(people_in_sent)):
                relations.append({
                    "source": people_in_sent[i],
                    "target": people_in_sent[j],
                    "relation_type": rel_type,
                    "evidence": sent.text.strip(),
                    "priority": "high" if rel_type in ("financial_transfer", "communication") else "supporting",
                })

    return relations
