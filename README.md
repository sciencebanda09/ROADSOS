# ROADSOS
### Road Accident Emergency Services Locator

Real-time emergency services locator, crash detection, AI emergency guide, and live location broadcast — built as an offline-capable PWA for road accident response in India and 60+ countries.

**Live demo:** https://roadsos-8ld0.onrender.com

---

## Screenshots

| Home | Services | AI Guide |
|------|----------|----------|
| ![Home](screenshots/Home.png) | ![Services](screenshots/services.png) | ![AI Guide](screenshots/ai-guide.png) |

| Medical ID | Incidents | Loading |
|------------|-----------|---------|
| ![Medical ID](screenshots/medical-id.png) | ![Incidents](screenshots/incidents.png) | ![Loading](screenshots/loading.png) |

---

## Project Structure

```
roadsos/
├── roadsos_core.py       — Core engine: OSM queries, SQLite cache, haversine, first aid data
├── app.py                — Flask server with REST endpoints
├── cli.py                — Colour terminal CLI
├── templates/
│   └── index.html        — Mobile-first PWA frontend (single file)
├── static/
│   ├── sw.js             — Service worker (offline cache + push notifications)
│   ├── manifest.json     — PWA manifest with home screen shortcuts
│   └── incident_photos/  — Auto-created; stores uploaded hazard photos
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/sciencebanda09/ROADSOS.git
cd ROADSOS
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Primary AI backend (Claude — recommended)
ANTHROPIC_API_KEY=your_key_here

# Fallback AI backend (Gemini — optional, free tier available)
GEMINI_API_KEY=your_key_here

# Web Push / VAPID (optional — enables push notifications)
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_MAILTO=mailto:you@example.com
```

**Generating VAPID keys** (one-time):
```bash
pip install py_vapid
python -c "
from py_vapid import Vapid
v = Vapid()
v.generate_keys()
print('VAPID_PRIVATE_KEY=' + v.private_pem().decode().strip())
print('VAPID_PUBLIC_KEY='  + v.public_key)
"
```

Get an Anthropic key at https://console.anthropic.com. Get a free Gemini key at https://aistudio.google.com/app/apikey.

The app works fully without any API key — AI guide falls back to a built-in offline keyword system, and push notifications are simply disabled.

### 3. Run

```bash
python app.py
```

---

## Features

### Crash Auto-Detection
Monitors the device accelerometer via the DeviceMotion API and detects sudden impacts above a 20 m/s² threshold. Triggers a 10-second countdown overlay before auto-SOS. One tap cancels ("I'm Okay"), or confirm to trigger the full SOS flow. Re-arms after 30 seconds. iOS 13+ requires permission on first interaction.

### Golden Hour Timer
Animated 60-minute countdown that starts automatically when SOS is triggered. Turns red and pulses in the final 10 minutes. Based on the clinical concept that trauma outcomes are significantly better when definitive care is reached within the first hour.

### AI Emergency Guide
Conversational in-app assistant for real emergencies. Uses Claude (Haiku) via the Anthropic API by default, with Gemini 1.5 Flash as fallback. The API key stays server-side and is never exposed to the browser. Covers first aid, CPR, triage, injury classification, and what to communicate to 108 or 112. Falls back fully offline to keyword-matched responses for 10 emergency types when no network or key is available.

### Medical ID
Critical medical data stored entirely in localStorage — never sent to the server. Includes blood type, date of birth, weight, allergies (shown prominently in red), medical conditions, current medications, and three emergency contacts with tap-to-call.

### Location Broadcast
Generates a shareable live-tracking link via the `/api/track` endpoint. The link shows a live map that auto-refreshes and expires 2 hours after creation. Also generates pre-filled WhatsApp and SMS emergency messages with Google Maps coordinates. In **Battery Saver mode** the update interval extends automatically to conserve power (see below).

### First Aid Knowledge Base
Eight injury types with step-by-step illustrated guides, fully available offline: Severe Bleeding, CPR, Fracture, Burns, Head Injury, Choking, Shock, Spinal Injury.

### Hold-to-SOS Button
Requires a 1.5-second hold to prevent accidental activation. Reveals country-specific emergency numbers on trigger and starts the Golden Hour timer.

### Nearby Services Search — Progressive Loading
Queries OpenStreetMap via the Overpass API across 10 categories. Results are cached in SQLite for 24 hours. High-priority categories (hospitals, ambulance, police) are fetched and rendered **first**, so critical services appear on screen within seconds while the remaining seven categories load in the background. All 10 categories are still fetched in parallel within each batch.

### Incident Community Features
- **Report hazards** — six incident types: accident, breakdown, pothole, flood, debris, road blocked.
- **Photo upload** — attach a JPEG or PNG photo (up to 5 MB) when reporting; photos are stored server-side and shown as thumbnails in the incident list and map popups.
- **Upvotes** — tap 👆 on any incident card to confirm it is still active. The upvote count is shown on the card; each device can upvote once per incident.
- **Auto-expire** — incidents are automatically marked inactive after their expiry window (default 6 hours, configurable 1–48 h per report). No manual cleanup required.

### Push Notifications
Tap **🔔 Notify me of nearby incidents** in the Incidents pane to subscribe. When a *serious* incident (accident, flood, or road-blocked) is reported anywhere near you, the server sends a Web Push notification — even when the app is in the background. Requires VAPID keys configured in `.env` (see setup). Based on the W3C Push API; works on Android Chrome and desktop browsers; limited on iOS (requires iOS 16.4+ with the app added to Home Screen).

### Battery Saver Mode
Automatically detected via the Battery Status API (Chrome/Android). When battery drops to ≤ 20% and the device is not charging, the live-tracking position update interval extends from 10 s to 30 s, and a **🪫 Saver ON** badge appears next to the notifications button. No user action required — it re-arms automatically when the battery is charged above 20% or the charger is connected.

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search` | Nearby services (`lat`, `lon`, `radius`, `categories`) |
| GET | `/api/emergency` | Emergency numbers by country code |
| GET | `/api/emergency/all` | All 60+ countries |
| GET | `/api/geocode` | Reverse geocode coordinates |
| GET | `/api/categories` | All service categories with metadata |
| GET | `/api/firstaid` | First aid topic index |
| GET | `/api/firstaid/<type>` | Step-by-step guide for one injury type |
| GET | `/api/incidents` | Crowdsourced incidents near a location |
| POST | `/api/incidents` | Report a road hazard (+ optional `photo` base64, `expires_hours`) |
| POST | `/api/incidents/<id>/upvote` | Confirm an incident is still active |
| GET | `/api/share` | Shareable location links |
| POST | `/api/track` | Start a live tracking session |
| GET | `/api/track/<token>` | Get current position for a token |
| PUT | `/api/track/<token>` | Update position |
| DELETE | `/api/track/<token>` | End tracking session |
| GET | `/track/<token>` | Live tracking map page |
| GET | `/api/push/vapid-public-key` | VAPID public key for push subscription |
| POST | `/api/push/subscribe` | Register a Web Push subscription |
| POST | `/api/push/unsubscribe` | Remove a Web Push subscription |
| POST | `/api/ai` | AI emergency guide (Claude / Gemini) |
| GET | `/api/health` | Health check |
| GET | `/api/version` | Version string |

---

## Database Schema

### `services`

| Column | Type | Description |
|--------|------|-------------|
| osm_id | TEXT | OpenStreetMap element ID |
| category | TEXT | hospital / police / ambulance / etc. |
| name | TEXT | Facility name |
| lat / lon | REAL | GPS coordinates |
| phone | TEXT | Contact number |
| address | TEXT | Street address |
| region_key | TEXT | Cache bucket key |
| cached_at | TEXT | ISO timestamp |

### `emergency_numbers`

| Column | Type |
|--------|------|
| country_code | TEXT (PK) |
| country_name | TEXT |
| police | TEXT |
| ambulance | TEXT |
| fire | TEXT |
| general | TEXT |

### `incidents`

| Column | Type | Description |
|--------|------|-------------|
| lat / lon | REAL | Location |
| type | TEXT | accident / breakdown / pothole / flood / debris / blocked |
| description | TEXT | Optional detail |
| reported_at | TEXT | ISO timestamp |
| expires_at | TEXT | ISO timestamp — auto-set from `expires_hours` |
| active | INTEGER | 1 = active; 0 = expired or manually resolved |
| upvotes | INTEGER | Community confirmations |
| photo_path | TEXT | Filename under `static/incident_photos/` (empty if none) |

### `live_tracks`

| Column | Type | Description |
|--------|------|-------------|
| token | TEXT (PK) | Secure random URL token |
| lat / lon | REAL | Current position |
| created_at | TEXT | ISO timestamp |
| updated_at | TEXT | Last position update |
| active | INTEGER | 0 = expired |

### `push_subscriptions`

| Column | Type | Description |
|--------|------|-------------|
| endpoint | TEXT (PK) | Browser push endpoint URL |
| p256dh | TEXT | ECDH public key |
| auth | TEXT | Auth secret |
| created_at | TEXT | ISO timestamp |

---

## Service Categories

| # | Category | OSM Tags |
|---|----------|----------|
| 1 | Hospital / Trauma | amenity=hospital, healthcare=hospital |
| 2 | Ambulance | emergency=ambulance_station |
| 3 | Police | amenity=police |
| 4 | Blood Bank | amenity=blood_bank |
| 5 | Fire Station | amenity=fire_station |
| 6 | Towing | shop=car_repair |
| 7 | Puncture Shop | shop=tyres |
| 8 | Pharmacy | amenity=pharmacy |
| 9 | Fuel Station | amenity=fuel |
| 10 | Car Service | shop=car |

---

## Offline Behaviour

On first run (online): fetches data from the OSM Overpass API and writes it to SQLite. On subsequent requests within 24 hours, the cache is served directly with no network required. If the network is unavailable, the last cached data is returned. The service worker additionally caches the home page, category list, first aid data, and Leaflet tile layers. Emergency numbers and the first aid guide are always available offline.

---

## CLI

```bash
# Search near a location
python cli.py --lat 28.6139 --lon 77.2090

# Wider radius, verbose output
python cli.py --lat 19.0760 --lon 72.8777 --radius 10 --top 5 --verbose

# Filter categories
python cli.py --lat 13.0827 --lon 80.2707 --categories hospital ambulance police

# Emergency numbers only
python cli.py --sos --country IN

# First aid guide (interactive menu)
python cli.py --firstaid

# Specific first aid topic
python cli.py --firstaid cpr
python cli.py --firstaid bleeding

# List all 60+ countries
python cli.py --list-countries
```

---

## Dependencies

- `flask` — web server
- `requests` — HTTP client for OSM Overpass and Nominatim
- `python-dotenv` — environment variable loading
- `flask-limiter` — rate limiting on incident reports
- `bleach` — HTML sanitisation
- `sqlite3` — built-in Python, no external database needed
- `pywebpush` — Web Push / VAPID for push notifications (optional)
- `py_vapid` — VAPID key generation utility (optional, dev-time only)
- `leaflet.js` (CDN) — interactive maps
- Anthropic Claude API or Google Gemini API Or Groq API- AI emergency guide (optional)