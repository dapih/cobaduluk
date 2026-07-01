---
description: Run the full Excel→JSON conversion pipeline on one table (Antigravity workflow).
---

When the user invokes this workflow with **$ARGUMENTS** (path to `.xlsx`, optional `--sheet NAME`, optional `--autonomous`):

```bash
PLUGIN_ROOT=$(python excel-to-json/scripts/resolve_plugin_root.py)
```

1. Load skill **`excel-to-json`** from `$PLUGIN_ROOT/skills/excel-to-json/SKILL.md`.
2. Execute `$PLUGIN_ROOT/workflows/full-pipeline.md` step by step.
3. For agent steps, read and follow the matching file under `$PLUGIN_ROOT/agents/`:
   - map → `structure-analyst.md`
   - schema → `schema-designer.md`
   - parse → `parser-builder.md`
   - review → `dq-reviewer.md`
4. Prefix every script with `$PLUGIN_ROOT/scripts/`. Resolve `$PLUGIN_ROOT` via `resolve_plugin_root.py` if not already set.
5. Respect all confirmation gates (reuse, mapping, schema evolve-or-keep, DQ fixes, learnings append). Skip gates only when `--autonomous` is passed (default KEEP on family evolve; never drop rows).
6. Log every milestone to `log-<job>.md`. Job outputs live under `docs/<job>/` in the user's project root.

Do not read the full xlsx or full JSON into context — only inspect reports and script output.
