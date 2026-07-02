"""
dq_check.py - generic, config-driven data-quality scanner for JSON instances.

Walks a produced JSON document and flags common conversion issues with zero AI
tokens: stray whitespace, broken hyphenation, placeholder values ('-', 'N/A'),
trailing conjunctions, duplicate array items, empty/null inconsistency, and
numeric-looking strings. Checks and parameters come from a rules file; if none
is given it looks for ../skill-rules/dq-checks.default.json next to this
script, then falls back to built-in defaults.

Usage:
    python dq_check.py <instance.json> [--rules rules.json]
        [--max-samples 5] [--out PREFIX] [--json]

Emits a markdown report to stdout, or PREFIX.dq.json / PREFIX.dq.md with --out.
Exit code 0 always (this is a reporting tool, not a validation gate).
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

DEFAULT_RULES = {
    "checks": {
        "whitespace": {"enabled": True, "severity": "warn"},
        "broken_hyphenation": {"enabled": True, "severity": "info"},
        "placeholder_values": {"enabled": True, "severity": "warn",
                               "tokens": ["-", "–", "—", "N/A", "n/a", "null", "NULL"]},
        "trailing_conjunction": {"enabled": True, "severity": "info",
                                 "words": ["dan", "atau", "and", "or"]},
        "duplicate_array_items": {"enabled": True, "severity": "warn"},
        "empty_vs_null": {"enabled": True, "severity": "info"},
        "numeric_string": {"enabled": True, "severity": "info"},
    },
    "max_samples_per_check": 5,
}

WS_BAD = re.compile(r"^\s|\s$|\s{2,}|\t")
HYPHEN = re.compile(r"\w-\s+\w")
NUMERIC = re.compile(r"^\d+([.,]\d+)?$")


def load_rules(path):
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            user = json.load(f)
        merged = json.loads(json.dumps(DEFAULT_RULES))
        merged.update({k: v for k, v in user.items() if k != "checks"})
        for name, cfg in user.get("checks", {}).items():
            merged["checks"].setdefault(name, {}).update(cfg)
        return merged
    here = os.path.dirname(os.path.abspath(__file__))
    fallback = os.path.join(here, "..", "skill-rules", "dq-checks.default.json")
    if os.path.exists(fallback):
        with open(fallback, encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_RULES


def render_md(report):
    L = [f"# Data-quality scan: {report['instance']}", ""]
    if not report["summary"]:
        L.append("No issues found by the configured checks.")
        return "\n".join(L)
    order = {"error": 0, "warn": 1, "info": 2}
    L.append("| Severity | Category | Count |")
    L.append("|---|---|---|")
    for row in sorted(report["summary"], key=lambda r: (order.get(r["severity"], 3), -r["count"])):
        L.append(f"| {row['severity'].upper()} | {row['category']} | {row['count']} |")
    L.append("")
    L.append("## Samples")
    for row in sorted(report["summary"], key=lambda r: (order.get(r["severity"], 3), -r["count"])):
        cat = row["category"]
        L.append(f"\n### {cat} ({row['severity'].upper()}, {row['count']})")
        for s in report["findings"].get(cat, []):
            L.append(f"- `{s['path']}` -> {s['value']}")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Scan a JSON instance for data-quality issues.")
    ap.add_argument("instance")
    ap.add_argument("--rules")
    ap.add_argument("--max-samples", type=int, default=None)
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    rules = load_rules(args.rules)
    checks = rules.get("checks", {})
    max_samples = args.max_samples if args.max_samples is not None else rules.get("max_samples_per_check", 5)

    def on(name):
        return checks.get(name, {}).get("enabled", False)

    with open(args.instance, encoding="utf-8") as f:
        doc = json.load(f)

    findings = defaultdict(list)
    counts = defaultdict(int)
    placeholders = set(checks.get("placeholder_values", {}).get("tokens", []))
    conj = checks.get("trailing_conjunction", {}).get("words", [])
    conj_re = re.compile(r"\s+(?:%s)\s*$" % "|".join(re.escape(w) for w in conj), re.IGNORECASE) if conj else None
    saw = {"empty": False, "null": False}

    def record(cat, path, value):
        counts[cat] += 1
        if len(findings[cat]) < max_samples:
            findings[cat].append({"path": path, "value": value[:120] if isinstance(value, str) else value})

    def on_scalar(path, v):
        if v is None:
            saw["null"] = True
            return
        if not isinstance(v, str):
            return
        if v == "":
            saw["empty"] = True
        if on("whitespace") and v and WS_BAD.search(v):
            record("whitespace", path, v)
        if on("broken_hyphenation") and HYPHEN.search(v):
            record("broken_hyphenation", path, v)
        if on("placeholder_values") and v.strip() in placeholders:
            record("placeholder_values", path, v)
        if on("trailing_conjunction") and conj_re and conj_re.search(v):
            record("trailing_conjunction", path, v)
        if on("numeric_string") and NUMERIC.match(v.strip()):
            record("numeric_string", path, v)

    def on_array(path, arr):
        if not on("duplicate_array_items"):
            return
        seen = set()
        for i, item in enumerate(arr):
            key = json.dumps(item, sort_keys=True, ensure_ascii=False) if isinstance(item, (dict, list)) else item
            if key in seen:
                record("duplicate_array_items", f"{path}/{i}",
                       item if not isinstance(item, (dict, list)) else "(complex item)")
            else:
                seen.add(key)

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}/{k}")
        elif isinstance(node, list):
            on_array(path, node)
            for i, v in enumerate(node):
                walk(v, f"{path}/{i}")
        else:
            on_scalar(path, node)

    walk(doc, "")

    if on("empty_vs_null") and saw["empty"] and saw["null"]:
        counts["empty_vs_null"] = 1
        findings["empty_vs_null"].append(
            {"path": "(global)", "value": 'both "" and null occur; standardize on one'})

    sev = {name: cfg.get("severity", "info") for name, cfg in checks.items()}
    report = {
        "instance": args.instance,
        "summary": [
            {"category": cat, "severity": sev.get(cat, "info"), "count": counts[cat]}
            for cat in sorted(counts, key=lambda c: counts[c], reverse=True)
        ],
        "findings": dict(findings),
    }

    md = render_md(report)
    if args.out:
        with open(args.out + ".dq.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        with open(args.out + ".dq.md", "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Wrote {args.out}.dq.json / .dq.md")
    elif args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
