"""
CrimeGraph AI — Live Crime News Globe

Fetches real-time crime news from RSS feeds and world news APIs,
maps them to coordinates, and serves them to the 3D globe.
"""

import json
import re
import logging
import hashlib
from datetime import datetime, timedelta
from fastapi import APIRouter
from xml.etree import ElementTree as ET
import urllib.request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# ── Curated crime news RSS feeds ────────────────────────
RSS_FEEDS = [
    {
        "name": "BBC World",
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "type": "world",
    },
    {
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "type": "world",
    },
    {
        "name": "Reuters World",
        "url": "https://www.reutersagency.com/feed/?best-topics=security&post_type=best",
        "type": "world",
    },
    {
        "name": "NPR Crime",
        "url": "https://feeds.npr.org/1004/rss.xml",
        "type": "crime",
    },
    {
        "name": "CNN Crime",
        "url": "http://rss.cnn.com/rss/crimejustice.rss",
        "type": "crime",
    },
    {
        "name": "The Guardian Crime",
        "url": "https://www.theguardian.com/uk/crime/rss",
        "type": "crime",
    },
]

# ── Location to coordinates mapping ─────────────────────
LOCATION_COORDS = {
    # Americas
    "new york": (40.7128, -74.0060), "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298), "miami": (25.7617, -80.1918),
    "houston": (29.7604, -95.3698), "phoenix": (33.4484, -112.0740),
    "san francisco": (37.7749, -122.4194), "dallas": (32.7767, -96.7970),
    "seattle": (47.6062, -122.3321), "boston": (42.3601, -71.0589),
    "washington": (38.9072, -77.0369), "atlanta": (33.7490, -84.3880),
    "denver": (39.7392, -104.9903), "detroit": (42.3314, -83.0458),
    "portland": (45.5152, -122.6784), "nashville": (36.1627, -86.7816),
    "las vegas": (36.1699, -115.1398), "austin": (30.2672, -97.7431),
    "mexico city": (19.4326, -99.1332), "toronto": (43.6532, -79.3832),
    "vancouver": (49.2827, -123.1207), "sao paulo": (-23.5505, -46.6333),
    "buenos aires": (-34.6037, -58.3816), "bogota": (4.7110, -74.0721),
    "lima": (-12.0464, -77.0428), "brazil": (-14.2350, -51.9253),
    "colombia": (4.5709, -74.2973),
    # Europe
    "london": (51.5074, -0.1278), "paris": (48.8566, 2.3522),
    "berlin": (52.5200, 13.4050), "madrid": (40.4168, -3.7038),
    "rome": (41.9028, 12.4964), "amsterdam": (52.3676, 4.9041),
    "vienna": (48.2082, 16.3738), "prague": (50.0755, 14.4378),
    "warsaw": (52.2297, 21.0122), "budapest": (47.4979, 19.0402),
    "stockholm": (59.3293, 18.0686), "oslo": (59.9139, 10.7522),
    "copenhagen": (55.6761, 12.5683), "helsinki": (60.1699, 24.9384),
    "dublin": (53.3498, -6.2603), "lisbon": (38.7223, -9.1393),
    "athens": (37.9838, 23.7275), "zurich": (47.3769, 8.5417),
    "brussels": (50.8503, 4.3517), "moscow": (55.7558, 37.6173),
    "istanbul": (41.0082, 28.9784), "ukraine": (48.3794, 31.1656),
    "romania": (45.9432, 24.9668),
    # Asia
    "tokyo": (35.6762, 139.6503), "beijing": (39.9042, 116.4074),
    "shanghai": (31.2304, 121.4737), "mumbai": (19.0760, 72.8777),
    "delhi": (28.7041, 77.1025), "bangalore": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707), "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867), "pune": (18.5204, 73.8567),
    "dubai": (25.2048, 55.2708), "abu dhabi": (24.4539, 54.3773),
    "doha": (25.2854, 51.5310), "singapore": (1.3521, 103.8198),
    "hong kong": (22.3193, 114.1694), "taipei": (25.0330, 121.5654),
    "bangkok": (13.7563, 100.5018), "jakarta": (-6.2088, 106.8456),
    "manila": (14.5995, 120.9842), "seoul": (37.5665, 126.9780),
    "karachi": (24.8607, 67.0011), "lahore": (31.5204, 74.3587),
    "tehran": (35.6892, 51.3890), "baghdad": (33.3152, 44.3661),
    "riyadh": (24.7136, 46.6753), "jeddah": (21.5433, 39.1728),
    "kuwait": (29.3759, 47.9774), "japan": (36.2048, 138.2529),
    "india": (20.5937, 78.9629), "china": (35.8617, 104.1954),
    "pakistan": (30.3753, 69.3451),
    # Africa
    "cairo": (30.0444, 31.2357), "cape town": (-33.9249, 18.4241),
    "lagos": (6.5244, 3.3792), "nairobi": (-1.2921, 36.8219),
    "johannesburg": (-26.2041, 28.0473), "casablanca": (33.5731, -7.5898),
    "ethiopia": (9.1450, 40.4897), "nigeria": (9.0820, 8.6753),
    "south africa": (-30.5595, 22.9375), "kenya": (-0.0236, 37.9062),
    "egypt": (26.8206, 30.8025),
    # Oceania
    "sydney": (-33.8688, 151.2093), "melbourne": (-37.8136, 144.9631),
    "auckland": (-36.8485, 174.7633), "australia": (-25.2744, 133.7751),
    # Common terms
    "global": (20, 0), "world": (20, 0), "international": (20, 0),
    "uk": (55.3781, -3.4360), "usa": (37.0902, -95.7129),
    "united states": (37.0902, -95.7129), "america": (37.0902, -95.7129),
    "europe": (50.0, 10.0), "asia": (30.0, 100.0), "africa": (5.0, 20.0),
    "middle east": (29.0, 47.0), "latin america": (-15.0, -60.0),
}

# ── Crime keywords for filtering ────────────────────────
CRIME_KEYWORDS = [
    "crime", "murder", "killing", "homicide", "shooting", "stabbing",
    "assault", "robbery", "burglary", "theft", "stolen", "kidnapping",
    "abduction", "arrest", "suspect", "police", "investigation",
    "suspicious", "incident", "attack", "bomb", "terrorism", "terror",
    "drug", "trafficking", "smuggling", "fraud", "cybercrime", "hack",
    "organized crime", "gang", "cartel", "smuggling", "extortion",
    "ransom", "hostage", "missing", "found dead", "body found",
    "crime scene", "evidence", "convicted", "sentenced", "verdict",
    "indicted", "bail", "custody", "detained", "seized", "raided",
    "emergency", "warning", "threat", "danger", "violation",
]


def _fetch_rss(url: str, timeout: int = 8) -> list:
    """Fetch and parse an RSS feed, return list of items."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "CrimeGraphAI/1.0 (RSS Reader)"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8", errors="replace")
        root = ET.fromstring(data)
        items = []
        # Handle both RSS 2.0 and Atom
        for item in root.iter():
            if item.tag == "item" or item.tag.endswith("}entry"):
                title = ""
                desc = ""
                link = ""
                pub_date = ""
                for child in item:
                    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if tag == "title":
                        title = child.text or ""
                    elif tag in ("description", "summary", "content"):
                        desc = child.text or ""
                    elif tag == "link":
                        link = child.text or child.get("href", "")
                    elif tag in ("pubDate", "published", "updated", "dc:date"):
                        pub_date = child.text or ""
                if title:
                    items.append({
                        "title": title.strip(),
                        "description": re.sub(r"<[^>]+>", "", desc)[:300].strip(),
                        "link": link.strip(),
                        "pubDate": pub_date.strip(),
                    })
        return items[:15]  # Limit per feed
    except Exception as e:
        logger.warning(f"RSS fetch failed for {url}: {e}")
        return []


def _extract_location(text: str) -> tuple:
    """Try to extract a location and return (lat, lng) or None."""
    text_lower = text.lower()
    # Check for city/country mentions
    for loc, coords in sorted(LOCATION_COORDS.items(), key=lambda x: -len(x[0])):
        if loc in text_lower:
            # Add small random offset so markers don't stack
            h = int(hashlib.md5(loc.encode()).hexdigest()[:4], 16)
            offset_lat = ((h % 100) - 50) * 0.05
            offset_lng = (((h >> 8) % 100) - 50) * 0.05
            return (coords[0] + offset_lat, coords[1] + offset_lng)
    return None


def _is_crime_related(title: str, desc: str) -> bool:
    combined = (title + " " + desc).lower()
    return any(kw in combined for kw in CRIME_KEYWORDS)


_cache = {"data": None, "timestamp": 0}


@router.get("/crime-news")
async def get_crime_news():
    import time
    now = time.time()
    if _cache["data"] and (now - _cache["timestamp"]) < 300:
        return _cache["data"]
    all_news = []
    seen_titles = set()
    for feed in RSS_FEEDS:
        items = _fetch_rss(feed["url"])
        for item in items:
            title = item["title"]
            if title.lower() in seen_titles: continue
            seen_titles.add(title.lower())
            coords = _extract_location(title + " " + item["description"])
            if coords is None: continue
            is_crime = _is_crime_related(title, item["description"])
            all_news.append({"id": hashlib.md5(title.encode()).hexdigest()[:12], "title": title, "description": item["description"], "source": feed["name"], "type": feed["type"], "is_crime": is_crime, "lat": coords[0], "lng": coords[1], "link": item["link"], "pubDate": item["pubDate"]})
    all_news.sort(key=lambda x: (-x["is_crime"], x["pubDate"]), reverse=True)
    if not all_news:
        all_news = _get_demo_news()
    result = {"items": all_news[:50], "total": len(all_news), "crime_count": sum(1 for n in all_news if n["is_crime"]), "updated_at": datetime.now().isoformat(), "sources": list(set(n["source"] for n in all_news))}
    _cache["data"] = result
    _cache["timestamp"] = now
    return result


def _get_demo_news():
    return [
        {"id": "demo1", "title": "Major Drug Trafficking Dismantled in Mexico City", "description": "Mexican authorities dismantled a drug trafficking ring.", "source": "Reuters", "type": "crime", "is_crime": True, "lat": 19.43, "lng": -99.13, "link": "#", "pubDate": ""},
        {"id": "demo2", "title": "Cybercrime Syndicate Arrested in Moscow", "description": "Russian police arrested cybercrime members.", "source": "BBC", "type": "crime", "is_crime": True, "lat": 55.76, "lng": 37.62, "link": "#", "pubDate": ""},
        {"id": "demo3", "title": "Armed Robbery at London Jewellery Store", "description": "Four suspects in armed robbery in central London.", "source": "Guardian", "type": "crime", "is_crime": True, "lat": 51.51, "lng": -0.13, "link": "#", "pubDate": ""},
        {"id": "demo4", "title": "Kidnapping Ring Busted in Lagos", "description": "Nigerian police broke up a kidnapping ring.", "source": "Al Jazeera", "type": "crime", "is_crime": True, "lat": 6.52, "lng": 3.38, "link": "#", "pubDate": ""},
        {"id": "demo5", "title": "Terror Plot Foiled in Paris", "description": "French agencies foiled a terror plot.", "source": "Reuters", "type": "crime", "is_crime": True, "lat": 48.86, "lng": 2.35, "link": "#", "pubDate": ""},
        {"id": "demo6", "title": "Organized Crime Raid in Tokyo", "description": "Japanese police raided Yakuza offices.", "source": "NHK", "type": "crime", "is_crime": True, "lat": 35.68, "lng": 139.65, "link": "#", "pubDate": ""},
        {"id": "demo7", "title": "Human Trafficking Dismantled in Dubai", "description": "UAE dismantled trafficking network.", "source": "Al Jazeera", "type": "crime", "is_crime": True, "lat": 25.20, "lng": 55.27, "link": "#", "pubDate": ""},
        {"id": "demo8", "title": "Bank Heist Attempt in Sao Paulo", "description": "Armed robbers attempted bank heist.", "source": "Reuters", "type": "crime", "is_crime": True, "lat": -23.55, "lng": -46.63, "link": "#", "pubDate": ""},
        {"id": "demo9", "title": "Mumbai Drug Bust Seizes Narcotics", "description": "Indian authorities seized narcotics at port.", "source": "NDTV", "type": "crime", "is_crime": True, "lat": 19.08, "lng": 72.88, "link": "#", "pubDate": ""},
        {"id": "demo10", "title": "Mass Shooting in Chicago", "description": "Multiple casualties in shooting incident.", "source": "CNN", "type": "crime", "is_crime": True, "lat": 41.88, "lng": -87.63, "link": "#", "pubDate": ""},
        {"id": "demo11", "title": "Wildfire Emergency in California", "description": "Governor declares emergency for wildfires.", "source": "AP", "type": "world", "is_crime": False, "lat": 34.05, "lng": -118.24, "link": "#", "pubDate": ""},
        {"id": "demo12", "title": "Protests Escalate in Berlin", "description": "Large protests in Berlin.", "source": "DW", "type": "world", "is_crime": False, "lat": 52.52, "lng": 13.41, "link": "#", "pubDate": ""},
        {"id": "demo13", "title": "Earthquake Hits Istanbul", "description": "6.2 magnitude earthquake in Istanbul.", "source": "Reuters", "type": "world", "is_crime": False, "lat": 41.01, "lng": 28.98, "link": "#", "pubDate": ""},
        {"id": "demo14", "title": "Animal Smuggling Intercepted in Sydney", "description": "Illegal animal trafficking ring intercepted.", "source": "ABC", "type": "crime", "is_crime": True, "lat": -33.87, "lng": 151.21, "link": "#", "pubDate": ""},
        {"id": "demo15", "title": "Bitcoin Fraud Arrested in Seoul", "description": "South Korean police arrested fraud suspects.", "source": "Yonhap", "type": "crime", "is_crime": True, "lat": 37.57, "lng": 126.98, "link": "#", "pubDate": ""},
        {"id": "demo16", "title": "Arms Cache Seized in Nairobi", "description": "Kenyan authorities seized weapons cache.", "source": "Nation", "type": "crime", "is_crime": True, "lat": -1.29, "lng": 36.82, "link": "#", "pubDate": ""},
        {"id": "demo17", "title": "Fraud Case in Singapore", "description": "Police uncovered financial fraud.", "source": "ST", "type": "crime", "is_crime": True, "lat": 1.35, "lng": 103.82, "link": "#", "pubDate": ""},
        {"id": "demo18", "title": "Gang Violence in Bogota", "description": "Surge in gang-related violence.", "source": "El Tiempo", "type": "crime", "is_crime": True, "lat": 4.71, "lng": -74.07, "link": "#", "pubDate": ""},
    ]
