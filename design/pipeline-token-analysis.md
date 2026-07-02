# Pipeline token analysis

**Key claim:** A 3,000-row table costs approximately the same model tokens as a 30-row table, because the model never reads the data — only the compact inspect report (fixed size regardless of row count). Row-level work is entirely handled by deterministic Python.

## Bucket 1 — Zero model tokens (deterministic Python, size-independent)

| Step | Script | What it processes |
|---|---|---|
| 1 — Prepare | `date`/`mkdir`/`cp`/template fill | Shell ops only |
| 2 — Inspect | `inspect_xlsx.py` | Full workbook → compact capped report |
| 2c — Match | `match_profile.py`, `fingerprint.py` | Cosine of stored vectors |
| 4b — Conformance | `conformance.py` | Header set-diff vs family canonical |
| 5 (parser runs) | generated `<job>.parser.py` | Every source row |
| 6 — Validate | `validate_json.py` | Full instance vs schema |
| 7 (scan) | `dq_check.py` | Full instance |
| 9 (lint) | `learnings.py --lint` | Regex + Jaccard on proposed entry |

The model never sees the full table or the full JSON. Even `inspect_xlsx.py` caps its samples.

## Bucket 2 — Model-involved steps

### What the model actually reads

| File / artifact | Read by |
|---|---|
| `<job>.inspect.md` | structure-analyst, schema-designer (indirectly) |
| `references/parsing-patterns.md` | structure-analyst, parser-builder |
| `references/schema-design.md` | schema-designer |
| `references/normalization-rules.md` | parser-builder |
| `references/data-quality-checks.md` | dq-reviewer |
| `learnings.md` (tag-filtered slice) | all 4 agents |
| `log-<job>.md` (accumulated) | schema-designer, parser-builder, dq-reviewer, orchestrator |
| `<job>.schema.json` | parser-builder, dq-reviewer |
| `<job>.parser.py` (fix iterations) | parser-builder |
| `<job>.dq.md` | dq-reviewer |
| family `family.schema.json` (if match) | schema-designer |
| conformance report (if match) | schema-designer |

### Per-step estimates

| Step | Role | Dominant inputs | Model output | Est. total tokens |
|---|---|---|---|---|
| 2b | orchestrator | sheet list from inspect | user question | ~300 |
| 3 | structure-analyst | inspect.md + parsing-patterns + learnings slice | mapping proposal | 10k–20k |
| 4 | schema-designer | schema-design + log + learnings slice [+ canonical] | schema.json + summary | 10k–20k |
| 4b read | schema-designer | conformance report (family match only) | evolve-or-keep call | ~1k |
| 5 | parser-builder | normalization-rules + log + schema + learnings slice + **iterations** | parser.py | 20k–50k |
| 6 read | orchestrator | validate output (pass/fail + counts) | gate decision | ~200 |
| 7 | dq-reviewer | dq.md + data-quality-checks + samples + learnings slice | dq report | 10k–20k |
| 8 | orchestrator | log (full) + summary template | summary.md | 5k–10k |
| 9 | orchestrator | log review + current learnings | 0–3 proposed entries | 1k–3k |

**Step 5 (parser-builder) is the cost driver** because write→run→read-errors→fix cycles compound: each iteration adds ~3k–5k tokens. 2–4 iterations is typical, meaning step 5 alone often exceeds all other steps combined.

### Full-run total (KKP1-scale, no family reuse)

| Scenario | Estimated total |
|---|---|
| From scratch | ~60k–130k tokens |
| Same-family warm-start | ~40k–90k tokens (fewer iterations, schema adapts rather than authors fresh) |

### What moves the number (not row count)

1. **Parser fix iterations** — each adds ~3–5k tokens; the biggest lever.
2. **Reference file size** — `parsing-patterns.md` and `schema-design.md` are read in full each agent invocation.
3. **Schema / parser complexity** — what the model authors and reads back.
4. **Agent system-prompt overhead** — each agent starts cold with its skill context.
5. **Family reuse** — same-family warm-start saves ~30–40% (shorter authoring, fewer iterations).

## Measured baseline (from real runs)

`python skills/excel-to-json/scripts/measure_tokens.py <job-id>` measures character counts for every artifact, approximates token counts, and writes a per-step breakdown. Run against both completed jobs:

| | KKP1 (table-20260628-1) | KKP2 (table-20260628-2) |
|---|---:|---:|
| Table rows | ~1,392 | ~few dozen entries |
| instance.json size | 380 kB / 95k tokens | 68 kB / 17k tokens |
| **instance.json model tokens** | **0** | **0** |
| Step 5 (parser-builder) | 13,157 tokens | 26,360 tokens |
| Step 3 (structure-analyst) | 4,908 tokens | 6,432 tokens |
| Step 4 (schema-designer) | 4,854 tokens | 6,545 tokens |
| Step 7 (DQ-reviewer) | 4,040 tokens | 6,500 tokens |
| Step 8 (summary) | 2,068 tokens | 4,684 tokens |
| Step 9 (learnings) | 1,397 tokens | 1,928 tokens |
| **Total model tokens** | **~32k** | **~54k** |

**What this shows:** KKP1 has 1,392 rows; KKP2 has far fewer — yet KKP2 costs ~70% *more* in model tokens. Why? KKP2's parser is more complex (deep nesting logic: 18k chars vs 7.6k), so step 5 nearly doubles. Row count is irrelevant. The driver is **parser complexity**, not data volume. The `instance.json` is 95k-token for KKP1 and 17k-token for KKP2 — neither ever enters the model context.

Full per-step breakdowns: [measured-tokens-table-20260628-1.md](measured-tokens-table-20260628-1.md) · [measured-tokens-table-20260628-2.md](measured-tokens-table-20260628-2.md)
