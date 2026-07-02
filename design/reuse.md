# Reuse & cross-job intelligence — design history

**Status:** Low tier, medium tier, and the learning-loop gate (#5) **built, wired, and committed** on `ref1`. See "Status & remaining work" at the end. Supersedes the reuse/learning notes in the (now untracked) `PLUGIN-CREATION-BRIEF.md`.

The operative reference for actually doing reuse mid-task (fingerprint, tiers, family model, `family.json` shape) is [`skills/excel-to-json/references/reuse.md`](../skills/excel-to-json/references/reuse.md). This file is the design rationale and build record: why reuse works the way it does, not how to use it.

## Problem

Two same-family tables converted independently produce divergent, inconsistent output. Evidence: KKP1 (`output/table-20260628-1`) and KKP2 (`output/table-20260628-2`) are both Indonesian fisheries PB-UMKU licensing annexes, yet their schemas diverged — the recursive list item is `{teks, sub[]}` in one and `{label, text, children[]}` in the other; grouping is `entri→tingkat_risiko→kewenangan` vs `Section→items→tiers`. Each was authored from scratch. Reuse should let a new same-family table **warm-start** from a past job so shape and vocabulary stay consistent and the work becomes a diff, not a rewrite.

## Decisions (locked)

- **Corpus = manual promotion.** A past job becomes reusable only when the user blesses it; do not auto-scan every `output/*/` job.
- **Always pause and ask** before reusing — never auto-apply a match. Reuse is warm-start + refine and still passes the normal gates (validate to 0 errors + row conservation).
- **Named families, medium curation.** A family has a name and a *canonical* schema maintained across members (not just a single saved template), with a conformance/diff step for new members and simple version stamps. Chosen because >3 same-family tables are expected.
- **Matching is structural, not header-text** (see spike).

## Spike result (2026-06-28)

Four inspect reports scored two ways (throwaway experiment, not committed): KKP1, KKP2, `edt2` (a near-duplicate of KKP1), and a synthetic flat sales table as negative control.

| pair | header-token Jaccard | structural cosine |
|---|---|---|
| KKP1 ↔ edt2 (near-duplicate) | 1.00 | 1.00 |
| KKP1 ↔ KKP2 (same family, diff layout) | **0.42** | **0.81** |
| KKP1 ↔ flat (unrelated) | 0.00 | 0.48 |
| KKP2 ↔ flat (unrelated) | 0.00 | 0.24 |

**Takeaway:** header-text matching is unreliable — the genuine same-family pair scored only 0.42 (13 vs 8 columns, different/Indonesian headers). Structural/pattern matching works — same-family 0.81 vs unrelated ≤0.48, a clear separation. The fingerprint must be pattern-based.

## Build order

1. **Low** — fingerprint + match script + promote (single-template clone) behind the always-ask gate. Testable now on KKP1→KKP2.
2. **Medium** — family canonical + conformance + evolve gate + versioning, added when a family's 2nd–3rd member arrives.

## Known refinements for the build

- Numbering detection currently false-positives on decimals (the flat table's `12.5` matched `1.`); restrict it to string / non-numeric cells.
- Thresholds (0.65 / 0.95) come from 4 tables (3 distinct structures); recalibrate as real families accumulate.
- Pin the store location given `output/` may be gitignored for real users — hence `families/` at repo root, tracked.
- Learning-loop gate (#5) is **built**: agents read `memory/learnings.md` filtered by tag (`learnings.py --tags`) and appends go through the lint gate (`learnings.py --lint`) at step 9.

## Status & remaining work (2026-06-28)

Built, tested, committed on `ref1`:
- **Low tier** — `fingerprint.py` + `match_profile.py` + `promote_family.py` + `/promote`, wired into the pipeline and the structure-analyst / schema-designer agents; both reuse tiers validated end-to-end (near-duplicate clone, same-family adapt).
- **Medium tier** — `conformance.py`; centroid match vector; canonical versioning + `--evolve` + `built_against` / `canonical_source`; relative member paths. Wired into `full-pipeline.md` / `run.md` (conformance step 4b + evolve-or-keep gate), `schema-designer.md`, `promote.md`, README/SKILL.
- KKP2 refactored to the family `{teks, sub}` idiom; `families/kkp-licensing` has 2 members (KKP1 canonical v1 + KKP2).

- **Learning-loop gate (#5)** — `skills/excel-to-json/scripts/learnings.py` (tag-filtered read view + `--lint` gate). All four agents read their tag slice at start; step 9 generalizes → lints → confirms → appends. Documented in `memory/README.md`.

Remaining: none — the reuse + learning design is fully built. Future tuning only: recalibrate fingerprint/conformance thresholds as the corpus grows; add a generated per-tag learnings view if the store ever gets large.
