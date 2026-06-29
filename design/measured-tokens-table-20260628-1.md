# Token budget -- table-20260628-1

Approximation: 1 token ~= 4 chars.  Actual values differ +/-20%.
Parser-builder iterations detected in log: **2**

## Per-step breakdown

| Step | Role | IN (tokens) | OUT (tokens) | Total | Notes |
|---|---|---:|---:|---:|---|
| 1 — Prepare | orchestrator | 0 | 0 | **0** | zero-token ⚙️ |
| 2 — Inspect | inspect_xlsx.py | 0 | 0 | **0** | zero-token ⚙️ |
| 2c — Match | match_profile.py | 0 | 0 | **0** | zero-token ⚙️ |
| 2b — Pick sheet | orchestrator | 857 | 100 | 957 | only if multi-sheet; skipped for single-sheet files _multi-sheet only_ |
| 3 — Structure-analyst | structure-analyst agent | 4,564 | 344 | 4,908 | inspect.md + parsing-patterns + learnings; outputs mapping in log |
| 4 — Schema-designer | schema-designer agent | 4,204 | 650 | 4,854 | schema-design + log + learnings [+ family canonical] |
| 4b — Conformance read | schema-designer agent | 325 | 200 | 525 | conformance report → evolve-or-keep call (family match only) _family match only_ |
| 5 — Parser-builder | parser-builder agent | 9,329 | 3,828 | 13,157 | write + iterate (2x validation cycles detected in log) |
| 5 (parser runs) | generated parser.py | 0 | 0 | **0** | zero-token ⚙️ |
| 6 — Validate | validate_json.py | 0 | 0 | **0** | zero-token ⚙️ |
| 6 read | orchestrator | 100 | 50 | 150 | reads validation result (1–3 lines) |
| 7 — DQ scan | dq_check.py | 0 | 0 | **0** | zero-token ⚙️ |
| 7 — DQ-reviewer | dq-reviewer agent | 3,134 | 906 | 4,040 | dq.md + dq-checks reference + inspect samples + learnings |
| 8 — Summary | orchestrator | 1,188 | 880 | 2,068 | full log + summary template → summary.md |
| 9 — Learnings (lint) | learnings.py --lint | 0 | 0 | **0** | zero-token ⚙️ |
| 9 — Learnings (model) | orchestrator | 997 | 400 | 1,397 | generalize → confirm → append (0–3 entries; 0 if no new insight) |

## Reference file sizes

| File | chars | ~tokens |
|---|---:|---:|
| parsing-patterns.md | 5,536 | 1,384 |
| schema-design.md | 3,652 | 913 |
| normalization-rules.md | 3,120 | 780 |
| data-quality-checks.md | 2,784 | 696 |
| SKILL.md | 7,016 | 1,754 |

## Per-job artifact sizes

| Artifact | chars | ~tokens |
|---|---:|---:|
| inspect.md | 3,428 | 857 |
| inspect.json | 17,068 | 4,267 |
| schema.json | 2,600 | 650 |
| parser.py | 7,656 | 1,914 |
| instance.json | 380,340 | 95,085 |
| dq.md | 1,596 | 399 |
| log.md | 2,752 | 688 |
| summary.md | 3,520 | 880 |
| dq-report.md | 3,624 | 906 |

## Learnings slices

| Slice (tags) | ~tokens |
|---|---:|
| structure, tooling | 397 |
| schema, structure, tooling | 543 |
| normalization, structure, tooling | 629 |
| dq, tooling | 0 |

Family canonical schema detected: **~650 tokens**
(Added to schema-designer input on a same-family match.)

## Summary

| | tokens |
|---|---:|
| Model input  (all steps) | 24,698 |
| Model output (all steps) | 7,358 |
| **Total model tokens**   | **32,056** |
| Zero-token steps         | 7 steps |

Zero-token steps: 1 — Prepare, 2 — Inspect, 2c — Match, 5 (parser runs), 6 — Validate, 7 — DQ scan, 9 — Learnings (lint)

> Row count is **irrelevant** to this total: every row is processed by the generated parser (zero-token step 5). Only the compact inspect report, fixed-size reference files, and model-authored artifacts enter the context window.