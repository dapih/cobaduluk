"""
fingerprint.py - structural fingerprint of a table, from its inspect.json.

Computes a header-AGNOSTIC, pattern-based signature so a new table can be
matched to a previously-promoted family (see design/reuse.md). Reads the output
of inspect_xlsx.py; never touches the raw workbook. Zero AI tokens.

Why pattern-based, not header text: same-family tables can differ in column
count and header wording/language. A spike scored a true same-family pair at
only 0.42 on header-token overlap but 0.81 on the structural cosine below.

Usage:
    python fingerprint.py <inspect.json> [--out PREFIX] [--json]

With --out writes PREFIX.fingerprint.json. Without, prints a human summary
(add --json for machine-readable to stdout).

Importable: load_report, features, vector, fingerprint, cosine.
"""
import argparse
import json
import math
import re
import sys

# Multi-level numbering styles found in detail / list columns.
NUM_PATS = [
    (re.compile(r"^\s*\d+\."), "1."),
    (re.compile(r"^\s*[a-z]\."), "a."),
    (re.compile(r"^\s*\d+\)"), "1)"),
    (re.compile(r"^\s*[a-z]\)"), "a)"),
]


def load_report(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _distinct_int(d):
    return 200 if d == "200+" else int(d)


def features(report):
    """Extract interpretable structural features from an inspect.json report."""
    s = report["sheet"]
    cols = s["columns"]
    max_row = s["dimensions"]["max_row"]
    fills = sorted(c["fill_rate"] for c in cols)

    enum_cols = code_cols = longtext_cols = numbering_cols = 0
    styles = set()
    for c in cols:
        di = _distinct_int(c["distinct"])
        is_str = c["inferred_type"] == "str"
        # Numbering only from STRING columns - avoids decimals like "12.5" in a
        # numeric column being misread as a "1." level (a spike false-positive).
        if is_str:
            tv = [str(x["value"]) for x in c.get("top_values", [])]
            matched = {label for v in tv for p, label in NUM_PATS if p.match(v)}
            if matched:
                numbering_cols += 1
                styles |= matched
        if is_str and 1 < di <= 15 and c["fill_rate"] > 0.1:
            enum_cols += 1
        if c["inferred_type"] == "int" and di > 20:
            code_cols += 1
        if c["max_len"] > 100:
            longtext_cols += 1

    min_fill = fills[0] if fills else 0.0
    rows_per_entry = round(1 / min_fill, 1) if min_fill > 0 else 0.0
    buckets = [0, 0, 0, 0, 0]
    for f in fills:
        i = 0 if f < 0.1 else 1 if f < 0.25 else 2 if f < 0.5 else 3 if f < 0.75 else 4
        buckets[i] += 1
    gaps = s["blank_row_gaps"]["count"]
    return {
        "ncol": len(cols),
        "max_row": max_row,
        "min_fill": min_fill,
        "rows_per_entry": rows_per_entry,
        "num_styles": len(styles),
        "numbering_cols": numbering_cols,
        "enum_cols": enum_cols,
        "code_cols": code_cols,
        "longtext_cols": longtext_cols,
        "merged": s["merged_cells"]["count"],
        "gap_density": round(gaps / max_row, 3) if max_row else 0.0,
        "fill_buckets": buckets,
        "headers": [(c["header"] or "").lower() for c in cols],
    }


def vector(feat):
    """Normalized structural vector used for cosine similarity (header-agnostic)."""
    b = feat["fill_buckets"]
    tot = sum(b) or 1
    denorm = 1.0 if feat["rows_per_entry"] >= 4 else feat["rows_per_entry"] / 4
    return [
        b[0] / tot, b[1] / tot, b[2] / tot, b[3] / tot, b[4] / tot,  # fill-rate shape
        min(feat["num_styles"], 4) / 4,     # multi-level numbering richness
        min(feat["enum_cols"], 4) / 4,      # enum-like columns
        min(feat["code_cols"], 3) / 3,      # code-like columns
        min(feat["longtext_cols"], 5) / 5,  # long-text / list columns
        denorm,                             # denormalized (entry-spanning) table?
        min(feat["gap_density"] * 10, 1.0),  # blank-gap density
    ]


def fingerprint(report):
    feat = features(report)
    return {"features": feat, "vector": vector(feat)}


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def main():
    ap = argparse.ArgumentParser(description="Structural fingerprint of a table from its inspect.json.")
    ap.add_argument("inspect", help="path to a <job>.inspect.json")
    ap.add_argument("--out", help="write PREFIX.fingerprint.json")
    ap.add_argument("--json", action="store_true", dest="as_json", help="machine-readable to stdout")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    try:
        report = load_report(args.inspect)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    fp = fingerprint(report)
    fp["source"] = args.inspect

    if args.out:
        with open(args.out + ".fingerprint.json", "w", encoding="utf-8") as f:
            json.dump(fp, f, ensure_ascii=False, indent=2)
        print(f"Wrote {args.out}.fingerprint.json")
    elif args.as_json:
        print(json.dumps(fp, ensure_ascii=False, indent=2))
    else:
        f = fp["features"]
        print(f"Fingerprint: {args.inspect}")
        print(f"  columns={f['ncol']} rows={f['max_row']} rows/entry={f['rows_per_entry']} "
              f"denormalized={'yes' if f['rows_per_entry'] >= 4 else 'no'}")
        print(f"  numbering_styles={f['num_styles']} enum_cols={f['enum_cols']} "
              f"code_cols={f['code_cols']} longtext_cols={f['longtext_cols']}")
        print(f"  fill_buckets(<.1/.25/.5/.75/1)={f['fill_buckets']} gap_density={f['gap_density']}")
        print(f"  vector={[round(x, 3) for x in fp['vector']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
