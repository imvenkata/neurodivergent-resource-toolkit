import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List


COVERAGE_COLUMNS = [
    "region_name",
    "last_run_iso",
    "keywords_attempted",
    "searches_attempted",
    "places_found",
    "new_added",
    "duplicates",
    "last_snapshot_path",
    "notes",
]


def get_coverage_path(project_root: Path) -> str:
    db_dir = project_root / "data" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    return str(db_dir / "coverage_status.csv")


def read_coverage(coverage_path: str) -> Dict[str, Dict[str, str]]:
    if not os.path.exists(coverage_path):
        return {}
    with open(coverage_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        out: Dict[str, Dict[str, str]] = {}
        for row in reader:
            out[row.get("region_name", "")] = row
        return out


def write_coverage(coverage_path: str, rows: List[Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(coverage_path), exist_ok=True)
    with open(coverage_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COVERAGE_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def upsert_region(
    project_root: Path,
    region_name: str,
    keywords_attempted: int,
    searches_attempted: int,
    places_found: int,
    new_added: int,
    duplicates: int,
    last_snapshot_path: str,
    notes: str = "",
) -> None:
    coverage_path = get_coverage_path(project_root)
    existing = read_coverage(coverage_path)

    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    row = {
        "region_name": region_name,
        "last_run_iso": now_iso,
        "keywords_attempted": str(keywords_attempted),
        "searches_attempted": str(searches_attempted),
        "places_found": str(places_found),
        "new_added": str(new_added),
        "duplicates": str(duplicates),
        "last_snapshot_path": last_snapshot_path,
        "notes": notes,
    }

    existing[region_name] = row
    write_coverage(coverage_path, list(existing.values()))


