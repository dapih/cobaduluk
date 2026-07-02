---
description: Promote a finished conversion job to a reusable "family" so future same-structure tables can be matched and warm-started.
argument-hint: <job-id> [family-name]
allowed-tools: Read, Bash, Glob, AskUserQuestion
---

Promote a clean job to a reusable family: **$ARGUMENTS**

Families let a *new* table that shares an existing table's structure reuse a past schema instead of starting from scratch. Matching is by **structural fingerprint, not headers** (see `${CLAUDE_PLUGIN_ROOT}/design/reuse.md`). Promotion is **manual and explicit** — only promote a job the user is satisfied with.

1. **Check the job is finished.** Confirm `output/<job-id>/<job-id>.inspect.json` and `<job-id>.schema.json` exist, and that the instance (`<job-id>.json`) last validated clean. If the schema is missing or the job never validated, say so and stop — only clean jobs make good canonicals.
2. **Pick the family name.** Use the second argument if given; otherwise ask for a short kebab-case name (e.g. `kkp-licensing`). If that family already exists, ask whether to **add this job as a member** (`--force`, canonical unchanged) or — if its structure should become the new family standard — **evolve the canonical** (`--force --evolve`). Pick another name if it is actually a different family.
3. **Promote** (deterministic):
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/promote_family.py" <job-id> --name <family> [--force] [--evolve]
   ```
   - **new family** (no flag) — creates `families/<family>/`, copies the job's schema to `family.schema.json` as the canonical (v1).
   - **`--force`** — adds the job as another **member**, keeping the existing canonical; the member records the `canonical_version` it was `built_against`.
   - **`--force --evolve`** — also **adopts this job's schema as a new canonical version** (bumps `canonical_version`, sets `canonical_source`). Use only when the table's structure should become the family standard (the "evolve" side of evolve-or-keep).

   The family's match vector is the **centroid** of member fingerprints; member paths are stored relative to the project root, so `family.json` stays portable.
4. **Report** the store path, canonical schema, and member count. Note that `families/` lives in the project root (tracked), not under `output/`.

To check whether a *new* table matches a promoted family, run:
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/match_profile.py" output/<new-job>/<new-job>.inspect.json
```
This is advisory and never reuses anything without the user confirming.
