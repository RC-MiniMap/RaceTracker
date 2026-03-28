import types
from types import SimpleNamespace
import pandas as pd
import numpy as np

# Compatibility shim: some fastf1 versions reference `np.NaN` which was
# removed in NumPy 2.0; provide an alias to maintain compatibility in tests.
if not hasattr(np, "NaN"):
    setattr(np, "NaN", np.nan)

import fastf1
import requests

from app.Services import f1_live_data as fld


def test_get_available_races(monkeypatch):
    # Prepare a fake schedule DataFrame
    df = pd.DataFrame(
        [
            {"EventName": "Bahrain Grand Prix", "RoundNumber": 1, "Date": "2024-03-02"},
            {
                "EventName": "Saudi Arabian Grand Prix",
                "RoundNumber": 2,
                "Date": "2024-03-10",
            },
        ]
    )

    monkeypatch.setattr(fastf1, "get_event_schedule", lambda year: df)

    out = fld.get_available_races(2024)
    assert isinstance(out, list)
    assert len(out) == 2
    assert out[0]["name"] == "Bahrain Grand Prix"
    assert out[0]["round"] == 1
    assert out[0]["date"] == "2024-03-02"


def test_get_race_lap_data(monkeypatch):
    # Build fake laps DataFrame
    laps = pd.DataFrame(
        [
            {
                "LapNumber": 1,
                "Position": 1,
                "Abbreviation": "VER",
                "Driver": "VER",
                "Number": 1,
                "Team": "Red Bull Racing",
                "LapTime": pd.to_timedelta("0 days 00:01:34.523"),
                "FirstName": "Max",
                "LastName": "Verstappen",
            },
            {
                "LapNumber": 1,
                "Position": 2,
                "Abbreviation": "HAM",
                "Driver": "HAM",
                "Number": 44,
                "Team": "Mercedes",
                "LapTime": pd.to_timedelta("0 days 00:01:35.000"),
                "FirstName": "Lewis",
                "LastName": "Hamilton",
            },
        ]
    )

    class FakeSession:
        def __init__(self):
            self.event = SimpleNamespace(EventName="Test GP")
            self.name = "Test GP"
            self.laps = laps

        def load(self, laps=True):
            # no-op for fake
            return None

    monkeypatch.setattr(fastf1, "get_session", lambda y, r, s: FakeSession())

    # Mock OpenF1 request
    class FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return [
                {"abbreviation": "VER", "image": "https://openf1.example/VER.jpg"},
                {"abbreviation": "HAM", "image": "https://openf1.example/HAM.jpg"},
            ]

    monkeypatch.setattr(requests, "get", lambda url, timeout=10: FakeResp())

    out = fld.get_race_lap_data(2024, 1)
    assert isinstance(out, dict)
    assert out["race_name"] == "Test GP"
    assert out["total_laps"] == 1
    assert isinstance(out["laps"], list)
    assert len(out["laps"]) == 1
    lap0 = out["laps"][0]
    assert lap0["lap_number"] == 1
    assert isinstance(lap0["standings"], list)
    assert len(lap0["standings"]) == 2
    first = lap0["standings"][0]
    assert first["abbreviation"] == "VER"
    assert first["headshot_url"] == "https://openf1.example/VER.jpg"
    assert first["driver_name"].lower().startswith("max")
