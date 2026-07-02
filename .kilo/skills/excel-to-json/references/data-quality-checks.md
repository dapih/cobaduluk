# Data-quality review

How to run the post-conversion review and write `data-quality-<job>.md`. The scan is deterministic (`dq_check.py`); your job is to **interpret** each finding — root cause, whether it's a real problem, and the recommended fix.

## Run the scan

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/dq_check.py" output/<job>/<job>.json --out output/<job>/<job>
```

Produces `<job>.dq.json` (machine) and `<job>.dq.md` (the summary table + samples). Tune which checks run via a copied `dq-checks.default.json`.

## The check catalog

| Category | Severity | Means | Usual recommendation |
|---|---|---|---|
| `whitespace` | warn | leading/trailing/double space slipped through | re-run `clean()` on that field in the parser |
| `broken_hyphenation` | info | `word- word` pattern remains | apply `dehyphenate()` if samples confirm wrapping |
| `placeholder_values` | warn | bare `-`/`N/A`/dash as a value | replace with empty string / drop from array |
| `trailing_conjunction` | info | item ends in `dan`/`and`/`or` | usually a cross-row fragment; keep + note, or rejoin if asked |
| `duplicate_array_items` | warn | identical items repeated in one array | dedup, or model the repeat as a sub-group |
| `empty_vs_null` | info | both `""` and `null` used | pick one convention per field |
| `numeric_string` | info | numeric value stored as string | often intentional (codes); confirm, don't auto-change |

Severity guide: **ERROR** = correctness is wrong (should have been caught by the schema); **WARN** = review and usually fix; **INFO** = advisory / source characteristic.

## Writing the report

Use [`templates/data-quality.md`](../../../templates/data-quality.md). For each open finding give: where (paths/entries), root cause, a short example, and the recommended fix. Then a **Recommendations** section listing proposed changes — proposed, not applied. Apply fixes only after the user confirms (workflow guideline).

Always include the **row-conservation line**: `rows in → entries out`, proving no source row was dropped.

## Distinguish source characteristics from parser bugs

Not every finding is a defect:
- A short or repetitive field value that is literally what the source says is a **source characteristic** — report it, don't "fix" it.
- A value the schema forbids is a **real error** — fix parser or schema.
- A formatting artifact (whitespace, wrap hyphen) is a **cleanup** — apply the safe transform.

Confirm by spot-checking the source cell (the inspect samples or the xlsx), and say which category each finding is.

## Close the loop

When fixes are applied, re-run `validate_json.py` and `dq_check.py`, and update the report's "Resolved since last run" section with before→after counts. The DQ report is a living record across iterations, not a one-shot.
