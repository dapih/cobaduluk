---
description: Run the full Excel→JSON pipeline (prepare → inspect → map → schema → parse → validate → data-quality → summary).
---

Orchestrate a complete conversion for: **$ARGUMENTS**

```bash
PLUGIN_ROOT=$(python excel-to-json/scripts/resolve_plugin_root.py)
```

Load skill `excel-to-json` from `$PLUGIN_ROOT/skills/excel-to-json/SKILL.md` and follow `$PLUGIN_ROOT/workflows/full-pipeline.md` exactly.

1. **Prepare** — new-job flow: job id `table-YYYYMMDD-HHMM<am|pm>`, create `docs/<job>/`, copy input as `<job>.xlsx`, start `log-<job>.md` from `$PLUGIN_ROOT/templates/log.md`. Ask before *moving* the original.
2. **Inspect & match** — `python "$PLUGIN_ROOT/scripts/inspect_xlsx.py" … --out docs/<job>/<job>` then `python "$PLUGIN_ROOT/scripts/match_profile.py" docs/<job>/<job>.inspect.json`. On near-duplicate or same-family, **ask whether to reuse** (gate). See `$PLUGIN_ROOT/design/reuse.md`.
3. **Map** — follow `$PLUGIN_ROOT/agents/structure-analyst.md`. Confirm mapping (gate).
4. **Schema** — follow `$PLUGIN_ROOT/agents/schema-designer.md`. On family match, run `conformance.py` and evolve-or-keep gate. See `$PLUGIN_ROOT/design/reuse.md`.
5. **Parse** — follow `$PLUGIN_ROOT/agents/parser-builder.md` to 0 validation errors; prove row conservation.
6. **Validate** — `python "$PLUGIN_ROOT/scripts/validate_json.py" … --counts` must exit 0.
7. **Review** — follow `$PLUGIN_ROOT/agents/dq-reviewer.md`. Apply fixes only if approved.
8. **Summary** — write `summary-<job>.md` from `$PLUGIN_ROOT/templates/`.
9. **Learn** — generalize → `python "$PLUGIN_ROOT/scripts/learnings.py" --lint --entry '…'` → confirm → append to `$PLUGIN_ROOT/memory/learnings.md`.

Rules: pass paths not contents; never drop rows; pause at gates unless `--autonomous` (default KEEP on family evolve); log to `log-<job>.md`.
