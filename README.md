<div align="center">

<img src="header.svg" width="100%" alt="ROADSOS — Road Accident Emergency Services Locator" />

<br/>

<img src="https://readme-typing-svg.herokuapp.com?font=Share+Tech+Mono&size=16&duration=2800&pause=900&color=FF1744&center=true&vCenter=true&multiline=false&width=700&lines=finds+help+before+you+finish+screaming+for+it;because+the+OSM+overpass+api+deserves+more+credit;golden+hour+countdown+%E2%80%94+not+just+a+vibe%2C+actually+clinical;works+offline+because+cell+towers+hate+emergencies;built+for+panic.+tested+on+three+hours+of+sleep." alt="Typing SVG" />

<br/><br/>

<!-- TECH STACK BADGES -->
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-built--in-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![PWA](https://img.shields.io/badge/PWA-Offline_Ready-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white)
![OpenStreetMap](https://img.shields.io/badge/OpenStreetMap-Overpass-7EBC6F?style=for-the-badge&logo=openstreetmap&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Haiku-D4613B?style=for-the-badge)

<br/>

<!-- STAT + JOKE BADGES -->
![Live](https://img.shields.io/badge/LIVE_DEMO-roadsos--8ld0.onrender.com-ff1744?style=flat-square&labelColor=0d1117)
![Countries](https://img.shields.io/badge/COUNTRIES_COVERED-60%2B-red?style=flat-square&labelColor=0d1117)
![License](https://img.shields.io/badge/LICENSE-MIT-green?style=flat-square&labelColor=0d1117)
![Sleep](https://img.shields.io/badge/SLEEP_LOST-immeasurable-black?style=flat-square&labelColor=0d1117)
![Coffee](https://img.shields.io/badge/COFFEE_CONSUMED-critical_levels-6F4E37?style=flat-square&labelColor=0d1117)
![Bugs](https://img.shields.io/badge/BUGS_FIXED-yes_some_of_them-yellow?style=flat-square&labelColor=0d1117)

</div>

---

## WHAT IS THIS

ROADSOS is an offline-capable Progressive Web App that locates the nearest emergency services — hospitals, ambulances, police, blood banks — after a road accident, and walks you through first aid while you wait for them to arrive. It detects crashes via your device accelerometer, starts a clinical 60-minute golden hour countdown, and broadcasts your live GPS location over WhatsApp or SMS. It covers 60+ countries and works without a network connection after the first load, because signal dies at exactly the wrong moment.

> "It's like Google Maps had a trauma response plan and actually followed through on it."

The AI guide runs on Claude Haiku by default, falls back to Gemini or Groq if that fails, and falls back to hardcoded keyword-matched offline responses if everything fails — because something always fails.

---

## FEATURES

| Feature | What It Does | Vibe |
|---|---|---|
| Crash Auto-Detection | DeviceMotion API watches for impacts above 20 m/s², fires a 10s cancel countdown | Your phone is now a judge |
| Golden Hour Timer | 60-minute animated countdown, pulses red in final 10 minutes | Medically accurate dread |
| AI Emergency Guide | Claude / Gemini / Groq with full offline fallback for 10 injury types | Three AI companies, one existential moment |
| Nearby Services | Queries OSM across 10 categories, critical ones load first | Triage for your API calls |
| Progressive Loading | Hospitals and police render while pharmacies are still thinking | Priorities, correctly ordered |
| Medical ID | Blood type, allergies, contacts — stored locally, never sent anywhere | The government cannot have this |
| Live Location Broadcast | Shareable link, auto-refreshes, expires in 2 hours | Temporary surveillance by consent |
| Push Notifications | W3C Web Push fires when an incident is reported near you | Anxiety as a service |
| Incident Reports | Crowdsourced hazards with photos, upvotes, auto-expiry | Reddit but for road crises |
| Battery Saver Mode | Detected via Battery Status API, extends update intervals at 20% | Negotiates with your hardware |
| First Aid Guides | 8 injury types, fully offline: CPR, burns, fractures, shock, more | The manual nobody wants to use |
| Hold-to-SOS | 1.5s hold to activate — prevents pocket-triggered emergencies | Intentional friction, good kind |
| Emergency Numbers | 60+ countries, auto-detected by GPS | A phone book no one printed |
| CLI Tool | Full-colour terminal interface for every feature | For the person who ssh'd into this |

---

## HOW IT WORKS

```
USER TRIGGERS SOS
       |
       v
+------+-------+
| DeviceMotion |  <-- accelerometer spike OR manual hold-to-SOS
| API / Button |      (1.5s hold prevents you activating this
+--------------+       while looking for your keys)
       |
       v
+----------------+       +------------------+
| GPS Coordinate |------>| Reverse Geocode  |  <-- Nominatim API
| acquired       |       | (country lookup) |      or "unknown" if
+----------------+       +------------------+      offline. fine.
       |                         |
       v                         v
+-------------------+    +----------------+
| Overpass API      |    | Emergency Nums |  <-- SQLite, baked in,
| (OSM query,       |    | from SQLite    |      no network needed
| 10 categories)    |    +----------------+
| cache -> SQLite   |
+-------------------+
       |
       | critical categories rendered FIRST
       | (hospital, ambulance, police)
       | background categories trickle in
       v
+--------------------+     +---------------------+
| Results on Leaflet |     | Live Tracking Link  |
| Map (offline tiles)|     | generated, shareable|
+--------------------+     | via WhatsApp / SMS  |
       |                   +---------------------+
       v
+-------------------+
| AI GUIDE CHAIN    |
|   1. Claude Haiku |  <-- preferred, server-side key
|   2. Gemini Flash |  <-- fallback
|   3. Groq Llama   |  <-- fallback to the fallback
|   4. Offline KB   |  <-- keyword match, always works
|      (10 types)   |      (this one ships in the app)
+-------------------+
       |
       v
+---------------------------+
| Golden Hour Timer running |  <-- 60 min countdown
| Medical ID accessible     |      pulses red at 10 min
| Push notifications armed  |      because subtlety is
+---------------------------+      for peacetime apps
```

---

## QUICK START

```bash
# clone and install
git clone https://github.com/sciencebanda09/ROADSOS.git
cd ROADSOS
pip install -r requirements.txt

# configure (optional — app works without any keys)
cp .env.example .env
# edit .env with your preferred AI key(s)

# run
python app.py
# open http://localhost:5000
# (yes, that's the entire setup. no docker-compose.yml. you're welcome.)
```

`.env` keys (all optional — graceful degradation at each level):

```env
ANTHROPIC_API_KEY=your_key_here    # recommended
GEMINI_API_KEY=your_key_here       # fallback
GROQ_API_KEY=your_key_here         # fallback to the fallback
VAPID_PRIVATE_KEY=...              # only needed for push notifications
VAPID_PUBLIC_KEY=...               # generate with py_vapid (see docs)
VAPID_MAILTO=mailto:you@example.com
```

---

## USAGE

**REST API — find nearby services:**

```bash
curl "http://localhost:5000/api/search?lat=28.6139&lon=77.2090&radius=5"

# response (truncated because the full thing is long):
{
  "hospital": [
    {
      "name": "AIIMS Trauma Centre",   # it found it
      "distance_km": 1.4,              # close enough
      "phone": "+91-11-26588500",      # tap to call
      "lat": 28.5672,
      "lon": 77.2100
    }
    ...
  ],
  "ambulance": [...],   # loads before pharmacy does. intentional.
  "police": [...]
}
```

**CLI — for when the browser is too many steps:**

```bash
# everything near New Delhi
python cli.py --lat 28.6139 --lon 77.2090 --radius 5 --verbose

# emergency numbers for India
python cli.py --sos --country IN

# interactive first aid — asks what's wrong, tells you what to do
python cli.py --firstaid
python cli.py --firstaid cpr         # skip the menu
python cli.py --firstaid bleeding    # red output. appropriate.

# list all 60+ supported countries
python cli.py --list-countries
```

**AI guide endpoint:**

```bash
curl -X POST http://localhost:5000/api/ai \
  -H "Content-Type: application/json" \
  -d '{"message": "person is unconscious and not breathing"}'

# returns step-by-step CPR instructions
# source: Claude, or Gemini, or Groq, or a lookup table that ships in the binary
# you will not notice the difference in an emergency. that's the point.
```

---

## PROJECT STRUCTURE

```
ROADSOS/
|
|-- app.py                  # Flask server, all 18 REST endpoints
|-- roadsos_core.py         # engine: OSM queries, haversine, first aid data, SQLite
|-- cli.py                  # colour terminal CLI (yes, colour. it's the least we could do.)
|-- schema.sql              # five tables. nothing fancy. it works.
|
|-- templates/
|   |-- index.html          # the entire frontend. one file. ~2500 lines.
|                           # (this is fine. everything is fine.)
|
|-- static/
|   |-- sw.js               # service worker: offline cache + push notifications
|   |-- manifest.json       # PWA manifest, home screen shortcuts
|
|-- screenshots/            # what it looks like when it isn't broken
|-- .env.example            # copy this. edit it. don't commit it.
|-- requirements.txt        # the usual suspects
|-- README.md               # you are here
```

---

## TECH STACK

| Layer | Technology | Why |
|---|---|---|
| Web Server | Flask 3.x | simple, synchronous, ships fast |
| Database | SQLite (built-in) | no external database to install or lose |
| Maps | Leaflet.js (CDN) + OpenStreetMap | free, accurate, offline-tileable |
| Service Discovery | OSM Overpass API | 10 categories, globally sourced |
| Geocoding | Nominatim (OSM) | reverse geocoding without a billing account |
| AI (primary) | Claude Haiku (Anthropic) | fast, cheap, actually good at emergencies |
| AI (fallback 1) | Gemini 2.0 Flash | for when Anthropic is having a day |
| AI (fallback 2) | Llama 3.1 via Groq | for when both of them are having a day |
| AI (offline) | keyword-matched lookup table | for when everyone is having a day |
| Push Notifications | W3C Web Push + VAPID (pywebpush) | background alerts, no proprietary SDK |
| Crash Detection | DeviceMotion API (browser) | no native app required |
| Offline | Service Worker + SQLite cache | first load fetches, everything else is local |
| Rate Limiting | flask-limiter | incident reports can't be spammed into oblivion |
| Input Sanitisation | bleach | because people will try |

---

## REST API REFERENCE

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/search` | nearby services by lat/lon/radius/categories |
| GET | `/api/emergency` | emergency numbers by country code |
| GET | `/api/emergency/all` | all 60+ countries at once |
| GET | `/api/geocode` | reverse geocode coordinates |
| GET | `/api/firstaid` | first aid topic index |
| GET | `/api/firstaid/<type>` | step-by-step guide for one injury type |
| GET | `/api/incidents` | crowdsourced incidents near a location |
| POST | `/api/incidents` | report a hazard (photo + expiry optional) |
| POST | `/api/incidents/<id>/upvote` | confirm incident is still active |
| POST | `/api/track` | start a live tracking session |
| GET | `/api/track/<token>` | get current position for a token |
| PUT | `/api/track/<token>` | update position |
| DELETE | `/api/track/<token>` | end tracking session |
| GET | `/track/<token>` | live tracking map page (shareable) |
| POST | `/api/push/subscribe` | register Web Push subscription |
| POST | `/api/push/unsubscribe` | remove subscription |
| POST | `/api/ai` | AI emergency guide |
| GET | `/api/health` | health check (returns 200 or the reason it doesn't) |

---

## LICENSE

MIT — use it, fork it, deploy it, credit it if you feel like it.

---

<div align="center">

<img src="footer.svg" width="100%" alt="footer" />

*Built for the golden hour. Designed for panic. Works without signal.*

</div>
