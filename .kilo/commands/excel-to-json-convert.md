---
description: Generate the parser and JSON instance; iterate to zero schema errors.
---

Convert the table to JSON for job: **$ARGUMENTS**

```bash
PLUGIN_ROOT=$(python excel-to-json/skills/excel-to-json/scripts/resolve_plugin_root.py)
```

Preconditions: `output/<job>/<job>.xlsx`, `<job>.inspect.*`, and `<job>.schema.json` must exist. If schema missing, stop — run `/excel-to-json-schema <job>` first.

Follow `$PLUGIN_ROOT/agents/parser-builder.md`:
1. Write `output/<job>/<job>.parser.py` (embed `$PLUGIN_ROOT/skills/excel-to-json/scripts` in `sys.path`).
2. Produce `output/<job>/<job>.json`.
3. Iterate `python "$PLUGIN_ROOT/skills/excel-to-json/scripts/validate_json.py" … --counts` to **0 errors**.
4. Prove **rows in → entries out**.

Log iterations to `log-<job>.md`.
