from flask import Blueprint, jsonify, abort, request
from app.Services.f1_live_data import get_available_races, get_race_lap_data

api = Blueprint("api", __name__)


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
