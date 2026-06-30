---
description: Inspect an Excel workbook structure (compact report, not full sheet).
---

Inspect: **$ARGUMENTS**

```bash
PLUGIN_ROOT=$(python tools/excel-to-json/scripts/resolve_plugin_root.py)
```

1. If argument is an existing `docs/<job-id>/`, use `docs/<job-id>/<job-id>.xlsx` and `--out docs/<job-id>/<job-id>`.
2. Else treat as file path; report to stdout unless `--out` given.
3. Run:
   ```
   python "$PLUGIN_ROOT/scripts/inspect_xlsx.py" <file> [--sheet NAME] [--out docs/<job>/<job>]
   ```
4. Summarize: sheets, header row, entry-boundary column, merged-cell signals. Do not transcribe data.

If multiple sheets, list them — one table per job. Next: `/excel-to-json-schema <job>` or `/excel-to-json-run`.
