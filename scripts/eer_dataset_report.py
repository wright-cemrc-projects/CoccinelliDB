from __future__ import annotations
import argparse
import csv
import json
import os
import sys
from collections import Counter
from datetime import datetime

INPUT_FIELDS_NEEDED = ("collection_id", "data_location")

SKIP_DIR_NAMES = {"evaluation"}


def walk_skipping_evaluation(top: str):
    for root, dirs, files in os.walk(top):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIR_NAMES]
        yield root, dirs, files

OUTPUT_FIELDS = [
    "collection_id",
    "data_location",
    "type_of_software",
    "eer_count",
    "earliest_eer_timestamp",
    "latest_eer_timestamp",
    "diff_hours",
    "eer_per_hour",
    "peak_eer_per_hour",
    "peak_hour_start",
    "notes",
]


def find_dataset_json(data_location: str) -> str | None:
    """Look for dataset.json directly in data_location, falling back to a recursive search."""
    direct = os.path.join(data_location, "dataset.json")
    if os.path.isfile(direct):
        return direct
    for root, _dirs, files in walk_skipping_evaluation(data_location):
        for name in files:
            if name == "dataset.json":
                return os.path.join(root, name)
    return None


def read_type_of_software(data_location: str, notes: list[str]) -> str:
    dataset_path = find_dataset_json(data_location)
    if dataset_path is None:
        notes.append("dataset.json not found")
        return ""
    try:
        with open(dataset_path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        notes.append(f"could not read dataset.json: {exc}")
        return ""
    type_of_software = data.get("TypeOfSoftware", "")
    if not type_of_software:
        notes.append("TypeOfSoftware missing from dataset.json")
    return type_of_software


def scan_eer_files(data_location: str, notes: list[str]) -> list[datetime]:
    timestamps: list[datetime] = []
    for root, _dirs, files in walk_skipping_evaluation(data_location):
        for name in files:
            if not name.lower().endswith(".eer"):
                continue
            path = os.path.join(root, name)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
            except OSError as exc:
                notes.append(f"could not stat {path}: {exc}")
                continue
            timestamps.append(mtime)
    if not timestamps:
        notes.append("no .eer files found")
    return timestamps


def peak_hourly_rate(timestamps: list[datetime]) -> tuple[int, datetime | None]:
    """Bin timestamps into 1-hour buckets (aligned to the top of the hour) and
    return the count and start time of the busiest bucket, to capture the
    fastest sustained rate even when collection is sporadic rather than
    continuous."""
    if not timestamps:
        return 0, None
    bin_counts: Counter[datetime] = Counter()
    for ts in timestamps:
        bin_start = ts.replace(minute=0, second=0, microsecond=0)
        bin_counts[bin_start] += 1
    peak_bin, peak_count = max(bin_counts.items(), key=lambda item: item[1])
    return peak_count, peak_bin


def process_row(row: dict) -> dict:
    collection_id = row.get("collection_id", "")
    data_location = row.get("data_location", "")
    notes: list[str] = []

    out = {
        "collection_id": collection_id,
        "data_location": data_location,
        "type_of_software": "",
        "eer_count": 0,
        "earliest_eer_timestamp": "",
        "latest_eer_timestamp": "",
        "diff_hours": "",
        "eer_per_hour": "",
        "peak_eer_per_hour": "",
        "peak_hour_start": "",
        "notes": "",
    }

    if not data_location:
        notes.append("no data_location given")
        out["notes"] = "; ".join(notes)
        return out

    if not os.path.isdir(data_location):
        notes.append("data_location not reachable")
        out["notes"] = "; ".join(notes)
        return out

    out["type_of_software"] = read_type_of_software(data_location, notes)

    timestamps = scan_eer_files(data_location, notes)
    count = len(timestamps)
    earliest = min(timestamps) if timestamps else None
    latest = max(timestamps) if timestamps else None
    out["eer_count"] = count
    if earliest is not None:
        out["earliest_eer_timestamp"] = earliest.isoformat()
    if latest is not None:
        out["latest_eer_timestamp"] = latest.isoformat()

    if earliest is not None and latest is not None:
        diff_hours = (latest - earliest).total_seconds() / 3600
        out["diff_hours"] = f"{diff_hours:.4f}"
        if diff_hours > 0:
            out["eer_per_hour"] = f"{count / diff_hours:.4f}"
        else:
            notes.append("earliest and latest timestamps identical, rate undefined")

    peak_count, peak_bin = peak_hourly_rate(timestamps)
    if peak_bin is not None:
        out["peak_eer_per_hour"] = str(peak_count)
        out["peak_hour_start"] = peak_bin.isoformat()

    out["notes"] = "; ".join(notes)
    return out


def main():
    parser = argparse.ArgumentParser(
        description="For each row in a collections CSV, read dataset.json's TypeOfSoftware "
                     "field from data_location, count *.eer files, and report the earliest/"
                     "latest file timestamps, their span in hours, the overall average rate/hour, "
                     "and the peak rate/hour from binning file timestamps into 1-hour buckets "
                     "(useful when collection is sporadic rather than continuous)."
    )
    parser.add_argument("input_csv", help="CSV with at least collection_id and data_location columns")
    parser.add_argument("output_csv", help="path to write the resulting report CSV")
    args = parser.parse_args()

    with open(args.input_csv, newline="") as f:
        reader = csv.DictReader(f)
        missing = [field for field in INPUT_FIELDS_NEEDED if field not in (reader.fieldnames or [])]
        if missing:
            parser.error(f"input CSV is missing required column(s): {', '.join(missing)}")
        rows = list(reader)

    results = []
    for row in rows:
        print(f"Processing collection {row.get('collection_id')}: {row.get('data_location')}")
        results.append(process_row(row))

    with open(args.output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nWrote {len(results)} row(s) to {args.output_csv}")


if __name__ == "__main__":
    main()
