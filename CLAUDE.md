# RaceTracker — AI Context

## What This Project Is

An F1 race replay dashboard. Users select a past race, then watch a leaderboard animate lap-by-lap as the race plays back in simulated real time.

**MVP scope:** Race selector, leaderboard (driver name, team, position, lap time, image, abbreviation, number), play/pause replay with a timeline slider.

---

## Team & Ownership

| Person | Role | Owns |
|--------|------|------|
| Simon  | Frontend (React) | `frontend/` |
| Kaleb  | Flask API routes | `app/api/` and `app/__init__.py` |
| Neil   | Backend data | `app/Services/f1_live_data.py` |

---

## Architecture

```
React (frontend/)         Flask (app/)
Vite on :5173      ──►   API routes on :5000
                          app/api/routes.py (Kaleb)
                               │
                               ▼
                          app/Services/f1_live_data.py (Neil)
                          uses: fastf1 Python library + OpenF1 API
```

**Key rule:** Flask is purely a JSON API. React handles all rendering. Neil's code is Python functions imported by Kaleb's routes — there is no third server.

---

## API Contract

### `GET /api/races`
```json
[
  { "year": 2024, "round": 1, "name": "Bahrain Grand Prix", "date": "2024-03-02" }
]
```

### `GET /api/race/<year>/<round>/laps`
```json
{
  "race_name": "Bahrain Grand Prix",
  "total_laps": 57,
  "laps": [
    {
      "lap_number": 1,
      "standings": [
        {
          "position": 1,
          "driver_name": "Max Verstappen",
          "abbreviation": "VER",
          "driver_number": 1,
          "team": "Red Bull Racing",
          "lap_time": "1:34.523",
          "headshot_url": "https://..."
        }
      ]
    }
  ]
}
```

**Do not change this shape without telling the whole team.** Simon's React components depend on it.

---

## How to Run (Development)

You need two terminals:

```bash
# Terminal 1 — Flask
uv run python run.py

# Terminal 2 — React
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser. The Vite proxy forwards `/api/*` calls to Flask on `:5000` automatically.

---

## Key Conventions

- All Flask routes under `/api/` return JSON only — no HTML
- Neil's functions live in `app/Services/f1_live_data.py` — Kaleb imports them
- FastF1 cache lives in `fastf1_cache/` (gitignored) — don't delete it, it saves download time
- Driver headshot images come from OpenF1 API, not FastF1
- React fetches all lap data in one request at race load time, then steps through it client-side with a timer

---


