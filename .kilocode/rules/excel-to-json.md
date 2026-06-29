# Excel → JSON conversion (excel-to-json)

Activate when the user wants to parse an xlsx file, convert a spreadsheet to JSON, create a JSON Schema for tabular data, or run any stage of the pipeline (inspect, schema, convert, validate, data-quality review).

**Core rule: the full table and the full JSON never enter context.** Run `inspect_xlsx.py` once; read its compact report; write a small parser; Python does every row. A 3,000-row table costs the same tokens as a 30-row table.

## Plugin root

This plugin lives at the repository root. Resolve all script paths from it:

```python
import subprocess, os
PLUGIN_ROOT = subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True
).strip()
```

Scripts are at `<PLUGIN_ROOT>/scripts/`. When generating a parser, write the absolute path literally into `sys.path.insert(0, ...)`.

## Pipeline (follow `workflows/full-pipeline.md` for the full sequence)

| Step | Tool | Gate |
|---|---|---|
| 1. Prepare job folder | `mkdir`, move input, fill log | confirm move |
| 2. Inspect | `python scripts/inspect_xlsx.py <file> --out docs/<job>/<job>` | — |
| 2c. Match families | `python scripts/match_profile.py docs/<job>/<job>.inspect.json` | always show; confirm before reuse |
| 3. Map columns | read `<job>.inspect.md` + `skills/excel-to-json/references/parsing-patterns.md` | confirm mapping |
| 4. Schema | read `skills/excel-to-json/references/schema-design.md`; write `<job>.schema.json` | confirm schema |
| 4b. Conformance | `python scripts/conformance.py` (family match only) | evolve-or-keep |
| 5. Parse | write parser, run it, iterate until 0 errors; assert rows_in == entries_out | confirm parser |
| 6. Validate | `python scripts/validate_json.py <job>.schema.json <job>.json --counts` | must exit 0 |
| 7. DQ review | `python scripts/dq_check.py <job>.json --out docs/<job>/<job>` | — |
| 8. Summary | write `summary-<job>.md` | — |
| 9. Learnings | generalize insight → `python scripts/learnings.py --lint --entry '...'` → confirm → append | lint must pass |

## References (read just-in-time)

- Column mapping, merged cells, numbering → `skills/excel-to-json/references/parsing-patterns.md`
- JSON Schema (Draft 2020-12, `$defs`, recursion) → `skills/excel-to-json/references/schema-design.md`
- Text cleanup decisions → `skills/excel-to-json/references/normalization-rules.md`
- DQ findings → `skills/excel-to-json/references/data-quality-checks.md`
- Job folder layout → `skills/excel-to-json/references/job-conventions.md`
- Reuse design → `design/reuse.md`
- Prior learnings (filtered) → `python scripts/learnings.py --tags <tags>`

## Non-negotiables

- Never read the full `.xlsx` or `.json` instance into context — only the inspect report.
- All gates in steps 2c, 4b, 6, 9 are mandatory; skip only if user explicitly says so.
- Row conservation: `rows_in == entries_out` always.
- Reuse is opt-in: always confirm before warm-starting from a family canonical.
- Learnings appends must pass `learnings.py --lint` before writing.
