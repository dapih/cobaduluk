---
description: Validate a job's JSON instance against its JSON Schema (Draft 2020-12).
argument-hint: <job-id | schema.json instance.json> [--counts]
allowed-tools: Read, Bash, Glob
---

Validate: **$ARGUMENTS**

- If given a **job id**, validate `docs/<job>/<job>.json` against `docs/<job>/<job>.schema.json`.
- If given **two paths**, validate the second (instance) against the first (schema).

Run:
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_json.py" <schema> <instance> --counts
```

Report: valid or not, the error count, and the first errors with their paths. Exit code 0 = valid, 1 = errors, 2 = bad input/schema. This is a deterministic gate — no model row-work. If there are errors, point the user to `/excel-to-json:convert <job>` (parser fix) or `/excel-to-json:schema <job>` (schema fix) depending on whether the source value is legitimate.
