"""F1 race data extraction via fastf1 library.

Primary functions:
  - get_available_races(year) -> list[dict]
  - get_race_lap_data(year, round_number) -> dict
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

import requests
import fastf1

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
            round_num = int(row.get("RoundNumber", 0))
            if round_num < 1:
                continue  # Skip pre-season testing (round 0)
            # fastf1 uses "EventDate" (not "Date")
            raw_date = row.get("EventDate") or row.get("Date")
            race_date = str(raw_date)[:10] if raw_date is not None else ""
            # Skip future races — no lap data available yet
            try:
                if race_date and date.fromisoformat(race_date) > date.today():
                    continue
            except ValueError:
                pass  # If date can't be parsed, include the race
            races.append(
                {
                    "year": year,
                    "round": round_num,
                    "name": str(row.get("EventName", "Unknown")),
                    "date": race_date,
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
        # First, look up the numeric session_key via the Sessions endpoint
        sessions_url = (
            f"https://api.openf1.org/v1/sessions?year={year}&session_name=Race"
        )
        sessions_resp = requests.get(sessions_url, timeout=10)
        sessions_resp.raise_for_status()
        sessions = sessions_resp.json()

        # Find the session matching our round number (1-indexed position in race sessions)
        # OpenF1 doesn't have a "round" field, so we pick the Nth race session of the year
        if not sessions or round_number < 1 or round_number > len(sessions):
            LOG.debug(
                "No matching OpenF1 session for %d round %d (found %d sessions)",
                year,
                round_number,
                len(sessions),
            )
            return {}

        session_key = sessions[round_number - 1].get("session_key")
        if not session_key:
            return {}

        # Now fetch drivers using the numeric session_key
        url = f"https://api.openf1.org/v1/drivers?session_key={session_key}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        headshots = {}
        for driver in data:
            abbr = driver.get("name_acronym", "") or driver.get("abbreviation", "")
            img = driver.get("headshot_url")
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
