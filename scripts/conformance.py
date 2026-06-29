"""
conformance.py - how does a new table differ from a family's CANONICAL?

Deterministic structural diff that informs the medium-tier "evolve-or-keep"
decision (design/reuse.md): given a new job's inspect.json (and optionally its
drafted schema), report header deltas, structural-feature deltas, and - with
--job-schema - schema field/$def deltas against the family canonical. Compares
against the canonical member specifically (family.canonical_source), not a blend
of members. Advisory only; it decides nothing. Zero AI tokens.

Usage:
    python conformance.py <job.inspect.json> --name <family>
        [--families families] [--docs docs] [--job-schema PATH] [--json]

Exit: 0 = ran, 2 = usage / IO error.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fingerprint import load_report, features, vector, fingerprint, cosine  # noqa: E402

NEAR_DUP, SAME_FAMILY = 0.95, 0.65
NUM_KEYS = ["ncol", "rows_per_entry", "num_styles", "enum_cols",
            "code_cols", "longtext_cols", "gap_density"]


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def canonical_fingerprint(fam, docs_dir):
    """Fingerprint of the canonical member (family.canonical_source), backfilled
    from its inspect.json if not stored. Falls back to the first member."""
    members = fam.get("members", [])
    cs = fam.get("canonical_source")
    chosen = next((m for m in members if m.get("job_id") == cs), members[0] if members else None)
    if chosen is None:
        return None
    fp = chosen.get("fingerprint")
    if not fp:
        insp = os.path.join(docs_dir, chosen["job_id"], chosen["job_id"] + ".inspect.json")
        if os.path.isfile(insp):
            fp = fingerprint(load_report(insp))
    return fp


def schema_fields(schema):
    """(set of $def names, set of all property names) anywhere in the schema."""
    defs = set(schema.get("$defs", {}).keys())
    props = set()

    def walk(n):
        if isinstance(n, dict):
            p = n.get("properties")
            if isinstance(p, dict):
                props.update(p.keys())
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(schema)
    return defs, props


def main():
    ap = argparse.ArgumentParser(description="Diff a new table against a family canonical.")
    ap.add_argument("inspect")
    ap.add_argument("--name", required=True)
    ap.add_argument("--families", default="families")
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--job-schema", dest="job_schema")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    fam_dir = os.path.join(args.families, args.name)
    fam_json = os.path.join(fam_dir, "family.json")
    if not os.path.isfile(fam_json):
        print(f"ERROR: family '{args.name}' not found at {fam_json}", file=sys.stderr)
        return 2
    try:
        feat = features(load_report(args.inspect))
        fam = load_json(fam_json)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    canon = canonical_fingerprint(fam, args.docs) or {}
    cfeat = canon.get("features", {})
    cos = round(cosine(vector(feat), canon["vector"]), 3) if canon.get("vector") else None

    canon_headers = {h for h in cfeat.get("headers", []) if h}
    new_headers = {h for h in feat.get("headers", []) if h}
    matched = sorted(new_headers & canon_headers)
    new_only = sorted(new_headers - canon_headers)
    missing = sorted(canon_headers - new_headers)

    feat_delta = {k: {"table": feat.get(k), "canonical": cfeat.get(k),
                      "delta": round((feat.get(k, 0) or 0) - (cfeat.get(k, 0) or 0), 2)}
                  for k in NUM_KEYS}

    schema_delta = None
    if args.job_schema:
        try:
            jd, jp = schema_fields(load_json(args.job_schema))
            cd, cp = schema_fields(load_json(os.path.join(fam_dir, fam.get("canonical_schema", "family.schema.json"))))
            schema_delta = {
                "shared_defs": sorted(jd & cd), "new_defs": sorted(jd - cd), "missing_defs": sorted(cd - jd),
                "shared_fields": sorted(jp & cp), "new_fields": sorted(jp - cp), "missing_fields": sorted(cp - jp),
            }
        except (OSError, json.JSONDecodeError) as e:
            print(f"WARNING: could not diff job schema: {e}", file=sys.stderr)

    if cos is not None and cos >= NEAR_DUP and not new_only and len(missing) <= 1:
        verdict = "conforms"
        advice = "Within the family canonical - reuse as-is (keep)."
    elif cos is not None and cos >= SAME_FAMILY:
        verdict = "same-family-with-delta"
        advice = ("Same family but structurally different - reuse the canonical idioms, then decide "
                  "EVOLVE (fold the new structure into the canonical, bump version) vs KEEP "
                  "(handle the delta in this job only).")
    else:
        verdict = "divergent"
        advice = "Weak structural match - treat as a new table / a different family."

    result = {
        "instance": args.inspect, "family": args.name,
        "canonical_version": fam.get("canonical_version", 1),
        "canonical_source": fam.get("canonical_source"),
        "structural_cosine": cos, "verdict": verdict,
        "headers": {"matched": matched, "new_in_table": new_only, "missing_from_table": missing},
        "feature_delta": feat_delta, "schema_delta": schema_delta, "advice": advice,
    }

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"Conformance: {args.inspect}")
    print(f"  vs family '{args.name}' canonical v{result['canonical_version']} "
          f"(source: {result['canonical_source']}; {len(fam.get('members', []))} member(s))")
    print(f"  structural cosine to canonical: {cos}   verdict: {verdict}")
    print(f"  headers: {len(matched)} matched, {len(new_only)} new, {len(missing)} missing")
    if new_only:
        print(f"    new in table:       {', '.join(new_only)}")
    if missing:
        print(f"    missing from table: {', '.join(missing)}")
    print("  feature deltas (table vs canonical):")
    for k in NUM_KEYS:
        d = feat_delta[k]
        flag = "" if d["delta"] == 0 else "   <-- differs"
        print(f"    {k:<16} {str(d['table']):>8} vs {str(d['canonical']):>8}  (delta {d['delta']:+}){flag}")
    if schema_delta:
        print("  schema vs canonical:")
        print(f"    shared $defs:   {', '.join(schema_delta['shared_defs']) or '-'}")
        print(f"    new $defs:      {', '.join(schema_delta['new_defs']) or '-'}")
        print(f"    missing $defs:  {', '.join(schema_delta['missing_defs']) or '-'}")
        print(f"    new fields:     {', '.join(schema_delta['new_fields']) or '-'}")
        print(f"    missing fields: {', '.join(schema_delta['missing_fields']) or '-'}")
    print(f"  -> {advice}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
