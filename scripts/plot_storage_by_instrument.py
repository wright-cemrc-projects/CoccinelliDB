from __future__ import annotations
import argparse
import csv
import os
import sys
import subprocess
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BAR_COLOR = "#2a78d6"       # palette: sequential hue, single-series bar
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

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

def get_ceph_rbytes(path):
    """
    Returns ceph.dir.rbytes as an integer for the given path.
    """
    try:
        output = subprocess.check_output(
            ["getfattr", "-d", "-n", "ceph.dir.rbytes", path],
            stderr=subprocess.STDOUT,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"getfattr failed: {e.output}")

    # Output example:
    # # file: folder/
    # ceph.dir.rbytes="7033913062661"

    for line in output.splitlines():
        if line.startswith("ceph.dir.rbytes="):
            value = line.split("=", 1)[1].strip().strip('"')
            print(path, " ", str(value))
            return int(value)

    raise ValueError("ceph.dir.rbytes not found in output")

def rescan_rows(rows: list[dict]) -> list[dict]:
    """Re-walk each row's data_location to refresh disk_bytes/disk_reachable in place."""
    for row in rows:
        data_location = row.get("data_location")
        if not data_location:
            row["disk_bytes"] = ""
            row["disk_reachable"] = False
            continue

        if os.path.isdir(data_location):
            print(f"Scanning {data_location} ...")
            row["disk_bytes"] = get_ceph_rbytes(data_location)
            row["disk_reachable"] = True
        else:
            print(f"  Not reachable from this host: {data_location}", file=sys.stderr)
            row["disk_bytes"] = ""
            row["disk_reachable"] = False
    return rows


def aggregate_by_instrument(rows: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    for row in rows:
        disk_bytes = row.get("disk_bytes")
        if disk_bytes in (None, ""):
            continue
        instrument = row.get("instrument_name") or "Unknown"
        totals[instrument] += int(disk_bytes)
    return totals


def best_unit(max_bytes: int) -> tuple[str, float]:
    """Pick one unit for the whole axis so ticks share a scale."""
    units = [("B", 1), ("KB", 1024), ("MB", 1024**2), ("GB", 1024**3), ("TB", 1024**4), ("PB", 1024**5)]
    label, divisor = units[0]
    for label, divisor in units:
        if max_bytes < divisor * 1024 or divisor == units[-1][1]:
            break
    return label, divisor


def plot_totals(totals: dict[str, int], output: str, subtitle: str = "") -> None:
    if not totals:
        print("No instruments with scannable storage — nothing to plot.")
        return

    items = sorted(totals.items(), key=lambda kv: kv[1])  # ascending so largest bar ends up on top
    names = [name for name, _ in items]
    sizes = [size for _, size in items]

    unit_label, divisor = best_unit(max(sizes))
    scaled = [s / divisor for s in sizes]

    fig_height = max(2.5, 0.5 * len(names) + 1)
    fig, ax = plt.subplots(figsize=(9, fig_height), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    bars = ax.barh(names, scaled, height=0.6, color=BAR_COLOR, zorder=3)

    ax.set_xlabel(f"Storage ({unit_label})", color=INK_MUTED, fontsize=10)
    title = "Storage used per instrument"
    if subtitle:
        ax.set_title(f"{title}\n{subtitle}", color=INK_PRIMARY, fontsize=13, loc="left", pad=12)
    else:
        ax.set_title(title, color=INK_PRIMARY, fontsize=13, loc="left", pad=12)

    ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=6))
    ax.grid(axis="x", color=GRIDLINE, linewidth=1, zorder=0)
    ax.set_axisbelow(True)

    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)

    ax.tick_params(axis="y", colors=INK_PRIMARY, length=0)
    ax.tick_params(axis="x", colors=INK_MUTED, length=0)

    max_scaled = max(scaled) if scaled else 0
    for bar, raw_bytes in zip(bars, sizes):
        width = bar.get_width()
        ax.text(
            width + max_scaled * 0.02,
            bar.get_y() + bar.get_height() / 2,
            human_readable(raw_bytes),
            va="center",
            ha="left",
            color=INK_PRIMARY,
            fontsize=9,
        )

    ax.set_xlim(0, max_scaled * 1.18 if max_scaled else 1)
    fig.tight_layout()
    fig.savefig(output, dpi=150, facecolor=SURFACE)
    print(f"Wrote chart to {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Read a collection-report CSV (columns: instrument_name, data_location, "
                     "start_date, end_date, ...), re-scan each data_location folder on disk for "
                     "its current size, and plot total storage per instrument as a bar chart."
    )
    parser.add_argument("input_csv", help="CSV with instrument_name/data_location columns, e.g. from weekly_collection_report.py")
    parser.add_argument("--output", default="storage_by_instrument.png",
                         help="path to write the chart; format is inferred from the extension "
                              "(.png, .pdf, .svg, ...)")
    parser.add_argument("--updated-csv", default=None,
                         help="write the CSV back out with refreshed disk_bytes/disk_reachable columns "
                              "(default: <input_csv>_updated.csv; pass --in-place to overwrite input_csv instead)")
    parser.add_argument("--in-place", action="store_true", help="overwrite input_csv instead of writing a new file")
    parser.add_argument("--no-update-csv", action="store_true",
                         help="skip writing an updated CSV; only re-scan in memory for the plot")
    args = parser.parse_args()

    with open(args.input_csv, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    rescan_rows(rows)

    if not args.no_update_csv:
        if args.in_place:
            updated_path = args.input_csv
        elif args.updated_csv:
            updated_path = args.updated_csv
        else:
            root, ext = os.path.splitext(args.input_csv)
            updated_path = f"{root}_updated{ext or '.csv'}"
        with open(updated_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote refreshed sizes to {updated_path}")

    totals = aggregate_by_instrument(rows)

    dates = [r["start_date"] for r in rows if r.get("start_date")] + [r["end_date"] for r in rows if r.get("end_date")]
    subtitle = f"{min(dates)[:10]} to {max(dates)[:10]}" if dates else ""

    plot_totals(totals, args.output, subtitle=subtitle)


if __name__ == "__main__":
    main()
