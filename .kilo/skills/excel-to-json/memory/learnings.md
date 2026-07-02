# Learnings

Generalizable insights from past conversions. Append new entries at pipeline step 9. See `README.md` for format. Seeded with engine-level heuristics; everything below is domain-agnostic.

## [structure] Entry boundaries are low-fill key columns
- Context: denormalized sheets where one logical record spans many rows.
- Insight: the column that starts a new top-level entry is usually the one with a *low* fill rate (≈ 1 / rows-per-entry) and often a monotonic integer or an ID/code. Use the inspect fill-rate profile to find it; confirm with the samples.
- Source: engine

## [structure] Merged cells read as None on continuation rows
- Context: openpyxl with `data_only=True`.
- Insight: a merged range returns its value only in the top-left cell; other cells are None. That is *why* header columns look empty on continuation rows — rely on it for the row state-machine rather than fighting it.
- Source: engine

## [structure] Blank-row gaps are usually separators, not new tables
- Context: inspect reports many single blank-row gaps.
- Insight: scattered single blank rows generally separate records within one table; treat as one table unless gaps are wide bands or a header row repeats. The inspector flags gaps; you interpret them.
- Source: engine

## [normalization] Clean formatting, preserve meaning
- Context: choosing which text transforms to apply.
- Insight: whitespace/zero-width cleanup and hyphen-plus-space de-wrapping are safe. Merging bare hyphens and trimming trailing conjunctions are risky (they change real terms / legal meaning) — keep them off unless the samples prove they are warranted.
- Source: engine

## [schema] Recursive item for multi-level lists
- Context: a detail column mixes numbering levels (`1.` / `a.` / `1)`).
- Insight: model it as a self-referential `{ "teks": string, "sub": [ $ref item ] }` `$def` and build it with `parser_lib.nest_by_pattern`. Keep `sub` optional.
- Source: engine

## [structure] Mid-entry heading rows are sub-group dividers, not list items
- Context: a denormalized entry whose detail column(s) carry an unnumbered, non-parenthetical heading partway down (e.g. a scope label like "Untuk Angkutan Laut Dalam Negeri…").
- Insight: treat it as a tier/sub-group divider and nest the details as a `tiers` array — flattening duplicates the items. A neighbouring header column that changes value on a continuation row is a secondary boundary signal.
- Source: table-20260628-2 (2026-06-28)

## [normalization] Intra-word line-break hyphens: merge only with guards
- Context: text imported from a PDF where a word was split across lines with a hyphen (e.g. "penang-kapan" → "penangkapan").
- Insight: merge only when both neighbours are lowercase letters (ideally the result is a real word); never merge reduplications or hyphenated proper nouns. This is the `dehyphenate(merge_no_space=True, protect_reduplication=True)` path — off by default, enabled per-table when samples show line-break splits.
- Source: table-20260628-2 (2026-06-28)

## [schema] Codes are strings
- Context: identifier-like numeric columns (codes, IDs).
- Insight: store as strings with a `pattern`, to preserve leading zeros and prevent arithmetic. Mixed-length codes are a data observation to note, not necessarily an error to fix.
- Source: engine
