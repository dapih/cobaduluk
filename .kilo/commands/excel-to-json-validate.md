---
description: Validate a job JSON instance against its JSON Schema.
---

Validate: **$ARGUMENTS**

```bash
PLUGIN_ROOT=$(python tools/excel-to-json/scripts/resolve_plugin_root.py)
```

- Job id → `docs/<job>/<job>.json` vs `docs/<job>/<job>.schema.json`.
- Two paths → validate instance (second) against schema (first).

```
python "$PLUGIN_ROOT/scripts/validate_json.py" <schema> <instance> --counts
```

Report error count and first errors. Exit 0 = valid. On failure, suggest `/excel-to-json-convert` (parser) or `/excel-to-json-schema` (schema).
