"""Bulk-apply reviewed image/lamella counts from a CSV and lock each row.

Each row identifies a Collection (by "id" or "data_location"), optionally
carries reviewed total_image_count / lamella_count values, and gets locked
(editable=False) once applied. A row whose collection is already finalized is
left alone and reported separately, not overwritten — this script can't be
used to silently re-lock a record with different numbers; that requires
unlocking it in the app first (Admin only), by design (see
app/services/collection_finalize_service.py).

Required columns: one of "id"/"collection_id", or "data_location" (per row)
Optional columns: image_count (or total_image_count), lamella_count
    Column names are matched case-insensitively with spaces or underscores
    ("Image Count", "image_count", "IMAGE COUNT" all work).

Usage:
    python scripts/finalize_collections.py --csv reviewed.csv
    python scripts/finalize_collections.py --csv reviewed.csv --commit

Without --commit this only previews what would happen; nothing is written.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.services.collection_finalize_service import AlreadyFinalized, finalize_collection

# Maps a normalized CSV header (lowercased, spaces -> underscores) to the
# canonical field name used below.
HEADER_ALIASES = {
    "id": "id",
    "collection_id": "id",
    "data_location": "data_location",
    "location": "data_location",
    "path": "data_location",
    "image_count": "total_image_count",
    "total_image_count": "total_image_count",
    "lamella_count": "lamella_count",
}


def normalize_row(row: dict) -> dict:
    """Re-key a CSV DictReader row onto the canonical field names above."""
    normalized = {}
    for header, value in row.items():
        if header is None:
            continue
        key = HEADER_ALIASES.get(header.strip().lower().replace(" ", "_"))
        if key:
            normalized[key] = value
    return normalized


def process_row(row: dict) -> int:
    """Finalize the row's collection. Returns its id. Raises ValueError/AlreadyFinalized."""
    fields = normalize_row(row)
    if not fields.get("id") and not fields.get("data_location"):
        raise ValueError("row has neither an id/collection_id nor a data_location column")

    collection = finalize_collection(
        collection_id=fields.get("id") or None,
        data_location=fields.get("data_location") or None,
        total_image_count=fields.get("total_image_count") or None,
        lamella_count=fields.get("lamella_count") or None,
    )
    return collection.id


def run_import(csv_path: str, verbose: bool) -> tuple[Counter, list[tuple[int, str]]]:
    counts = Counter()
    errors: list[tuple[int, str]] = []

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        normalized_headers = {HEADER_ALIASES.get((h or "").strip().lower().replace(" ", "_")) for h in (reader.fieldnames or [])}
        if not ({"id", "data_location"} & normalized_headers):
            raise SystemExit(
                "CSV needs an identifier column: 'id' (or 'collection_id'), or 'data_location'."
            )

        for line_no, row in enumerate(reader, start=2):  # header is line 1
            try:
                collection_id = process_row(row)
            except AlreadyFinalized as err:
                counts["already_finalized"] += 1
                if verbose:
                    print(f"  line {line_no}: collection {err.collection_id} already finalized, skipped")
                continue
            except ValueError as err:
                errors.append((line_no, str(err)))
                continue

            counts["finalized"] += 1
            if verbose:
                print(f"  line {line_no}: finalized collection {collection_id}")

    return counts, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", required=True, help="Path to the input CSV file.")
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write the changes. Without this flag, the run reports "
             "what it would do, then rolls everything back.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Print a line per row processed.")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        try:
            counts, errors = run_import(args.csv, args.verbose)
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
        print(f"  collections finalized  : {counts['finalized']}")
        print(f"  already finalized      : {counts['already_finalized']}")
        print(f"  rows with errors       : {len(errors)}")

        if errors:
            print("\nErrors:")
            for line_no, message in errors:
                print(f"  line {line_no}: {message}")

        if not args.commit and counts["finalized"]:
            print("\nRe-run with --commit to write these changes.")


if __name__ == "__main__":
    main()
