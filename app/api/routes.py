"""F1 Race Replay API routes.

Endpoints:
  GET /api/races?year=<year> - List available races for a given year
  GET /api/race/<year>/<round>/laps - Get lap-by-lap standings (original replay data)
  GET /api/race/<year>/<round>/driver-ratings?lap=<N> - Get live driver ratings at lap N
"""

from flask import Blueprint, jsonify, request
import logging

from app.Services.race_analyzer import RaceAnalyzer
from app.Services.f1_live_data import get_available_races, get_race_lap_data

LOG = logging.getLogger(__name__)
api = Blueprint("api", __name__, url_prefix="/api")

# Cache for loaded races (to avoid re-loading on every request)
_race_cache = {}


def _get_analyzer(year: int, round_number: int) -> RaceAnalyzer:
    """Get or create a RaceAnalyzer for a race, with caching."""
    cache_key = f"{year}-{round_number}"
    if cache_key not in _race_cache:
        analyzer = RaceAnalyzer(year, round_number)
        if analyzer.load():
            _race_cache[cache_key] = analyzer
        else:
            return None
    return _race_cache.get(cache_key)


@api.route("/races", methods=["GET"])
def races():
    """List available F1 races for a given year.

    Query params:
      year: F1 season year (default: current year)

    Returns:
      [{"year": int, "round": int, "name": str, "date": "YYYY-MM-DD"}, ...]
    """
    try:
        year = request.args.get("year", default=2024, type=int)
        races_list = get_available_races(year)
        return jsonify(races_list)
    except Exception as e:
        LOG.exception("Error fetching races for year %d: %s", year, e)
        return jsonify({"error": str(e)}), 500


@api.route("/race/<int:year>/<int:round_num>/laps", methods=["GET"])
def race_laps(year, round_num):
    """Get lap-by-lap standings (original replay data).

    Returns:
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
        lap_data = get_race_lap_data(year, round_num)
        return jsonify(lap_data)
    except Exception as e:
        LOG.exception("Error fetching lap data for %d/%d: %s", year, round_num, e)
        return jsonify({"error": str(e)}), 500


@api.route("/race/<int:year>/<int:round_num>/driver-ratings", methods=["GET"])
def driver_ratings(year, round_num):
    """Get live driver ratings at a specific lap.

    Query params:
      lap: Target lap number (1-indexed, required)

    Returns:
      {
          "race_name": str,
          "lap": int,
          "total_laps": int,
          "ratings": {
              "VER": {
                  "overall_rating": 6.8,
                  "pace": 1.5,
                  "racecraft": 0.2,
                  "execution": 0.8,
                  "position_impact": 1.2,
                  "discipline": -0.5,
                  "is_provisional": false
              },
              ...
          }
      }
    """
    try:
        lap = request.args.get("lap", type=int)
        if lap is None:
            return jsonify({"error": "Missing required query param: lap"}), 400

        analyzer = _get_analyzer(year, round_num)
        if not analyzer:
            return jsonify({"error": "Failed to load race data"}), 500

        ratings = analyzer.get_ratings_at_lap(lap)
        if not ratings:
            return jsonify({"error": f"Invalid lap number: {lap}"}), 400

        return jsonify(ratings)
    except Exception as e:
        LOG.exception(
            "Error calculating ratings for %d/%d lap %s: %s",
            year,
            round_num,
            request.args.get("lap"),
            e,
        )
        return jsonify({"error": str(e)}), 500
