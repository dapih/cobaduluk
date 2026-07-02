---
description: Data-quality review and report with proposed fixes (not auto-applied).
---

Data-quality review for job: **$ARGUMENTS**

```bash
PLUGIN_ROOT=$(python excel-to-json/scripts/resolve_plugin_root.py)
```

Precondition: `docs/<job>/<job>.json` exists (ideally schema-valid).

Follow `$PLUGIN_ROOT/agents/dq-reviewer.md`:
1. `python "$PLUGIN_ROOT/scripts/dq_check.py" docs/<job>/<job>.json --out docs/<job>/<job>`
2. Write `data-quality-<job>.md` from `$PLUGIN_ROOT/templates/data-quality.md`
3. Apply fixes **only** if the user approves; re-validate after.

Report severity summary and top recommendations.
