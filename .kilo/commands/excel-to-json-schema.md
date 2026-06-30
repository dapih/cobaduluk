---
description: Create, refine, or validate a JSON Schema for a conversion job.
---

Schema work for job: **$ARGUMENTS**

```bash
PLUGIN_ROOT=$(python tools/excel-to-json/scripts/resolve_plugin_root.py)
```

Follow `$PLUGIN_ROOT/agents/schema-designer.md`.

- **`--validate-only`**: run `python "$PLUGIN_ROOT/scripts/validate_json.py" docs/<job>/<job>.schema.json docs/<job>/<job>.json --counts`; report pass/fail.
- **`--from-instance`**: infer schema from existing `<job>.json`, iterate to 0 errors.
- **default**: author/refine `<job>.schema.json` from `log-<job>.md`; ask before changing required fields/enums/types.

Log to `log-<job>.md`. Next step for convert: `/excel-to-json-convert <job>`.
