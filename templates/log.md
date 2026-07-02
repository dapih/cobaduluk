<!--
TEMPLATE: log report. Copy to docs/<job-id>/log-<job-id>.md and fill in.
This is the running record of the job. Append entries chronologically; never
rewrite history. One line per milestone, result, change, or decision.
Entry format:  - [YYYY-MM-DD HH:MM] [step] message
-->
# Log: {{job_id}}

**Source:** {{source_file}}
**Sheet / table:** {{sheet}}
**Started:** {{start_datetime}}
**Status:** {{status}}  <!-- in-progress | done | blocked -->

## Milestones
- [{{datetime}}] [new-job] Created job folder; moved input as `{{job_id}}.xlsx`.
- [{{datetime}}] [inspect] Inspected sheet `{{sheet}}` ({{rows}}x{{cols}}); header row {{header_row}}.

## Decisions
<!-- Record each non-obvious choice and why (e.g. column->field mapping, schema shape). -->
- [{{datetime}}] [structure] {{decision}}

## Changes
<!-- Every edit to schema/instance/parser worth noting. -->
- [{{datetime}}] [{{file}}] {{change}}

## Validation history
| When | Schema errors | Rows in / entries out | Notes |
|---|---|---|---|
| {{datetime}} | {{errors}} | {{rows_in}} / {{entries_out}} | {{notes}} |

## Open items / next steps
- {{item}}
