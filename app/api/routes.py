from flask import Blueprint, jsonify

api = Blueprint("api", __name__)


@api.route("/races")
def get_races():
    # Hardcoded contract JSON example
    return jsonify(
        [{"year": 2024, "round": 1, "name": "Bahrain Grand Prix", "date": "2024-03-02"}]
    )


@api.route("/race/<int:year>/<int:round>/laps")
def get_race_laps(year, round):
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
