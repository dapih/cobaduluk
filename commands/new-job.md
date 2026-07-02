---
description: Create a new conversion job folder under output/, move/copy the Excel input in, and start its log.
argument-hint: <path-to-xlsx> [job-id]
allowed-tools: Read, Write, Bash, Glob, AskUserQuestion
---

Set up a job folder for: **$ARGUMENTS**

1. Determine the **job id**:
   - If a second argument was given, use it.
   - Else build `table-YYYYMMDD-HHMM<am|pm>` from the **moment the job is created** (local time): the `YYYYMMDD` date plus the 12-hour clock time as zero-padded `HHMM` with a lowercase `am`/`pm` suffix — e.g. 7:30 PM on 2026-06-28 → `table-20260628-0730pm`. Get both at once with `date +%Y%m%d-%I%M%P` (GNU `%P` yields lowercase `am`/`pm`; if `%P` is unavailable use `%p` and lowercase the result). In the rare event that `output/<that-id>/` already exists (a second job within the same minute), append `-2`, `-3`, … to disambiguate.
2. Create `output/<job-id>/`.
3. Place the input: **copy** the source xlsx into the folder as `<job-id>.xlsx` by default. Only **move** (delete the original) if the user explicitly asks — confirm first.
4. Start the log: copy `${CLAUDE_PLUGIN_ROOT}/skills/excel-to-json/templates/log.md` to `output/<job-id>/log-<job-id>.md` and fill the header (job id, source file, sheet if known, start datetime, status `in-progress`). Add a first milestone line.
5. Report the created path and the job id, and suggest the next step (`/excel-to-json:inspect <job-id>` or `/excel-to-json:run`).

Keep it deterministic — this step uses no model row-work. Validate the source file exists and is an `.xlsx`/`.xlsm` before creating anything.
