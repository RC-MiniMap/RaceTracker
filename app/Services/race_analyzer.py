"""Race analysis orchestrator: combines fastf1 lap data, incidents, and rating engine.

This module bridges get_race_lap_data() + load_incidents() with the rating engine,
producing live driver ratings for API endpoints.

Usage:
    analyzer = RaceAnalyzer(year=2024, round_number=1)
    ratings_at_lap_5 = analyzer.get_ratings_at_lap(5)
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Optional

from app.Services.f1_live_data import get_race_lap_data, load_incidents
from app.Services.rating_engine import (
    DriverRaceData,
    LapSnapshot,
    calculate_live_ratings,
    ratings_to_json,
)

LOG = logging.getLogger(__name__)


class RaceAnalyzer:
    """Orchestrates race data loading and live rating calculation."""

    def __init__(self, year: int, round_number: int):
        """Initialize analyzer with race details.

        Args:
            year: F1 season year
            round_number: F1 race round (1-indexed)
        """
        self.year = year
        self.round_number = round_number
        self._lap_data = None
        self._incidents = None
        self._driver_race_data = None
        self._total_laps = 0

    def load(self) -> bool:
        """Load all race data and incidents.

        Returns:
            True if successful, False otherwise
        """
        try:
            LOG.info("Loading race data for %d/%d...", self.year, self.round_number)

            # Get lap-by-lap standings
            self._lap_data = get_race_lap_data(self.year, self.round_number)
            if not self._lap_data or not self._lap_data.get("laps"):
                LOG.error("No lap data returned")
                return False

            self._total_laps = self._lap_data.get("total_laps", 0)

            # Load incidents
            self._incidents = load_incidents(self.year, self.round_number)
            LOG.info("Loaded %d drivers with incidents", len(self._incidents))

            # Build DriverRaceData objects
            self._build_driver_race_data()

            return True
        except Exception as e:
            LOG.exception("Failed to load race data: %s", e)
            return False

    def _build_driver_race_data(self) -> None:
        """Convert lap standings + incidents into DriverRaceData objects."""
        self._driver_race_data = {}

        if not self._lap_data or not self._lap_data.get("laps"):
            return

        # Extract all drivers and their grid positions from first lap
        drivers_seen = {}
        first_lap = self._lap_data["laps"][0] if self._lap_data["laps"] else {}

        for standing in first_lap.get("standings", []):
            abbr = standing.get("abbreviation", "")
            if abbr:
                drivers_seen[abbr] = {
                    "grid_position": standing.get("position", 0),
                    "number": standing.get("driver_number", 0),
                    "name": standing.get("driver_name", ""),
                }

        # Build race data for each driver across all laps
        for abbr, driver_info in drivers_seen.items():
            laps_list = []

            # Iterate through each lap and find this driver's position
            for lap_standing in self._lap_data.get("laps", []):
                for standing in lap_standing.get("standings", []):
                    if standing.get("abbreviation") == abbr:
                        lap_time_str = standing.get("lap_time", "")
                        lap_time = self._parse_lap_time(lap_time_str)

                        snap = LapSnapshot(
                            lap_number=lap_standing.get("lap_number", 0),
                            position=standing.get("position", 0),
                            lap_time=lap_time,
                            compound=standing.get("compound"),
                            gap_to_leader=standing.get("gap_to_leader"),
                            status="OK",
                        )
                        laps_list.append(snap)
                        break

            # Get incidents for this driver
            incidents = self._incidents.get(abbr, [])

            driver_race_data = DriverRaceData(
                driver_code=abbr,
                grid_position=driver_info["grid_position"],
                laps=laps_list,
                incidents=incidents,
                final_position=laps_list[-1].position if laps_list else None,
                final_status="OK",
            )

            self._driver_race_data[abbr] = driver_race_data

    @staticmethod
    def _parse_lap_time(lap_time_str: str) -> float:
        """Convert "M:SS.mmm" format to seconds (float)."""
        if not lap_time_str or ":" not in lap_time_str:
            return 0.0
        try:
            parts = lap_time_str.split(":")
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        except (ValueError, IndexError):
            return 0.0

    def get_ratings_at_lap(self, lap_number: int) -> Dict[str, Any]:
        """Get live ratings for all drivers at a specific lap.

        Args:
            lap_number: Target lap number (1-indexed)

        Returns:
            Dict with structure: {
                "race_name": str,
                "lap": int,
                "total_laps": int,
                "ratings": {
                    "VER": {"overall_rating": 6.8, "pace": 1.5, ..., "is_provisional": bool},
                    "HAM": {...},
                    ...
                }
            }
        """
        if not self._driver_race_data:
            LOG.warning("Driver race data not loaded; call load() first")
            return {}

        if lap_number < 1 or lap_number > self._total_laps:
            LOG.warning(
                "Invalid lap number: %d (total: %d)", lap_number, self._total_laps
            )
            return {}

        # Create clipped copies of driver data (don't mutate originals)
        all_drivers = []
        for driver in self._driver_race_data.values():
            clipped = copy.copy(driver)
            clipped.laps = [
                snap for snap in driver.laps if snap.lap_number <= lap_number
            ]
            all_drivers.append(clipped)

        # Calculate ratings
        try:
            ratings = calculate_live_ratings(
                all_drivers, current_lap=lap_number, total_laps=self._total_laps
            )
            ratings_json = ratings_to_json(ratings)

            return {
                "race_name": self._lap_data.get("race_name", "Unknown"),
                "lap": lap_number,
                "total_laps": self._total_laps,
                "ratings": ratings_json,
            }
        except Exception as e:
            LOG.exception("Failed to calculate ratings for lap %d: %s", lap_number, e)
            return {}

    def get_race_summary(self) -> Dict[str, Any]:
        """Get race metadata and summary."""
        return {
            "year": self.year,
            "round_number": self.round_number,
            "race_name": self._lap_data.get("race_name", "Unknown")
            if self._lap_data
            else "Unknown",
            "total_laps": self._total_laps,
            "drivers_count": len(self._driver_race_data)
            if self._driver_race_data
            else 0,
        }


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)

    # Quick test
    analyzer = RaceAnalyzer(2024, 1)
    if analyzer.load():
        print("Race loaded successfully!")
        print(json.dumps(analyzer.get_race_summary(), indent=2))

        # Get ratings at lap 5
        ratings = analyzer.get_ratings_at_lap(5)
        print("\nRatings at lap 5:")
        print(json.dumps(ratings, indent=2))
    else:
        print("Failed to load race data")
