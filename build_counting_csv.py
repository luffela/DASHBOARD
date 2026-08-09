#!/usr/bin/env python3
"""
build_counting_csv.py
======================
Build Table 2 ("Counting raw data") from the Table 1 classification CSV
produced by roboflow_to_raw_csv.py -- the per-interval, per-class Manual
Count vs Automated Count table the thesis panel asked for.

INPUT
-----
A Table 1 CSV (ideally generated with --dedupe-by-tracker so each row is one
unique vehicle, not one detection per frame). This script tallies rows by
(Location, Date, Peak Period, Interval, AI Predicted Class) to get the
Automated Count.

Manual Count (the human tally) is NOT in the Table 1 CSV, since nobody counts
by hand off the AI's own detections. Provide it one of two ways:

  1. --manual-counts a CSV with columns:
       Location, Date, Peak Period, Interval, Vehicle Class, Manual Count
     This is merged in and Difference / % Error are computed directly.

  2. Omit --manual-counts: the output CSV is a template with a blank
     "Manual Count" column and spreadsheet formulas for Difference / % Error,
     ready to fill in by hand in Excel/Sheets (same pattern as Table 1's
     "Correct?" column).

USAGE
-----
    python build_counting_csv.py raw_vehicles.csv -o counting_raw.csv
    python build_counting_csv.py raw_vehicles.csv -o counting_raw.csv \
        --manual-counts manual_tally.csv
"""

import argparse
import csv
import sys
from collections import defaultdict


def load_automated_counts(path):
    """Tally Table 1 rows into {(Location, Date, Period, Interval, Class): count}."""
    counts = defaultdict(int)
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"Location", "Date", "Peak Period", "Interval", "AI Predicted Class"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            sys.exit(f"Input CSV is missing columns: {', '.join(sorted(missing))}")
        for row in reader:
            key = (
                row["Location"],
                row["Date"],
                row["Peak Period"],
                row["Interval"],
                row["AI Predicted Class"],
            )
            counts[key] += 1
    return counts


def load_manual_counts(path):
    """Read a manual tally CSV into {(Location, Date, Period, Interval, Class): count}."""
    counts = {}
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"Location", "Date", "Peak Period", "Interval", "Vehicle Class", "Manual Count"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            sys.exit(f"--manual-counts CSV is missing columns: {', '.join(sorted(missing))}")
        for row in reader:
            key = (
                row["Location"],
                row["Date"],
                row["Peak Period"],
                row["Interval"],
                row["Vehicle Class"],
            )
            try:
                counts[key] = int(row["Manual Count"])
            except (TypeError, ValueError):
                continue
    return counts


def main():
    ap = argparse.ArgumentParser(
        description="Build the per-interval counting raw CSV (Table 2) from a Table 1 CSV."
    )
    ap.add_argument("input", help="Table 1 CSV from roboflow_to_raw_csv.py")
    ap.add_argument("-o", "--output", default="counting_raw.csv", help="Output CSV path")
    ap.add_argument("--manual-counts", help="Optional manual tally CSV to merge in")
    args = ap.parse_args()

    automated = load_automated_counts(args.input)
    manual = load_manual_counts(args.manual_counts) if args.manual_counts else {}

    keys = sorted(set(automated) | set(manual))
    if not keys:
        sys.exit("No rows found in the input CSV.")

    fieldnames = [
        "Location", "Date", "Peak Period", "Interval", "Vehicle Class",
        "Manual Count", "Automated Count", "Difference", "% Error",
    ]

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for i, key in enumerate(keys, start=1):
            location, date, period, interval, vclass = key
            auto_count = automated.get(key, 0)
            excel_row = i + 1  # +1 for header row

            if args.manual_counts:
                manual_count = manual.get(key, 0)
                diff = auto_count - manual_count
                pct_error = (abs(diff) / manual_count * 100) if manual_count else ""
                w.writerow({
                    "Location": location,
                    "Date": date,
                    "Peak Period": period,
                    "Interval": interval,
                    "Vehicle Class": vclass,
                    "Manual Count": manual_count,
                    "Automated Count": auto_count,
                    "Difference": diff,
                    "% Error": f"{pct_error:.2f}" if pct_error != "" else "",
                })
            else:
                # Template mode: leave Manual Count blank, add formulas.
                # Column F = Manual Count, Column G = Automated Count.
                w.writerow({
                    "Location": location,
                    "Date": date,
                    "Peak Period": period,
                    "Interval": interval,
                    "Vehicle Class": vclass,
                    "Manual Count": "",
                    "Automated Count": auto_count,
                    "Difference": f'=IF(F{excel_row}="","",G{excel_row}-F{excel_row})',
                    "% Error": f'=IF(F{excel_row}="","",ABS(G{excel_row}-F{excel_row})/F{excel_row}*100)',
                })

    print(f"Wrote {len(keys)} interval/class rows -> {args.output}")
    if not args.manual_counts:
        print("\nNEXT STEPS:")
        print("  1. Open the CSV, fill the 'Manual Count' column with the human tally.")
        print("  2. Difference and % Error auto-fill in Excel/Sheets.")
        print("  3. Feed this file into compute_validation_metrics.py --counting")


if __name__ == "__main__":
    main()
