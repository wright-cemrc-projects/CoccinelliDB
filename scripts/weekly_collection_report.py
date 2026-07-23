from __future__ import annotations
import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models import Collection, InstrumentSession

CSV_FIELDS = [
    "collection_id",
    "collection_type",
    "start_date",
    "end_date",
    "instrument_name",
    "instrument_model",
    "facility_name",
    "project_string_id",
    "people",
    "data_location",
    "total_image_count",
    "disk_bytes",
    "disk_reachable",
]


def human_readable(num_bytes: int | None) -> str:
    if num_bytes is None:
        return ""
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if value < 1024 or unit == "PB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


def directory_size(path: str) -> int:
    """Sum file sizes under `path`. Unreadable files/subdirs are skipped, not fatal."""
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError as exc:
                print(f"  Skipping {os.path.join(root, name)}: {exc}", file=sys.stderr)
    return total


def collect_rows(since: datetime, compute_footprint: bool) -> list[dict]:
    """Find Collections active in the last `since` window and gather instrument/people/footprint info."""
    collections = (
        db.session.query(Collection)
        .join(Collection.instrument_session)
        .filter(
            db.or_(
                Collection.end_date >= since,
                db.and_(Collection.end_date.is_(None), Collection.start_date >= since),
            )
        )
        .order_by(Collection.start_date)
        .all()
    )

    rows = []
    for collection in collections:
        session: InstrumentSession = collection.instrument_session
        instrument = session.instrument
        facility = session.facility
        project = session.project

        people = [f"{p.first_name} {p.last_name}" for p in session.persons]

        disk_bytes = None
        disk_reachable = False
        if compute_footprint and collection.data_location:
            if os.path.isdir(collection.data_location):
                disk_reachable = True
                print(f"Scanning {collection.data_location} ...")
                disk_bytes = directory_size(collection.data_location)
            else:
                print(f"  Not reachable from this host: {collection.data_location}", file=sys.stderr)

        rows.append({
            "collection_id": collection.id,
            "collection_type": collection.collection_type,
            "start_date": collection.start_date.isoformat() if collection.start_date else "",
            "end_date": collection.end_date.isoformat() if collection.end_date else "",
            "instrument_name": instrument.name if instrument else "",
            "instrument_model": instrument.model if instrument else "",
            "facility_name": facility.name if facility else "",
            "project_string_id": project.project_id if project else "",
            "people": "; ".join(people),
            "data_location": collection.data_location or "",
            "total_image_count": collection.total_image_count,
            "disk_bytes": disk_bytes,
            "disk_reachable": disk_reachable,
        })
    return rows


def write_csv(rows: list[dict], path: str) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: list[dict], path: str) -> None:
    with open(path, "w") as f:
        json.dump(rows, f, indent=2)


def print_table(rows: list[dict]) -> None:
    if not rows:
        print("No collections found in this window.")
        return

    for row in rows:
        size = human_readable(row["disk_bytes"]) if row["disk_bytes"] is not None else (
            "unreachable" if not row["disk_reachable"] and row["data_location"] else "n/a"
        )
        print(
            f"[{row['collection_id']}] {row['start_date']} -> {row['end_date']} "
            f"| {row['instrument_name']} ({row['facility_name']}) "
            f"| project={row['project_string_id'] or '-'} "
            f"| people={row['people'] or '-'} "
            f"| images={row['total_image_count'] if row['total_image_count'] is not None else '-'} "
            f"| size={size} "
            f"| {row['data_location']}"
        )
    total_bytes = sum(r["disk_bytes"] for r in rows if r["disk_bytes"] is not None)
    if total_bytes:
        print(f"\n{len(rows)} collection(s), total footprint scanned: {human_readable(total_bytes)}")
    else:
        print(f"\n{len(rows)} collection(s)")


def main():
    parser = argparse.ArgumentParser(
        description="Report Collections active in the last N days: instrument, facility, "
                     "project, people on the session, and (optionally) their on-disk size. "
                     "Must run somewhere that can both reach the CoccinelliDB and, for "
                     "--footprint, mount the data_location paths."
    )
    parser.add_argument("--days", type=int, default=7, help="how many days back to look (default: 7)")
    parser.add_argument("--footprint", action="store_true",
                         help="walk each data_location to compute actual bytes on disk (slow)")
    parser.add_argument("--output", default=None, help="write results to this file instead of stdout")
    parser.add_argument("--format", choices=["table", "csv", "json"], default="table",
                         help="output format (default: table; csv/json imply --output)")
    args = parser.parse_args()

    if args.format in ("csv", "json") and not args.output:
        parser.error(f"--format {args.format} requires --output")

    app = create_app()
    with app.app_context():
        since = datetime.utcnow() - timedelta(days=args.days)
        rows = collect_rows(since, compute_footprint=args.footprint)

    if args.format == "csv":
        write_csv(rows, args.output)
        print(f"Wrote {len(rows)} row(s) to {args.output}")
    elif args.format == "json":
        write_json(rows, args.output)
        print(f"Wrote {len(rows)} row(s) to {args.output}")
    else:
        print_table(rows)
        if args.output:
            write_csv(rows, args.output)
            print(f"\nAlso wrote {len(rows)} row(s) to {args.output}")


if __name__ == "__main__":
    main()
