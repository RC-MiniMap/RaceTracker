"""Small Ergast API client for pulling F1 race data with file caching and CLI.

Usage examples:
  python -m app.Services.f1_live_data schedule
  python -m app.Services.f1_live_data last-results --refresh

This module is synchronous and depends only on `requests` from the project's
existing requirements. It stores cached JSON under the repository `data/` dir.
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOG = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


CACHE_DIR = _repo_root() / "data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ErgastClient:
    BASE = "https://ergast.com/api/f1"

    def __init__(self, timeout: int = 10, retries: int = 3, backoff: float = 0.5):
        self.timeout = timeout
        self.session = requests.Session()
        retry = Retry(
            total=retries,
            backoff_factor=backoff,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.BASE}{path}"
        LOG.debug("GET %s %s", url, params)
        r = self.session.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _cache_path(self, name: str) -> Path:
        return CACHE_DIR / f"{name}.json"

    def _read_cache(self, name: str, ttl: Optional[int]) -> Optional[Dict[str, Any]]:
        p = self._cache_path(name)
        if not p.exists():
            return None
        if ttl is not None:
            age = time.time() - p.stat().st_mtime
            if age > ttl:
                return None
        try:
            return json.loads(p.read_text())
        except Exception:
            LOG.exception("Failed to read cache %s", p)
            return None

    def _write_cache(self, name: str, data: Dict[str, Any]) -> None:
        p = self._cache_path(name)
        p.write_text(json.dumps(data, indent=2))

    def get_current_schedule(self, force_refresh: bool = False, ttl: int = 60 * 60) -> Dict[str, Any]:
        cache_name = "current_schedule"
        if not force_refresh:
            cached = self._read_cache(cache_name, ttl)
            if cached is not None:
                return cached
        data = self._get("/current.json")
        self._write_cache(cache_name, data)
        return data

    def get_race_results(self, season: int | str, round_: int | str, force_refresh: bool = False, ttl: Optional[int] = None) -> Dict[str, Any]:
        cache_name = f"results_{season}_{round_}"
        if not force_refresh:
            cached = self._read_cache(cache_name, ttl)
            if cached is not None:
                return cached
        data = self._get(f"/{season}/{round_}/results.json")
        self._write_cache(cache_name, data)
        return data

    def get_last_race_results(self, force_refresh: bool = False, ttl: int = 10 * 60) -> Dict[str, Any]:
        cache_name = "results_last"
        if not force_refresh:
            cached = self._read_cache(cache_name, ttl)
            if cached is not None:
                return cached
        data = self._get("/current/last/results.json")
        self._write_cache(cache_name, data)
        return data


def _print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2))


def cli(argv: Optional[list[str]] = None) -> None:
    ap = argparse.ArgumentParser(description="Ergast F1 data fetcher")
    sub = ap.add_subparsers(dest="cmd")

    p_sched = sub.add_parser("schedule", help="Fetch current season schedule")
    p_sched.add_argument("--refresh", action="store_true")

    p_last = sub.add_parser("last-results", help="Fetch last race results")
    p_last.add_argument("--refresh", action="store_true")

    p_res = sub.add_parser("results", help="Fetch results for season/round")
    p_res.add_argument("--season", required=True)
    p_res.add_argument("--round", required=True)
    p_res.add_argument("--refresh", action="store_true")

    p_cache = sub.add_parser("show-cache", help="Show cache file info")
    p_cache.add_argument("--list", action="store_true")

    p_clear = sub.add_parser("clear-cache", help="Clear cache files")

    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    client = ErgastClient()

    if args.cmd == "schedule":
        data = client.get_current_schedule(force_refresh=args.refresh)
        _print_json(data)
    elif args.cmd == "last-results":
        data = client.get_last_race_results(force_refresh=args.refresh)
        _print_json(data)
    elif args.cmd == "results":
        data = client.get_race_results(args.season, args.round, force_refresh=args.refresh)
        _print_json(data)
    elif args.cmd == "show-cache":
        if args.list:
            for p in sorted(CACHE_DIR.glob("*.json")):
                mtime = datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                size = p.stat().st_size
                print(f"{p.name}\t{size} bytes\t{mtime}")
        else:
            for p in sorted(CACHE_DIR.glob("*.json")):
                print(p)
    elif args.cmd == "clear-cache":
        for p in sorted(CACHE_DIR.glob("*.json")):
            try:
                p.unlink()
            except Exception:
                LOG.exception("Failed to remove %s", p)
        print("cache cleared")
    else:
        ap.print_help()


if __name__ == "__main__":
    cli()