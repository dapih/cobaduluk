"""
match_profile.py - match a table to previously-promoted families.

Given a job's inspect.json, computes its structural fingerprint and scores it
(cosine) against each family in the families/ store, printing a compact,
token-frugal match report with a reuse-tier verdict per design/reuse.md.
Advisory only: it never reuses anything - the orchestrator asks first.
Zero AI tokens.

Usage:
    python match_profile.py <job.inspect.json> [--families DIR] [--top N] [--json]

Exit: 0 = ran (read the report for the verdict), 2 = usage / IO error.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fingerprint import load_report, fingerprint, cosine  # noqa: E402

# Provisional thresholds (design/reuse.md) - recalibrate as the corpus grows.
NEAR_DUP = 0.95     # clone schema + parser wholesale, re-pointing columns
SAME_FAMILY = 0.65  # warm-start from the family canonical, then adapt


def tier(score):
    if score >= NEAR_DUP:
        return "near-duplicate"
    if score >= SAME_FAMILY:
        return "same-family"
    return "unrelated"


def load_families(families_dir):
    out = []
    if not os.path.isdir(families_dir):
        return out
    for name in sorted(os.listdir(families_dir)):
        fpath = os.path.join(families_dir, name, "family.json")
        if os.path.isfile(fpath):
            try:
                with open(fpath, encoding="utf-8") as f:
                    fam = json.load(f)
                fam["_dir"] = os.path.join(families_dir, name)
                out.append(fam)
            except (OSError, json.JSONDecodeError):
                pass
    return out


def main():
    ap = argparse.ArgumentParser(description="Match a table to promoted families by structural fingerprint.")
    ap.add_argument("inspect", help="path to the job's <job>.inspect.json")
    ap.add_argument("--families", default="families", help="families store dir (default: families)")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--json", action="store_true", dest="as_json")
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
    families = load_families(args.families)

    scored = []
    for fam in families:
        vec = fam.get("fingerprint", {}).get("vector")
        if vec:
            scored.append((cosine(fp["vector"], vec), fam))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: args.top]
    best = top[0] if top else None

    result = {
        "instance": args.inspect,
        "families_dir": args.families,
        "verdict": tier(best[0]) if best else "no-families",
        "best": ({"name": best[1]["name"], "score": round(best[0], 3), "tier": tier(best[0])}
                 if best else None),
        "matches": [
            {
                "name": fam["name"],
                "score": round(score, 3),
                "tier": tier(score),
                "members": len(fam.get("members", [])),
                "canonical_schema": os.path.join(
                    fam["_dir"], fam.get("canonical_schema", "family.schema.json")).replace("\\", "/"),
            }
            for score, fam in top
        ],
    }

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"Instance: {args.inspect}")
    if not families:
        print(f"No families found in '{args.families}/'. Promote a clean job first "
              "(/excel-to-json:promote <job-id>).")
        return 0
    print(f"Verdict: {result['verdict']}"
          + (f"  (best: {result['best']['name']} = {result['best']['score']:.2f})" if best else ""))
    print("Matches (by structural cosine):")
    for m in result["matches"]:
        print(f"  {m['score']:.2f}  [{m['tier']:<14}] {m['name']}  "
              f"({m['members']} member(s))  -> {m['canonical_schema']}")
    if best and result["best"]["tier"] == "near-duplicate":
        print("\nSuggestion: near-duplicate - offer to clone this family's schema + parser, "
              "re-pointing columns. ALWAYS confirm with the user first.")
    elif best and result["best"]["tier"] == "same-family":
        print("\nSuggestion: same family - offer to warm-start from this family's canonical "
              "schema, then adapt. ALWAYS confirm with the user first.")
    else:
        print("\nNo strong match - proceed with the normal from-scratch flow.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
