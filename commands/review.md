---
description: Run the post-conversion data-quality review and write the report with proposed fixes (delegates to dq-reviewer).
argument-hint: <job-id>
allowed-tools: Read, Write, Edit, Bash, Glob, Task
---

Data-quality review for job: **$ARGUMENTS**

Precondition: `docs/<job>/<job>.json` exists (ideally already schema-valid).

Delegate to the **dq-reviewer** agent to:
1. run `dq_check.py --out docs/<job>/<job>`;
2. interpret each finding as a real error, a cleanup, or a source characteristic (spot-check the source);
3. write `docs/<job>/data-quality-<job>.md` from the template, including the row-conservation line and a prioritized **Recommendations** section (proposed, not applied — including the standing `-`/blank → empty suggestion);
4. apply fixes **only** if the user approves, then re-validate and update the "Resolved" section.

Report the severity summary and the top recommendations. Do not modify the instance or schema without confirmation.
