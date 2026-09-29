"""
Geocoding Service — Maps location names to lat/lng coordinates.

Uses a comprehensive built-in database of global cities for fast lookup,
with Nominatim (OpenStreetMap) API as fallback for unknown locations.
No country restrictions — works worldwide.
"""

import re
import json
import urllib.request
import urllib.parse
import time
from typing import Optional

# ── Built-in Global City Database ──────────────────────────
# Comprehensive database of cities worldwide
INDIAN_LOCATIONS = {
    # ═══ INDIA ═══
    # Major Cities
    "mumbai": {"lat": 19.0760, "lng": 72.8777, "state": "Maharashtra", "country": "India"},
    "delhi": {"lat": 28.6139, "lng": 77.2090, "state": "Delhi", "country": "India"},
    "new delhi": {"lat": 28.6139, "lng": 77.2090, "state": "Delhi", "country": "India"},
    "bangalore": {"lat": 12.9716, "lng": 77.5946, "state": "Karnataka", "country": "India"},
    "bengaluru": {"lat": 12.9716, "lng": 77.5946, "state": "Karnataka", "country": "India"},
    "chennai": {"lat": 13.0827, "lng": 80.2707, "state": "Tamil Nadu", "country": "India"},
    "kolkata": {"lat": 22.5726, "lng": 88.3639, "state": "West Bengal", "country": "India"},
    "hyderabad": {"lat": 17.3850, "lng": 78.4867, "state": "Telangana", "country": "India"},
    "pune": {"lat": 18.5204, "lng": 73.8567, "state": "Maharashtra", "country": "India"},
    "ahmedabad": {"lat": 23.0225, "lng": 72.5714, "state": "Gujarat", "country": "India"},
    "jaipur": {"lat": 26.9124, "lng": 75.7873, "state": "Rajasthan", "country": "India"},
    "lucknow": {"lat": 26.8467, "lng": 80.9462, "state": "Uttar Pradesh", "country": "India"},
    "kanpur": {"lat": 26.4499, "lng": 80.3319, "state": "Uttar Pradesh", "country": "India"},
    "nagpur": {"lat": 21.1458, "lng": 79.0882, "state": "Maharashtra", "country": "India"},
    "indore": {"lat": 22.7196, "lng": 75.8577, "state": "Madhya Pradesh", "country": "India"},
    "bhopal": {"lat": 23.2599, "lng": 77.4126, "state": "Madhya Pradesh", "country": "India"},
    "patna": {"lat": 25.6093, "lng": 85.1376, "state": "Bihar", "country": "India"},
    "vadodara": {"lat": 22.3072, "lng": 73.1812, "state": "Gujarat", "country": "India"},
    "surat": {"lat": 21.1702, "lng": 72.8311, "state": "Gujarat", "country": "India"},
    "coimbatore": {"lat": 11.0168, "lng": 76.9558, "state": "Tamil Nadu", "country": "India"},
    "kochi": {"lat": 9.9312, "lng": 76.2673, "state": "Kerala", "country": "India"},
    "thiruvananthapuram": {"lat": 8.5241, "lng": 76.9366, "state": "Kerala", "country": "India"},
    "trivandrum": {"lat": 8.5241, "lng": 76.9366, "state": "Kerala", "country": "India"},
    "madurai": {"lat": 9.9252, "lng": 78.1198, "state": "Tamil Nadu", "country": "India"},
    "mysore": {"lat": 12.2958, "lng": 76.6394, "state": "Karnataka", "country": "India"},
    "mysuru": {"lat": 12.2958, "lng": 76.6394, "state": "Karnataka", "country": "India"},
    "chandigarh": {"lat": 30.7333, "lng": 76.7794, "state": "Chandigarh", "country": "India"},
    "amritsar": {"lat": 31.6340, "lng": 74.8723, "state": "Punjab", "country": "India"},
    "jodhpur": {"lat": 26.2389, "lng": 73.0243, "state": "Rajasthan", "country": "India"},
    "udaipur": {"lat": 24.5854, "lng": 73.7125, "state": "Rajasthan", "country": "India"},
    "guwahati": {"lat": 26.1445, "lng": 91.7362, "state": "Assam", "country": "India"},
    "bhubaneswar": {"lat": 20.2961, "lng": 85.8245, "state": "Odisha", "country": "India"},
    "raipur": {"lat": 21.2514, "lng": 81.6296, "state": "Chhattisgarh", "country": "India"},
    "ranchi": {"lat": 23.3441, "lng": 85.3096, "state": "Jharkhand", "country": "India"},
    "dehradun": {"lat": 30.3165, "lng": 78.0322, "state": "Uttarakhand", "country": "India"},
    "shimla": {"lat": 31.1048, "lng": 77.1734, "state": "Himachal Pradesh", "country": "India"},
    "manali": {"lat": 32.2396, "lng": 77.1887, "state": "Himachal Pradesh", "country": "India"},
    "goa": {"lat": 15.2993, "lng": 74.1240, "state": "Goa", "country": "India"},
    "panaji": {"lat": 15.4909, "lng": 73.8278, "state": "Goa", "country": "India"},
    "chengalpattu": {"lat": 12.6914, "lng": 79.9770, "state": "Tamil Nadu", "country": "India"},
    "chengalpattu storage facility": {"lat": 12.6914, "lng": 79.9770, "state": "Tamil Nadu", "country": "India"},
    "chennai warehouse": {"lat": 13.0827, "lng": 80.2707, "state": "Tamil Nadu", "country": "India"},
    "vellore": {"lat": 12.9165, "lng": 79.1325, "state": "Tamil Nadu", "country": "India"},
    "salem": {"lat": 11.6643, "lng": 78.1460, "state": "Tamil Nadu", "country": "India"},
    "tiruchirappalli": {"lat": 10.7905, "lng": 78.7047, "state": "Tamil Nadu", "country": "India"},
    "trichy": {"lat": 10.7905, "lng": 78.7047, "state": "Tamil Nadu", "country": "India"},
    "erode": {"lat": 11.3410, "lng": 77.7172, "state": "Tamil Nadu", "country": "India"},
    "tirunelveli": {"lat": 8.7139, "lng": 77.7567, "state": "Tamil Nadu", "country": "India"},
    "ooty": {"lat": 11.4102, "lng": 76.6950, "state": "Tamil Nadu", "country": "India"},
    "kodaikanal": {"lat": 10.2381, "lng": 77.4892, "state": "Tamil Nadu", "country": "India"},
    "navi mumbai": {"lat": 19.0330, "lng": 73.0297, "state": "Maharashtra", "country": "India"},
    "thane": {"lat": 19.2183, "lng": 72.9781, "state": "Maharashtra", "country": "India"},
    "nashik": {"lat": 19.9975, "lng": 73.7898, "state": "Maharashtra", "country": "India"},
    "aurangabad": {"lat": 19.8762, "lng": 75.3433, "state": "Maharashtra", "country": "India"},
    "kolhapur": {"lat": 16.7050, "lng": 74.2433, "state": "Maharashtra", "country": "India"},
    "solapur": {"lat": 17.6599, "lng": 75.9064, "state": "Maharashtra", "country": "India"},
    "mangalore": {"lat": 12.9141, "lng": 74.8560, "state": "Karnataka", "country": "India"},
    "mangaluru": {"lat": 12.9141, "lng": 74.8560, "state": "Karnataka", "country": "India"},
    "hubli": {"lat": 15.3647, "lng": 75.1240, "state": "Karnataka", "country": "India"},
    "belgaum": {"lat": 15.8497, "lng": 74.4977, "state": "Karnataka", "country": "India"},
    "belagavi": {"lat": 15.8497, "lng": 74.4977, "state": "Karnataka", "country": "India"},
    "calicut": {"lat": 11.2588, "lng": 75.7804, "state": "Kerala", "country": "India"},
    "kozhikode": {"lat": 11.2588, "lng": 75.7804, "state": "Kerala", "country": "India"},
    "thrissur": {"lat": 10.5276, "lng": 76.2144, "state": "Kerala", "country": "India"},
    "kollam": {"lat": 8.8932, "lng": 76.6141, "state": "Kerala", "country": "India"},
    "kottayam": {"lat": 9.5916, "lng": 76.5223, "state": "Kerala", "country": "India"},
    "howrah": {"lat": 22.5958, "lng": 88.2636, "state": "West Bengal", "country": "India"},
    "darjeeling": {"lat": 27.0360, "lng": 88.2627, "state": "West Bengal", "country": "India"},
    "siliguri": {"lat": 26.7271, "lng": 88.3953, "state": "West Bengal", "country": "India"},
    "warangal": {"lat": 17.9784, "lng": 79.5941, "state": "Telangana", "country": "India"},
    "nizamabad": {"lat": 18.6725, "lng": 78.0940, "state": "Telangana", "country": "India"},
    "rajkot": {"lat": 22.3039, "lng": 70.8022, "state": "Gujarat", "country": "India"},
    "jamnagar": {"lat": 22.4707, "lng": 70.0577, "state": "Gujarat", "country": "India"},
    "gandhinagar": {"lat": 23.2156, "lng": 72.6369, "state": "Gujarat", "country": "India"},
    "agra": {"lat": 27.1767, "lng": 78.0081, "state": "Uttar Pradesh", "country": "India"},
    "varanasi": {"lat": 25.3176, "lng": 82.9739, "state": "Uttar Pradesh", "country": "India"},
    "noida": {"lat": 28.5355, "lng": 77.3910, "state": "Uttar Pradesh", "country": "India"},
    "ghaziabad": {"lat": 28.6692, "lng": 77.4538, "state": "Uttar Pradesh", "country": "India"},
    "meerut": {"lat": 28.9845, "lng": 77.7064, "state": "Uttar Pradesh", "country": "India"},
    "allahabad": {"lat": 25.4358, "lng": 81.8463, "state": "Uttar Pradesh", "country": "India"},
    "prayagraj": {"lat": 25.4358, "lng": 81.8463, "state": "Uttar Pradesh", "country": "India"},
    "gwalior": {"lat": 26.2183, "lng": 78.1828, "state": "Madhya Pradesh", "country": "India"},
    "jabalpur": {"lat": 23.1815, "lng": 79.9864, "state": "Madhya Pradesh", "country": "India"},
    "ujjain": {"lat": 23.1793, "lng": 75.7849, "state": "Madhya Pradesh", "country": "India"},
    "ludhiana": {"lat": 30.9010, "lng": 75.8573, "state": "Punjab", "country": "India"},
    "jalandhar": {"lat": 31.3260, "lng": 75.5762, "state": "Punjab", "country": "India"},
    "patiala": {"lat": 30.3398, "lng": 76.3869, "state": "Punjab", "country": "India"},
    "gurgaon": {"lat": 28.4595, "lng": 77.0266, "state": "Haryana", "country": "India"},
    "gurugram": {"lat": 28.4595, "lng": 77.0266, "state": "Haryana", "country": "India"},
    "faridabad": {"lat": 28.4089, "lng": 77.3178, "state": "Haryana", "country": "India"},
    "panipat": {"lat": 29.3909, "lng": 76.9635, "state": "Haryana", "country": "India"},
    "cuttack": {"lat": 20.4625, "lng": 85.8830, "state": "Odisha", "country": "India"},
    "puri": {"lat": 19.8135, "lng": 85.8312, "state": "Odisha", "country": "India"},
    "dibrugarh": {"lat": 27.4728, "lng": 94.9120, "state": "Assam", "country": "India"},
    "jorhat": {"lat": 26.7509, "lng": 94.2037, "state": "Assam", "country": "India"},
    "jamshedpur": {"lat": 22.8046, "lng": 86.2029, "state": "Jharkhand", "country": "India"},
    "dhanbad": {"lat": 23.7957, "lng": 86.4304, "state": "Jharkhand", "country": "India"},
    "bokaro": {"lat": 23.6693, "lng": 86.1511, "state": "Jharkhand", "country": "India"},
    "bilaspur": {"lat": 22.0797, "lng": 82.1409, "state": "Chhattisgarh", "country": "India"},
    "durg": {"lat": 21.1924, "lng": 81.2849, "state": "Chhattisgarh", "country": "India"},
    "haridwar": {"lat": 29.9457, "lng": 78.1642, "state": "Uttarakhand", "country": "India"},
    "rishikesh": {"lat": 30.0869, "lng": 78.2676, "state": "Uttarakhand", "country": "India"},
    "nainital": {"lat": 29.3816, "lng": 79.4493, "state": "Uttarakhand", "country": "India"},

    # Indian Landmarks
    "india gate": {"lat": 28.6129, "lng": 77.2295, "state": "Delhi", "country": "India"},
    "red fort": {"lat": 28.6562, "lng": 77.2410, "state": "Delhi", "country": "India"},
    "taj mahal": {"lat": 27.1751, "lng": 78.0421, "state": "Uttar Pradesh", "country": "India"},
    "gateway of india": {"lat": 18.9220, "lng": 72.8347, "state": "Maharashtra", "country": "India"},
    "marine drive": {"lat": 18.9432, "lng": 72.8234, "state": "Maharashtra", "country": "India"},
    "charminar": {"lat": 17.3616, "lng": 78.4747, "state": "Telangana", "country": "India"},
    "golden temple": {"lat": 31.6200, "lng": 74.8765, "state": "Punjab", "country": "India"},

    # ═══ NORTH AMERICA ═══
    "new york": {"lat": 40.7128, "lng": -74.0060, "state": "New York", "country": "United States"},
    "los angeles": {"lat": 34.0522, "lng": -118.2437, "state": "California", "country": "United States"},
    "san francisco": {"lat": 37.7749, "lng": -122.4194, "state": "California", "country": "United States"},
    "chicago": {"lat": 41.8781, "lng": -87.6298, "state": "Illinois", "country": "United States"},
    "houston": {"lat": 29.7604, "lng": -95.3698, "state": "Texas", "country": "United States"},
    "phoenix": {"lat": 33.4484, "lng": -112.0740, "state": "Arizona", "country": "United States"},
    "philadelphia": {"lat": 39.9526, "lng": -75.1652, "state": "Pennsylvania", "country": "United States"},
    "san antonio": {"lat": 29.4241, "lng": -98.4936, "state": "Texas", "country": "United States"},
    "san diego": {"lat": 32.7157, "lng": -117.1611, "state": "California", "country": "United States"},
    "dallas": {"lat": 32.7767, "lng": -96.7970, "state": "Texas", "country": "United States"},
    "san jose": {"lat": 37.3382, "lng": -121.8863, "state": "California", "country": "United States"},
    "austin": {"lat": 30.2672, "lng": -97.7431, "state": "Texas", "country": "United States"},
    "jacksonville": {"lat": 30.3322, "lng": -81.6557, "state": "Florida", "country": "United States"},
    "fort worth": {"lat": 32.7555, "lng": -97.3308, "state": "Texas", "country": "United States"},
    "columbus": {"lat": 39.9612, "lng": -82.9988, "state": "Ohio", "country": "United States"},
    "charlotte": {"lat": 35.2271, "lng": -80.8431, "state": "North Carolina", "country": "United States"},
    "indianapolis": {"lat": 39.7684, "lng": -86.1581, "state": "Indiana", "country": "United States"},
    "san francisco": {"lat": 37.7749, "lng": -122.4194, "state": "California", "country": "United States"},
    "seattle": {"lat": 47.6062, "lng": -122.3321, "state": "Washington", "country": "United States"},
    "denver": {"lat": 39.7392, "lng": -104.9903, "state": "Colorado", "country": "United States"},
    "washington": {"lat": 38.9072, "lng": -77.0369, "state": "District of Columbia", "country": "United States"},
    "washington dc": {"lat": 38.9072, "lng": -77.0369, "state": "District of Columbia", "country": "United States"},
    "boston": {"lat": 42.3601, "lng": -71.0589, "state": "Massachusetts", "country": "United States"},
    "el paso": {"lat": 31.7619, "lng": -106.4850, "state": "Texas", "country": "United States"},
    "nashville": {"lat": 36.1627, "lng": -86.7816, "state": "Tennessee", "country": "United States"},
    "detroit": {"lat": 42.3314, "lng": -83.0458, "state": "Michigan", "country": "United States"},
    "oklahoma city": {"lat": 35.4676, "lng": -97.5164, "state": "Oklahoma", "country": "United States"},
    "portland": {"lat": 45.5152, "lng": -122.6784, "state": "Oregon", "country": "United States"},
    "las vegas": {"lat": 36.1699, "lng": -115.1398, "state": "Nevada", "country": "United States"},
    "memphis": {"lat": 35.1495, "lng": -90.0490, "state": "Tennessee", "country": "United States"},
    "louisville": {"lat": 38.2527, "lng": -85.7585, "state": "Kentucky", "country": "United States"},
    "baltimore": {"lat": 39.2904, "lng": -76.6122, "state": "Maryland", "country": "United States"},
    "milwaukee": {"lat": 43.0389, "lng": -87.9065, "state": "Wisconsin", "country": "United States"},
    "albuquerque": {"lat": 35.0844, "lng": -106.6504, "state": "New Mexico", "country": "United States"},
    "tucson": {"lat": 32.2226, "lng": -110.9747, "state": "Arizona", "country": "United States"},
    "fresno": {"lat": 36.7378, "lng": -119.7871, "state": "California", "country": "United States"},
    "sacramento": {"lat": 38.5816, "lng": -121.4944, "state": "California", "country": "United States"},
    "miami": {"lat": 25.7617, "lng": -80.1918, "state": "Florida", "country": "United States"},
    "atlanta": {"lat": 33.7490, "lng": -84.3880, "state": "Georgia", "country": "United States"},
    "minneapolis": {"lat": 44.9778, "lng": -93.2650, "state": "Minnesota", "country": "United States"},
    "new orleans": {"lat": 29.9511, "lng": -90.0715, "state": "Louisiana", "country": "United States"},
    "honolulu": {"lat": 21.3069, "lng": -157.8583, "state": "Hawaii", "country": "United States"},
    "anchorage": {"lat": 61.2181, "lng": -149.9003, "state": "Alaska", "country": "United States"},
    "pittsburgh": {"lat": 40.4406, "lng": -79.9959, "state": "Pennsylvania", "country": "United States"},
    "cincinnati": {"lat": 39.1031, "lng": -84.5120, "state": "Ohio", "country": "United States"},
    "st louis": {"lat": 38.6270, "lng": -90.1994, "state": "Missouri", "country": "United States"},
    "kansas city": {"lat": 39.0997, "lng": -94.5786, "state": "Missouri", "country": "United States"},
    "havana": {"lat": 23.1136, "lng": -82.3666, "state": "La Habana", "country": "Canada"},
    "toronto": {"lat": 43.6532, "lng": -79.3832, "state": "Ontario", "country": "Canada"},
    "vancouver": {"lat": 49.2827, "lng": -123.1207, "state": "British Columbia", "country": "Canada"},
    "montreal": {"lat": 45.5017, "lng": -73.5673, "state": "Quebec", "country": "Canada"},
    "calgary": {"lat": 51.0447, "lng": -114.0719, "state": "Alberta", "country": "Canada"},
    "ottawa": {"lat": 45.4215, "lng": -75.6972, "state": "Ontario", "country": "Canada"},
    "edmonton": {"lat": 53.5461, "lng": -113.4938, "state": "Alberta", "country": "Canada"},
    "winnipeg": {"lat": 49.8951, "lng": -97.1384, "state": "Manitoba", "country": "Canada"},
    "mexico city": {"lat": 19.4326, "lng": -99.1332, "state": "Mexico City", "country": "Mexico"},
    "guadalajara": {"lat": 20.6597, "lng": -103.3496, "state": "Jalisco", "country": "Mexico"},
    "monterrey": {"lat": 25.6866, "lng": -100.3161, "state": "Nuevo Leon", "country": "Mexico"},
    "cancun": {"lat": 21.1619, "lng": -86.8515, "state": "Quintana Roo", "country": "Mexico"},
    "tijuana": {"lat": 32.5149, "lng": -117.0382, "state": "Baja California", "country": "Mexico"},

    # ═══ EUROPE ═══
    "london": {"lat": 51.5074, "lng": -0.1278, "state": "England", "country": "United Kingdom"},
    "manchester": {"lat": 53.4808, "lng": -2.2426, "state": "England", "country": "United Kingdom"},
    "birmingham": {"lat": 52.4862, "lng": -1.8904, "state": "England", "country": "United Kingdom"},
    "glasgow": {"lat": 55.8642, "lng": -4.2518, "state": "Scotland", "country": "United Kingdom"},
    "edinburgh": {"lat": 55.9533, "lng": -3.1883, "state": "Scotland", "country": "United Kingdom"},
    "paris": {"lat": 48.8566, "lng": 2.3522, "state": "Ile-de-France", "country": "France"},
    "marseille": {"lat": 43.2965, "lng": 5.3698, "state": "Provence-Alpes-Cote d'Azur", "country": "France"},
    "lyon": {"lat": 45.7640, "lng": 4.8357, "state": "Auvergne-Rhone-Alpes", "country": "France"},
    "berlin": {"lat": 52.5200, "lng": 13.4050, "state": "Berlin", "country": "Germany"},
    "munich": {"lat": 48.1351, "lng": 11.5820, "state": "Bavaria", "country": "Germany"},
    "hamburg": {"lat": 53.5511, "lng": 9.9937, "state": "Hamburg", "country": "Germany"},
    "frankfurt": {"lat": 50.1109, "lng": 8.6821, "state": "Hesse", "country": "Germany"},
    "cologne": {"lat": 50.9375, "lng": 6.9603, "state": "North Rhine-Westphalia", "country": "Germany"},
    "rome": {"lat": 41.9028, "lng": 12.4964, "state": "Lazio", "country": "Italy"},
    "milan": {"lat": 45.4642, "lng": 9.1900, "state": "Lombardy", "country": "Italy"},
    "naples": {"lat": 40.8518, "lng": 14.2681, "state": "Campania", "country": "Italy"},
    "turin": {"lat": 45.0703, "lng": 7.6869, "state": "Piedmont", "country": "Italy"},
    "madrid": {"lat": 40.4168, "lng": -3.7038, "state": "Madrid", "country": "Spain"},
    "barcelona": {"lat": 41.3874, "lng": 2.1686, "state": "Catalonia", "country": "Spain"},
    "amsterdam": {"lat": 52.3676, "lng": 4.9041, "state": "North Holland", "country": "Netherlands"},
    "rotterdam": {"lat": 51.9244, "lng": 4.4777, "state": "South Holland", "country": "Netherlands"},
    "brussels": {"lat": 50.8503, "lng": 4.3517, "state": "Brussels-Capital", "country": "Belgium"},
    "vienna": {"lat": 48.2082, "lng": 16.3738, "state": "Vienna", "country": "Austria"},
    "zurich": {"lat": 47.3769, "lng": 8.5417, "state": "Zurich", "country": "Switzerland"},
    "geneva": {"lat": 46.2044, "lng": 6.1432, "state": "Geneva", "country": "Switzerland"},
    "stockholm": {"lat": 59.3293, "lng": 18.0686, "state": "Stockholm", "country": "Sweden"},
    "oslo": {"lat": 59.9139, "lng": 10.7522, "state": "Oslo", "country": "Norway"},
    "copenhagen": {"lat": 55.6761, "lng": 12.5683, "state": "Capital Region", "country": "Denmark"},
    "helsinki": {"lat": 60.1699, "lng": 24.9384, "state": "Uusimaa", "country": "Finland"},
    "dublin": {"lat": 53.3498, "lng": -6.2603, "state": "Leinster", "country": "Ireland"},
    "lisbon": {"lat": 38.7223, "lng": -9.1393, "state": "Lisbon", "country": "Portugal"},
    "athens": {"lat": 37.9838, "lng": 23.7275, "state": "Attica", "country": "Greece"},
    "warsaw": {"lat": 52.2297, "lng": 21.0122, "state": "Masovia", "country": "Poland"},
    "krakow": {"lat": 50.0647, "lng": 19.9450, "state": "Lesser Poland", "country": "Poland"},
    "prague": {"lat": 50.0755, "lng": 14.4378, "state": "Prague", "country": "Czech Republic"},
    "budapest": {"lat": 47.4979, "lng": 19.0402, "state": "Budapest", "country": "Hungary"},
    "bucharest": {"lat": 44.4268, "lng": 26.1025, "state": "Bucharest", "country": "Romania"},
    "sofia": {"lat": 42.6977, "lng": 23.3219, "state": "Sofia City", "country": "Bulgaria"},
    "belgrade": {"lat": 44.7866, "lng": 20.4489, "state": "Belgrade", "country": "Serbia"},
    "zagreb": {"lat": 45.8150, "lng": 15.9819, "state": "City of Zagreb", "country": "Croatia"},
    "kyiv": {"lat": 50.4501, "lng": 30.5234, "state": "Kyiv", "country": "Ukraine"},
    "kiev": {"lat": 50.4501, "lng": 30.5234, "state": "Kyiv", "country": "Ukraine"},
    "moscow": {"lat": 55.7558, "lng": 37.6173, "state": "Moscow", "country": "Russia"},
    "saint petersburg": {"lat": 59.9343, "lng": 30.3351, "state": "Saint Petersburg", "country": "Russia"},
    "istanbul": {"lat": 41.0082, "lng": 28.9784, "state": "Istanbul", "country": "Turkey"},
    "ankara": {"lat": 39.9334, "lng": 32.8597, "state": "Ankara", "country": "Turkey"},
    "reykjavik": {"lat": 64.1466, "lng": -21.9426, "state": "Capital Region", "country": "Iceland"},

    # ═══ ASIA ═══
    "tokyo": {"lat": 35.6762, "lng": 139.6503, "state": "Tokyo", "country": "Japan"},
    "osaka": {"lat": 34.6937, "lng": 135.5023, "state": "Osaka", "country": "Japan"},
    "kyoto": {"lat": 35.0116, "lng": 135.7681, "state": "Kyoto", "country": "Japan"},
    "yokohama": {"lat": 35.4437, "lng": 139.6380, "state": "Kanagawa", "country": "Japan"},
    "seoul": {"lat": 37.5665, "lng": 126.9780, "state": "Seoul", "country": "South Korea"},
    "busan": {"lat": 35.1796, "lng": 129.0756, "state": "Busan", "country": "South Korea"},
    "beijing": {"lat": 39.9042, "lng": 116.4074, "state": "Beijing", "country": "China"},
    "shanghai": {"lat": 31.2304, "lng": 121.4737, "state": "Shanghai", "country": "China"},
    "guangzhou": {"lat": 23.1291, "lng": 113.2644, "state": "Guangdong", "country": "China"},
    "shenzhen": {"lat": 22.5431, "lng": 114.0579, "state": "Guangdong", "country": "China"},
    "hong kong": {"lat": 22.3193, "lng": 114.1694, "state": "Hong Kong", "country": "China"},
    "taipei": {"lat": 25.0330, "lng": 121.5654, "state": "Taipei", "country": "Taiwan"},
    "bangkok": {"lat": 13.7563, "lng": 100.5018, "state": "Bangkok", "country": "Thailand"},
    "singapore": {"lat": 1.3521, "lng": 103.8198, "state": "Singapore", "country": "Singapore"},
    "kuala lumpur": {"lat": 3.1390, "lng": 101.6869, "state": "Kuala Lumpur", "country": "Malaysia"},
    "jakarta": {"lat": -6.2088, "lng": 106.8456, "state": "Jakarta", "country": "Indonesia"},
    "manila": {"lat": 14.5995, "lng": 120.9842, "state": "Metro Manila", "country": "Philippines"},
    "hanoi": {"lat": 21.0278, "lng": 105.8342, "state": "Hanoi", "country": "Vietnam"},
    "ho chi minh": {"lat": 10.8231, "lng": 106.6297, "state": "Ho Chi Minh City", "country": "Vietnam"},
    "phnom penh": {"lat": 11.5564, "lng": 104.9282, "state": "Phnom Penh", "country": "Cambodia"},
    "yangon": {"lat": 16.8661, "lng": 96.1951, "state": "Yangon", "country": "Myanmar"},
    "vientiane": {"lat": 17.9757, "lng": 102.6331, "state": "Vientiane", "country": "Laos"},
    "colombo": {"lat": 6.9271, "lng": 79.8612, "state": "Western Province", "country": "Sri Lanka"},
    "kathmandu": {"lat": 27.7172, "lng": 85.3240, "state": "Bagmati", "country": "Nepal"},
    "dhaka": {"lat": 23.8103, "lng": 90.4125, "state": "Dhaka", "country": "Bangladesh"},
    "karachi": {"lat": 24.8607, "lng": 67.0011, "state": "Sindh", "country": "Pakistan"},
    "lahore": {"lat": 31.5204, "lng": 74.3587, "state": "Punjab", "country": "Pakistan"},
    "islamabad": {"lat": 33.6844, "lng": 73.0479, "state": "Islamabad Capital Territory", "country": "Pakistan"},
    "rawalpindi": {"lat": 33.5651, "lng": 73.0169, "state": "Punjab", "country": "Pakistan"},
    "dubai": {"lat": 25.2048, "lng": 55.2708, "state": "Dubai", "country": "UAE"},
    "abu dhabi": {"lat": 24.4539, "lng": 54.3773, "state": "Abu Dhabi", "country": "UAE"},
    "doha": {"lat": 25.2854, "lng": 51.5310, "state": "Ad Dawhah", "country": "Qatar"},
    "riyadh": {"lat": 24.7136, "lng": 46.6753, "state": "Riyadh", "country": "Saudi Arabia"},
    "jeddah": {"lat": 21.4858, "lng": 39.1925, "state": "Makkah", "country": "Saudi Arabia"},
    "manama": {"lat": 26.2285, "lng": 50.5860, "state": "Capital Governorate", "country": "Bahrain"},
    "kuwait city": {"lat": 29.3759, "lng": 47.9774, "state": "Al Asimah", "country": "Kuwait"},
    "muscat": {"lat": 23.5880, "lng": 58.3829, "state": "Muscat", "country": "Oman"},
    "amman": {"lat": 31.9454, "lng": 35.9284, "state": "Amman", "country": "Jordan"},
    "beirut": {"lat": 33.8938, "lng": 35.5018, "state": "Beirut", "country": "Lebanon"},
    "tel aviv": {"lat": 32.0853, "lng": 34.7818, "state": "Tel Aviv", "country": "Israel"},
    "jerusalem": {"lat": 31.7683, "lng": 35.2137, "state": "Jerusalem", "country": "Israel"},
    "baghdad": {"lat": 33.3152, "lng": 44.3661, "state": "Baghdad", "country": "Iraq"},
    "tehran": {"lat": 35.6892, "lng": 51.3890, "state": "Tehran", "country": "Iran"},
    "damascus": {"lat": 33.5138, "lng": 36.2765, "state": "Damascus", "country": "Syria"},
    "kabul": {"lat": 34.5553, "lng": 69.2075, "state": "Kabul", "country": "Afghanistan"},

    # ═══ AFRICA ═══
    "cairo": {"lat": 30.0444, "lng": 31.2357, "state": "Cairo", "country": "Egypt"},
    "alexandria": {"lat": 31.2001, "lng": 29.9187, "state": "Alexandria", "country": "Egypt"},
    "lagos": {"lat": 6.5244, "lng": 3.3792, "state": "Lagos", "country": "Nigeria"},
    "abuja": {"lat": 9.0579, "lng": 7.4951, "state": "FCT", "country": "Nigeria"},
    "nairobi": {"lat": -1.2921, "lng": 36.8219, "state": "Nairobi", "country": "Kenya"},
    "mombasa": {"lat": -4.0435, "lng": 39.6682, "state": "Coast", "country": "Kenya"},
    "johannesburg": {"lat": -26.2041, "lng": 28.0473, "state": "Gauteng", "country": "South Africa"},
    "cape town": {"lat": -33.9249, "lng": 18.4241, "state": "Western Cape", "country": "South Africa"},
    "durban": {"lat": -29.8587, "lng": 31.0218, "state": "KwaZulu-Natal", "country": "South Africa"},
    "casablanca": {"lat": 33.5731, "lng": -7.5898, "state": "Casablanca-Settat", "country": "Morocco"},
    "tunis": {"lat": 36.8065, "lng": 10.1815, "state": "Tunis", "country": "Tunisia"},
    "algiers": {"lat": 36.7538, "lng": 3.0588, "state": "Algiers", "country": "Algeria"},
    "accra": {"lat": 5.6037, "lng": -0.1870, "state": "Greater Accra", "country": "Ghana"},
    "addis ababa": {"lat": 9.0250, "lng": 38.7469, "state": "Addis Ababa", "country": "Ethiopia"},
    "dar es salaam": {"lat": -6.7924, "lng": 39.2083, "state": "Dar es Salaam", "country": "Tanzania"},
    "kampala": {"lat": 0.3476, "lng": 32.5825, "state": "Central Region", "country": "Uganda"},
    "kigali": {"lat": -1.9403, "lng": 29.8739, "state": "Kigali", "country": "Rwanda"},
    "kinshasa": {"lat": -4.4419, "lng": 15.2663, "state": "Kinshasa", "country": "DR Congo"},
    "luanda": {"lat": -8.8390, "lng": 13.2894, "state": "Luanda", "country": "Angola"},
    "maputo": {"lat": -25.9692, "lng": 32.5732, "state": "Maputo", "country": "Mozambique"},

    # ═══ SOUTH AMERICA ═══
    "sao paulo": {"lat": -23.5505, "lng": -46.6333, "state": "Sao Paulo", "country": "Brazil"},
    "rio de janeiro": {"lat": -22.9068, "lng": -43.1729, "state": "Rio de Janeiro", "country": "Brazil"},
    "brasilia": {"lat": -15.7975, "lng": -47.8919, "state": "Federal District", "country": "Brazil"},
    "buenos aires": {"lat": -34.6037, "lng": -58.3816, "state": "Buenos Aires", "country": "Argentina"},
    "santiago": {"lat": -33.4489, "lng": -70.6693, "state": "Santiago Metropolitan", "country": "Chile"},
    "lima": {"lat": -12.0464, "lng": -77.0428, "state": "Lima", "country": "Peru"},
    "bogota": {"lat": 4.7110, "lng": -74.0721, "state": "Bogota D.C.", "country": "Colombia"},
    "medellin": {"lat": 6.2476, "lng": -75.5658, "state": "Antioquia", "country": "Colombia"},
    "caracas": {"lat": 10.4806, "lng": -66.9036, "state": "Capital District", "country": "Venezuela"},
    "quito": {"lat": -0.1807, "lng": -78.4678, "state": "Pichincha", "country": "Ecuador"},
    "montevideo": {"lat": -34.9011, "lng": -56.1645, "state": "Montevideo", "country": "Uruguay"},
    "la paz": {"lat": -16.4897, "lng": -68.1193, "state": "La Paz", "country": "Bolivia"},
    "asuncion": {"lat": -25.2637, "lng": -57.5759, "state": "Central Department", "country": "Paraguay"},
    "georgetown": {"lat": 6.8013, "lng": -58.1553, "state": "Demerara-Mahaica", "country": "Guyana"},
    "paramaribo": {"lat": 5.8520, "lng": -55.2038, "state": "Paramaribo", "country": "Suriname"},

    # ═══ OCEANIA ═══
    "sydney": {"lat": -33.8688, "lng": 151.2093, "state": "New South Wales", "country": "Australia"},
    "melbourne": {"lat": -37.8136, "lng": 144.9631, "state": "Victoria", "country": "Australia"},
    "brisbane": {"lat": -27.4698, "lng": 153.0251, "state": "Queensland", "country": "Australia"},
    "perth": {"lat": -31.9505, "lng": 115.8605, "state": "Western Australia", "country": "Australia"},
    "adelaide": {"lat": -34.9285, "lng": 138.6007, "state": "South Australia", "country": "Australia"},
    "auckland": {"lat": -36.8485, "lng": 174.7633, "state": "Auckland", "country": "New Zealand"},
    "wellington": {"lat": -41.2865, "lng": 174.7762, "state": "Wellington", "country": "New Zealand"},
}

# ── Location name variants / aliases ─────────────────────
LOCATION_ALIASES = {
    "chennai port": "chennai",
    "chennai railway station": "chennai",
    "chennai airport": "chennai",
    "mumbai airport": "mumbai",
    "delhi airport": "delhi",
    "bangalore airport": "bangalore",
    "delhi cantt": "delhi",
    "mumbai central": "mumbai",
    "andheri": "mumbai",
    "bandra": "mumbai",
    "dadar": "mumbai",
    "powai": "mumbai",
    "borivali": "mumbai",
    "malad": "mumbai",
    "colaba": "mumbai",
    "fort": "mumbai",
    "connaught place": "delhi",
    "karol bagh": "delhi",
    "chandni chowk": "delhi",
    "dwarka": "delhi",
    "rohini": "delhi",
    "saket": "delhi",
    "lajpat nagar": "delhi",
    "defence colony": "delhi",
    "hauz khas": "delhi",
    "mg road": "bangalore",
    "koramangala": "bangalore",
    "indiranagar": "bangalore",
    "whitefield": "bangalore",
    "electronic city": "bangalore",
    "hsr layout": "bangalore",
    "jp nagar": "bangalore",
    "jayanagar": "bangalore",
    "t nagar": "chennai",
    "adyar": "chennai",
    "velachery": "chennai",
    "anna nagar": "chennai",
    "porur": "chennai",
    "chromepet": "chennai",
    "tambaram": "chennai",
    "sholinganallur": "chennai",
    "salt lake": "kolkata",
    "park street": "kolkata",
    "new town": "kolkata",
    "howrah station": "howrah",
    "begumpet": "hyderabad",
    "gachibowli": "hyderabad",
    "secunderabad": "hyderabad",
    "jubilee hills": "hyderabad",
    "banjara hills": "hyderabad",
    "kondapur": "hyderabad",
    "manhattan": "new york",
    "brooklyn": "new york",
    "queens": "new york",
    "bronx": "new york",
    "staten island": "new york",
    "hollywood": "los angeles",
    "beverly hills": "los angeles",
    "silicon valley": "san francisco",
    "bay area": "san francisco",
    "wall street": "new york",
    "the pentagon": "washington",
    "capitol hill": "washington",
    "chinatown": "san francisco",
    "little tokyo": "los angeles",
    "south beach": "miami",
    "times square": "new york",
    "central park": "new york",
    "notting hill": "london",
    "camden": "london",
    "shoreditch": "london",
    "westminster": "london",
    "whitehall": "london",
    "mayfair": "london",
    "kensington": "london",
    "champs elysees": "paris",
    "montmartre": "paris",
    "shibuya": "tokyo",
    "shinjuku": "tokyo",
    "ginza": "tokyo",
    "roppongi": "tokyo",
    "gangnam": "seoul",
    "kowloon": "hong kong",
    "causeway bay": "hong kong",
    "petronas towers": "kuala lumpur",
    "sentosa": "singapore",
    "orchard road": "singapore",
    "marina bay": "singapore",
    "red light district": "amsterdam",
    "kreuzberg": "berlin",
    "mitte": "berlin",
    "ichigaya": "tokyo",
    "roppongi hills": "tokyo",
    "aeroflot": "moscow",
    "red square": "moscow",
    "kremlin": "moscow",
}


def normalize_location(name: str) -> str:
    """Normalize a location name for lookup."""
    return name.strip().lower()


def geocode_location(name: str) -> Optional[dict]:
    """
    Geocode a location name to lat/lng coordinates.
    Returns dict with lat, lng, state, country or None if not found.
    """
    normalized = normalize_location(name)

    # 1. Direct lookup in database
    if normalized in INDIAN_LOCATIONS:
        return INDIAN_LOCATIONS[normalized]

    # 2. Check aliases
    if normalized in LOCATION_ALIASES:
        alias_target = LOCATION_ALIASES[normalized]
        return INDIAN_LOCATIONS.get(alias_target)

    # 3. Partial match — check if any database key is contained in the input
    for key, coords in INDIAN_LOCATIONS.items():
        if key in normalized or normalized in key:
            return coords

    # 4. Try Nominatim API as fallback (NO country restrictions)
    return _nominatim_geocode(name)


def _nominatim_geocode(name: str) -> Optional[dict]:
    """Fallback geocoding using OpenStreetMap Nominatim API.
    No forced country restriction — works worldwide."""
    try:
        query = urllib.parse.quote(name)
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        req = urllib.request.Request(url, headers={
            "User-Agent": "CrimeGraphAI/1.0 (crime-graph-prototype)"
        })
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data:
                return {
                    "lat": float(data[0]["lat"]),
                    "lng": float(data[0]["lon"]),
                    "state": data[0].get("state", ""),
                    "country": data[0].get("country", ""),
                }
    except Exception:
        pass
    return None


def geocode_all_locations(location_names: list[str]) -> dict:
    """
    Geocode a list of location names.
    Returns dict mapping location name -> coordinates.
    """
    results = {}
    for name in location_names:
        coords = geocode_location(name)
        if coords:
            results[name] = coords
        # Small delay for Nominatim rate limiting
        time.sleep(0.1)
    return results


def get_map_bounds(locations: dict) -> dict:
    """Calculate map bounds to fit all geocoded locations.
    Dynamically computed based on actual locations, not defaulting to India."""
    if not locations:
        # Default to world view
        return {"north": 70.0, "south": -60.0, "east": 180.0, "west": -180.0}

    lats = [v["lat"] for v in locations.values()]
    lngs = [v["lng"] for v in locations.values()]

    # If all locations are in a small cluster, add more padding
    lat_range = max(lats) - min(lats)
    lng_range = max(lngs) - min(lngs)

    if lat_range < 5 and lng_range < 5:
        padding = 5.0  # Small cluster — add more padding
    elif lat_range < 20 and lng_range < 20:
        padding = 3.0
    else:
        padding = 2.0

    return {
        "north": max(lats) + padding,
        "south": min(lats) - padding,
        "east": max(lngs) + padding,
        "west": min(lngs) - padding,
    }
