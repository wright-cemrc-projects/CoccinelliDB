from __future__ import annotations
import argparse
import csv
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models import Collection, Facility, InstrumentSession

# Column headers exactly as required by the reporting template.
# Columns marked with '*' are filled from the database; the rest are left
# blank for manual entry.
CSV_FIELDS = [
    "EM_ID*",
    "Start Date*",
    "Start Time*",
    "End Date*",
    "End Time*",
    "EM_Use_Category",
    "PROJECT_ID*",
    "EM Outcome Category",
    "Image Count*",
    "Lamella Count (FIB-SEM only)",
    "EM Performance QC Check #1",
    "EM Performance QC Check #2",
]


def resolve_facility(name: str | None) -> Facility | None:
    """Look up a Facility by name (case-insensitive), or raise if it doesn't exist."""
    if not name:
        return None
    facility = Facility.query.filter(db.func.lower(Facility.name) == name.lower()).first()
    if not facility:
        available = ", ".join(f.name for f in Facility.query.order_by(Facility.name).all())
        raise SystemExit(f"No facility named '{name}' found. Available: {available or 'none'}")
    return facility


def collect_rows(start: datetime, end: datetime, facility_id: int | None = None) -> list[dict]:
    """Find Collections whose start_date falls within [start, end], inclusive."""
    query = (
        db.session.query(Collection)
        .join(Collection.instrument_session)
        .filter(Collection.start_date >= start, Collection.start_date < end)
    )
    if facility_id is not None:
        query = query.filter(InstrumentSession.facility_id == facility_id)
    collections = query.order_by(Collection.start_date).all()

    rows = []
    for collection in collections:
        session: InstrumentSession = collection.instrument_session
        instrument = session.instrument
        project = session.project

        rows.append({
            "EM_ID*": instrument.name if instrument else "",
            "Start Date*": collection.start_date.strftime("%Y-%m-%d") if collection.start_date else "",
            "Start Time*": collection.start_date.strftime("%H:%M") if collection.start_date else "",
            "End Date*": collection.end_date.strftime("%Y-%m-%d") if collection.end_date else "",
            "End Time*": collection.end_date.strftime("%H:%M") if collection.end_date else "",
            "EM_Use_Category": "",
            "PROJECT_ID*": project.project_id if project else "",
            "EM Outcome Category": "",
            "Image Count*": collection.total_image_count,
            "Lamella Count (FIB-SEM only)": "",
            "EM Performance QC Check #1": "",
            "EM Performance QC Check #2": "",
        })
    return rows


def write_csv(rows: list[dict], path: str) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Report Collections between two dates in the EM usage report template "
                     "format. Only starred columns (EM_ID*, Start/End Date*, Start/End Time*, "
                     "PROJECT_ID*, Image Count*) are filled from the database; the remaining "
                     "columns are left blank for manual entry."
    )
    parser.add_argument("--start", required=True, help="start date, inclusive (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="end date, inclusive (YYYY-MM-DD)")
    parser.add_argument("--facility", default=None, help="limit to instruments at this facility (name)")
    parser.add_argument("--output", required=True, help="path to write the CSV to")
    args = parser.parse_args()

    try:
        start = datetime.strptime(args.start, "%Y-%m-%d")
        end = datetime.strptime(args.end, "%Y-%m-%d") + timedelta(days=1)
    except ValueError as exc:
        parser.error(f"invalid date: {exc}")

    app = create_app()
    with app.app_context():
        facility = resolve_facility(args.facility)
        rows = collect_rows(start, end, facility.id if facility else None)

    write_csv(rows, args.output)
    print(f"Wrote {len(rows)} row(s) to {args.output}")


if __name__ == "__main__":
    main()
