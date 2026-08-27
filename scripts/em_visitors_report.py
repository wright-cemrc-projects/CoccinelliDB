from __future__ import annotations
import argparse
import csv
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, func

from app import create_app, db
from app.models import Facility, InstrumentSession, Person, session_person_link

# Column headers exactly as required by the reporting template.
# All columns are filled from the database; sessions are per-(session, person)
# and rows for persons whose session role is "staff" are excluded.
CSV_FIELDS = [
    "Project_ID*",
    "Person_ID*",
    "Session Start Date*",
    "Session End Date*",
    "Organization*",
    "Session Type*",
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
    """One row per (session, non-staff person) for sessions overlapping [start, end)."""
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

        stmt = (
            select(session_person_link.c.onsite, Person.first_name, Person.last_name, Person.organization)
            .join(Person, session_person_link.c.person_id == Person.id)
            .where(
                session_person_link.c.session_id == session.id,
                func.lower(session_person_link.c.role) != "staff",
            )
        )

        for onsite, first_name, last_name, organization in db.session.execute(stmt).all():
            rows.append({
                "Project_ID*": project.project_id if project else "",
                "Person_ID*": f"{last_name}, {first_name}",
                "Session Start Date*": session.start_date.strftime("%Y-%m-%d") if session.start_date else "",
                "Session End Date*": session.end_date.strftime("%Y-%m-%d") if session.end_date else "",
                "Organization*": organization or "",
                "Session Type*": "Onsite" if onsite else "Remote",
            })
    return rows


def write_csv(rows: list[dict], path: str) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Report visitors (non-staff persons) on InstrumentSessions between two "
                     "dates, in the EM visitors report template format. A person is 'staff' "
                     "if their session role is 'staff'; those rows are excluded. Session Type "
                     "is 'Onsite' or 'Remote' based on the person's onsite flag for that session."
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
