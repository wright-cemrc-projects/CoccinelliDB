from __future__ import annotations
import argparse
import csv
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import func, select

from app import create_app, db
from app.models import Facility, InstrumentSession, session_person_link

# Column headers exactly as required by the reporting template.
# Columns marked with '*' are filled from the database; the rest are left
# blank for manual entry. "Service Category*" and "Notes*" have no matching
# field on InstrumentSession, so they're left blank too, for manual entry.
CSV_FIELDS = [
    "Project_ID*",
    "Date*",
    "Total Staff hours*",
    "Service Category*",
    "Included Training",
    "Notes*",
]


def total_staff_hours(session_id: int) -> float:
    """Sum the `hours` column of session_person_link for one session."""
    stmt = select(func.coalesce(func.sum(session_person_link.c.hours), 0.0)).where(
        session_person_link.c.session_id == session_id
    )
    return db.session.execute(stmt).scalar()


def days_in_range(session_start: datetime, session_end: datetime | None, range_start, range_end) -> list:
    """Calendar days the session was active, clipped to [range_start, range_end]."""
    first_day = max(session_start.date(), range_start)
    last_day = min((session_end or session_start).date(), range_end)
    if first_day > last_day:
        return []
    return [first_day + timedelta(days=n) for n in range((last_day - first_day).days + 1)]


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
    """One row per calendar day each InstrumentSession overlapping [start, end) was active."""
    range_start = start.date()
    range_end = (end - timedelta(days=1)).date()

    query = db.session.query(InstrumentSession).filter(
        InstrumentSession.start_date < end,
        db.or_(
            InstrumentSession.end_date >= start,
            db.and_(InstrumentSession.end_date.is_(None), InstrumentSession.start_date >= start),
        ),
    )
    if facility_id is not None:
        query = query.filter(InstrumentSession.facility_id == facility_id)
    sessions = query.order_by(InstrumentSession.start_date).all()

    rows = []
    for session in sessions:
        project = session.project
        hours = total_staff_hours(session.id)
        for day in days_in_range(session.start_date, session.end_date, range_start, range_end):
            rows.append({
                "Project_ID*": project.project_id if project else "",
                "Date*": day.strftime("%Y-%m-%d"),
                "Total Staff hours*": hours,
                "Service Category*": "",
                "Included Training": "",
                "Notes*": "",
            })
    return rows


def write_csv(rows: list[dict], path: str) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Report InstrumentSessions between two dates in the EM daily usage "
                     "report template format. A session spanning multiple days produces one "
                     "row per calendar day it was active (staff hours repeated, not split). "
                     "Only Project_ID*, Date*, and Total Staff hours* are filled from the "
                     "database; the remaining columns are left blank for manual entry."
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
