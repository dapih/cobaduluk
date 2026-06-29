---
name: excel-to-json
description: Convert a complex Excel/xlsx table into validated, schema-backed JSON. Use when the user wants to parse a spreadsheet into JSON, create or validate a JSON Schema for tabular data, convert an Excel table that has merged cells or hierarchical / multi-level rows, or run any stage of the pipeline (inspect, schema, convert, validate, data-quality review). Triggers on phrases like "convert this Excel to JSON", "parse the xlsx", "make a JSON schema for this table", "validate my JSON instance", "data quality check the conversion".
---

# Excel → JSON conversion

Convert one complex Excel table into a JSON instance backed by a JSON Schema, with a data-quality review and standardized reports. Built for **token frugality**: deterministic Python does all row-level work; the model only analyzes structure, authors the schema, writes the parser, and reviews samples.

## Core principle: code does the work, the model supervises

The model must **never** read or transcribe the full table or the full JSON. That is the single most important rule here. Instead:

1. Run `inspect_xlsx.py` once → read its *compact* report (samples + profiles, not all rows).
2. From that report, decide the column→field mapping and schema shape.
3. Write a small per-table **parser script** that imports `parser_lib.py` and does the row work.
4. Run the parser, then `validate_json.py`, then `dq_check.py` — all deterministic.

A 3,000-row table costs the same model tokens as a 30-row table, because the model reads the report and writes a parser either way. Do not "swarm" the model over rows.

## The job folder is the shared state

Every conversion lives in `docs/<job-id>/` (id format `table-YYYYMMDD-HHMM<am|pm>`, stamped at creation time), created in the **user's project root** (the current working directory) — *not* inside the plugin. Plugin assets (scripts, templates, rules) are read from `${CLAUDE_PLUGIN_ROOT}`. All steps read and write the job folder; agents hand off through files, not through context. See [references/job-conventions.md](references/job-conventions.md) for the exact layout and file names.

## Pipeline

| Step | Done by | Output in job folder |
|---|---|---|
| 1. Prepare folder, move input | `new-job` command | `<job>.xlsx`, `log-<job>.md` |
| 2. Inspect structure | `inspect_xlsx.py` | `<job>.inspect.md` / `.json` |
| 2c. Match against promoted families (opt-in reuse) | `match_profile.py` | match report; chosen family canonical |
| 3. Propose column→field map + hierarchy | **structure-analyst** agent | mapping in log / `summary` draft |
| 4. Author / refine schema | **schema-designer** agent | `<job>.schema.json` |
| 5. Write parser, run, iterate to 0 errors | **parser-builder** agent | `<job>.parser.py`, `<job>.json` |
| 6. Validate instance vs schema | `validate_json.py` | gate: 0 errors |
| 7. Data-quality review + report | **dq-reviewer** agent | `data-quality-<job>.md` |
| 8. Summary + field↔column map | this skill / orchestrator | `summary-<job>.md` |
| 9. Record durable learnings (generalize-and-confirm gate) | orchestrator + `learnings.py --lint` | append to `${CLAUDE_PLUGIN_ROOT}/memory/learnings.md` |

The full ordered procedure (with confirmation gates) is in [`workflows/full-pipeline.md`](../../workflows/full-pipeline.md).

Before mapping, the orchestrator may **match** the new table against families promoted from past jobs and, with the user's confirmation, warm-start the schema/parser from a canonical instead of starting from scratch. On a same-family match it also runs a **conformance** diff (`conformance.py`) and surfaces an **evolve-or-keep** decision for the family canonical (which is versioned; the match key is the members' centroid). Reuse never skips the validation or row-conservation gates. See [../../design/reuse.md](../../design/reuse.md).

## Running the scripts

All scripts are under `${CLAUDE_PLUGIN_ROOT}/scripts/`. Run with `python` (3.9+, needs `openpyxl` + `jsonschema`):

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/inspect_xlsx.py" <file.xlsx> [--sheet NAME] --out docs/<job>/<job>
python "${CLAUDE_PLUGIN_ROOT}/scripts/match_profile.py" docs/<job>/<job>.inspect.json
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_json.py" docs/<job>/<job>.schema.json docs/<job>/<job>.json --counts
python "${CLAUDE_PLUGIN_ROOT}/scripts/dq_check.py" docs/<job>/<job>.json --out docs/<job>/<job>
```

The per-table parser imports the shared helpers. Because the job folder is in the user's project (not under the plugin), insert the **absolute** plugin scripts path written literally into the parser at generation time:

```python
import sys
sys.path.insert(0, r"<absolute path to scripts/>")
from parser_lib import clean, dehyphenate, nest_by_pattern, dedupe, as_int_str, write_json
```

Resolve the scripts path using whichever anchor is available:
- **Claude Code**: `${CLAUDE_PLUGIN_ROOT}/scripts` (set by the harness)
- **All other tools**: `<git rev-parse --show-toplevel>/scripts` (the repo root is the plugin root)

Do not compute this path relative to the parser's own `__file__` — `docs/` does not sit under the plugin when it is globally installed.

## When to read which reference (just-in-time)

- Mapping columns / handling merged cells, continuation rows, multi-level numbering → [references/parsing-patterns.md](references/parsing-patterns.md)
- Designing the JSON Schema (Draft 2020-12, `$defs`, recursion, enums, nullable, codes) → [references/schema-design.md](references/schema-design.md)
- Deciding which text cleanups are safe vs risky → [references/normalization-rules.md](references/normalization-rules.md)
- Interpreting DQ findings and writing recommendations → [references/data-quality-checks.md](references/data-quality-checks.md)
- Job-folder layout and naming → [references/job-conventions.md](references/job-conventions.md)
- Worked-output exemplars (form, not domain) → [references/examples/](references/examples/)
- Reusing a past schema/parser for a same-structure table → [../../design/reuse.md](../../design/reuse.md)
- Reading prior learnings (filtered) / appending through the gate → `scripts/learnings.py` + [../../memory/README.md](../../memory/README.md)

## Non-negotiables

- **Never drop a source row** unless the user explicitly says so. After parsing, assert that every populated source row is represented; report `rows in → entries out`.
- **A schema is required** before converting. If the user has none, create one (step 4); if they supply one, validate/refine it.
- **Ask before crucial steps**: moving the input file, modifying an existing schema or instance, and applying any DQ fix. Skip these confirmations only when the user asked for an autonomous run.
- **Log every milestone, decision, and change** to `log-<job>.md`.
- **Stay token-frugal**: pass file paths, not file contents. Read script reports, not raw data. Cap samples.

## Partial workflows

Each step is independently runnable — the user may want only part of the pipeline (e.g. "make a schema for this existing JSON", "just validate", "only the DQ review"). Use the matching command (`schema`, `convert`, `validate`, `review`, `inspect`) against an existing job folder without forcing the whole run.
