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

## F1 Live Data Implementation (Neil)

### Status
✅ **Complete** — Fastf1-backed functions implemented, tested, and pushed to `feature/f1_replay_data.py`.

### What Was Built

#### Core Functions (app/Services/f1_live_data.py)

**`get_available_races(year: int) -> list[dict]`**
- Uses `fastf1.get_event_schedule(year)` to fetch F1 calendar
- Returns: `[{"year": int, "round": int, "name": str, "date": "YYYY-MM-DD"}, ...]`
- Example:
  ```python
  races = get_available_races(2024)
  # [{"year": 2024, "round": 1, "name": "Bahrain Grand Prix", "date": "2024-03-02"}, ...]
  ```

**`get_race_lap_data(year: int, round_number: int) -> dict`**
- Loads race session via `fastf1.get_session(year, round, "R")` then `session.load(laps=True)`
- Returns structure matching the API contract above:
  ```python
  data = get_race_lap_data(2024, 1)
  # {
  #   "race_name": "Bahrain Grand Prix",
  #   "total_laps": 57,
  #   "laps": [
  #     {
  #       "lap_number": 1,
  #       "standings": [
  #         {
  #           "position": 1,
  #           "driver_name": "Max Verstappen",
  #           "abbreviation": "VER",
  #           "driver_number": 1,
  #           "team": "Red Bull Racing",
  #           "lap_time": "1:34.523",
  #           "headshot_url": "https://..."
  #         },
  #         ...
  #       ]
  #     },
  #     ...
  #   ]
  # }
  ```
- Enriches driver data with headshot URLs from OpenF1 API

#### OpenF1 Headshot Integration

**`_fetch_openf1_headshots(year: int, round_number: int) -> dict`**
- Endpoint: `https://api.openf1.org/v1/drivers?session_key=<year>-<round>-R`
- Maps driver abbreviations to headshot URLs
- Returns dict: `{"VER": "https://...", "HAM": "https://...", ...}`
- Falls back to `null` if API fails or driver not found

#### Configuration & Setup

- **FastF1 cache enabled:** `fastf1.Cache.enable_cache("fastf1_cache")`
- **Cache directory:** `fastf1_cache/` (gitignored to avoid re-downloading sessions)
- **Data cache directory:** `data/` (gitignored, reserved for OpenF1 responses and future caching)
- **Dependencies added:** `fastf1`, `requests` in `pyproject.toml`

### Testing

#### Unit Tests (`tests/test_f1_live_data.py`)
- Mocks `fastf1` and `OpenF1` APIs with fake DataFrames and responses
- Validates JSON shape matches the API contract
- **2 tests pass** when run: `uv run python3 -m pytest tests/test_f1_live_data.py -q`
- Includes NumPy 2.x compatibility shim for fastf1 compatibility

#### Local Test Harness (`tests/run_tests_local.py`)
- Provides fake `pandas`, `fastf1`, `requests` modules
- Allows testing without external dependencies or network calls
- Useful for CI environments or restricted installations
- Run with: `python3 tests/run_tests_local.py`
- Output confirms both functions work end-to-end

#### How to Run Tests Locally
```bash
# Install dependencies via uv
uv add fastf1 requests pandas pytest

# Create cache directory (fastf1 requires this)
mkdir -p fastf1_cache

# Run unit tests
uv run python3 -m pytest tests/test_f1_live_data.py -q
# Output: 2 passed

# Or run the local harness (no external deps)
python3 tests/run_tests_local.py
# Output: All checks passed
```

### Implementation Details

#### How It Works
1. **Schedule fetching:** `get_available_races` iterates `fastf1.get_event_schedule(year)` DataFrame and extracts race metadata
2. **Lap loading:** `get_race_lap_data` loads a race session, iterates laps DataFrame, and builds standings per lap
3. **Headshot enrichment:** For each lap standing, `_fetch_openf1_headshots` maps driver abbreviation to OpenF1 image URL
4. **Format conversion:** Lap times (pandas Timedelta) converted to "M:SS.mmm" format for frontend consumption

#### Compatibility & Robustness
- **FastF1 column tolerance:** Uses multiple candidate keys (e.g., `Abbreviation` / `Driver`, `FirstName` / `GivenName`) to handle fastf1 version differences
- **Graceful degradation:** Missing headshots default to `null`; missing fields default to empty string or `None`
- **Error handling:** Network calls wrapped in try/except; returns predictable empty/null structures on failure
- **NumPy 2.x support:** Includes compatibility shim (`np.NaN` → `np.nan`) for newer NumPy versions

#### Known Limitations & Future Work
1. **Headshot matching:** By abbreviation only; if OpenF1 uses different identifiers, some URLs may be null
   - *Fix:* Add name-based fallback or local driver ID mapping
2. **No retry logic:** OpenF1 calls use basic HTTP with no backoff
   - *Fix:* Add `requests.adapters.Retry` or `tenacity` for transient failures
3. **Per-request session loading:** Each call redownloads fastf1 session from cache (fast but no in-memory memoization)
   - *Fix:* Add optional memoization decorator for frequently-accessed races
4. **Ergast client coexists:** Original Ergast API client remains in same module (harmless but unused)
   - *Fix:* Remove if deprecated or migrate to separate module

### Git History

- **Branch:** `feature/f1_replay_data.py`
- **Latest commit:** `3691173 feat(services): add tests and local fastf1 helpers; test harness`
- **Files modified:**
  - `app/Services/f1_live_data.py` — added `get_available_races`, `get_race_lap_data`, `_fetch_openf1_headshots`
  - `tests/test_f1_live_data.py` — unit tests (2 tests, mocked fastf1/OpenF1)
  - `tests/run_tests_local.py` — local test harness (no external deps)
  - `.gitignore` — added `fastf1_cache/`, `data/`
  - `pyproject.toml` — added `requests` dependency
  - `app/__init__.py` — fixed package initialization

### Next Steps (Pending)

- [ ] **Wire into Flask routes** (`app/api/routes.py` — Kaleb owns):
  - `GET /api/races?year=<year>` → calls `get_available_races(year)`
  - `GET /api/race/<year>/<round>/laps` → calls `get_race_lap_data(year, round)`
  - Return JSON matching the API contract above
- [ ] **Add OpenF1 response caching:** Write to `data/openf1_<year>_<round>.json` with TTL to avoid repeated calls
- [ ] **Add retry/backoff logic** for transient network failures (OpenF1 + fastf1 downloads)
- [ ] **Add GitHub Actions CI:** Run `uv run python3 -m pytest` on PRs to ensure tests always pass
- [ ] **Confirm JSON shape with frontend:** Simon validates that the lap data structure works with React components

### How Kaleb Should Import

```python
# In app/api/routes.py
from app.Services.f1_live_data import get_available_races, get_race_lap_data

@app.route('/api/races')
def races():
    year = request.args.get('year', datetime.now().year)
    return jsonify(get_available_races(int(year)))

@app.route('/api/race/<int:year>/<int:round_>/laps')
def race_laps(year, round_):
    return jsonify(get_race_lap_data(year, round_))
```

---
