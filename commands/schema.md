---
description: Create, refine, or validate a JSON Schema (Draft 2020-12) for a conversion job (delegates to schema-designer).
argument-hint: <job-id> [--from-instance] [--validate-only]
allowed-tools: Read, Write, Edit, Bash, Glob, Task
---

Schema work for job: **$ARGUMENTS**

Pick the mode from the flags:

- **`--validate-only`**: do not author anything. Run the schema self-check and, if `<job>.json` exists, validate the instance:
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_json.py" docs/<job>/<job>.schema.json docs/<job>/<job>.json --counts
  ```
  Report pass/fail and the first errors.

- **`--from-instance`**: the user has a `<job>.json` but no schema. Delegate to the **schema-designer** agent to infer a Draft 2020-12 schema from the instance's structure, then validate the instance against it and iterate to 0 errors. (Use this for the "create schema for an existing instance" partial workflow.)

- **default**: delegate to the **schema-designer** agent to author/refine `<job>.schema.json` from the mapping recorded in `log-<job>.md`. If a schema already exists, refine it and **ask before changing** required fields, enums, or types.

A valid schema is a prerequisite for `/excel-to-json:convert`. Keep the schema precise but not stricter than the source warrants. Log decisions to `log-<job>.md`.
