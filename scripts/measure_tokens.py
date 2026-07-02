"""
measure_tokens.py — approximate token counts for every artifact that enters the
model's context window in a completed excel-to-json job.

Usage:
    python scripts/measure_tokens.py <job-id>  [--families DIR] [--out PATH]

Approximation: 1 token ≈ 4 UTF-8 characters (GPT/Claude tokeniser rule of thumb).
Actual counts will differ ±20 % depending on content; this gives the right order of
magnitude for design decisions.

The script measures three buckets per step:
  IN  — files the model reads (input tokens, amortised per step)
  OUT — files the model writes (output tokens, amortised per step)
  ZERO — deterministic script work, 0 model tokens

Iteration multiplier for step 5: looks at the number of validation error cycles
by counting "fix" or "iteration" references in log-<job>.md; falls back to 2.
"""

import argparse
import json
import os
import re
import sys

CHARS_PER_TOKEN = 4


def chars(path: str) -> int:
    """Return character count of a file, or 0 if missing."""
    if not os.path.isfile(path):
        return 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        return len(fh.read())


def tokens(path: str) -> int:
    return chars(path) // CHARS_PER_TOKEN


def token_of(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def guess_iterations(log_path: str) -> int:
    """Count validation-fix cycles from the log."""
    if not os.path.isfile(log_path):
        return 2
    with open(log_path, encoding="utf-8", errors="replace") as fh:
        content = fh.read()
    hits = len(re.findall(r"(?i)(fix iteration|validation error|re-run|iteration \d+)", content))
    return max(2, min(hits, 10))


def learnings_slice(learnings_path: str, tags: list[str]) -> int:
    """Estimate tokens for a tag-filtered learnings slice."""
    if not os.path.isfile(learnings_path):
        return 0
    with open(learnings_path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    result, capture = [], False
    for line in lines:
        if line.startswith("## ["):
            capture = any(f"[{t}]" in line or f"[{t} " in line for t in tags)
        if capture:
            result.append(line)
    return len("".join(result)) // CHARS_PER_TOKEN


def main() -> None:
    ap = argparse.ArgumentParser(description="Estimate model token budget for a completed job.")
    ap.add_argument("job", help="job id, e.g. table-20260628-1")
    ap.add_argument("--families", default="families", help="families store directory")
    ap.add_argument("--out", default=None, help="write markdown report to this path")
    args = ap.parse_args()

    job = args.job

    # Resolve paths
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    job_dir = os.path.join(root, "docs", job)
    plugin = root  # plugin root is the repo root in dev

    refs = os.path.join(plugin, "skills", "excel-to-json", "references")
    mem = os.path.join(plugin, "memory", "learnings.md")
    families_dir = os.path.join(root, args.families)

    j = lambda *parts: os.path.join(job_dir, *parts)
    r = lambda name: os.path.join(refs, name)

    # --- Shared reference files (read once per agent invocation) ---------------
    ref = {
        "parsing_patterns":    tokens(r("parsing-patterns.md")),
        "schema_design":       tokens(r("schema-design.md")),
        "normalization_rules": tokens(r("normalization-rules.md")),
        "dq_checks":           tokens(r("data-quality-checks.md")),
        "job_conventions":     tokens(r("job-conventions.md")),
        "skill_md":            tokens(os.path.join(plugin, "skills", "excel-to-json", "SKILL.md")),
    }

    # --- Per-job artifacts -------------------------------------------------------
    art = {
        "inspect_md":   tokens(j(f"{job}.inspect.md")),
        "inspect_json":  tokens(j(f"{job}.inspect.json")),
        "schema":        tokens(j(f"{job}.schema.json")),
        "parser":        tokens(j(f"{job}.parser.py")),
        "instance_json": tokens(j(f"{job}.json")),
        "dq_md":         tokens(j(f"{job}.dq.md")),
        "dq_json":       tokens(j(f"{job}.dq.json")),
        "log":           tokens(j(f"log-{job}.md")),
        "summary":       tokens(j(f"summary-{job}.md")),
        "dq_report":     tokens(j(f"data-quality-{job}.md")),
    }

    # --- Learnings slices (tag-filtered) ----------------------------------------
    learn = {
        "structure_tooling":            learnings_slice(mem, ["structure", "tooling"]),
        "schema_structure_tooling":     learnings_slice(mem, ["schema", "structure", "tooling"]),
        "normalization_structure_tooling": learnings_slice(mem, ["normalization", "structure", "tooling"]),
        "dq_tooling":                   learnings_slice(mem, ["dq", "tooling"]),
    }

    # --- Family canonical (if any) ----------------------------------------------
    family_schema_tokens = 0
    family_match = False
    if os.path.isdir(families_dir):
        for fam in os.listdir(families_dir):
            fschema = os.path.join(families_dir, fam, "family.schema.json")
            if os.path.isfile(fschema):
                family_schema_tokens = max(family_schema_tokens, tokens(fschema))
                family_match = True

    iterations = guess_iterations(j(f"log-{job}.md"))

    # --- Per-step budget --------------------------------------------------------
    # (IN = tokens the model reads, OUT = tokens the model writes)
    steps: list[dict] = [
        {
            "step": "1 — Prepare",
            "role": "orchestrator",
            "note": "shell ops + fill log template",
            "zero_token": True,
            "in": 0,
            "out": 0,
        },
        {
            "step": "2 — Inspect",
            "role": "inspect_xlsx.py",
            "note": "full workbook → compact capped report",
            "zero_token": True,
            "in": 0,
            "out": 0,
        },
        {
            "step": "2c — Match",
            "role": "match_profile.py",
            "note": "cosine vs stored family vectors",
            "zero_token": True,
            "in": 0,
            "out": 0,
        },
        {
            "step": "2b — Pick sheet",
            "role": "orchestrator",
            "note": "only if multi-sheet; skipped for single-sheet files",
            "zero_token": False,
            "in": art["inspect_md"],
            "out": 100,
            "conditional": "multi-sheet only",
        },
        {
            "step": "3 — Structure-analyst",
            "role": "structure-analyst agent",
            "note": f"inspect.md + parsing-patterns + learnings; outputs mapping in log",
            "zero_token": False,
            "in":  (ref["skill_md"] + art["inspect_md"] + ref["parsing_patterns"]
                    + learn["structure_tooling"] + art["log"] // 4),
            "out": art["log"] // 2,  # mapping section of log
        },
        {
            "step": "4 — Schema-designer",
            "role": "schema-designer agent",
            "note": "schema-design + log + learnings [+ family canonical]",
            "zero_token": False,
            "in":  (ref["skill_md"] + ref["schema_design"] + art["log"] // 2
                    + learn["schema_structure_tooling"]
                    + (family_schema_tokens if family_match else 0)),
            "out": art["schema"],
        },
        {
            "step": "4b — Conformance read",
            "role": "schema-designer agent",
            "note": "conformance report → evolve-or-keep call (family match only)",
            "zero_token": False,
            "in": family_schema_tokens // 2 if family_match else 0,
            "out": 200 if family_match else 0,
            "conditional": "family match only",
        },
        {
            "step": "5 — Parser-builder",
            "role": "parser-builder agent",
            "note": f"write + iterate ({iterations}x validation cycles detected in log)",
            "zero_token": False,
            # Base read: skill + normalization + log + schema + learnings
            # + iterations × (parser read-back + error output + fix)
            "in":  (ref["skill_md"] + ref["normalization_rules"] + art["log"]
                    + art["schema"] + learn["normalization_structure_tooling"]
                    + iterations * (art["parser"] + 500)),   # 500 = approx error dump
            "out": art["parser"] * iterations,
        },
        {
            "step": "5 (parser runs)",
            "role": "generated parser.py",
            "note": "processes every source row — no model involvement",
            "zero_token": True,
            "in": 0,
            "out": 0,
        },
        {
            "step": "6 — Validate",
            "role": "validate_json.py",
            "note": "jsonschema validation — zero tokens; orchestrator reads pass/fail only",
            "zero_token": True,
            "in": 0,
            "out": 0,
        },
        {
            "step": "6 read",
            "role": "orchestrator",
            "note": "reads validation result (1–3 lines)",
            "zero_token": False,
            "in": 100,
            "out": 50,
        },
        {
            "step": "7 — DQ scan",
            "role": "dq_check.py",
            "note": "full instance scan — zero tokens",
            "zero_token": True,
            "in": 0,
            "out": 0,
        },
        {
            "step": "7 — DQ-reviewer",
            "role": "dq-reviewer agent",
            "note": "dq.md + dq-checks reference + inspect samples + learnings",
            "zero_token": False,
            "in":  (ref["skill_md"] + art["dq_md"] + ref["dq_checks"]
                    + art["inspect_md"] // 3 + learn["dq_tooling"]),
            "out": art["dq_report"],
        },
        {
            "step": "8 — Summary",
            "role": "orchestrator",
            "note": "full log + summary template → summary.md",
            "zero_token": False,
            "in":  art["log"] + 500,
            "out": art["summary"],
        },
        {
            "step": "9 — Learnings (lint)",
            "role": "learnings.py --lint",
            "note": "regex + Jaccard on proposed entry — zero tokens",
            "zero_token": True,
            "in": 0,
            "out": 0,
        },
        {
            "step": "9 — Learnings (model)",
            "role": "orchestrator",
            "note": "generalize → confirm → append (0–3 entries; 0 if no new insight)",
            "zero_token": False,
            "in":  art["log"] // 4 + token_of(open(mem, encoding="utf-8").read() if os.path.isfile(mem) else ""),
            "out": 400,  # ~2 entries × ~200 tokens each
        },
    ]

    # --- Totals -----------------------------------------------------------------
    model_in  = sum(s["in"]  for s in steps if not s.get("zero_token"))
    model_out = sum(s["out"] for s in steps if not s.get("zero_token"))
    model_total = model_in + model_out
    zero_steps  = [s["step"] for s in steps if s.get("zero_token")]

    # --- Report -----------------------------------------------------------------
    lines = [
        f"# Token budget -- {job}",
        "",
        "Approximation: 1 token ~= 4 chars.  Actual values differ +/-20%.",
        f"Parser-builder iterations detected in log: **{iterations}**",
        "",
        "## Per-step breakdown",
        "",
        "| Step | Role | IN (tokens) | OUT (tokens) | Total | Notes |",
        "|---|---|---:|---:|---:|---|",
    ]
    for s in steps:
        if s.get("zero_token"):
            lines.append(f"| {s['step']} | {s['role']} | 0 | 0 | **0** | zero-token ⚙️ |")
        else:
            tot = s["in"] + s["out"]
            note = s.get("note", "")
            cond = f" _{s['conditional']}_" if "conditional" in s else ""
            lines.append(
                f"| {s['step']} | {s['role']} | {s['in']:,} | {s['out']:,} | {tot:,} |"
                f" {note}{cond} |"
            )

    lines += [
        "",
        "## Reference file sizes",
        "",
        "| File | chars | ~tokens |",
        "|---|---:|---:|",
    ]
    ref_map = {
        "parsing-patterns.md":    ref["parsing_patterns"],
        "schema-design.md":       ref["schema_design"],
        "normalization-rules.md": ref["normalization_rules"],
        "data-quality-checks.md": ref["dq_checks"],
        "SKILL.md":               ref["skill_md"],
    }
    for name, tok in ref_map.items():
        lines.append(f"| {name} | {tok * CHARS_PER_TOKEN:,} | {tok:,} |")

    lines += [
        "",
        "## Per-job artifact sizes",
        "",
        "| Artifact | chars | ~tokens |",
        "|---|---:|---:|",
    ]
    art_names = {
        "inspect.md":    art["inspect_md"],
        "inspect.json":  art["inspect_json"],
        "schema.json":   art["schema"],
        "parser.py":     art["parser"],
        "instance.json": art["instance_json"],
        "dq.md":         art["dq_md"],
        "log.md":        art["log"],
        "summary.md":    art["summary"],
        "dq-report.md":  art["dq_report"],
    }
    for name, tok in art_names.items():
        lines.append(f"| {name} | {tok * CHARS_PER_TOKEN:,} | {tok:,} |")

    lines += [
        "",
        "## Learnings slices",
        "",
        "| Slice (tags) | ~tokens |",
        "|---|---:|",
        f"| structure, tooling | {learn['structure_tooling']:,} |",
        f"| schema, structure, tooling | {learn['schema_structure_tooling']:,} |",
        f"| normalization, structure, tooling | {learn['normalization_structure_tooling']:,} |",
        f"| dq, tooling | {learn['dq_tooling']:,} |",
    ]

    if family_match:
        lines += [
            "",
            f"Family canonical schema detected: **~{family_schema_tokens:,} tokens**",
            "(Added to schema-designer input on a same-family match.)",
        ]

    lines += [
        "",
        "## Summary",
        "",
        f"| | tokens |",
        f"|---|---:|",
        f"| Model input  (all steps) | {model_in:,} |",
        f"| Model output (all steps) | {model_out:,} |",
        f"| **Total model tokens**   | **{model_total:,}** |",
        f"| Zero-token steps         | {len(zero_steps)} steps |",
        "",
        "Zero-token steps: " + ", ".join(zero_steps),
        "",
        "> Row count is **irrelevant** to this total: every row is processed by the "
        "generated parser (zero-token step 5). Only the compact inspect report, "
        "fixed-size reference files, and model-authored artifacts enter the context window.",
    ]

    report = "\n".join(lines)

    # Always write the file when --out is given
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"Written to {args.out}", file=sys.stderr)

    # Print to stdout with safe encoding fallback
    sys.stdout.buffer.write((report + "\n").encode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
