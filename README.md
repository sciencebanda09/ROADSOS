<div align="center">
  <pre style="font-size: 12px; line-height: 1.1; color: #ccc;">
<span style="color: #ff3333;">██████╗ ██████╗ █████╗ ██████╗ </span><span style="color: #ffffff;">███████╗ ██████╗ ███████╗</span>
<span style="color: #ff3333;">██╔══██╗██╔═══██╗██╔══██╗██╔══██╗</span><span style="color: #ffffff;">██╔════╝██╔═══██╗██╔════╝</span>
<span style="color: #ff3333;">██████╔╝██║ ██║███████║██║ ██║</span><span style="color: #ffffff;">███████╗██║ ██║███████╗</span>
<span style="color: #ff3333;">██╔══██╗██║ ██║██╔══██║██║ ██║</span><span style="color: #ffffff;">╚════██║██║ ██║╚════██║</span>
<span style="color: #ff3333;">██║ ██║╚██████╔╝██║ ██║██████╔╝</span><span style="color: #ffffff;">███████║╚██████╔╝███████║</span>
<span style="color: #ff3333;">╚═╝ ╚═╝ ╚═════╝ ╚═╝ ╚═╝╚═════╝ </span><span style="color: #ffffff;">╚══════╝ ╚═════╝ ╚══════╝</span>
  </pre>
</div>

### **Road Accident Emergency Services Locator**
*Every second counts. ROADSOS finds help before you finish asking.*

[![Live Demo](https://img.shields.io/badge/🚨_LIVE_DEMO-roadsos--8ld0.onrender.com-ff1744?style=for-the-badge)](https://roadsos-8ld0.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![PWA](https://img.shields.io/badge/PWA-Offline_Ready-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## Screenshots

| Home | Nearby Services | AI Guide |
|:----:|:---------------:|:--------:|
| ![Home](screenshots/Home.png) | ![Services](screenshots/services.png) | ![AI Guide](screenshots/ai-guide.png) |

| Medical ID | Incidents | Loading |
|:----------:|:---------:|:-------:|
| ![Medical ID](screenshots/medical-id.png) | ![Incidents](screenshots/incidents.png) | ![Loading](screenshots/loading.png) |

---

## What is ROADSOS?

When a road accident happens, the difference between life and death is often measured in minutes. Victims and bystanders struggle to locate hospitals, ambulances, and police — especially in unfamiliar areas or low-connectivity zones.

**ROADSOS** solves this with a single, fast, offline-capable app that:

- Finds the **nearest trauma centres, ambulances, police, blood banks** and more in seconds
- Gives **AI-powered first aid guidance** via Claude, Gemini, or Groq — or offline as a fallback
-  **Broadcasts your live location** via a shareable link — even over WhatsApp or SMS
- Works across **60+ countries** with localised emergency numbers
- Functions **fully offline** after first load — no network, no problem

---

## Features

### Crash Auto-Detection
The app silently monitors your device accelerometer via the **DeviceMotion API**. A sudden impact above **20 m/s²** triggers a 10-second countdown overlay — tap *"I'm Okay"* to cancel, or let it auto-trigger the full SOS flow. Re-arms every 30 seconds. iOS 13+ asks for permission on first interaction.

### ⏱ Golden Hour Timer
An animated **60-minute countdown** starts the moment SOS is triggered — based on the clinical concept that trauma survival rates drop sharply after the first hour. Pulses red in the final 10 minutes to communicate urgency.

### AI Emergency Guide
A conversational in-app assistant built for real emergencies. Powered by **Claude Haiku** (Anthropic) by default, with **Gemini 2.0 Flash** and **Llama 3.1 (Groq)** as fallbacks. API keys are kept server-side — never exposed to the browser. Covers CPR, bleeding, fractures, burns, choking, shock, and spinal injury. Falls back **fully offline** to keyword-matched responses for 10 emergency types when there's no network.

### Nearby Services — Progressive Loading
Queries **OpenStreetMap** via the Overpass API across **10 service categories**. Critical categories (hospitals, ambulance, police) load and render **first** while the rest fetch in the background — so you see the most important results in seconds, not after everything loads.

| # | Category | # | Category |
|---|----------|---|----------|
| 🏥 | Hospital / Trauma Centre | 🩸 | Blood Bank |
| 🚑 | Ambulance Station | 🚒 | Fire Station |
| 👮 | Police Station | 💊 | Pharmacy |
| 🔧 | Towing / Car Repair | ⛽ | Fuel Station |
| 🔩 | Puncture Shop | 🚗 | Car Service |

### Medical ID
Critical medical data stored **entirely in localStorage** — never sent to the server. Blood type, allergies (highlighted in red), conditions, medications, and **3 emergency contacts** with tap-to-call.

### Live Location Broadcast
Generates a shareable live-tracking link that auto-refreshes and expires after **2 hours**. Also creates pre-filled **WhatsApp** and **SMS** messages with Google Maps coordinates. Automatically extends update interval in Battery Saver mode.

### Push Notifications
Subscribe to nearby incident alerts. When a serious incident (accident, flood, road blocked) is reported near you, the server fires a **W3C Web Push** notification — even with the app in the background. Works on Android Chrome and desktop; iOS 16.4+ with app added to Home Screen.

### Community Incident Reports
Report live road hazards — accidents, breakdowns, potholes, floods, debris, blocked roads. Attach photos, set expiry windows (1–48 hours), and upvote active incidents. Auto-expire cleans up stale reports without manual effort.

### Battery Saver Mode
Detected automatically via the **Battery Status API**. When battery drops to ≤ 20% and unplugged, location update intervals extend from 10s to 30s and a badge appears. Reverts automatically when charging resumes.

### First Aid Knowledge Base
Eight injury types with step-by-step guides — **fully available offline**: Severe Bleeding, CPR, Fracture, Burns, Head Injury, Choking, Shock, Spinal Injury.

### Hold-to-SOS Button
Requires a **1.5-second hold** to prevent accidental activation. Reveals country-specific emergency numbers on trigger and starts the Golden Hour timer.

---

## Global Coverage

Emergency numbers for **60+ countries** — police, ambulance, fire, and general emergency lines — baked directly into the SQLite database. Auto-detected from your GPS coordinates via reverse geocoding.

```bash
python cli.py --list-countries   # See all supported countries
python cli.py --sos --country US # Emergency numbers for any country
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/sciencebanda09/ROADSOS.git
cd ROADSOS
pip install -r requirements.txt
```

### 2. Configure (Optional)

```bash
cp .env.example .env
```

```env
# AI backend — pick one or all (Claude is recommended)
ANTHROPIC_API_KEY=your_key_here   # https://console.anthropic.com
GEMINI_API_KEY=your_key_here      # https://aistudio.google.com/app/apikey
GROQ_API_KEY=your_key_here        # https://console.groq.com

# Push notifications (optional)
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_MAILTO=mailto:you@example.com
```

> **No API key?** The app works fully without one — AI guide falls back to offline keyword matching, push notifications are disabled.

**Generate VAPID keys (one-time):**
```bash
pip install py_vapid
python -c "from py_vapid import Vapid; v=Vapid(); v.generate_keys(); print('VAPID_PRIVATE_KEY='+v.private_pem().decode().strip()); print('VAPID_PUBLIC_KEY='+v.public_key)"
```

### 3. Run

```bash
python app.py
```

Open `http://localhost:5000` — that's it.

---

## CLI Tool

A fully-featured colour terminal interface for quick lookups:

```bash
# Find all emergency services near a location
python cli.py --lat 28.6139 --lon 77.2090

# Wider radius with contact details
python cli.py --lat 19.0760 --lon 72.8777 --radius 10 --top 5 --verbose

# Filter to specific categories
python cli.py --lat 13.0827 --lon 80.2707 --categories hospital ambulance police

# Emergency numbers for any country
python cli.py --sos --country IN

# Interactive first aid guide
python cli.py --firstaid
python cli.py --firstaid cpr
python cli.py --firstaid bleeding

# List all 60+ supported countries
python cli.py --list-countries
```

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/search` | Nearby services (`lat`, `lon`, `radius`, `categories`) |
| `GET` | `/api/emergency` | Emergency numbers by country code |
| `GET` | `/api/emergency/all` | All 60+ countries |
| `GET` | `/api/geocode` | Reverse geocode coordinates |
| `GET` | `/api/categories` | All service categories with metadata |
| `GET` | `/api/firstaid` | First aid topic index |
| `GET` | `/api/firstaid/<type>` | Step-by-step guide for one injury type |
| `GET` | `/api/incidents` | Crowdsourced incidents near a location |
| `POST` | `/api/incidents` | Report a road hazard (+ optional photo, expires_hours) |
| `POST` | `/api/incidents/<id>/upvote` | Confirm an incident is still active |
| `POST` | `/api/track` | Start a live tracking session |
| `GET` | `/api/track/<token>` | Get current position for a token |
| `PUT` | `/api/track/<token>` | Update position |
| `DELETE` | `/api/track/<token>` | End tracking session |
| `GET` | `/track/<token>` | Live tracking map page |
| `POST` | `/api/push/subscribe` | Register a Web Push subscription |
| `POST` | `/api/push/unsubscribe` | Remove a Web Push subscription |
| `POST` | `/api/ai` | AI emergency guide |
| `GET` | `/api/health` | Health check |

---

## Database Schema

Five SQLite tables — see [`schema.sql`](schema.sql) for the full export.

| Table | Purpose |
|-------|---------|
| `services` | Cached OSM service locations (hospital, police, etc.) |
| `emergency_numbers` | Country-level emergency contacts for 60+ countries |
| `incidents` | Crowdsourced road hazard reports with photos & upvotes |
| `live_tracks` | Active live location sharing sessions |
| `push_subscriptions` | Web Push subscriber endpoints |

---

## Project Structure

```
ROADSOS/
├── roadsos_core.py       ← Core engine: OSM queries, SQLite, haversine, first aid data
├── app.py                ← Flask server — all REST endpoints
├── cli.py                ← Colour terminal CLI
├── schema.sql            ← Full database schema
├── templates/
│   └── index.html        ← Mobile-first PWA frontend (single file, ~2500 lines)
├── static/
│   ├── sw.js             ← Service worker: offline cache + push notifications
│   └── manifest.json     ← PWA manifest with home screen shortcuts
├── screenshots/          ← App screenshots for README
├── .env.example          ← Environment variable template
├── requirements.txt
└── README.md
```

---

## Dependencies

| Package | Role |
|---------|------|
| `flask` | Web server |
| `requests` | HTTP client for OSM Overpass & Nominatim |
| `python-dotenv` | Environment variable loading |
| `flask-limiter` | Rate limiting on incident reports |
| `bleach` | HTML sanitisation |
| `sqlite3` | Built-in — no external database needed |
| `pywebpush` | Web Push / VAPID notifications *(optional)* |
| `leaflet.js` | Interactive maps *(CDN)* |
| Anthropic / Gemini / Groq | AI emergency guide *(optional)* |

---

## Offline Behaviour

On first load, ROADSOS fetches from OpenStreetMap and caches everything to SQLite. Subsequent requests within 24 hours are served directly from cache — no network needed. The service worker caches the shell, first aid data, category list, and Leaflet tiles. Emergency numbers and the first aid guide are **always** available offline, even on first install.

---

<div align="center">

**Built for the golden hour. Designed for panic. Works without signal.**

*Made with ❤️ for road safety in India and beyond*

</div>
