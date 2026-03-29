"""F1 race data extraction via fastf1 library with Ergast fallback.

Primary functions:
  - get_available_races(year) -> list[dict]
  - get_race_lap_data(year, round_number) -> dict
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

import requests
import fastf1
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOG = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# Setup cache directories
CACHE_DIR = _repo_root() / "data"
FASTF1_CACHE_DIR = _repo_root() / "fastf1_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
FASTF1_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Enable fastf1 cache
fastf1.Cache.enable_cache(str(FASTF1_CACHE_DIR))


# =============================================================================
# FastF1-based Functions (Primary)
# =============================================================================


def get_available_races(year: int) -> List[Dict[str, Any]]:
    """Fetch F1 race schedule for a given year using fastf1.

    Args:
        year: F1 season year (e.g., 2024)

    Returns:
        List of race dicts: [{"year": int, "round": int, "name": str, "date": "YYYY-MM-DD"}, ...]
    """
    try:
        schedule = fastf1.get_event_schedule(year)
        races = []
        for _, row in schedule.iterrows():
            races.append(
                {
                    "year": year,
                    "round": int(row.get("RoundNumber", 0)),
                    "name": str(row.get("EventName", "Unknown")),
                    "date": str(row.get("EventDate", ""))[:10],
                }
            )
        return races
    except Exception as e:
        LOG.exception("Failed to fetch available races for %d: %s", year, e)
        return []


def _format_lap_time(timedelta_obj) -> str:
    """Convert pandas Timedelta to M:SS.mmm format."""
    if timedelta_obj is None or str(timedelta_obj) == "NaT":
        return ""
    try:
        total_seconds = timedelta_obj.total_seconds()
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:06.3f}"
    except Exception:
        return ""


def _fetch_openf1_headshots(year: int, round_number: int) -> Dict[str, str]:
    """Fetch driver headshot URLs from OpenF1 API.

    Returns dict mapping abbreviation -> headshot URL, or empty dict on failure.
    """
    try:
        # OpenF1 session_key format: YYYY-NN-R or YYYY-NN-Q or YYYY-NN-S
        session_key = f"{year}-{round_number:02d}-R"
        url = f"https://api.openf1.org/v1/drivers?session_key={session_key}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        headshots = {}
        for driver in data:
            abbr = driver.get("abbreviation", "") or driver.get(
                "driver_abbreviation", ""
            )
            img = driver.get("headshot_url") or driver.get("image")
            if abbr and img:
                headshots[abbr] = img
        return headshots
    except Exception as e:
        LOG.debug(
            "Could not fetch OpenF1 headshots for %d/%d: %s", year, round_number, e
        )
        return {}


def get_race_lap_data(year: int, round_number: int) -> Dict[str, Any]:
    """Fetch lap-by-lap race data using fastf1, with OpenF1 headshot enrichment.

    Args:
        year: F1 season year
        round_number: F1 race round (1-indexed)

    Returns:
        Dict with structure:
        {
            "race_name": str,
            "total_laps": int,
            "laps": [
                {
                    "lap_number": int,
                    "standings": [
                        {
                            "position": int,
                            "driver_name": str,
                            "abbreviation": str,
                            "driver_number": int,
                            "team": str,
                            "lap_time": "M:SS.mmm",
                            "headshot_url": str or null
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    """
    try:
        # Load race session
        session = fastf1.get_session(year, round_number, "R")
        session.load(laps=True)

        race_name = (
            session.event.EventName
            if hasattr(session.event, "EventName")
            else "Unknown"
        )

        # Fetch headshots
        headshots = _fetch_openf1_headshots(year, round_number)

        # Group laps by lap number and build standings
        laps_data = []
        lap_groups = session.laps.groupby("LapNumber")
        total_laps = len(lap_groups)

        for lap_num, lap_group in lap_groups:
            # Sort by position to get standings order
            standings_at_lap = []
            for _, row in lap_group.sort_values("Position").iterrows():
                try:
                    # Handle multiple possible column names for driver code
                    abbr = row.get("Abbreviation") or row.get("Driver", "")
                    # Handle multiple column names for driver name
                    first_name = row.get("FirstName", "")
                    last_name = row.get("LastName", "")
                    driver_name = f"{first_name} {last_name}".strip() or abbr

                    standings_at_lap.append(
                        {
                            "position": int(row.get("Position", 0)),
                            "driver_name": driver_name,
                            "abbreviation": abbr,
                            "driver_number": int(row.get("Number", 0)),
                            "team": str(row.get("Team", "")),
                            "lap_time": _format_lap_time(row.get("LapTime")),
                            "headshot_url": headshots.get(abbr),
                        }
                    )
                except Exception as e:
                    LOG.warning("Failed to process lap row: %s", e)
                    continue

            laps_data.append(
                {
                    "lap_number": int(lap_num),
                    "standings": standings_at_lap,
                }
            )

        return {
            "race_name": race_name,
            "total_laps": total_laps,
            "laps": laps_data,
        }
    except Exception as e:
        LOG.exception(
            "Failed to fetch race lap data for %d/%d: %s", year, round_number, e
        )
        return {"race_name": "Unknown", "total_laps": 0, "laps": []}


# =============================================================================
# Incident Data Loader
# =============================================================================


def load_incidents(year: int, round_number: int) -> Dict[str, List[Dict[str, Any]]]:
    """Load FIA incidents (penalties, track limits, spins) from fastf1 session data.

    Returns dict mapping driver abbreviation -> list of incident dicts:
    [
        {
            "type": "penalty_major"|"penalty_minor"|"track_limit"|"spin"|"contact"|"dnf_fault",
            "lap": int,
            "details": str,
            "severity": 0-10  (for user display)
        },
        ...
    ]

    Note: Currently parses from fastf1 lap status and incident columns.
    Future: Integrate with FIA official penalty database if available.
    """
    incidents_by_driver = {}

    try:
        session = fastf1.get_session(year, round_number, "R")
        session.load(laps=True)

        # Extract incidents from lap data
        # fastf1 provides several incident indicators:
        # - LapStatus: e.g., "Completed", "DNF", "Crashed", "+1Lap", etc.
        # - We can also look at position drops, large time penalties, etc.

        # Handle both "Abbreviation" and "Driver" column names
        abbr_col = (
            "Abbreviation" if "Abbreviation" in session.laps.columns else "Driver"
        )
        if abbr_col not in session.laps.columns:
            LOG.warning("No driver abbreviation column found; skipping incidents")
            return {}

        for driver_abbr in session.laps[abbr_col].unique():
            driver_laps = session.laps[session.laps[abbr_col] == driver_abbr]
            incidents = []

            # Track DNF or crash
            for idx, (_, lap) in enumerate(driver_laps.iterrows()):
                status = str(lap.get("Status", ""))

                # DNF/Crash detection
                if "DNF" in status or "Crashed" in status:
                    incidents.append(
                        {
                            "type": "dnf_fault",
                            "lap": int(lap.get("LapNumber", idx)),
                            "details": f"DNF: {status}",
                            "severity": 10,
                        }
                    )
                    break  # Only one DNF per race

                # Spin detection: sudden position loss + time spike
                if idx > 0:
                    prev_pos = driver_laps.iloc[idx - 1].get("Position")
                    curr_pos = lap.get("Position")

                    if (
                        curr_pos
                        and prev_pos
                        and isinstance(curr_pos, (int, float))
                        and isinstance(prev_pos, (int, float))
                    ):
                        if curr_pos > prev_pos + 2:
                            # Could be a spin/incident
                            incidents.append(
                                {
                                    "type": "spin",
                                    "lap": int(lap.get("LapNumber", idx)),
                                    "details": f"Possible spin: P{int(prev_pos)} → P{int(curr_pos)}",
                                    "severity": 7,
                                }
                            )

            if incidents:
                incidents_by_driver[driver_abbr] = incidents

        return incidents_by_driver
    except Exception as e:
        LOG.debug("Failed to load incidents for %d/%d: %s", year, round_number, e)
        return {}


class ErgastClient:
    BASE = "https://ergast.com/api/f1"

    def __init__(self, timeout: int = 10, retries: int = 3, backoff: float = 0.5):
        self.timeout = timeout
        self.session = requests.Session()
        retry = Retry(
            total=retries,
            backoff_factor=backoff,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url = f"{self.BASE}{path}"
        LOG.debug("GET %s %s", url, params)
        r = self.session.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _cache_path(self, name: str) -> Path:
        return CACHE_DIR / f"{name}.json"

    def _read_cache(self, name: str, ttl: Optional[int]) -> Optional[Dict[str, Any]]:
        p = self._cache_path(name)
        if not p.exists():
            return None
        if ttl is not None:
            age = time.time() - p.stat().st_mtime
            if age > ttl:
                return None
        try:
            return json.loads(p.read_text())
        except Exception:
            LOG.exception("Failed to read cache %s", p)
            return None

    def _write_cache(self, name: str, data: Dict[str, Any]) -> None:
        p = self._cache_path(name)
        p.write_text(json.dumps(data, indent=2))

    def get_current_schedule(
        self, force_refresh: bool = False, ttl: int = 60 * 60
    ) -> Dict[str, Any]:
        cache_name = "current_schedule"
        if not force_refresh:
            cached = self._read_cache(cache_name, ttl)
            if cached is not None:
                return cached
        data = self._get("/current.json")
        self._write_cache(cache_name, data)
        return data

    def get_race_results(
        self,
        season: int | str,
        round_: int | str,
        force_refresh: bool = False,
        ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        cache_name = f"results_{season}_{round_}"
        if not force_refresh:
            cached = self._read_cache(cache_name, ttl)
            if cached is not None:
                return cached
        data = self._get(f"/{season}/{round_}/results.json")
        self._write_cache(cache_name, data)
        return data

    def get_last_race_results(
        self, force_refresh: bool = False, ttl: int = 10 * 60
    ) -> Dict[str, Any]:
        cache_name = "results_last"
        if not force_refresh:
            cached = self._read_cache(cache_name, ttl)
            if cached is not None:
                return cached
        data = self._get("/current/last/results.json")
        self._write_cache(cache_name, data)
        return data


def _print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2))


def cli(argv: Optional[list[str]] = None) -> None:
    ap = argparse.ArgumentParser(description="Ergast F1 data fetcher")
    sub = ap.add_subparsers(dest="cmd")

    p_sched = sub.add_parser("schedule", help="Fetch current season schedule")
    p_sched.add_argument("--refresh", action="store_true")

    p_last = sub.add_parser("last-results", help="Fetch last race results")
    p_last.add_argument("--refresh", action="store_true")

    p_res = sub.add_parser("results", help="Fetch results for season/round")
    p_res.add_argument("--season", required=True)
    p_res.add_argument("--round", required=True)
    p_res.add_argument("--refresh", action="store_true")

    p_cache = sub.add_parser("show-cache", help="Show cache file info")
    p_cache.add_argument("--list", action="store_true")

    p_clear = sub.add_parser("clear-cache", help="Clear cache files")

    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    client = ErgastClient()

    if args.cmd == "schedule":
        data = client.get_current_schedule(force_refresh=args.refresh)
        _print_json(data)
    elif args.cmd == "last-results":
        data = client.get_last_race_results(force_refresh=args.refresh)
        _print_json(data)
    elif args.cmd == "results":
        data = client.get_race_results(
            args.season, args.round, force_refresh=args.refresh
        )
        _print_json(data)
    elif args.cmd == "show-cache":
        if args.list:
            for p in sorted(CACHE_DIR.glob("*.json")):
                mtime = datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                size = p.stat().st_size
                print(f"{p.name}\t{size} bytes\t{mtime}")
        else:
            for p in sorted(CACHE_DIR.glob("*.json")):
                print(p)
    elif args.cmd == "clear-cache":
        for p in sorted(CACHE_DIR.glob("*.json")):
            try:
                p.unlink()
            except Exception:
                LOG.exception("Failed to remove %s", p)
        print("cache cleared")
    else:
        ap.print_help()


if __name__ == "__main__":
    cli()
