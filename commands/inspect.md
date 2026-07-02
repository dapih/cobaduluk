---
description: Inspect an Excel workbook's structure (sheets, header row, column profiles, samples, blank-gaps) without loading the full sheet.
argument-hint: <path-to-xlsx | job-id> [--sheet NAME]
allowed-tools: Read, Bash, Glob
---

Inspect: **$ARGUMENTS**

1. Resolve the target:
   - If the argument matches an existing `docs/<job-id>/` folder, use `docs/<job-id>/<job-id>.xlsx` and write the report to `docs/<job-id>/<job-id>` (so it produces `<job-id>.inspect.md` / `.json`).
   - Otherwise treat the argument as a file path and print the report to stdout.
2. Run:
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/inspect_xlsx.py" <file> [--sheet NAME] [--out docs/<job>/<job>]
   ```
3. Read the report and give a brief, high-signal summary: sheet(s) and size, detected header row, the likely entry-boundary column (low fill rate), which columns are header vs detail, any multi-level numbering, and any merged-cell / blank-gap signals worth noting before conversion.

Do not transcribe the data — rely on the report's profiles and samples. If multiple sheets exist, list them and note that one table = one job.
