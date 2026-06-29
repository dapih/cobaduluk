# Token budget -- table-20260628-2

Approximation: 1 token ~= 4 chars.  Actual values differ +/-20%.
Parser-builder iterations detected in log: **2**

## Per-step breakdown

| Step | Role | IN (tokens) | OUT (tokens) | Total | Notes |
|---|---|---:|---:|---:|---|
| 1 — Prepare | orchestrator | 0 | 0 | **0** | zero-token ⚙️ |
| 2 — Inspect | inspect_xlsx.py | 0 | 0 | **0** | zero-token ⚙️ |
| 2c — Match | match_profile.py | 0 | 0 | **0** | zero-token ⚙️ |
| 2b — Pick sheet | orchestrator | 787 | 100 | 887 | only if multi-sheet; skipped for single-sheet files _multi-sheet only_ |
| 3 — Structure-analyst | structure-analyst agent | 5,025 | 1,407 | 6,432 | inspect.md + parsing-patterns + learnings; outputs mapping in log |
| 4 — Schema-designer | schema-designer agent | 5,267 | 1,278 | 6,545 | schema-design + log + learnings [+ family canonical] |
| 4b — Conformance read | schema-designer agent | 325 | 200 | 525 | conformance report → evolve-or-keep call (family match only) _family match only_ |
| 5 — Parser-builder | parser-builder agent | 17,308 | 9,052 | 26,360 | write + iterate (2x validation cycles detected in log) |
| 5 (parser runs) | generated parser.py | 0 | 0 | **0** | zero-token ⚙️ |
| 6 — Validate | validate_json.py | 0 | 0 | **0** | zero-token ⚙️ |
| 6 read | orchestrator | 100 | 50 | 150 | reads validation result (1–3 lines) |
| 7 — DQ scan | dq_check.py | 0 | 0 | **0** | zero-token ⚙️ |
| 7 — DQ-reviewer | dq-reviewer agent | 2,909 | 3,591 | 6,500 | dq.md + dq-checks reference + inspect samples + learnings |
| 8 — Summary | orchestrator | 3,315 | 1,369 | 4,684 | full log + summary template → summary.md |
| 9 — Learnings (lint) | learnings.py --lint | 0 | 0 | **0** | zero-token ⚙️ |
| 9 — Learnings (model) | orchestrator | 1,528 | 400 | 1,928 | generalize → confirm → append (0–3 entries; 0 if no new insight) |

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
| inspect.md | 3,148 | 787 |
| inspect.json | 11,768 | 2,942 |
| schema.json | 5,112 | 1,278 |
| parser.py | 18,104 | 4,526 |
| instance.json | 68,468 | 17,117 |
| dq.md | 788 | 197 |
| log.md | 11,260 | 2,815 |
| summary.md | 5,476 | 1,369 |
| dq-report.md | 14,364 | 3,591 |

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
| Model input  (all steps) | 36,564 |
| Model output (all steps) | 17,447 |
| **Total model tokens**   | **54,011** |
| Zero-token steps         | 7 steps |

Zero-token steps: 1 — Prepare, 2 — Inspect, 2c — Match, 5 (parser runs), 6 — Validate, 7 — DQ scan, 9 — Learnings (lint)

> Row count is **irrelevant** to this total: every row is processed by the generated parser (zero-token step 5). Only the compact inspect report, fixed-size reference files, and model-authored artifacts enter the context window.