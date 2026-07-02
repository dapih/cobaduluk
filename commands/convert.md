---
description: Generate the per-table parser and produce the JSON instance, iterating to zero schema-validation errors (delegates to parser-builder).
argument-hint: <job-id>
allowed-tools: Read, Write, Edit, Bash, Glob, Task
---

Convert the table to JSON for job: **$ARGUMENTS**

Preconditions (check first): `output/<job>/<job>.xlsx`, `output/<job>/<job>.inspect.*`, and `output/<job>/<job>.schema.json` must exist. If the schema is missing, stop and tell the user to run `/excel-to-json:schema <job>` first — a schema is required before converting.

Delegate to the **parser-builder** agent to:
1. write `output/<job>/<job>.parser.py` (importing `parser_lib`), implementing the mapping from `log-<job>.md`;
2. run it to produce `output/<job>/<job>.json`;
3. iterate `validate_json.py` to **0 errors**, deciding parser-vs-schema for each;
4. prove **row conservation** (`rows in → entries out`) — never drop a row unless the user authorized it.

Report the final counts, the row-conservation proof, and any schema changes made. Log iterations to `log-<job>.md`.
