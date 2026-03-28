from flask import Blueprint, jsonify, abort, request

api = Blueprint("api", __name__)

@api.app_errorhandler(404)
def handle_404(error):
    return jsonify({"error": error.description if hasattr(error, "description") else "Not found"}), 404

@api.app_errorhandler(400)
def handle_400(error):
    return jsonify({"error": error.description if hasattr(error, "description") else "Bad Request"}), 400

@api.app_errorhandler(500)
def handle_500(error):
    return jsonify({"error": "Internal server error"}), 500

@api.route("/races")
def get_races():
    # Hardcoded contract JSON example
    return jsonify(
        [{"year": 2024, "round": 1, "name": "Bahrain Grand Prix", "date": "2024-03-02"}]
    )

@api.route("/race/<int:year>/<int:round>/laps")
def get_race_laps(year, round):
    if year < 2018 or year > 2026:
        abort(400, description="Unsupported year")
    if round < 1:
        abort(400, description="Round must be higher than one")
    race_data = get_race_laps_from_live_data(year,round)
    if race_data is None: 
        abort(404, description = "Race not found")
    return jsonify(race_data)
    
    # Hardcoded contract JSON example
    return jsonify(
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
                            "headshot_url": "https://example.com/max.jpg",
                        }
                    ],
                }
            ],
        }
    )
