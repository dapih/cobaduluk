# Roadmap — future development

All items below are **not blocking** the current pipeline — the plugin is fully functional. They are improvements to consider as usage grows.

## Tuning (data-driven, do after more families accumulate)

- **Recalibrate fingerprint thresholds.** `NEAR_DUP=0.95` and `SAME_FAMILY=0.65` were set from a 4-structure spike (3 distinct shapes). Revisit once 5+ families exist; look for pairs that should tier-up/down.
- **Recalibrate conformance thresholds.** `conformance.py` reports `conforms / same-family-with-delta / divergent` but the delta magnitudes that trigger each verdict were eyeballed. Tune from real data.
- **Learnings density.** If `memory/learnings.md` grows past ~30 entries and tag slices become noisy, generate a per-tag file view or introduce sub-tags.

## Feature ideas (not yet prioritized)

- **Hooks (deferred).** A `PreToolUse` hook that blocks the model from reading the full xlsx or full json instance was discussed but deferred — drift has not been observed in practice. Revisit if an agent is found reading raw data instead of the inspect report.
- **Multi-sheet jobs.** Currently each sheet is a separate job. A `--multi-sheet` flag on `new-job` could group them under one job folder with per-sheet inspect reports and a shared schema.
- **CSV support.** `inspect_xlsx.py` is xlsx-only. A thin CSV reader shim producing the same inspect JSON shape would let the pipeline work on any tabular input without changing downstream steps.
- **Cross-job dashboard.** A script that reads all `summary-<job>.md` files and produces a single markdown table — useful once many jobs exist in a project.
- **Automated conformance gate on promote.** Currently `promote_family.py` adds a member without checking if it structurally drifts far from the canonical. A `--strict` flag that rejects members scoring below a threshold could protect the family centroid from drift.

## Open decisions

| Decision | Status | Notes |
|---|---|---|
| Hooks for pipeline invariants | Deferred | Discussed; not triggered by observed behavior. Reopen if drift seen. |
| Per-tag learnings files | Deferred | Only if `learnings.md` grows unwieldy (>30 entries) |
| `ref1` → `main` PR | Not started | The feature branch is complete; open when ready to ship |
| Plugin install path / `@local` id | Uncertain | README note: exact paths follow observed convention, not official docs |

## How to evaluate a change before merging

1. **Run `python skills/excel-to-json/scripts/measure_tokens.py <job>`** on a completed job before and after the change. Token budget should not increase without a documented reason.
2. **Check parser-builder iteration count** in the job log. Fewer iterations = better learnings or clearer reference docs.
3. **Validate that all gates still fire**: step 2c match, step 4b conformance, step 6 validate, step 9 lint. Run `grep -n "gate\|confirm\|lint" skills/excel-to-json/workflows/full-pipeline.md` to verify nothing was removed.
4. **Fingerprint thresholds**: any change to `fingerprint.py` or `match_profile.py` must be re-spiked against the existing inspect reports in `output/` and the results compared to the spike table in `design/reuse.md`.
