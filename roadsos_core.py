import requests
import sqlite3
import json
import math
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
DB_PATH       = os.environ.get("ROADSOS_DB", "roadsos.db")
CACHE_TTL_HRS = 24
USER_AGENT    = "ROADSOS/3.0.0 (emergency-services-locator)"

SERVICE_QUERIES: Dict[str, List[tuple]] = {
    "hospital": [
        ("amenity",   "hospital"),
        ("amenity",   "clinic"),
        ("healthcare","hospital"),
        ("amenity",   "trauma_centre"),
        ("healthcare","trauma_centre"),
    ],
    "police": [
        ("amenity", "police"),
    ],
    "ambulance": [
        ("emergency",  "ambulance_station"),
        ("amenity",    "ambulance_station"),
        ("healthcare", "ambulance_station"),
    ],
    "towing": [
        ("shop",      "car_repair"),
        ("amenity",   "vehicle_inspection"),
        ("emergency", "ses_station"),
    ],
    "puncture_shop": [
        ("shop",   "tyres"),
        ("repair", "tyres"),
    ],
    "fuel_station": [
        ("amenity", "fuel"),
    ],
    "car_showroom": [
        ("shop",    "car"),
        ("shop",    "vehicle"),
    ],
    "blood_bank": [
        ("amenity",    "blood_bank"),
        ("healthcare", "blood_bank"),
        ("amenity",    "blood_donation"),
    ],
    "fire_station": [
        ("amenity", "fire_station"),
    ],
    "pharmacy": [
        ("amenity", "pharmacy"),
        ("healthcare", "pharmacy"),
    ],
}

CATEGORY_INFO: Dict[str, dict] = {
    "hospital":      {"label": "Hospitals / Trauma",      "color": "#FF1744", "icon": "🏥", "priority": 1},
    "ambulance":     {"label": "Ambulance Services",       "color": "#FF6D00", "icon": "🚑", "priority": 2},
    "police":        {"label": "Police Stations",          "color": "#2979FF", "icon": "👮", "priority": 3},
    "blood_bank":    {"label": "Blood Banks",              "color": "#D50000", "icon": "🩸", "priority": 4},
    "fire_station":  {"label": "Fire Stations",            "color": "#FF3D00", "icon": "🚒", "priority": 5},
    "towing":        {"label": "Towing / Vehicle Rescue",  "color": "#AA00FF", "icon": "🚗", "priority": 6},
    "puncture_shop": {"label": "Puncture Shops",           "color": "#00BFA5", "icon": "🔧", "priority": 7},
    "pharmacy":      {"label": "Pharmacies",               "color": "#00C853", "icon": "💊", "priority": 8},
    "fuel_station":  {"label": "Fuel Stations",            "color": "#FFD600", "icon": "⛽", "priority": 9},
    "car_showroom":  {"label": "Car Service / Showrooms",  "color": "#00B0FF", "icon": "🏪", "priority": 10},
}

FIRST_AID_DATA = {
    "bleeding": {
        "title": "Severe Bleeding",
        "icon": "🩸",
        "color": "#FF1744",
        "severity": "critical",
        "steps": [
            {"num": 1, "title": "Call for Help", "body": "Call 108 / 112 immediately. Keep the victim calm and still.", "warn": None},
            {"num": 2, "title": "Direct Pressure", "body": "Press firmly on the wound with a clean cloth, bandage, or your hand. Maintain constant pressure — do NOT lift to check.", "warn": "If blood soaks through, add more material on top. Never remove original dressing."},
            {"num": 3, "title": "Elevate", "body": "Raise the injured limb above heart level if no bone fracture is suspected.", "warn": None},
            {"num": 4, "title": "Tourniquet (Last Resort)", "body": "If bleeding from a limb cannot be controlled: tie a tourniquet 2–3 inches above wound. Tighten until bleeding stops. Note the time.", "warn": "Only use on limbs. Never on neck, chest, or abdomen. Mark 'TK' + time on victim's forehead."},
            {"num": 5, "title": "Monitor", "body": "Keep victim warm (shock prevention). Do not give food/water. Stay until ambulance arrives.", "warn": None},
        ]
    },
    "fracture": {
        "title": "Fracture / Broken Bone",
        "icon": "🦴",
        "color": "#FF9100",
        "severity": "serious",
        "steps": [
            {"num": 1, "title": "Do Not Move", "body": "Immobilize the injured area. If spinal injury is suspected, do NOT move the person unless in immediate danger.", "warn": "Moving someone with a spinal fracture can cause permanent paralysis."},
            {"num": 2, "title": "Splint the Injury", "body": "Pad the area with soft material. Splint using a rigid object (stick, board) tied above and below the fracture. Keep splint loose enough to check circulation.", "warn": None},
            {"num": 3, "title": "Control Bleeding", "body": "If bone has broken through skin (open fracture), cover with clean cloth. Do NOT push the bone back.", "warn": None},
            {"num": 4, "title": "Ice & Elevation", "body": "Apply ice pack wrapped in cloth to reduce swelling. Elevate the limb if possible.", "warn": None},
            {"num": 5, "title": "Watch for Shock", "body": "Pale/clammy skin, rapid breathing, confusion = signs of shock. Keep person warm, calm, and lying down.", "warn": None},
        ]
    },
    "cpr": {
        "title": "CPR (Unresponsive Person)",
        "icon": "❤️",
        "color": "#FF1744",
        "severity": "critical",
        "steps": [
            {"num": 1, "title": "Check Responsiveness", "body": "Tap shoulders firmly, shout 'Are you okay?'. If no response, call 108/112 immediately. Send someone for an AED if available.", "warn": None},
            {"num": 2, "title": "Check Breathing", "body": "Tilt head back, lift chin. Look, listen and feel for breathing for no more than 10 seconds. Occasional gasps are NOT normal breathing.", "warn": None},
            {"num": 3, "title": "30 Chest Compressions", "body": "Place heel of hand on centre of chest. Push HARD and FAST — at least 5cm deep, 100–120 per minute. Sing 'Staying Alive' to keep rhythm.", "warn": "Allow full chest recoil between compressions. Minimize interruptions."},
            {"num": 4, "title": "2 Rescue Breaths", "body": "Tilt head, lift chin, pinch nose, make seal with mouth. Give 2 breath (1 second each). Watch for chest rise.", "warn": "If unwilling to give rescue breaths: hands-only CPR (continuous compressions) is still effective."},
            {"num": 5, "title": "Repeat 30:2", "body": "Continue cycles of 30 compressions + 2 breaths. Only stop if the person starts breathing normally, AED arrives, or professional help takes over.", "warn": None},
        ]
    },
    "choking": {
        "title": "Choking / Airway Blockage",
        "icon": "🫁",
        "color": "#FF9100",
        "severity": "critical",
        "steps": [
            {"num": 1, "title": "Encourage Coughing", "body": "If person can cough, speak, or breathe — encourage them to keep coughing. Do NOT do anything yet.", "warn": None},
            {"num": 2, "title": "5 Back Blows", "body": "Stand to the side, support chest with one hand. Give 5 sharp blows between shoulder blades with heel of hand.", "warn": None},
            {"num": 3, "title": "5 Abdominal Thrusts", "body": "Stand behind person, hands around waist. One fist just above navel, cover with other hand. Pull sharply inward and upward 5 times.", "warn": "Do NOT use abdominal thrusts on pregnant women or infants. Use chest thrusts instead."},
            {"num": 4, "title": "Alternate", "body": "Alternate between 5 back blows and 5 abdominal thrusts until object dislodged or person loses consciousness.", "warn": None},
            {"num": 5, "title": "If Unconscious", "body": "Lower carefully to ground. Start CPR. Each time you open airway for rescue breaths, look for object and remove if visible.", "warn": None},
        ]
    },
    "burns": {
        "title": "Burns",
        "icon": "🔥",
        "color": "#FF6D00",
        "severity": "serious",
        "steps": [
            {"num": 1, "title": "Cool the Burn", "body": "Run cool (not cold/ice) water over burn for at least 20 minutes. Start within 3 hours of injury.", "warn": "Never use ice, butter, toothpaste, or any creams. Do NOT burst blisters."},
            {"num": 2, "title": "Remove Constrictions", "body": "Remove jewellery, watches, belts near burn before swelling starts. Do NOT remove clothing stuck to skin.", "warn": None},
            {"num": 3, "title": "Cover", "body": "Cover loosely with cling film (lengthwise, not around the limb) or clean non-fluffy material. This reduces pain and infection risk.", "warn": None},
            {"num": 4, "title": "Call Emergency", "body": "Call 108 for: burns larger than 3x3 inches, face/hands/genitals, deep burns, burns in children/elderly, chemical or electrical burns.", "warn": None},
            {"num": 5, "title": "Treat for Shock", "body": "Keep person warm, elevate burned limb if possible, do not give food or water, reassure victim.", "warn": None},
        ]
    },
    "head_injury": {
        "title": "Head Injury",
        "icon": "🧠",
        "color": "#AA00FF",
        "severity": "critical",
        "steps": [
            {"num": 1, "title": "Do Not Move", "body": "Assume spinal injury with any significant head trauma. Keep head and neck still. Do NOT remove helmets.", "warn": "Moving a person with spinal injury can cause permanent paralysis or death."},
            {"num": 2, "title": "Call 108 Immediately", "body": "Head injuries can be fatal or cause brain damage. Always call for professional help even if person seems okay.", "warn": None},
            {"num": 3, "title": "Control Bleeding", "body": "Apply firm pressure with clean cloth. Do NOT apply direct pressure if skull fracture is suspected. Do NOT remove object if embedded.", "warn": None},
            {"num": 4, "title": "Recovery Position", "body": "If unconscious but breathing: roll onto side (maintaining spinal alignment, 2 helpers if possible) to prevent choking on vomit.", "warn": None},
            {"num": 5, "title": "Monitor & Watch For", "body": "Danger signs: loss of consciousness, seizures, unequal pupils, clear fluid from nose/ears, worsening headache, repeated vomiting.", "warn": None},
        ]
    },
    "shock": {
        "title": "Shock (Circulatory)",
        "icon": "⚡",
        "color": "#FF1744",
        "severity": "critical",
        "steps": [
            {"num": 1, "title": "Recognize Shock", "body": "Signs: pale/cold/clammy skin, rapid weak pulse, fast shallow breathing, confusion or anxiety, blue lips/fingernails.", "warn": "Shock is life-threatening. Call 108 immediately."},
            {"num": 2, "title": "Position Correctly", "body": "Lay person flat. Raise legs 30cm (unless head, neck, spine, leg injury suspected). Do NOT raise legs for head injury.", "warn": None},
            {"num": 3, "title": "Keep Warm", "body": "Cover with blanket or jacket. Insulate from cold ground. Prevent heat loss — shock reduces body temperature.", "warn": None},
            {"num": 4, "title": "Control Bleeding", "body": "Treat any visible bleeding with direct pressure. Uncontrolled blood loss is the most common cause of traumatic shock.", "warn": None},
            {"num": 5, "title": "Nothing by Mouth", "body": "Do NOT give food, drink, or medication. Person may need surgery and having food in stomach increases risk.", "warn": None},
        ]
    },
    "spinal": {
        "title": "Suspected Spinal Injury",
        "icon": "🦾",
        "color": "#FF9100",
        "severity": "critical",
        "steps": [
            {"num": 1, "title": "STOP — Do Not Move", "body": "Unless there is immediate danger (fire, drowning), do NOT move the person. Call 108 and wait for professionals.", "warn": "This is the single most important rule. Incorrect movement = permanent disability."},
            {"num": 2, "title": "Stabilize Head", "body": "If you must keep head still: cup both hands around head WITHOUT moving it. Keep ears aligned with shoulders. Ask an assistant to hold this position.", "warn": None},
            {"num": 3, "title": "Reassure", "body": "Tell them you're there, help is coming, and they should stay still. Ask them not to turn or nod their head.", "warn": None},
            {"num": 4, "title": "Check Breathing", "body": "Watch chest rise. If person stops breathing and CPR is needed, carefully tilt head to open airway — saving life takes priority.", "warn": None},
            {"num": 5, "title": "Watch for Spinal Signs", "body": "Indicators: neck/back pain, weakness/numbness in limbs, loss of bladder/bowel control, unusual posture, inability to move.", "warn": None},
        ]
    }
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi    = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)), 3)

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c    = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            osm_id      TEXT,
            category    TEXT    NOT NULL,
            name        TEXT,
            lat         REAL    NOT NULL,
            lon         REAL    NOT NULL,
            phone       TEXT    DEFAULT '',
            address     TEXT    DEFAULT '',
            website     TEXT    DEFAULT '',
            tags        TEXT    DEFAULT '{}',
            region_key  TEXT,
            cached_at   TEXT,
            UNIQUE(osm_id, category)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cache_meta (
            region_key  TEXT,
            category    TEXT,
            cached_at   TEXT,
            record_count INTEGER DEFAULT 0,
            PRIMARY KEY (region_key, category)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS emergency_numbers (
            country_code TEXT PRIMARY KEY,
            country_name TEXT,
            police       TEXT,
            ambulance    TEXT,
            fire         TEXT,
            general      TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            lat         REAL NOT NULL,
            lon         REAL NOT NULL,
            type        TEXT NOT NULL,
            description TEXT DEFAULT '',
            reported_at TEXT NOT NULL,
            active      INTEGER DEFAULT 1
        )
    """)

    seed = [
        ("IN","India",             "100",   "102/108","101",  "112"),
        ("US","United States",     "911",   "911",    "911",  "911"),
        ("GB","United Kingdom",    "999",   "999",    "999",  "112"),
        ("AU","Australia",         "000",   "000",    "000",  "000"),
        ("DE","Germany",           "110",   "112",    "112",  "112"),
        ("FR","France",            "17",    "15",     "18",   "112"),
        ("JP","Japan",             "110",   "119",    "119",  "110"),
        ("CN","China",             "110",   "120",    "119",  "120"),
        ("BR","Brazil",            "190",   "192",    "193",  "192"),
        ("CA","Canada",            "911",   "911",    "911",  "911"),
        ("ZA","South Africa",      "10111", "10177",  "10177","112"),
        ("NG","Nigeria",           "112",   "112",    "112",  "112"),
        ("PK","Pakistan",          "15",    "1122",   "16",   "1122"),
        ("BD","Bangladesh",        "999",   "199",    "999",  "999"),
        ("RU","Russia",            "102",   "103",    "101",  "112"),
        ("IT","Italy",             "113",   "118",    "115",  "112"),
        ("ES","Spain",             "091",   "112",    "080",  "112"),
        ("MX","Mexico",            "911",   "911",    "911",  "911"),
        ("KE","Kenya",             "999",   "999",    "999",  "999"),
        ("EG","Egypt",             "122",   "123",    "180",  "123"),
        ("SG","Singapore",         "999",   "995",    "995",  "995"),
        ("MY","Malaysia",          "999",   "999",    "994",  "999"),
        ("EU","European Union",    "112",   "112",    "112",  "112"),
        ("NZ","New Zealand",       "111",   "111",    "111",  "111"),
        ("AR","Argentina",         "101",   "107",    "100",  "107"),
        ("CL","Chile",             "133",   "131",    "132",  "131"),
        ("CO","Colombia",          "112",   "125",    "119",  "123"),
        ("TR","Turkey",            "155",   "112",    "110",  "112"),
        ("SA","Saudi Arabia",      "999",   "997",    "998",  "911"),
        ("AE","UAE",               "999",   "998",    "997",  "999"),
        ("IQ","Iraq",              "104",   "122",    "115",  "104"),
        ("IR","Iran",              "110",   "115",    "125",  "115"),
        ("TH","Thailand",          "191",   "1669",   "199",  "191"),
        ("ID","Indonesia",         "110",   "118",    "113",  "112"),
        ("PH","Philippines",       "117",   "911",    "911",  "911"),
        ("VN","Vietnam",           "113",   "115",    "114",  "113"),
        ("KR","South Korea",       "112",   "119",    "119",  "112"),
        ("NG","Nigeria",           "112",   "112",    "112",  "112"),
        ("GH","Ghana",             "191",   "193",    "192",  "112"),
        ("ET","Ethiopia",          "911",   "907",    "939",  "911"),
        ("TZ","Tanzania",          "112",   "114",    "115",  "112"),
        ("UG","Uganda",            "999",   "999",    "999",  "999"),
        ("PL","Poland",            "997",   "999",    "998",  "112"),
        ("UA","Ukraine",           "102",   "103",    "101",  "112"),
        ("SE","Sweden",            "112",   "112",    "112",  "112"),
        ("NO","Norway",            "112",   "113",    "110",  "112"),
        ("DK","Denmark",           "112",   "112",    "112",  "112"),
        ("FI","Finland",           "112",   "112",    "112",  "112"),
        ("NL","Netherlands",       "112",   "112",    "112",  "112"),
        ("BE","Belgium",           "101",   "100",    "100",  "112"),
        ("CH","Switzerland",       "117",   "144",    "118",  "112"),
        ("AT","Austria",           "133",   "144",    "122",  "112"),
        ("PT","Portugal",          "112",   "112",    "112",  "112"),
        ("GR","Greece",            "100",   "166",    "199",  "112"),
        ("CZ","Czech Republic",    "158",   "155",    "150",  "112"),
        ("RO","Romania",           "112",   "112",    "112",  "112"),
        ("HU","Hungary",           "107",   "104",    "105",  "112"),
        ("IL","Israel",            "100",   "101",    "102",  "112"),
        ("LK","Sri Lanka",         "119",   "110",    "111",  "119"),
        ("NP","Nepal",             "100",   "102",    "101",  "100"),
        ("MM","Myanmar",           "199",   "192",    "191",  "199"),
        ("KH","Cambodia",          "117",   "119",    "118",  "117"),
        ("QA","Qatar",             "999",   "999",    "999",  "999"),
        ("KW","Kuwait",            "112",   "112",    "112",  "112"),
    ]
    c.executemany("INSERT OR IGNORE INTO emergency_numbers VALUES (?,?,?,?,?,?)", seed)

    c.execute("CREATE INDEX IF NOT EXISTS idx_svc_region   ON services(region_key, category)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_svc_latlon   ON services(lat, lon)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_svc_category ON services(category)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_inc_latlon   ON incidents(lat, lon)")

    conn.commit()
    conn.close()


def get_region_key(lat, lon, radius_km):
    return f"{round(lat,2)}_{round(lon,2)}_{int(radius_km)}"


def is_cache_valid(region_key, category, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    row  = conn.execute(
        "SELECT cached_at FROM cache_meta WHERE region_key=? AND category=?",
        (region_key, category)
    ).fetchone()
    conn.close()
    if row:
        try:
            return datetime.now() - datetime.fromisoformat(row[0]) < timedelta(hours=CACHE_TTL_HRS)
        except Exception:
            pass
    return False


def save_to_cache(services, region_key, category, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c    = conn.cursor()
    now  = datetime.now().isoformat()
    for svc in services:
        c.execute("""
            INSERT OR REPLACE INTO services
                (osm_id, category, name, lat, lon, phone, address, website, tags, region_key, cached_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            svc.get("osm_id"), category, svc.get("name","Unknown"),
            svc["lat"], svc["lon"],
            svc.get("phone",""), svc.get("address",""), svc.get("website",""),
            json.dumps(svc.get("tags",{})), region_key, now
        ))
    c.execute("""
        INSERT OR REPLACE INTO cache_meta (region_key, category, cached_at, record_count)
        VALUES (?,?,?,?)
    """, (region_key, category, now, len(services)))
    conn.commit()
    conn.close()


def get_from_cache(region_key, category, lat, lon, radius_km, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT osm_id,category,name,lat,lon,phone,address,website,tags "
        "FROM services WHERE region_key=? AND category=?",
        (region_key, category)
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        dist = haversine(lat, lon, r[3], r[4])
        if dist <= radius_km * 1.15:
            results.append({
                "osm_id":r[0],"category":r[1],"name":r[2],
                "lat":r[3],"lon":r[4],
                "phone":r[5] or "","address":r[6] or "","website":r[7] or "",
                "tags":json.loads(r[8] or "{}"),
                "distance_km":round(dist,2)
            })
    return sorted(results, key=lambda x: x["distance_km"])


def fetch_from_osm(lat, lon, radius_m, category):
    pairs = SERVICE_QUERIES.get(category, [])
    parts = []
    for key, val in pairs:
        parts.append(f'node["{key}"="{val}"](around:{radius_m},{lat},{lon});')
        parts.append(f'way["{key}"="{val}"](around:{radius_m},{lat},{lon});')
    query = "[out:json][timeout:30];\n(\n" + "\n".join(parts) + "\n);\nout center tags;"

    for url in OVERPASS_URLS:
        try:
            resp = requests.post(url, data={"data": query},
                                 headers={"User-Agent": USER_AGENT}, timeout=25)
            resp.raise_for_status()
            elements = resp.json().get("elements", [])
            results, seen = [], set()
            for el in elements:
                eid = str(el.get("id",""))
                if eid in seen: continue
                seen.add(eid)
                tags   = el.get("tags",{})
                el_lat = el.get("lat") or el.get("center",{}).get("lat")
                el_lon = el.get("lon") or el.get("center",{}).get("lon")
                if not el_lat or not el_lon: continue
                name  = (tags.get("name") or tags.get("name:en") or tags.get("operator") or
                         f"Unnamed {CATEGORY_INFO.get(category,{}).get('label','Service')}")
                phone = (tags.get("phone") or tags.get("contact:phone") or
                         tags.get("telephone") or tags.get("emergency:phone") or "")
                website = tags.get("website") or tags.get("contact:website") or ""
                addr  = ", ".join(filter(None,[
                    tags.get("addr:housenumber",""),
                    tags.get("addr:street",""),
                    tags.get("addr:city",""),
                    tags.get("addr:state",""),
                    tags.get("addr:country",""),
                ]))
                results.append({
                    "osm_id":eid,"name":name,"lat":el_lat,"lon":el_lon,
                    "phone":phone,"address":addr,"website":website,"tags":tags
                })
            return results
        except requests.RequestException:
            continue
        except Exception:
            continue
    return None


def get_nearby_services(lat, lon, radius_km=5.0, categories=None, force_refresh=False, db_path=DB_PATH):
    if categories is None:
        categories = list(SERVICE_QUERIES.keys())
    radius_m   = int(radius_km * 1000)
    region_key = get_region_key(lat, lon, radius_km)
    output     = {}
    for cat in sorted(categories, key=lambda c: CATEGORY_INFO.get(c,{}).get("priority",99)):
        use_cache = is_cache_valid(region_key, cat, db_path) and not force_refresh
        if use_cache:
            data   = get_from_cache(region_key, cat, lat, lon, radius_km, db_path)
            source = "cache"
        else:
            live = fetch_from_osm(lat, lon, radius_m, cat)
            if live is not None:
                save_to_cache(live, region_key, cat, db_path)
                data   = get_from_cache(region_key, cat, lat, lon, radius_km, db_path)
                source = "live"
            else:
                data   = get_from_cache(region_key, cat, lat, lon, radius_km, db_path)
                source = "offline_cache"
        output[cat] = {"data": data, "source": source, "count": len(data)}
    return output


def get_emergency_numbers(country_code="IN", db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    row  = conn.execute(
        "SELECT * FROM emergency_numbers WHERE country_code=?",
        (country_code.upper(),)
    ).fetchone()
    conn.close()
    if row:
        return dict(zip(("country_code","country_name","police","ambulance","fire","general"), row))
    return {"country_code":"EU","country_name":"International",
            "police":"112","ambulance":"112","fire":"112","general":"112"}


def get_all_emergency_numbers(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT * FROM emergency_numbers ORDER BY country_name").fetchall()
    conn.close()
    keys = ("country_code","country_name","police","ambulance","fire","general")
    return [dict(zip(keys, r)) for r in rows]


def reverse_geocode(lat, lon):
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat":lat,"lon":lon,"format":"json"},
            headers={"User-Agent":USER_AGENT},
            timeout=10
        )
        d    = resp.json()
        addr = d.get("address",{})
        return {
            "display_name": d.get("display_name",""),
            "country_code": addr.get("country_code","in").upper(),
            "city":  addr.get("city") or addr.get("town") or addr.get("village",""),
            "country": addr.get("country",""),
            "road": addr.get("road",""),
            "state": addr.get("state",""),
        }
    except Exception:
        return {"display_name":"","country_code":"IN","city":"","country":"","road":"","state":""}


def report_incident(lat, lon, inc_type, description="", db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    now  = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO incidents (lat,lon,type,description,reported_at,active) VALUES (?,?,?,?,?,1)",
        (lat, lon, inc_type, description, now)
    )
    conn.commit()
    conn.close()


def get_incidents(lat, lon, radius_km=5.0, db_path=DB_PATH):
    conn    = sqlite3.connect(db_path)
    cutoff  = (datetime.now() - timedelta(hours=6)).isoformat()
    rows    = conn.execute(
        "SELECT id,lat,lon,type,description,reported_at FROM incidents "
        "WHERE active=1 AND reported_at > ? ORDER BY reported_at DESC",
        (cutoff,)
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        dist = haversine(lat, lon, r[1], r[2])
        if dist <= radius_km:
            results.append({
                "id":r[0],"lat":r[1],"lon":r[2],"type":r[3],
                "description":r[4],"reported_at":r[5],"distance_km":round(dist,2)
            })
    return sorted(results, key=lambda x: x["distance_km"])


def get_first_aid(injury_type=None):
    if injury_type and injury_type in FIRST_AID_DATA:
        return FIRST_AID_DATA[injury_type]
    return FIRST_AID_DATA
