---
description: Run the full Excel→JSON conversion pipeline on one table (prepare → inspect → map → schema → parse → validate → data-quality → summary), pausing at confirmation gates.
argument-hint: <path-to-xlsx> [--sheet NAME] [--autonomous]
allowed-tools: Read, Write, Edit, Bash, Glob, Task, AskUserQuestion
---

Orchestrate a complete conversion for: **$ARGUMENTS**

Load the `excel-to-json` skill and follow `${CLAUDE_PLUGIN_ROOT}/skills/excel-to-json/workflows/full-pipeline.md` exactly. Summary of your job:

1. **Prepare** — run the `new-job` flow: pick a creation-time job id `table-YYYYMMDD-HHMM<am|pm>` (e.g. `table-20260628-0730pm`), create `output/<job>/`, copy the input in as `<job>.xlsx`, start `log-<job>.md` from the template. Ask before *moving* (vs copying) the user's original.
2. **Inspect & match** — run `inspect_xlsx.py --out output/<job>/<job>` (if the workbook has multiple sheets/tables, list them and ask which one — one table per job). Then **match** the table against promoted families: `python "${CLAUDE_PLUGIN_ROOT}/skills/excel-to-json/scripts/match_profile.py" output/<job>/<job>.inspect.json`. On a **near-duplicate** or **same-family** verdict, present it and **ask whether to reuse** (a gate): near-duplicate → clone the family's canonical schema + the matched member's parser and re-point columns; same-family → warm-start the schema from the canonical and let the next steps adapt. No strong match (or no families) → continue from scratch; reuse never skips a gate. See `${CLAUDE_PLUGIN_ROOT}/skills/excel-to-json/references/reuse.md`.
3. **Map** — delegate to the **structure-analyst** agent. Present its proposed column→field mapping + open questions and **get the user's confirmation** (this is a crucial gate). On a same-family reuse, it aligns field names to the chosen family canonical.
4. **Schema** — delegate to the **schema-designer** agent. If the user supplied a schema, or a family canonical was chosen for reuse, refine/adapt it (ask before changing meaning); else author one. Self-validate it. On a **family match**, run `conformance.py … --job-schema …` to show the delta vs the canonical and surface the **evolve-or-keep** decision (gate): KEEP → register as a member (`promote_family --force`) or leave the canonical alone; EVOLVE → adopt this schema as a new canonical version (`promote_family --force --evolve`). See `${CLAUDE_PLUGIN_ROOT}/skills/excel-to-json/references/reuse.md`.
5. **Parse** — delegate to the **parser-builder** agent: write `<job>.parser.py`, run, and iterate `validate_json.py` to **0 errors**, proving row conservation (`rows in → entries out`).
6. **Validate** — confirm the final `validate_json.py` pass is clean (gate).
7. **Review** — delegate to the **dq-reviewer** agent to write `data-quality-<job>.md` with proposed fixes. Apply fixes only if the user approves; then re-validate.
8. **Summary** — write `summary-<job>.md` from the template, including the field↔column mapping and plain-language table + schema descriptions.
9. **Learn (generalize-and-confirm gate)** — for each candidate insight worth keeping: **generalize** it (strip instance markers — column letters, file/value names, language-specific examples), pick a tag (`structure|schema|normalization|dq|tooling`), set Source to the job id, then **lint** it: `python "${CLAUDE_PLUGIN_ROOT}/skills/excel-to-json/scripts/learnings.py" --lint --entry '<entry>'` (flags bad format, instance-markers, near-duplicates). Resolve every WARN — strip flagged markers; if it overlaps an existing entry, **merge** rather than add. Then **get the user's confirmation** (skip only in `--autonomous`) and append to `${CLAUDE_PLUGIN_ROOT}/skills/excel-to-json/memory/learnings.md`. Keep entries short and domain-agnostic.

Rules:
- **Pass file paths, not contents.** Never load the full xlsx or full JSON into the conversation. Let the scripts and agents do row-level work.
- **Never drop a source row** unless the user explicitly authorizes it.
- **Confirmation gates** (step 1 move, step 2 reuse, step 3 mapping, step 4 schema change + evolve-or-keep, step 7 fixes, step 9 learnings append): pause and ask — *unless* `--autonomous` was passed, in which case proceed with sensible defaults (prefer the family canonical when a strong match exists; default to KEEP — never evolve a canonical autonomously) but still report what you did and never drop rows.
- Log every milestone, decision, and change to `log-<job>.md`.
- Keep a short running status so the user can follow the pipeline.
