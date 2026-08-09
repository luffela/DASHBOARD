#!/usr/bin/env python3
"""
roboflow_to_raw_csv.py
======================
Flatten Roboflow detection/tracking JSON output into the RAW, one-row-per-vehicle
CSV that the thesis panel asked for ("ungrouped data / individual vehicle").

WHAT THIS DOES
--------------
Roboflow gives you JSON where each detection looks like:
    { "x":640, "y":359.5, "width":1276, "height":719,
      "confidence":0.982, "class":"06", "class_id":5, "detection_id":"7a..." }
This script reads one or many such JSON files and writes a CSV with one row per
detection (or, with --dedupe-by-tracker, one row per unique tracked vehicle).

It adds the columns you need for the Manual-vs-Automated / ground-truth comparison:
    Manual Class   <- YOU fill this in (what a human says the vehicle is)
    Correct?       <- auto-filled once Manual Class is entered (=IF match)

WHY DEDUPE MATTERS (read this)
------------------------------
If your JSON comes from VIDEO frames, the SAME vehicle appears in many frames and
will produce many detection rows. That is fine for CLASSIFICATION checking, but for
COUNTING you must count each vehicle ONCE. If Roboflow tracking (ByteTrack) is on,
each detection has a tracker_id -> use --dedupe-by-tracker to keep one row per
unique vehicle. Without a tracker_id, raw detections are per-frame, not per-vehicle.

USAGE
-----
Single image/JSON:
    python roboflow_to_raw_csv.py input.json -o raw_vehicles.csv \
        --location "Rizal-Osmena" --date 2026-04-27 --period Morning --interval A

A folder of JSON files (one per frame or per image):
    python roboflow_to_raw_csv.py ./json_folder -o raw_vehicles.csv \
        --location "Rizal-Osmena" --date 2026-04-27 --period Morning --interval A

Keep only confident detections and dedupe tracked vehicles:
    python roboflow_to_raw_csv.py input.json -o raw_vehicles.csv \
        --min-confidence 0.5 --dedupe-by-tracker
"""

import argparse
import csv
import json
import os
import sys

# ---------------------------------------------------------------------------
# FHWA class-code -> full name mapping (from your System Outputs table).
# Roboflow model class names are the two-digit codes "01".."10".
# Edit these names if your labels differ.
# ---------------------------------------------------------------------------
CLASS_MAP = {
    "01": "Motorcycles",
    "02": "Passenger cars",
    "03": "Four tire single unit (light) trucks",
    "04": "Buses",
    "05": "Two axle, six tire single unit trucks",
    "06": "Three axle single unit trucks",
    "07": "Four or more axle single unit trucks",
    "08": "Four or less axle single trailer trucks",
    "09": "Five axle tractor semi-trailers",
    "10": "Six or more axle trailer trucks",
}


def class_name(code):
    """Return the readable class name for a Roboflow class code/label."""
    if code is None:
        return ""
    key = str(code).strip()
    # normalise "6" -> "06" so single-digit labels still map
    if key.isdigit():
        key = key.zfill(2)
    return CLASS_MAP.get(key, str(code))


def iter_predictions(obj, source_name):
    """
    Yield (frame_key, prediction_dict) from any of the shapes Roboflow emits:
      - single image:      {"predictions":[...], "image":{...}}
      - bare list:         [ {...}, {...} ]
      - video per-frame:   [{"frame_offset":..,"time":..,"predictions":[...]}, ...]
                           or {"frames":[...]} / {"predictions":{...frames...}}
    frame_key is a best-effort frame/time label (may be blank).
    """
    # Case 1: dict
    if isinstance(obj, dict):
        # video output that nests frames
        if "frames" in obj and isinstance(obj["frames"], list):
            for fr in obj["frames"]:
                fk = fr.get("frame_offset", fr.get("time", ""))
                for p in fr.get("predictions", []) or []:
                    yield fk, p
            return
        # standard single-image output
        preds = obj.get("predictions")
        if isinstance(preds, list):
            for p in preds:
                yield "", p
            return
        # some SDK video outputs: predictions is a dict keyed by frame
        if isinstance(preds, dict):
            for fk, plist in preds.items():
                for p in plist or []:
                    yield fk, p
            return
        # a single prediction object on its own
        if "class" in obj or "class_id" in obj:
            yield "", obj
            return
    # Case 2: list
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict) and (
                "predictions" in item or "frame_offset" in item or "time" in item
            ):
                fk = item.get("frame_offset", item.get("time", ""))
                for p in item.get("predictions", []) or []:
                    yield fk, p
            elif isinstance(item, dict):
                yield "", item
        return


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def gather_files(input_path):
    """Return a list of JSON files from a file or a directory."""
    if os.path.isdir(input_path):
        files = [
            os.path.join(input_path, fn)
            for fn in sorted(os.listdir(input_path))
            if fn.lower().endswith(".json")
        ]
        if not files:
            sys.exit(f"No .json files found in folder: {input_path}")
        return files
    if os.path.isfile(input_path):
        return [input_path]
    sys.exit(f"Input not found: {input_path}")


def main():
    ap = argparse.ArgumentParser(
        description="Flatten Roboflow JSON into a raw per-vehicle CSV."
    )
    ap.add_argument("input", help="Roboflow JSON file OR a folder of JSON files")
    ap.add_argument("-o", "--output", default="raw_vehicles.csv", help="Output CSV path")
    ap.add_argument("--location", default="", help="Road section / location label")
    ap.add_argument("--date", default="", help="Recording date, e.g. 2026-04-27")
    ap.add_argument("--period", default="", help="Peak period: Morning/Noon/Afternoon")
    ap.add_argument("--interval", default="", help="Interval: A/B/C/D")
    ap.add_argument("--min-confidence", type=float, default=0.0,
                    help="Drop detections below this confidence (0-1)")
    ap.add_argument("--dedupe-by-tracker", action="store_true",
                    help="Keep one row per unique tracker_id (for COUNTING). "
                         "Requires tracking output from Roboflow.")
    args = ap.parse_args()

    files = gather_files(args.input)

    rows = []
    seen_trackers = set()
    dropped_low_conf = 0
    no_tracker_warned = False

    for path in files:
        try:
            data = load_json(path)
        except json.JSONDecodeError as e:
            print(f"  ! Skipping unreadable JSON: {path} ({e})", file=sys.stderr)
            continue

        for frame_key, p in iter_predictions(data, os.path.basename(path)):
            if not isinstance(p, dict):
                continue
            conf = p.get("confidence", "")
            try:
                conf_val = float(conf)
            except (TypeError, ValueError):
                conf_val = None
            if conf_val is not None and conf_val < args.min_confidence:
                dropped_low_conf += 1
                continue

            code = p.get("class", p.get("class_id", ""))
            tracker = p.get("tracker_id", p.get("track_id", ""))

            if args.dedupe_by_tracker:
                if tracker in (None, ""):
                    if not no_tracker_warned:
                        print("  ! --dedupe-by-tracker set but detections have no "
                              "tracker_id; rows are per-frame, not per-vehicle.",
                              file=sys.stderr)
                        no_tracker_warned = True
                else:
                    key = (path if os.path.isfile(args.input) else "", tracker)
                    # dedupe across the whole run by tracker id
                    if tracker in seen_trackers:
                        continue
                    seen_trackers.add(tracker)

            rows.append({
                "Vehicle No.": "",  # filled after sorting
                "Location": args.location,
                "Date": args.date,
                "Peak Period": args.period,
                "Interval": args.interval,
                "Source File": os.path.basename(path),
                "Frame/Time": frame_key,
                "Tracker ID": tracker,
                "AI Class Code": code,
                "AI Predicted Class": class_name(code),
                "Confidence": conf,
                "x": p.get("x", ""),
                "y": p.get("y", ""),
                "width": p.get("width", ""),
                "height": p.get("height", ""),
                "detection_id": p.get("detection_id", ""),
                "Manual Class": "",   # <-- YOU FILL: human ground-truth class
                "Correct?": "",       # <-- auto formula added below
            })

    if not rows:
        sys.exit("No detections found. Check the JSON structure / input path.")

    # Number the vehicles 1..N in order
    for i, r in enumerate(rows, start=1):
        r["Vehicle No."] = i

    fieldnames = [
        "Vehicle No.", "Location", "Date", "Peak Period", "Interval",
        "Source File", "Frame/Time", "Tracker ID",
        "AI Class Code", "AI Predicted Class", "Confidence",
        "x", "y", "width", "height", "detection_id",
        "Manual Class", "Correct?",
    ]

    # Spreadsheet formula for Correct? — compares Manual Class vs AI Predicted Class.
    # Column Q = Manual Class, Column J = AI Predicted Class (given the order above).
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            excel_row = r["Vehicle No."] + 1  # +1 for header row
            # Only produce a result once a Manual Class is typed in.
            r["Correct?"] = (
                f'=IF(Q{excel_row}="","",'
                f'IF(EXACT(TRIM(Q{excel_row}),TRIM(J{excel_row})),'
                f'"CORRECT","WRONG"))'
            )
            w.writerow(r)

    print(f"Wrote {len(rows)} rows -> {args.output}")
    if dropped_low_conf:
        print(f"  ({dropped_low_conf} detections dropped below "
              f"confidence {args.min_confidence})")
    if args.dedupe_by_tracker and seen_trackers:
        print(f"  ({len(seen_trackers)} unique tracked vehicles kept)")
    print("\nNEXT STEPS:")
    print("  1. Open the CSV, fill the 'Manual Class' column with the human count.")
    print("  2. The 'Correct?' column auto-fills (CORRECT/WRONG) in Excel/Sheets.")
    print("  3. Build the confusion matrix from Manual Class vs AI Predicted Class.")


if __name__ == "__main__":
    main()
