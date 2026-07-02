# Job folder conventions

Every conversion is one **job** with its own folder under `output/` in the **user's project root** (the current working directory) — created where the plugin is *used*, never inside the plugin install. Plugin assets (scripts, templates, rules) are read from `${CLAUDE_PLUGIN_ROOT}`. The folder is the unit of work and the shared state between steps and agents.

## Layout

```
output/
  table-20240115-0930am/                          ← one job (id = table-YYYYMMDD-HHMM<am|pm>)
    table-20240115-0930am.xlsx                    source input (moved here in step 1)
    table-20240115-0930am.inspect.md / .json      structure report
    table-20240115-0930am.schema.json             JSON Schema (Draft 2020-12)
    table-20240115-0930am.json                    generated instance
    table-20240115-0930am.parser.py               generated parser (reproduces the instance)
    table-20240115-0930am.dq.md / .dq.json        raw DQ scan output
    log-table-20240115-0930am.md                  running log (milestones, decisions, changes)
    data-quality-table-20240115-0930am.md         written DQ report (interpreted)
    summary-table-20240115-0930am.md              summary + field↔column mapping
    normalization.json / dq-checks.json           (optional) per-job tuned rules
```

## Naming

- **Job id**: `table-YYYYMMDD-HHMM<am|pm>`, stamped from the **moment the job is created** (local time): the `YYYYMMDD` date + the 12-hour clock time as zero-padded `HHMM` + a lowercase `am`/`pm` suffix — e.g. `table-20260628-0730pm`. In the rare case that id already exists (a second job within the same minute), append `-2`, `-3`, … to disambiguate.
- **Stem files** (`xlsx`, `schema.json`, `json`, `parser.py`, inspect, dq) are named `<job-id>.<ext>`.
- **Report files** are prefixed: `log-<job-id>.md`, `data-quality-<job-id>.md`, `summary-<job-id>.md`.
- One table per job. Multiple tables/sheets → multiple jobs.

## Lifecycle

1. **new-job** creates the folder, copies or moves the input in as `<job-id>.xlsx` (ask before moving the user's original), and starts `log-<job-id>.md` from `${CLAUDE_PLUGIN_ROOT}/templates/log.md`.
2. All later steps read/write **inside the job folder** and reference files by path. Do not load whole files into context when a path will do.
3. Reports are copied from `${CLAUDE_PLUGIN_ROOT}/templates/` and filled in.
4. On completion, `summary-<job-id>.md` is the entry point a reader opens first.

## Just-in-time references

Load a file only when the current step needs it: the schema when validating, the inspect report when mapping, the dq output when reviewing. This keeps each step's context small and the run cheap.
