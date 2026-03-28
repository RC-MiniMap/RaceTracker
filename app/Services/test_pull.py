import fastf1

fastf1.Cache.enable_cache("data/cache")

session = fastf1.get_session(2024, "Monaco", "R")
session.load()

print("Session loaded successfully")
print("Session name:", session.name)
print("Number of laps rows:", len(session.laps))
print("Drivers:", session.drivers)