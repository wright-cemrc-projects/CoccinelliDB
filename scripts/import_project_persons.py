"""Bulk-import persons and link them to projects from a CSV file.

Each row identifies a project (by project_id, creating it under --facility or
the row's own "facility" column if it doesn't exist yet) and a person (matched
by email or net_id, creating them if new), then links the two with an optional
role. Existing projects and persons are matched, not duplicated — safe to
re-run the same file, e.g. after fixing a few rows that failed.

Required columns: project_id, first_name, last_name, email
Optional columns: net_id, role, facility, organization, address1, address2,
                   state, country, telephone

Usage:
    python scripts/import_project_persons.py --csv people.csv --facility MCCET
    python scripts/import_project_persons.py --csv people.csv --commit

Without --commit this only previews what would happen; nothing is written.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyisemail import is_email

from app import create_app, db
from app.models import Facility
from app.services.project_import_service import (
    find_or_create_person,
    find_or_create_project,
    link_person_to_project,
)

REQUIRED_COLUMNS = {"project_id", "first_name", "last_name", "email"}
PERSON_EXTRA_FIELDS = ("organization", "address1", "address2", "state", "country", "telephone")


def resolve_facility_id(name: str, cache: dict[str, int]) -> int:
    """Look up a Facility by name (case-insensitive), or raise if it doesn't exist.

    Facilities aren't created by this script — mistyping one should fail the
    row rather than silently spawn a new facility.
    """
    key = name.strip().lower()
    if key in cache:
        return cache[key]

    facility = Facility.query.filter(db.func.lower(Facility.name) == key).first()
    if not facility:
        available = ", ".join(f.name for f in Facility.query.order_by(Facility.name).all())
        raise ValueError(f"No facility named '{name}' found. Available: {available or 'none'}")
    cache[key] = facility.id
    return facility.id


def process_row(row: dict, default_facility_id: int | None, facility_cache: dict[str, int]) -> dict:
    """Find-or-create the row's project and person, and link them.

    Returns a summary dict for reporting. Raises ValueError on anything that
    stops this one row from being imported (missing data, unknown facility, an
    invalid email address). Everything that can raise is checked *before* the
    first write below, so a rejected row never leaves a half-created project
    or person behind: there's no per-row transaction to unwind one (SAVEPOINTs
    would normally do this, but this project's SQLite setup doesn't have the
    standard pysqlite fix that makes savepoint rollback reliable — see the
    commit that added this comment). One bad row failing partway through
    would otherwise still get flushed to the DB when the whole run commits.
    """
    missing = [col for col in REQUIRED_COLUMNS if not (row.get(col) or "").strip()]
    if missing:
        raise ValueError(f"missing required value(s): {', '.join(missing)}")

    facility_name = (row.get("facility") or "").strip()
    if facility_name:
        facility_id = resolve_facility_id(facility_name, facility_cache)
    elif default_facility_id is not None:
        facility_id = default_facility_id
    else:
        raise ValueError("no facility column on this row and no --facility default given")

    email = row["email"].strip()
    if not is_email(email, check_dns=True):
        raise ValueError(f"'{email}' is not a valid email address.")

    # Nothing below this point can raise ValueError — every precondition it
    # depends on (facility exists, email is well-formed, required columns are
    # non-blank) was just checked above.
    project_result = find_or_create_project(row["project_id"].strip(), facility_id)

    person_result = find_or_create_person(
        first_name=row["first_name"].strip(),
        last_name=row["last_name"].strip(),
        email=email,
        net_id=(row.get("net_id") or "").strip() or None,
        **{field: (row.get(field) or "").strip() or None for field in PERSON_EXTRA_FIELDS},
    )

    newly_linked = link_person_to_project(
        project_result.record, person_result.record, (row.get("role") or "").strip() or None
    )

    return {
        "project_id": project_result.record.project_id,
        "project_created": project_result.created,
        "person": str(person_result.record),
        "person_created": person_result.created,
        "newly_linked": newly_linked,
    }


def run_import(csv_path: str, default_facility_name: str | None, verbose: bool) -> tuple[Counter, list[tuple[int, str]]]:
    counts = Counter()
    errors: list[tuple[int, str]] = []
    facility_cache: dict[str, int] = {}

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing_columns:
            raise SystemExit(f"CSV is missing required column(s): {', '.join(sorted(missing_columns))}")

        # Checked after the file's own columns, so a malformed CSV is reported
        # as that, not as a confusing "no facility" error unrelated to --facility.
        default_facility_id = (
            resolve_facility_id(default_facility_name, facility_cache) if default_facility_name else None
        )

        for line_no, row in enumerate(reader, start=2):  # header is line 1
            # Only ValueError is caught here — process_row's own checks (missing
            # fields, an unknown facility, an invalid email) always raise it
            # before touching the session, so one bad row is skippable without
            # leaving anything staged. Anything else is a real bug, not a bad
            # row, and should abort the run with a full traceback rather than
            # limp on with a session that may be broken.
            try:
                result = process_row(row, default_facility_id, facility_cache)
            except ValueError as err:
                errors.append((line_no, str(err)))
                continue

            counts["rows_ok"] += 1
            counts["projects_created"] += result["project_created"]
            counts["persons_created"] += result["person_created"]
            counts["links_created"] += result["newly_linked"]
            if verbose:
                action = "linked" if result["newly_linked"] else "already linked"
                print(
                    f"  line {line_no}: {result['person']} "
                    f"({'new' if result['person_created'] else 'existing'}) "
                    f"{action} to project '{result['project_id']}' "
                    f"({'new' if result['project_created'] else 'existing'})"
                )

    return counts, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", required=True, help="Path to the input CSV file.")
    parser.add_argument(
        "--facility",
        help="Facility name to use for rows without their own 'facility' column "
             "(and for creating new projects). Required unless every row has one.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write the changes. Without this flag, the import runs and "
             "reports what it would do, then rolls everything back.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Print a line per row processed.")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        try:
            counts, errors = run_import(args.csv, args.facility, args.verbose)
        except SystemExit:
            raise
        except Exception:
            db.session.rollback()
            raise

        if args.commit:
            db.session.commit()
        else:
            db.session.rollback()

        print()
        print(f"{'Committed' if args.commit else 'DRY RUN — nothing written'}:")
        print(f"  rows imported cleanly : {counts['rows_ok']}")
        print(f"  rows with errors      : {len(errors)}")
        print(f"  projects created      : {counts['projects_created']}")
        print(f"  persons created       : {counts['persons_created']}")
        print(f"  project-person links  : {counts['links_created']}")

        if errors:
            print("\nErrors:")
            for line_no, message in errors:
                print(f"  line {line_no}: {message}")

        if not args.commit and counts["rows_ok"]:
            print("\nRe-run with --commit to write these changes.")


if __name__ == "__main__":
    main()
