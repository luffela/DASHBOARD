#!/usr/bin/env python3
"""
compute_validation_metrics.py
==============================
Compute the metrics the thesis panel asked for in Comment #2, directly from
the raw per-vehicle / per-interval tables:

  --classification raw_vehicles.csv   (Table 1, from roboflow_to_raw_csv.py,
                                        with the "Manual Class" column filled in)
      -> confusion matrix, precision/recall/F1 per class, classification accuracy

  --counting counting_raw.csv         (Table 2, from build_counting_csv.py,
                                        with the "Manual Count" column filled in)
      -> counting accuracy, MAPE, R (coefficient of determination)

Pass either or both flags. A Markdown report is written with -o (default
validation_report.md) that can be pasted into the Word file the panel wants
(validation notes step E).

USAGE
-----
    python compute_validation_metrics.py --classification raw_vehicles.csv
    python compute_validation_metrics.py --counting counting_raw.csv
    python compute_validation_metrics.py \
        --classification raw_vehicles.csv --counting counting_raw.csv \
        -o validation_report.md
"""

import argparse
import csv
import sys
from collections import defaultdict


def read_classification_rows(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"Manual Class", "AI Predicted Class"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            sys.exit(f"--classification CSV is missing columns: {', '.join(sorted(missing))}")
        rows = [r for r in reader if r["Manual Class"].strip()]
    return rows


def classification_metrics(rows):
    classes = sorted({r["Manual Class"].strip() for r in rows} |
                      {r["AI Predicted Class"].strip() for r in rows})

    # confusion[actual][predicted] = count
    confusion = {a: {p: 0 for p in classes} for a in classes}
    for r in rows:
        actual = r["Manual Class"].strip()
        predicted = r["AI Predicted Class"].strip()
        confusion[actual][predicted] += 1

    total = len(rows)
    correct = sum(confusion[c][c] for c in classes)
    accuracy = correct / total if total else 0.0

    per_class = {}
    for c in classes:
        tp = confusion[c][c]
        fp = sum(confusion[a][c] for a in classes if a != c)
        fn = sum(confusion[c][p] for p in classes if p != c)
        precision = tp / (tp + fp) if (tp + fp) else None
        recall = tp / (tp + fn) if (tp + fn) else None
        f1 = (2 * precision * recall / (precision + recall)
              if precision is not None and recall is not None and (precision + recall) else None)
        support = sum(confusion[c].values())
        per_class[c] = {"precision": precision, "recall": recall, "f1": f1, "support": support}

    return {
        "classes": classes,
        "confusion": confusion,
        "per_class": per_class,
        "accuracy": accuracy,
        "total": total,
        "correct": correct,
    }


def read_counting_rows(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"Manual Count", "Automated Count"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            sys.exit(f"--counting CSV is missing columns: {', '.join(sorted(missing))}")
        rows = []
        for r in reader:
            try:
                manual = int(float(r["Manual Count"]))
            except (TypeError, ValueError):
                continue  # unfilled template row, skip
            try:
                automated = int(float(r["Automated Count"]))
            except (TypeError, ValueError):
                continue
            rows.append({**r, "Manual Count": manual, "Automated Count": automated})
    return rows


def counting_metrics(rows):
    n = len(rows)
    if n == 0:
        return None

    manual_vals = [r["Manual Count"] for r in rows]
    automated_vals = [r["Automated Count"] for r in rows]

    abs_diffs = [abs(m - a) for m, a in zip(manual_vals, automated_vals)]
    sum_manual = sum(manual_vals)
    counting_accuracy = 1 - (sum(abs_diffs) / sum_manual) if sum_manual else None

    pct_errors = [abs(m - a) / m for m, a in zip(manual_vals, automated_vals) if m]
    mape = (sum(pct_errors) / len(pct_errors) * 100) if pct_errors else None

    mean_manual = sum_manual / n
    ss_res = sum((m - a) ** 2 for m, a in zip(manual_vals, automated_vals))
    ss_tot = sum((m - mean_manual) ** 2 for m in manual_vals)
    r_squared = (1 - ss_res / ss_tot) if ss_tot else None

    return {
        "n": n,
        "counting_accuracy": counting_accuracy,
        "mape": mape,
        "r_squared": r_squared,
    }


def fmt_pct(x):
    return f"{x * 100:.1f}%" if x is not None else "n/a"


def fmt_num(x, digits=3):
    return f"{x:.{digits}f}" if x is not None else "n/a"


def render_report(cls_result, cnt_result):
    lines = ["# Validation Metrics Report", ""]

    if cls_result:
        lines.append("## Classification validation (Table 1)")
        lines.append("")
        lines.append(f"- Manually verified vehicles: {cls_result['total']}")
        lines.append(f"- Correctly classified: {cls_result['correct']}")
        lines.append(f"- **Classification accuracy: {fmt_pct(cls_result['accuracy'])}**")
        lines.append("")

        classes = cls_result["classes"]
        lines.append("### Confusion matrix (rows = Manual/actual, columns = AI Predicted)")
        lines.append("")
        header = "| Actual \\ Predicted | " + " | ".join(classes) + " |"
        sep = "|---" * (len(classes) + 1) + "|"
        lines.append(header)
        lines.append(sep)
        for a in classes:
            row = [str(cls_result["confusion"][a][p]) for p in classes]
            lines.append(f"| {a} | " + " | ".join(row) + " |")
        lines.append("")

        lines.append("### Precision / Recall / F1 per class")
        lines.append("")
        lines.append("| Class | Support | Precision | Recall | F1 |")
        lines.append("|---|---|---|---|---|")
        for c in classes:
            m = cls_result["per_class"][c]
            lines.append(
                f"| {c} | {m['support']} | {fmt_num(m['precision'])} | "
                f"{fmt_num(m['recall'])} | {fmt_num(m['f1'])} |"
            )
        lines.append("")

    if cnt_result:
        lines.append("## Counting validation (Table 2)")
        lines.append("")
        lines.append(f"- Interval/class rows compared: {cnt_result['n']}")
        lines.append(f"- **Counting accuracy: {fmt_pct(cnt_result['counting_accuracy'])}**")
        lines.append(f"- **MAPE: {fmt_num(cnt_result['mape'], 2)}%**")
        lines.append(f"- **R (coefficient of determination): {fmt_num(cnt_result['r_squared'])}**")
        lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        description="Compute confusion matrix / P-R-F1 / counting accuracy / MAPE / R from raw tables."
    )
    ap.add_argument("--classification", help="Table 1 CSV (roboflow_to_raw_csv.py output, Manual Class filled in)")
    ap.add_argument("--counting", help="Table 2 CSV (build_counting_csv.py output, Manual Count filled in)")
    ap.add_argument("-o", "--output", default="validation_report.md", help="Markdown report output path")
    args = ap.parse_args()

    if not args.classification and not args.counting:
        sys.exit("Provide at least one of --classification or --counting.")

    cls_result = None
    if args.classification:
        rows = read_classification_rows(args.classification)
        if not rows:
            print("  ! No rows with a filled-in 'Manual Class' found; skipping classification metrics.",
                  file=sys.stderr)
        else:
            cls_result = classification_metrics(rows)

    cnt_result = None
    if args.counting:
        rows = read_counting_rows(args.counting)
        if not rows:
            print("  ! No rows with a filled-in 'Manual Count' found; skipping counting metrics.",
                  file=sys.stderr)
        else:
            cnt_result = counting_metrics(rows)

    if not cls_result and not cnt_result:
        sys.exit("Nothing to report -- fill in Manual Class / Manual Count first.")

    report = render_report(cls_result, cnt_result)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\nWrote report -> {args.output}")


if __name__ == "__main__":
    main()
