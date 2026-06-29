# Full pipeline (canonical sequence)

The ordered procedure the `run` command follows. Each step names the tool that does it and whether it is a confirmation gate. Techniques for each step live in the skill references; this file is the *order of operations*.

Legend: 🤖 = deterministic script · 🧠 = agent (judgment) · ⛔ = confirmation gate (skip only in `--autonomous`).

| # | Step | Tool | Gate | Output |
|---|---|---|---|---|
| 1 | Prepare job folder, place input, start log | `new-job` cmd 🤖 | ⛔ if moving original | `<job>.xlsx`, `log-<job>.md` |
| 2 | Inspect structure | `inspect_xlsx.py` 🤖 | — | `<job>.inspect.md/.json` |
| 2b | Pick sheet/table if several | ask user | ⛔ | chosen sheet |
| 2c | Match against promoted families | `match_profile.py` 🤖 | ⛔ if a strong match → confirm reuse | match report; chosen family canonical |
| 3 | Propose column→field map + hierarchy | `structure-analyst` 🧠 | ⛔ confirm mapping | mapping in log |
| 4 | Author / refine schema | `schema-designer` 🧠 | ⛔ if changing an existing schema | `<job>.schema.json`, schema-summary |
| 4b | (on a family match) Conformance vs canonical | `conformance.py` 🤖 | ⛔ evolve-or-keep | delta report; maybe a new canonical version |
| 5 | Write parser, run, iterate to 0 errors | `parser-builder` 🧠 | — | `<job>.parser.py`, `<job>.json` |
| 6 | Final schema validation | `validate_json.py` 🤖 | gate: 0 errors | clean validation |
| 7 | Data-quality review + report | `dq-reviewer` 🧠 | ⛔ before applying any fix | `data-quality-<job>.md` |
| 8 | Summary + field↔column mapping | orchestrator | — | `summary-<job>.md` |
| 9 | Record durable learnings (generalize-and-confirm gate) | orchestrator + `learnings.py --lint` 🤖 | ⛔ confirm each append | append to `memory/learnings.md` |

## Invariants (every run)
- **One table per job.** Multiple tables/sheets → multiple jobs.
- **A schema is required** before step 5. No schema, no convert.
- **No row is dropped** unless the user explicitly authorizes it; step 5 proves `rows in → entries out` and step 7 restates it.
- **Paths, not contents.** The model never ingests the full table or full JSON.
- **Log** every milestone, decision, and change.

## Reuse from a past family (step 2c)
After inspect, score the new table against the promoted-family store:
`python "${CLAUDE_PLUGIN_ROOT}/scripts/match_profile.py" docs/<job>/<job>.inspect.json`
Matching is by structural fingerprint, not headers (see `design/reuse.md`). Act on the verdict — **always confirm before reusing**:
- **near-duplicate** (cosine ≥ ~0.95): offer to clone the family canonical schema and the matched member's parser, re-pointing columns; parser-builder then adapts and validates.
- **same family** (~0.65–0.95): offer to warm-start the schema from the canonical; structure-analyst aligns field names to it and schema-designer adapts the `$defs` / hierarchy.
- **no strong match** (< ~0.65, or no families yet): proceed from scratch.
Reuse never skips a gate — the parser still proves row conservation and the instance still validates to 0 errors. In `--autonomous`, skip the confirm but prefer the canonical on a strong match and report it.

## Family conformance & evolution (medium tier, step 4b)
On a same-family match, once the schema is drafted, quantify how this table differs from the canonical:
`python "${CLAUDE_PLUGIN_ROOT}/scripts/conformance.py" docs/<job>/<job>.inspect.json --name <family> --job-schema docs/<job>/<job>.schema.json`
It reports header, structural-feature, and schema `$def`/field deltas vs the **canonical member**, plus an advisory verdict (`conforms` / `same-family-with-delta` / `divergent`). Use it for the **evolve-or-keep** decision (a ⛔ gate — manual, at the user's discretion):
- **KEEP** — the delta is table-specific; handle it in this job only. Optionally register the table as a member without changing the canonical: `promote_family.py <job> --name <family> --force`.
- **EVOLVE** — the delta should become the family standard; adopt this job's schema as a new canonical version: `promote_family.py <job> --name <family> --force --evolve` (bumps `canonical_version`).
Members record the `canonical_version` they were `built_against`; older members are **not** re-migrated. The family's match vector is the **centroid** of member fingerprints, so matching sharpens as the family grows. Never evolve a canonical in `--autonomous` — that is a deliberate human decision; default to KEEP.

## Learning-loop gate (step 9)
Agents read prior learnings at start, filtered to their concern: `learnings.py --tags <tags>` (structure-analyst → `structure,tooling`; schema-designer → `schema,structure,tooling`; parser-builder → `normalization,structure,tooling`; dq-reviewer → `dq,tooling`). At step 9, every new insight is **generalized then confirmed** before it lands: strip instance markers, tag it, set Source to the job id, run `learnings.py --lint` (flags bad format / instance-markers / near-duplicates), resolve WARNs (merge near-dups instead of adding), and get user confirmation (skip only in `--autonomous`). The store stays small, domain-agnostic, and deduped — see `memory/README.md`.

## Partial-workflow entry points
The user may run only part of this. Each maps to a command against an existing job folder:

| The user wants… | Command(s) |
|---|---|
| Just understand the table | `inspect` |
| A schema for an existing instance | `schema <job> --from-instance` |
| Just (re)generate the JSON | `convert` (needs schema) |
| Just validate | `validate` |
| Just the data-quality review | `review` |
| The whole thing | `run` |

## Fix loop (steps 5–7)
When validation fails, decide **parser vs schema** per error (see `references/schema-design.md` → "Two-way fixes"); fix one cause; re-validate. When DQ fixes are approved, re-run validate + dq and update the report's "Resolved" section. Iterate until clean and the user is satisfied.
