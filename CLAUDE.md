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

## Live Driver Rating System (PHASE 2-5 COMPLETE)

### Overview
A **live F1 driver rating system** that updates lap-by-lap during race replays. Ratings use a Sofascore/Sportmonks-inspired model (3-10 scale, 6.5 baseline) with five scoring categories:
- **Pace**: Rolling lap time vs. field average (-2 to +2)
- **Racecraft**: Overtakes, defenses, net position changes (-2 to +2)
- **Execution**: Pit stops, tire strategy, restarts (-2 to +2)
- **Position Impact**: Current position vs. grid + expected (-2 to +2)
- **Discipline**: Penalties, spins, DNF (-2 to +2)

**Combined formula**: `Rating = clip(3, 10, 6.5 + 0.35*P + 0.30*RC + 0.20*EX + 0.25*PI - 0.40*DI)`

**Provisional threshold**: Ratings marked "provisional" for first 3 laps to avoid jitter.

### Implementation Status

#### ✅ Completed
1. **Rating Engine** (`app/Services/rating_engine.py`):
   - Five scoring functions with tunable thresholds
   - Data classes: `LapSnapshot`, `DriverRaceData`, `LiveRatingSnapshot`
   - Live calculators for single driver and all drivers
   - Event detector for overtakes, pit stops, incidents
   - JSON formatter for API responses

2. **Race Data Extraction** (`app/Services/f1_live_data.py`):
   - `get_available_races(year)` — F1 schedule via fastf1
   - `get_race_lap_data(year, round)` — Lap-by-lap standings with headshot URLs
   - `load_incidents(year, round)` — Extract DNF, spins, crashes from fastf1 session data
   - OpenF1 integration for driver headshot images (graceful degradation if API fails)
   - Robust error handling + debug logging

3. **Race Analyzer** (`app/Services/race_analyzer.py`):
   - Orchestrates lap data + incidents + rating calculation
   - Caches loaded races to avoid re-fetching
   - `get_ratings_at_lap(N)` returns full rating snapshot for all drivers
   - `get_race_summary()` provides metadata

4. **Flask API Integration** (`app/api/routes.py`):
   - `GET /api/races?year=<Y>` — List available races
   - `GET /api/race/<Y>/<R>/laps` — Lap-by-lap standings (original replay data)
   - `GET /api/race/<Y>/<R>/driver-ratings?lap=<N>` — Live ratings at lap N
   - Request-level caching to avoid redundant loads
   - Proper error handling + logging

5. **Testing**:
   - Unit tests pass: `test_get_available_races`, `test_get_race_lap_data`
   - Manual validation on 2024 Bahrain (57 laps, 20 drivers)
   - Ratings update lap-by-lap, provisional status works correctly
   - API endpoints tested and working

#### ⚠️ Known Issues / Tuning Needed
1. **Rating Monotonicity**: Final ratings don't perfectly correlate with finishing positions
   - Root cause: Pace scores converge as drivers settle into similar lap times; position_impact dominates
   - Solution: Adjust weights or use additional discriminators (tire wear modeling, sector times, etc.)
   
2. **Incident Detection**: Relies on basic fastf1 status parsing, not official FIA penalties
   - Current: Detects DNF and sudden position drops (proxy for spins)
   - Future: Integrate FIA penalty database API or scraper for official incidents
   
3. **Racecraft Scoring**: Basic overtake/defense counting
   - Current: Tracks position changes, not quality of overtakes (e.g., DRS vs skill)
   - Future: Analyze gap shrinkage, sector times during overtakes for more nuance

#### Next Steps (Post-MVP)
1. **Weight tuning**: Collect user feedback on whether ratings "feel right"; adjust WEIGHT_* constants
2. **FIA incident source**: Replace basic incident detection with official penalties + track-limit warnings
3. **Tire modeling**: Add tire deg impact to pace scoring (harder tires, fresher tires, stint age)
4. **Sector-level analysis**: Use sector times instead of full lap times for finer pace discrimination
5. **Machine learning**: Train a model on historical F1 races + expert ratings to replace hand-tuned weights
6. **Caching strategy**: Persist analyzer instances across requests; consider Redis for distributed caching

### File Structure
```
app/
  Services/
    __init__.py
    f1_live_data.py        (get_available_races, get_race_lap_data, load_incidents)
    rating_engine.py       (scoring functions, data classes, calculators)
    race_analyzer.py       (orchestrator: loads data → calculates ratings)
  api/
    __init__.py
    routes.py              (Flask endpoints: /api/races, /api/race/.../laps, .../driver-ratings)
  dashboard/
    __init__.py
    routes.py              (legacy dashboard routes)
  __init__.py
tests/
  test_f1_live_data.py    (unit tests for get_available_races, get_race_lap_data)
  run_tests_local.py      (local test harness without external deps)
```

### Example API Usage
```bash
# Get 2024 schedule
curl http://localhost:5000/api/races?year=2024

# Get lap-by-lap standings for 2024 Bahrain
curl http://localhost:5000/api/race/2024/1/laps

# Get live ratings at lap 25 of 2024 Bahrain
curl http://localhost:5000/api/race/2024/1/driver-ratings?lap=25
# Response:
# {
#   "race_name": "Bahrain Grand Prix",
#   "lap": 25,
#   "total_laps": 57,
#   "ratings": {
#     "VER": {"overall_rating": 7.48, "pace": 0.5, "racecraft": 0.2, ..., "is_provisional": false},
#     ...
#   }
# }
```

---



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
