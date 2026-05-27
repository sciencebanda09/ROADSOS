from flask import Flask, render_template, request, jsonify
from roadsos_core import (
    init_db, get_nearby_services, get_emergency_numbers, get_all_emergency_numbers,
    reverse_geocode, CATEGORY_INFO, SERVICE_QUERIES, DB_PATH,
    report_incident, get_incidents, get_first_aid, FIRST_AID_DATA
)
import os
import requests as req_lib
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
DB  = os.environ.get("ROADSOS_DB", DB_PATH)

@app.route("/favicon.ico")
def favicon():
    from flask import Response
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><circle cx="16" cy="16" r="14" fill="#ff2d55"/><text x="16" y="21" text-anchor="middle" font-size="16" font-family="Arial" font-weight="bold" fill="white">S</text></svg>'
    return Response(svg, mimetype='image/svg+xml')

@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORY_INFO)

@app.route("/api/search")
def api_search():
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lon are required numeric parameters"}), 400
    radius        = float(request.args.get("radius", 5.0))
    cats_param    = request.args.get("categories", "")
    categories    = [c.strip() for c in cats_param.split(",") if c.strip()] or None
    force_refresh = request.args.get("refresh", "0") == "1"
    results = get_nearby_services(lat=lat, lon=lon, radius_km=radius,
                                  categories=categories, force_refresh=force_refresh, db_path=DB)
    output = {}
    for cat, info in results.items():
        output[cat] = {
            "label":  CATEGORY_INFO.get(cat, {}).get("label", cat),
            "icon":   CATEGORY_INFO.get(cat, {}).get("icon",  "📍"),
            "color":  CATEGORY_INFO.get(cat, {}).get("color", "#888"),
            "source": info["source"],
            "count":  info["count"],
            "services": [
                {"name": s["name"], "lat": s["lat"], "lon": s["lon"],
                 "distance_km": s["distance_km"], "phone": s.get("phone",""),
                 "address": s.get("address",""), "website": s.get("website",""),
                 "category": cat}
                for s in info["data"][:20]
            ]
        }
    total = sum(v["count"] for v in output.values())
    return jsonify({"lat":lat,"lon":lon,"radius":radius,"total":total,"results":output})

@app.route("/api/emergency")
def api_emergency():
    country = request.args.get("country", "IN")
    return jsonify(get_emergency_numbers(country, DB))

@app.route("/api/emergency/all")
def api_emergency_all():
    return jsonify(get_all_emergency_numbers(DB))

@app.route("/api/geocode")
def api_geocode():
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lon required"}), 400
    return jsonify(reverse_geocode(lat, lon))

@app.route("/api/categories")
def api_categories():
    return jsonify({k: {"label":v["label"],"icon":v["icon"],"color":v["color"],"priority":v["priority"]}
                    for k, v in CATEGORY_INFO.items()})

@app.route("/api/firstaid")
def api_firstaid_all():
    """Return all first aid topics (for offline caching)."""
    result = {}
    for key, data in FIRST_AID_DATA.items():
        result[key] = {
            "title": data["title"],
            "icon": data["icon"],
            "color": data["color"],
            "severity": data["severity"],
            "step_count": len(data["steps"])
        }
    return jsonify(result)

@app.route("/api/firstaid/<injury_type>")
def api_firstaid(injury_type):
    """Return detailed first aid steps for a specific injury."""
    data = get_first_aid(injury_type)
    if data is None:
        return jsonify({"error": "Unknown injury type"}), 404
    return jsonify(data)

@app.route("/api/incidents", methods=["GET"])
def api_get_incidents():
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lon required"}), 400
    radius = float(request.args.get("radius", 10.0))
    return jsonify({"incidents": get_incidents(lat, lon, radius, DB)})

@app.route("/api/incidents", methods=["POST"])
def api_report_incident():
    data = request.get_json()
    try:
        lat   = float(data["lat"])
        lon   = float(data["lon"])
        itype = str(data["type"])
        desc  = str(data.get("description",""))
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "lat, lon, type required"}), 400
    report_incident(lat, lon, itype, desc, DB)
    return jsonify({"status": "reported"})

@app.route("/api/share")
def api_share():
    """Generate a shareable emergency link with location."""
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lon required"}), 400
    location_name = request.args.get("name", f"{lat:.5f},{lon:.5f}")
    maps_link = f"https://maps.google.com/?q={lat},{lon}"
    osm_link  = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}"
    return jsonify({
        "maps_link": maps_link,
        "osm_link":  osm_link,
        "whatsapp":  f"https://wa.me/?text=🚨+ROAD+ACCIDENT+at+{location_name}+%0ANeed+help!+My+location:+{maps_link}",
        "sms_body":  f"🚨 ROAD ACCIDENT - Need Help! Location: {maps_link}",
        "coords":    {"lat": lat, "lon": lon}
    })


AI_SYSTEM = (
    "You are ROADSOS AI — an emergency guide inside a road accident response app used in India. "
    "Be CONCISE and CALM — the user may be panicking. Use numbered steps. Lead with the most "
    "critical action first. Always mention calling 108 (ambulance) or 112 (emergency) for serious "
    "cases. Cover: first aid, CPR, bleeding, fractures, burns, choking, shock, spinal injury. "
    "Format with line breaks. Keep under 200 words unless a procedure needs more detail."
)

@app.route("/api/ai", methods=["POST"])
def api_ai():
    """
    Free AI guide via Google Gemini 1.5 Flash.
    Expects JSON: { "history": [{"role": "user"|"assistant", "content": "..."}] }
    Returns JSON: { "reply": "..." }
    """
    GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
    if not GEMINI_KEY:
        return jsonify({"error": "GEMINI_API_KEY not set"}), 503

    data = request.get_json() or {}
    history = data.get("history", [])
    if not history:
        return jsonify({"error": "No history provided"}), 400

    contents = []
    for turn in history:
        role = "user" if turn["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": turn["content"]}]})

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": AI_SYSTEM}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 400, "temperature": 0.4}
    }
    try:
        r = req_lib.post(url, json=payload, timeout=10)
        r.raise_for_status()
        reply = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "version": "3.1.0"})

@app.route('/static/sw.js')
def sw():
    from flask import send_from_directory
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

if __name__ == "__main__":
    init_db(DB)
    print("🚨 ROADSOS starting on http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
