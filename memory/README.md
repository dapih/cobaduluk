# Memory: cross-job learnings

This is the plugin's continuous-improvement store — a plain-text knowledge base that grows as it converts more tables. It is **not** self-modifying AI; it is durable notes that future runs read to avoid re-deriving the same decisions.

## What goes in `learnings.md`
Only **generalizable** insights — patterns that will help a *different* table next time:
- structural heuristics ("a low-fill monotonic integer column marks entry boundaries");
- normalization decisions and their rationale ("merge hyphen+space only; never bare hyphens");
- schema idioms that worked ("recursive `{teks, sub[]}` for numbered lists");
- pitfalls ("merged cells read as None on continuation rows").

Do **not** record table-specific content (actual field names, enums, values) — that belongs in the job's own `summary-<job>.md`. Keep this domain-agnostic so the engine stays general.

## Entry format
```
## [tag] short title
- Context: when this applies
- Insight: what to do / what to expect
- Source: <job-id> or "engine"
```
Tags: `structure`, `schema`, `normalization`, `dq`, `tooling`.

## Reading it (per agent, filtered)
At the start of a run, each agent loads only its relevant slice rather than the whole file:
`python "${CLAUDE_PLUGIN_ROOT}/scripts/learnings.py" --tags <tags>` — structure-analyst → `structure,tooling`; schema-designer → `schema,structure,tooling`; parser-builder → `normalization,structure,tooling`; dq-reviewer → `dq,tooling`. Apply entries whose Context matches the table; ignore the rest.

## Appending it (generalize-and-confirm gate, step 9)
Every new entry passes a gate before it lands. **Generalize** it first — strip instance markers (column letters, data-file names, job ids, language-specific examples) so only the transferable rule remains — then lint it:
`python "${CLAUDE_PLUGIN_ROOT}/scripts/learnings.py" --lint --entry '<entry>'`
The linter flags format problems, instance-markers, and near-duplicates. Resolve every WARN — strip flagged markers; **merge** into the nearest entry instead of adding a near-dup. Then confirm with the user and append. Keep it concise — prune duplicates and anything that turns out wrong.
