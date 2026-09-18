from __future__ import annotations
import argparse
import csv
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models import Collection, Facility, InstrumentSession

# Column headers matching the reporting template exactly, plus trailing
# "Dataset Location", "Finalized", and "Instrument Session ID" columns giving
# the collection's data location(s) on disk, its review status, and the id of
# the InstrumentSession the row came from (to help find and merge rows that
# belong together).
#
# Filled from the database: EM_ID, Start/End Date, Start/End Time,
# EM_Use_Category ("Data Collection" for SPA/Cryo-ET, "Screening" for
# screening), PROJECT_ID, Image Count, Lamella Count (FIB-SEM only),
# Dataset Location, Finalized, Instrument Session ID. "EM Performance QC
# Check #1" defaults to "OK" (override by hand if a session actually failed
# QC); "EM Outcome Category" and "EM Performance QC Check #2" are left blank
# for manual entry.
CSV_FIELDS = [
    "EM_ID",
    "Start Date",
    "Start Time",
    "End Date",
    "End Time",
    "EM_Use_Category",
    "PROJECT_ID",
    "EM Outcome Category",
    "Image Count",
    "Lamella Count (FIB-SEM only)",
    "EM Performance QC Check #1",
    "EM Performance QC Check #2",
    "Dataset Location",
    "Finalized",
    "Instrument Session ID",
]

# collection_type values (normalized: lowercased, spaces/hyphens/underscores
# stripped) that count as "Data Collection" rather than screening/setup work.
# Collection.collection_type is free text from the instrument client API, not
# a strict enum, so a few spellings of the same thing are recognized.
_DATA_COLLECTION_TYPES = {"spa", "cryoet", "cryoem", "tomography", "tomo"}
_SCREENING_TYPES = {"screening"}


def resolve_facility(name: str | None) -> Facility | None:
    """Look up a Facility by name (case-insensitive), or raise if it doesn't exist."""
    if not name:
        return None
    facility = Facility.query.filter(db.func.lower(Facility.name) == name.lower()).first()
    if not facility:
        available = ", ".join(f.name for f in Facility.query.order_by(Facility.name).all())
        raise SystemExit(f"No facility named '{name}' found. Available: {available or 'none'}")
    return facility


def _normalize_type(collection_type: str | None) -> str:
    if not collection_type:
        return ""
    return collection_type.strip().lower().replace("-", "").replace("_", "").replace(" ", "")


def _is_data_collection_type(collection_type: str | None) -> bool:
    """Is this a SPA / Cryo-ET (tomography) collection, i.e. real data collection
    rather than screening or setup work?"""
    return _normalize_type(collection_type) in _DATA_COLLECTION_TYPES


def _is_screening_type(collection_type: str | None) -> bool:
    return _normalize_type(collection_type) in _SCREENING_TYPES


def _use_category(group: list[Collection]) -> str:
    """EM_Use_Category for a row: "Data Collection" if any collection in it is
    SPA/Cryo-ET (real data collection outranks screening in a mixed row), else
    "Screening" if any is screening, else blank for manual entry."""
    if any(_is_data_collection_type(c.collection_type) for c in group):
        return "Data Collection"
    if any(_is_screening_type(c.collection_type) for c in group):
        return "Screening"
    return ""


def _combined_count(values: list[int | None]) -> int | str:
    """Sum whichever counts are present; blank (not 0) if none of them are."""
    present = [v for v in values if v is not None]
    return sum(present) if present else ""


def collect_rows(start: datetime, end: datetime, facility_id: int | None = None) -> list[dict]:
    """Find Collections whose start_date falls within [start, end], combining
    any that share an InstrumentSession into a single row: counts summed, the
    time range widened to cover all of them, and Dataset Location listing
    every one of their folders, joined with '; '.
    """
    query = (
        db.session.query(Collection)
        .join(Collection.instrument_session)
        .filter(Collection.start_date >= start, Collection.start_date < end)
    )
    if facility_id is not None:
        query = query.filter(InstrumentSession.facility_id == facility_id)
    collections = query.order_by(Collection.start_date).all()

    # A plain dict (not itertools.groupby) so collections don't need to
    # already be sorted by session — insertion order still puts each group at
    # the position of its earliest collection, keeping rows in roughly
    # chronological order.
    groups: dict[int, list[Collection]] = {}
    for collection in collections:
        groups.setdefault(collection.instrument_session_id, []).append(collection)

    rows = []
    for group in groups.values():
        session: InstrumentSession = group[0].instrument_session
        instrument = session.instrument
        project = session.project

        start_dates = [c.start_date for c in group if c.start_date]
        # A collection with no end_date is still "ongoing" as of its own
        # start, so that's the fallback when working out the combined end.
        end_dates = [c.end_date or c.start_date for c in group if (c.end_date or c.start_date)]
        combined_start = min(start_dates) if start_dates else None
        combined_end = max(end_dates) if end_dates else None

        rows.append({
            "EM_ID": instrument.name if instrument else "",
            "Start Date": combined_start.strftime("%Y-%m-%d") if combined_start else "",
            "Start Time": combined_start.strftime("%H:%M") if combined_start else "",
            "End Date": combined_end.strftime("%Y-%m-%d") if combined_end else "",
            "End Time": combined_end.strftime("%H:%M") if combined_end else "",
            "EM_Use_Category": _use_category(group),
            "PROJECT_ID": project.project_id if project else "",
            "EM Outcome Category": "",
            "Image Count": _combined_count([c.total_image_count for c in group]),
            "Lamella Count (FIB-SEM only)": _combined_count([c.lamella_count for c in group]),
            "EM Performance QC Check #1": "OK",
            "EM Performance QC Check #2": "",
            "Dataset Location": "; ".join(c.data_location for c in group if c.data_location),
            "Finalized": "Yes" if all(not c.editable for c in group) else "No",
            "Instrument Session ID": session.id,
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
                     "format. Collections sharing an InstrumentSession are combined into one "
                     "row: counts summed, the time range widened to cover all of them, and "
                     "Dataset Location listing every folder joined with '; '. EM_ID, Start/End "
                     "Date, Start/End Time, EM_Use_Category, PROJECT_ID, Image Count, Lamella "
                     "Count (FIB-SEM only), Dataset Location, and Finalized are filled from the "
                     "database, along with the Instrument Session ID each row came from (to help "
                     "find and merge rows that belong together). EM_Use_Category is set to "
                     "'Data Collection' when any collection in the row is SPA or Cryo-ET "
                     "(tomography), otherwise 'Screening' when any is screening; Finalized is 'Yes' only if "
                     "every collection in the row has been locked after review. EM Performance "
                     "QC Check #1 defaults to 'OK'; EM Outcome Category and QC Check #2 are left "
                     "blank for manual entry."
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
