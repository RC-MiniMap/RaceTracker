from flask import Blueprint, jsonify, abort, request
from app.Services.f1_live_data import get_available_races, get_race_lap_data
from app.Services.race_analyzer import RaceAnalyzer

api = Blueprint("api", __name__)

# Cache loaded analyzers to avoid re-loading on every request
_analyzer_cache = {}


def _get_analyzer(year: int, round_number: int):
    """Get or create a cached RaceAnalyzer for a race."""
    cache_key = f"{year}-{round_number}"
    if cache_key not in _analyzer_cache:
        analyzer = RaceAnalyzer(year, round_number)
        if analyzer.load():
            _analyzer_cache[cache_key] = analyzer
        else:
            return None
    return _analyzer_cache.get(cache_key)


@api.app_errorhandler(404)
def handle_404(error):
    return jsonify(
        {"error": error.description if hasattr(error, "description") else "Not found"}
    ), 404


@api.app_errorhandler(400)
def handle_400(error):
    return jsonify(
        {"error": error.description if hasattr(error, "description") else "Bad Request"}
    ), 400


@api.app_errorhandler(500)
def handle_500(error):
    return jsonify({"error": "Internal server error"}), 500


@api.route("/races")
def get_races():
    races = []
    for year in range(2018, 2027):  # inclusive 2018, exclusive 2027
        races += get_available_races(year)
    return jsonify(races)


@api.route("/race/<int:year>/<int:round>/laps")
def get_race_laps(year, round):
    if year < 2018 or year > 2026:
        abort(400, description="Unsupported year")
    if round < 1:
        abort(400, description="Round must be higher than one")
    race_data = get_race_lap_data(year, round)
    if not race_data or race_data.get("total_laps", 0) == 0:
        abort(404, description="Race not found")
    return jsonify(race_data)


@api.route("/race/<int:year>/<int:round>/driver-ratings")
def get_driver_ratings(year, round):
    """Get live driver ratings at a specific lap.

    Query params:
        lap: Target lap number (1-indexed, required)
    """
    if year < 2018 or year > 2026:
        abort(400, description="Unsupported year")
    if round < 1:
        abort(400, description="Round must be higher than one")

    lap = request.args.get("lap", type=int)
    if lap is None:
        abort(400, description="Missing required query param: lap")

    analyzer = _get_analyzer(year, round)
    if not analyzer:
        abort(500, description="Failed to load race data for rating calculation")

    ratings = analyzer.get_ratings_at_lap(lap)
    if not ratings:
        abort(400, description=f"Invalid lap number: {lap}")

    return jsonify(ratings)
