# 🛰️ Routr

A full-stack fleet management and route optimization app built with Streamlit, FastAPI, and OR-Tools. Manage multiple vehicles, drivers, warehouses, and delivery routes from a single dashboard.

---

## Features

**Admin**
- Multi-vehicle and multi-driver management
- Multiple warehouses as route start points
- Add stops to a pool with full recipient details (name, phone, delivery note)
- Auto-split stops into N optimized routes using geographic clustering + TSP
- Per-route manual optimization with Guided Local Search
- Real-time delivery status updates per stop (delivered, delayed, rescheduled, cancelled)
- Route progress tracking with visual progress bars
- Driver stats dashboard — delivery rate, completed routes, issues reported
- Notification inbox filtered by route events and delivery updates
- Map-based warehouse pinning

**Driver**
- Sees only their assigned routes
- Start, complete, report issues, and message admin directly from the app
- Per-stop status updates with reason messages sent to admin
- Google Maps navigation link for the full optimized route
- Can self-assign available routes from the sidebar

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend / Optimizer | FastAPI + OR-Tools |
| Database | PostgreSQL (production) / SQLite (local) |
| Maps | Folium + OpenStreetMap |
| Geocoding | Photon (Geopy) |
| Deployment | Railway |

---

## Running Locally

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Start the app**
```bash
python run.py
```

This starts both the FastAPI backend (port 8000) and the Streamlit frontend in one command. Open the URL Streamlit prints in the terminal.

**Default login:** `admin` / `admin123` — change this after first login.

---

## Project Structure

```
routr/
├── app.py            # Streamlit frontend — admin and driver views
├── backend.py        # FastAPI backend — route optimization API
├── database.py       # SQLAlchemy models and DB setup
├── run.py            # Single launcher for both processes
├── Procfile          # Railway deployment config
├── requirements.txt  # Python dependencies
└── .gitignore
```

---

## Deploying to Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add a PostgreSQL database from the Railway dashboard — the `DATABASE_URL` is set automatically
4. Add one environment variable: `BACKEND_URL = http://127.0.0.1:8000`
5. Railway deploys automatically on every push

---

## Delivery Status Flow

```
Pending → Out for Delivery → Delivered
                          ↘ Delayed → Rescheduled
                          ↘ Cancelled
```

When a stop is marked delayed, rescheduled, or cancelled, the driver enters a reason message which is logged to the admin notification inbox and would be sent via SMS to the recipient in a live deployment (Twilio-ready).

---

## Route Optimization

Routes are optimized using Google OR-Tools:
- **Clustering** — stops are grouped geographically using k-means with Haversine distance
- **TSP** — each cluster is optimized using PATH_CHEAPEST_ARC as a starting solution, then improved with Guided Local Search (for routes > 6 stops)
- **Open path** — when a warehouse is set, the route starts there and ends at the last stop with no forced return
