# Reuse: matching and warm-starting from past jobs

How to recognize when a new table matches a family you've promoted from a past job, and how to warm-start from it instead of converting from scratch. Design rationale and build history live in [`design/reuse.md`](../../../design/reuse.md); this file is the operative reference for doing the matching and reuse itself.

## Fingerprint (from `<job>.inspect.json`, zero model tokens)

Matching is **structural, not header-text**: same-family tables can use different column counts and header wording/language, so header-token overlap is unreliable. Pattern features, header-agnostic:
- fill-rate distribution shape (bucketed) — denormalized tables show a characteristic low/mid/high spread;
- denormalization ratio (`1/min_fill` ≈ rows-per-entry) — much greater than 1 signals an entry-spanning table;
- multi-level numbering richness (distinct `1.` / `a.` / `1)` styles present);
- counts of enum-like (low-distinct str), code-like (high-distinct int), and long-text (`max_len`>100) columns;
- blank-gap density, merged-cell count, column count (low weight).

Compare with cosine similarity. Header tokens may remain only as a weak tie-breaker.

## Reuse tiers

- **cosine ≥ ~0.95 — near-duplicate** (same report, new version/region): offer to clone the matched job's schema and parser wholesale; the parser only needs columns re-pointed.
- **~0.65–0.95 — same family, different shape:** warm-start from the family canonical; the schema-designer diffs the new table and adapts nesting/fields. The reusable unit is idioms (recursive list `$def`, dehyphenation config, codes-as-strings, `nest_by_pattern` levels) and the hierarchy approach, not a verbatim clone.
- **< ~0.65 — treat as new:** normal from-scratch flow.

Thresholds are provisional; see [`design/reuse.md`](../../../design/reuse.md) for calibration history and recalibrate as the corpus of real families grows.

## Family model and flow

Project-local store, **tracked** (not under a possibly-gitignored `output/`): `families/<name>/`
- `family.json` — name, fingerprint centroid, member job ids, canonical version;
- `family.schema.json` — the canonical shape.

1. **Promote** a clean job → seed or extend the family; the user names it.
2. **Match** a new job (always-ask; never auto-apply) → warm-start from the *canonical*, not the latest member.
3. **Conformance step** (deterministic) → report new / missing / renamed columns vs the canonical.
4. **Evolve-or-keep gate** → propose whether a delta is table-specific (this job only) or a family evolution (bump canonical version). The user confirms.
5. **Versioning** → members record the canonical version they were built against; no forced re-migration of older members.

Reuse never skips a gate: the parser still proves row conservation and the instance still validates, exactly as a from-scratch job would.

## `family.json` shape

```
families/<name>/
  family.json
  family.schema.json        # the canonical (matches canonical_version)
```
`family.json` fields:
- `name`, `created`, `canonical_version`, `canonical_source` (job id whose schema is the current canonical), `canonical_schema` (filename);
- `fingerprint`: `{ vector: <centroid of member vectors>, n_members }` — what `match_profile.py` scores against;
- `members[]`: each `{ job_id, schema, parser, added, built_against, fingerprint{features,vector} }`, with paths relative to the project root.
