"""Download every daily layer x year into data/raw as JSON files (the bronze source).

A year file is kept once it reaches 31 December; the current year (or any year still open when
it was last fetched) is downloaded again, so re-runs only refresh what can have changed.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from .config import DAILY_LAYERS, RAW_DIR, REF_DIR, REFERENCE_LAYERS, YEARS
from .portwatch import Client


def _year_is_closed(path: Path, year: int) -> bool:
    if not path.exists():
        return False
    rows = json.loads(path.read_text(encoding="utf-8"))
    return bool(rows) and max(r["date"] for r in rows) == f"{year}-12-31"


def _write(path: Path, rows: list[dict], source: str) -> None:
    stamp = datetime.now(UTC).isoformat(timespec="seconds")
    for row in rows:
        row["_source"] = source
        row["_extracted_at"] = stamp
    path.write_text(json.dumps(rows), encoding="utf-8")


def extract(years: list[int] = YEARS, force: bool = False, client: Client | None = None) -> None:
    client = client or Client()
    REF_DIR.mkdir(parents=True, exist_ok=True)
    for local, (service, where) in REFERENCE_LAYERS.items():
        path = REF_DIR / f"{local}.json"
        if force or not path.exists():
            rows = client.query(service, where)
            _write(path, rows, service)
            print(f"reference  {local:<20} {len(rows):>6} rows")

    port_ids = json.loads((REF_DIR / "egypt_ports.json").read_text(encoding="utf-8"))
    egypt_port_ids = ", ".join(f"'{r['portid']}'" for r in port_ids)

    for layer in DAILY_LAYERS:
        layer_dir = RAW_DIR / layer.name
        layer_dir.mkdir(parents=True, exist_ok=True)
        for year in years:
            path = layer_dir / f"{year}.json"
            if not force and _year_is_closed(path, year):
                continue
            where = layer.where.format(egypt_port_ids=egypt_port_ids)
            rows = client.query(layer.service, f"({where}) AND year = {year}")
            _write(path, rows, layer.service)
            last = max((r["date"] for r in rows), default="-")
            print(f"{layer.name:<20} {year}  {len(rows):>6} rows  (last date {last})")
