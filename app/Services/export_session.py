from pathlib import Path
import json
from datetime import datetime, timezone

import fastf1

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
RAW_DIR = DATA_DIR / "raw"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

fastf1.Cache.enable_cache(str(CACHE_DIR))

session = fastf1.get_session(2024, "Monaco", "R")
session.load()

year = session.event["EventYear"]
event_name = session.event["EventName"]
event_slug = event_name.lower().replace(" ", "-").replace("_", "-")
session_code = "R"
session_name = "Race"

session_folder = RAW_DIR / str(year) / event_slug / session_code.replace("R", "race")
session_folder.mkdir(parents=True, exist_ok=True)

# 1) Session manifest
manifest = {
    "season": year,
    "event": event_name,
    "session": session_code,
    "session_name": session_name,
    "t0_date": getattr(session, "t0_date", None),
    "pulled_at_utc": datetime.now(timezone.utc).isoformat(),
    "drivers": [str(d) for d in session.drivers],
}

manifest_path = session_folder / "session_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

print("Wrote:", manifest_path)

# 2) Drivers
drivers = []
for d in session.drivers:
    drivers.append({
        "driver_number": str(d),
        "driver_code": str(d),
        "broadcast_name": str(d),
        "full_name": None,
        "team_name": None,
    })

drivers_path = session_folder / "drivers.json"
drivers_path.write_text(json.dumps(drivers, indent=2), encoding="utf-8")
print("Wrote:", drivers_path)

# 3) Laps
laps_df = session.laps.copy()
laps_csv = session_folder / "laps.csv"
laps_df.to_csv(laps_csv, index=False)
print("Wrote:", laps_csv)

# 4) Car telemetry for first driver
first_driver = str(session.drivers[0])
car_df = session.car_data[first_driver].copy()
car_csv = session_folder / f"car_{first_driver}.csv"
car_df.to_csv(car_csv, index=False)
print("Wrote:", car_csv)

# 5) Position telemetry for same driver
pos_df = session.pos_data[first_driver].copy()
pos_csv = session_folder / f"pos_{first_driver}.csv"
pos_df.to_csv(pos_csv, index=False)
print("Wrote:", pos_csv)

print("\nExport complete.")
print("Open the folder:")
print(session_folder)