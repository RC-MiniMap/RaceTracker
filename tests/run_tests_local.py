"""Run lightweight local tests without external dependencies by providing
minimal fake implementations of fastf1, pandas and requests.

This lets you validate the behavior of app.Services.f1_live_data in CI-less
environments where packages aren't installed.
"""

import sys
from types import SimpleNamespace, ModuleType


class _Series:
    def __init__(self, values):
        self._vals = values

    def max(self):
        return max(self._vals) if self._vals else None

    def unique(self):
        return sorted(set(self._vals))

    def __eq__(self, other):
        return [v == other for v in self._vals]


class DataFrame:
    def __init__(self, rows):
        # rows: list[dict]
        self._rows = rows

    @property
    def empty(self):
        return len(self._rows) == 0

    @property
    def columns(self):
        if not self._rows:
            return []
        keys = set()
        for r in self._rows:
            keys.update(r.keys())
        return list(keys)

    def iterrows(self):
        for i, r in enumerate(self._rows):
            yield i, r

    def __getitem__(self, key):
        # df['Col'] -> Series
        if isinstance(key, str):
            vals = [r.get(key) for r in self._rows]
            return _Series(vals)
        # df[mask] where mask is list of booleans
        if isinstance(key, list):
            filtered = [r for r, m in zip(self._rows, key) if m]
            return DataFrame(filtered)
        raise KeyError(key)

    def sort_values(self, key):
        sorted_rows = sorted(self._rows, key=lambda r: (r.get(key) is None, r.get(key)))
        return DataFrame(sorted_rows)


def to_timedelta(s):
    # accept pandas-like string: '0 days 00:01:34.523' or seconds
    if isinstance(s, str) and "days" in s:
        # parse last part
        part = s.split()[-1]
        # part may be H:M:S.mmm or M:S.mmm
        parts = part.split(":")
        if len(parts) == 3:
            hh, mm, ss = parts
            total = int(hh) * 3600 + int(mm) * 60 + float(ss)
        elif len(parts) == 2:
            mm, ss = parts
            total = int(mm) * 60 + float(ss)
        else:
            total = float(parts[0])
    else:
        total = float(s)

    class TD:
        def __init__(self, secs):
            self._s = secs

        def total_seconds(self):
            return self._s

    return TD(total)


def isna(x):
    return x is None


def to_datetime(val):
    class DT:
        def __init__(self, v):
            self._v = v

        def date(self):
            class D:
                def __init__(self, s):
                    self._s = s

                def isoformat(self):
                    return str(self._s)

            return D(self._v)

    return DT(val)


# Inject fake pandas
fake_pd = ModuleType("pandas")
fake_pd.DataFrame = DataFrame
fake_pd.to_timedelta = to_timedelta
fake_pd.isna = isna
fake_pd.to_datetime = to_datetime
sys.modules["pandas"] = fake_pd


# Inject fake fastf1
def get_event_schedule(year):
    return DataFrame(
        [
            {"EventName": "Bahrain Grand Prix", "RoundNumber": 1, "Date": "2024-03-02"},
            {
                "EventName": "Saudi Arabian Grand Prix",
                "RoundNumber": 2,
                "Date": "2024-03-10",
            },
        ]
    )


class FakeSession:
    def __init__(self, laps):
        self.event = SimpleNamespace(EventName="Test GP")
        self.name = "Test GP"
        self.laps = laps

    def load(self, laps=True):
        return None


def get_session(year, rnd, kind):
    laps = DataFrame(
        [
            {
                "LapNumber": 1,
                "Position": 1,
                "Abbreviation": "VER",
                "Driver": "VER",
                "Number": 1,
                "Team": "Red Bull Racing",
                "LapTime": to_timedelta("0 days 00:01:34.523"),
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
                "LapTime": to_timedelta("0 days 00:01:35.000"),
                "FirstName": "Lewis",
                "LastName": "Hamilton",
            },
        ]
    )
    return FakeSession(laps)


fake_fastf1 = ModuleType("fastf1")
fake_fastf1.get_event_schedule = get_event_schedule
fake_fastf1.get_session = get_session
fake_fastf1.Cache = SimpleNamespace(enable_cache=lambda path: None)
sys.modules["fastf1"] = fake_fastf1


# Inject fake requests
class FakeResp:
    def raise_for_status(self):
        return None

    def json(self):
        return [
            {"abbreviation": "VER", "image": "https://openf1.example/VER.jpg"},
            {"abbreviation": "HAM", "image": "https://openf1.example/HAM.jpg"},
        ]


fake_requests = ModuleType("requests")


class _Adapters:
    class HTTPAdapter:
        def __init__(self, *a, **k):
            pass


fake_requests.adapters = _Adapters


class _Session:
    def __init__(self):
        pass

    def get(self, url, params=None, timeout=10):
        return FakeResp()

    def mount(self, prefix, adapter):
        return None


fake_requests.Session = _Session
fake_requests.get = lambda url, timeout=10: FakeResp()

# also provide requests.adapters module for 'from requests.adapters import HTTPAdapter'
req_adapters = ModuleType("requests.adapters")
req_adapters.HTTPAdapter = _Adapters.HTTPAdapter
sys.modules["requests.adapters"] = req_adapters

sys.modules["requests"] = fake_requests


def run():
    from app.Services import f1_live_data as fld

    print("Testing get_available_races(2024)")
    races = fld.get_available_races(2024)
    print("->", races)
    assert isinstance(races, list) and len(races) == 2

    print("Testing get_race_lap_data(2024,1)")
    rd = fld.get_race_lap_data(2024, 1)
    print("-> race_name:", rd.get("race_name"))
    print("-> total_laps:", rd.get("total_laps"))
    assert rd.get("race_name") == "Test GP"
    assert rd.get("total_laps") == 1
    assert isinstance(rd.get("laps"), list) and len(rd.get("laps")) == 1

    print("All checks passed")


if __name__ == "__main__":
    run()
