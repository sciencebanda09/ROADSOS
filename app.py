from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from roadsos_core import (
    init_db, get_nearby_services, get_emergency_numbers, get_all_emergency_numbers,
    reverse_geocode, CATEGORY_INFO, SERVICE_QUERIES, DB_PATH,
    report_incident, get_incidents, get_first_aid, FIRST_AID_DATA,
    create_track, update_track, get_track, delete_track,
    upvote_incident, auto_expire_incidents,
    store_push_subscription, remove_push_subscription, get_all_push_subscriptions,
)
import os
import re
import base64
import json
import secrets
import requests as req_lib
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

app = Flask(__name__)
DB  = os.environ.get("ROADSOS_DB", DB_PATH)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

APP_VERSION = "3.2.0"

ALLOWED_INC_TYPES = {"accident", "breakdown", "pothole", "flood", "debris", "blocked"}

# Incident photo storage
PHOTO_DIR = os.path.join(os.path.dirname(__file__), "static", "incident_photos")
os.makedirs(PHOTO_DIR, exist_ok=True)
MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB

# VAPID keys for Web Push (generate once: python -c "from py_vapid import Vapid; v=Vapid(); v.generate_keys(); print(v.private_pem().decode()); print(v.public_key)")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY  = os.environ.get("VAPID_PUBLIC_KEY",  "")
VAPID_CLAIMS      = {"sub": os.environ.get("VAPID_MAILTO", "mailto:admin@roadsos.app")}

def strip_html(text: str) -> str:
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()


@app.route("/favicon.ico")
def favicon():
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
    resp = jsonify(get_emergency_numbers(country, DB))
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp

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
@limiter.limit("5 per hour")
def api_report_incident():
    data = request.get_json() or {}
    try:
        lat   = float(data["lat"])
        lon   = float(data["lon"])
        itype = str(data["type"]).strip().lower()
        desc  = str(data.get("description", ""))
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "lat, lon, type required"}), 400
    if itype not in ALLOWED_INC_TYPES:
        return jsonify({"error": f"type must be one of: {', '.join(sorted(ALLOWED_INC_TYPES))}"}), 400
    desc = strip_html(desc)[:300]

    # Optional: expires_hours override (1–48)
    try:
        expires_hours = max(1, min(48, int(data.get("expires_hours", 6))))
    except (TypeError, ValueError):
        expires_hours = 6

    # Optional: base64-encoded photo (JPEG or PNG, max 5 MB)
    photo_filename = ""
    photo_b64 = data.get("photo")
    if photo_b64:
        try:
            # Strip data-URI prefix if present
            if "," in photo_b64:
                photo_b64 = photo_b64.split(",", 1)[1]
            photo_bytes = base64.b64decode(photo_b64)
            if len(photo_bytes) > MAX_PHOTO_BYTES:
                return jsonify({"error": "Photo exceeds 5 MB limit"}), 413
            # Detect image type by magic bytes
            if photo_bytes[:3] == b"\xff\xd8\xff":
                ext = "jpg"
            elif photo_bytes[:8] == b"\x89PNG\r\n\x1a\n":
                ext = "png"
            else:
                return jsonify({"error": "Only JPEG and PNG photos are accepted"}), 415
            photo_filename = f"{secrets.token_hex(12)}.{ext}"
            with open(os.path.join(PHOTO_DIR, photo_filename), "wb") as f:
                f.write(photo_bytes)
        except Exception as e:
            return jsonify({"error": f"Photo processing failed: {e}"}), 400

    report_incident(lat, lon, itype, desc, DB,
                    expires_hours=expires_hours, photo_path=photo_filename)

    # Auto-expire stale incidents on each new report (cheap maintenance)
    auto_expire_incidents(DB)

    # Push notification to subscribers for serious incident types
    serious = {"accident", "flood", "blocked"}
    if itype in serious and VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY:
        _send_push_notifications(itype, desc, lat, lon)

    return jsonify({"status": "reported"})


@app.route("/api/incidents/<int:inc_id>/upvote", methods=["POST"])
@limiter.limit("30 per hour")
def api_upvote_incident(inc_id):
    ok = upvote_incident(inc_id, DB)
    if not ok:
        return jsonify({"error": "Incident not found, expired, or already resolved"}), 404
    return jsonify({"status": "upvoted"})


@app.route("/static/incident_photos/<path:filename>")
def incident_photo(filename):
    return send_from_directory(PHOTO_DIR, filename)

@app.route("/api/share")
def api_share():
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


@app.route("/api/track", methods=["POST"])
def api_create_track():
    data = request.get_json() or {}
    try:
        lat = float(data["lat"])
        lon = float(data["lon"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "lat and lon required"}), 400
    token = create_track(lat, lon, DB)
    track_url = f"{request.host_url}track/{token}"
    return jsonify({"token": token, "url": track_url})


@app.route("/api/track/<token>", methods=["GET"])
def api_get_track(token):
    track = get_track(token, DB)
    if not track:
        return jsonify({"error": "Track not found or expired"}), 404
    return jsonify(track)


@app.route("/api/track/<token>", methods=["PUT"])
def api_update_track(token):
    data = request.get_json() or {}
    try:
        lat = float(data["lat"])
        lon = float(data["lon"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "lat and lon required"}), 400
    ok = update_track(token, lat, lon, DB)
    if not ok:
        return jsonify({"error": "Track not found or expired"}), 404
    return jsonify({"status": "updated"})


@app.route("/api/track/<token>", methods=["DELETE"])
def api_delete_track(token):
    delete_track(token, DB)
    return jsonify({"status": "stopped"})


@app.route("/track/<token>")
def view_track(token):
    track = get_track(token, DB)
    if not track:
        return "<h2 style='font-family:sans-serif;color:#888'>This tracking link has expired or is invalid.</h2>", 404

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>ROADSOS Live Track</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:#09090b;color:#f4f4f5;font-family:sans-serif;height:100dvh;display:flex;flex-direction:column}}
    #header{{padding:12px 16px;background:#141418;border-bottom:1px solid #2a2a35;display:flex;align-items:center;gap:10px;flex-shrink:0}}
    .logo{{font-size:1.2rem;font-weight:900;letter-spacing:1px}}
    .logo em{{color:#f43f5e;font-style:normal}}
    #status{{font-size:.75rem;color:#a1a1aa;margin-left:auto}}
    #pulse{{width:8px;height:8px;border-radius:50%;background:#10b981;animation:pulse 1.5s infinite;flex-shrink:0}}
    @keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 rgba(16,185,129,.4)}}50%{{box-shadow:0 0 0 8px rgba(16,185,129,0)}}}}
    #map{{flex:1}}
    #footer{{padding:10px 16px;background:#141418;border-top:1px solid #2a2a35;font-size:.7rem;color:#71717a;text-align:center}}
  </style>
</head>
<body>
  <div id="header">
    <div class="logo">ROAD<em>SOS</em></div>
    <span>Live Track</span>
    <div id="pulse"></div>
    <span id="status">Connecting...</span>
  </div>
  <div id="map"></div>
  <div id="footer">Updates every 20s · Expires 2hrs from creation · Powered by ROADSOS</div>
  <script>
    const TOKEN = {repr(token)};
    const map = L.map('map').setView([{track['lat']}, {track['lon']}], 15);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19}}).addTo(map);
    map.getContainer().style.filter='saturate(.5) brightness(.6)';

    const icon = L.divIcon({{
      html:`<div style="width:22px;height:22px;background:#f43f5e;border:3px solid white;border-radius:50%;box-shadow:0 0 12px rgba(244,63,94,.6),0 0 0 8px rgba(244,63,94,.15)"></div>`,
      className:'',iconSize:[22,22],iconAnchor:[11,11]
    }});
    let marker = L.marker([{track['lat']}, {track['lon']}],{{icon}}).addTo(map);

    function refresh(){{
      fetch('/api/track/'+TOKEN)
        .then(r=>r.json())
        .then(d=>{{
          if(d.error){{ document.getElementById('pulse').style.background='#f59e0b'; document.getElementById('status').textContent='Tracking ended'; return; }}
          marker.setLatLng([d.lat,d.lon]);
          map.panTo([d.lat,d.lon]);
          const ago = Math.round((Date.now()-new Date(d.updated_at+'Z').getTime())/1000);
          document.getElementById('status').textContent = ago<5?'Just updated':`${{ago}}s ago`;
        }}).catch(()=>{{ document.getElementById('status').textContent='Connection lost'; }});
    }}
    refresh();
    setInterval(refresh, 20000);
  </script>
</body>
</html>"""
    return html


@app.route("/api/version")
def api_version():
    return jsonify({"version": APP_VERSION})


# ── Web Push ──────────────────────────────────────────────────────────────────

def _send_push_notifications(inc_type: str, description: str, lat: float, lon: float):
    """Fire-and-forget: push a notification to all stored subscribers."""
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        return  # pywebpush not installed; silently skip

    subscriptions = get_all_push_subscriptions(DB)
    payload = json.dumps({
        "title": f"⚠️ {inc_type.capitalize()} reported nearby",
        "body":  description or f"A {inc_type} was reported near {lat:.4f}, {lon:.4f}",
        "icon":  "/static/manifest.json",
        "lat":   lat,
        "lon":   lon,
    })
    dead = []
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub["endpoint"],
                    "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
                },
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
            )
        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status in (404, 410):
                dead.append(sub["endpoint"])
    for ep in dead:
        remove_push_subscription(ep, DB)


@app.route("/api/push/vapid-public-key")
def api_vapid_key():
    if not VAPID_PUBLIC_KEY:
        return jsonify({"error": "Push notifications not configured"}), 503
    return jsonify({"key": VAPID_PUBLIC_KEY})


@app.route("/api/push/subscribe", methods=["POST"])
def api_push_subscribe():
    data = request.get_json() or {}
    endpoint = data.get("endpoint", "").strip()
    keys     = data.get("keys", {})
    p256dh   = keys.get("p256dh", "").strip()
    auth     = keys.get("auth", "").strip()
    if not (endpoint and p256dh and auth):
        return jsonify({"error": "endpoint, keys.p256dh and keys.auth are required"}), 400
    store_push_subscription(endpoint, p256dh, auth, DB)
    return jsonify({"status": "subscribed"})


@app.route("/api/push/unsubscribe", methods=["POST"])
def api_push_unsubscribe():
    data     = request.get_json() or {}
    endpoint = data.get("endpoint", "").strip()
    if endpoint:
        remove_push_subscription(endpoint, DB)
    return jsonify({"status": "unsubscribed"})


AI_SYSTEM = (
    "You are ROADSOS AI — an emergency guide inside a road accident response app used in India. "
    "Be CONCISE and CALM — the user may be panicking. Use numbered steps. Lead with the most "
    "critical action first. Always mention calling 108 (ambulance) or 112 (emergency) for serious "
    "cases. Cover: first aid, CPR, bleeding, fractures, burns, choking, shock, spinal injury. "
    "Format with line breaks. Keep under 200 words unless a procedure needs more detail."
)

@app.route("/api/ai", methods=["POST"])
def api_ai():
    ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    GEMINI_KEY    = os.environ.get("GEMINI_API_KEY", "")

    data = request.get_json() or {}
    history = data.get("history", [])
    if not history:
        return jsonify({"error": "No history provided"}), 400

    # --- Anthropic (Claude) ---
    if ANTHROPIC_KEY:
        messages = [
            {"role": t["role"], "content": t["content"]}
            for t in history
            if t["role"] in ("user", "assistant")
        ]
        payload = {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 512,
            "system": AI_SYSTEM,
            "messages": messages,
        }
        try:
            r = req_lib.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            reply = r.json()["content"][0]["text"]
            return jsonify({"reply": reply})
        except Exception as e:
            print(f"Anthropic error: {e}", flush=True)
            try:
                print(f"Anthropic response: {r.text}", flush=True)
            except:
                pass
            return jsonify({"error": str(e)}), 502

    # --- Groq (fast free tier) ---
    GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
    if GROQ_KEY:
        messages = [{"role": "system", "content": AI_SYSTEM}]
        for turn in history:
            if turn["role"] in ("user", "assistant"):
                messages.append({"role": turn["role"], "content": turn["content"]})
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "max_tokens": 400,
            "temperature": 0.4,
        }
        try:
            r = req_lib.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"]
            return jsonify({"reply": reply})
        except Exception as e:
            print(f"Groq error: {e}", flush=True)
            try:
                print(f"Groq response: {r.text}", flush=True)
            except:
                pass
            return jsonify({"error": str(e)}), 502

    # --- Gemini fallback ---
    if GEMINI_KEY:
        contents = []
        for turn in history:
            role = "user" if turn["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": turn["content"]}]})
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": AI_SYSTEM}]},
            "contents": contents,
            "generationConfig": {"maxOutputTokens": 400, "temperature": 0.4},
        }
        try:
            r = req_lib.post(url, json=payload, timeout=10)
            r.raise_for_status()
            reply = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            return jsonify({"reply": reply})
        except Exception as e:
            print(f"Gemini error: {e}", flush=True)
            try:
                print(f"Gemini response: {r.text}", flush=True)
            except:
                pass
            return jsonify({"error": str(e)}), 502

    return jsonify({"error": "No AI key configured. Set GROQ_API_KEY or GEMINI_API_KEY."}), 503


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "version": APP_VERSION})

@app.route('/static/sw.js')
def sw():
    from flask import send_from_directory
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

if __name__ == "__main__":
    init_db(DB)
    port = int(os.environ.get("PORT", 5000))
    print(f"🚨 ROADSOS v{APP_VERSION} starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)