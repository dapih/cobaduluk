# Data-Quality Report: table-20260628-1

**Instance:** table-20260628-1.json
**Schema:** table-20260628-1.schema.json
**Top-level entries:** 94
**Schema validation:** PASSED (0 errors)
**Source rows accounted for:** 1392 non-empty rows in → 94 entries / 145 risk-groups out (no row dropped)
**Generated:** 2026-06-28

---

## Summary

| Severity | Category | Issues | Scope | Status / Recommendation |
|---|---|---|---|---|
| WARN | duplicate_array_items | 82 | within risk-groups | Dedup, or model the repeat as a sub-group (authority-level). Proposed. |
| ~~WARN~~ | broken_hyphenation (intra-word) | 0 | text fields | **RESOLVED** — applied reduplication-safe dehyphenation (`pe-nangkap`→`penangkap`); `undang-undang` preserved. |
| INFO | trailing_conjunction | 381 | persyaratan/kewajiban/parameter | Cross-row sentence fragments; keep as-is unless rejoining is wanted. |
| INFO | numeric_string | 94 | kode_kbli | Intentional — codes kept as strings to preserve leading zeros. No change. |

---

## Open issues

### WARN — duplicate_array_items (82)
**Where:** persyaratan/kewajiban/parameter arrays inside several risk-groups (e.g. `/entri/0/tingkat_risiko/1/...`).
**Root cause:** the source repeats identical detail rows across different business scales/authorities that share one risk-group; all rows append to the same array.
**Recommended fix:** order-preserving `dedupe()` of `parameter`/`pb_umku` (already applied) — extend to `persyaratan`/`kewajiban` **only after** confirming the repeat is pure redundancy and not two distinct items that happen to share a numbering prefix. Alternatively, split by authority into a third level.

### ~~WARN~~ → RESOLVED — broken hyphenation, intra-word
**Where (was):** `judul_kbli`, `parameter`, `persyaratan`, `kewajiban` — e.g. `pe-nangkap`, `ber-ukuran`, `meng-gunakan`, `pengambil-an`.
**Root cause:** the source PDF→Excel wrapped words at line breaks producing a hyphen with **no following space**.
**Fix applied:** the parser uses `dehyphenate(..., merge_no_space=True)` with `protect_reduplication=True`, so line-break splits merge (`pe-nangkap`→`penangkap`, `ber-ukuran`→`berukuran`) while reduplications are kept — verified `undang-undang` survives in the output. Re-validated: 0 errors.

### INFO — trailing_conjunction (381)
**Where:** items ending in `dan` / `atau`. **Root cause:** multi-row cells split at line boundaries; the item continues into the next. **Recommendation:** keep as-is (default) — trimming can change legal meaning; rejoin only on request.

### INFO — numeric_string (94)
`kode_kbli` values are all-digit strings. **This is intentional** (schema stores codes as strings). Note: codes mix 4- and 5-digit lengths — a source characteristic to be aware of for cross-system joins, not an error.

---

## Recommendations
1. ✅ **Reduplication-safe dehyphenation** — applied (`merge_no_space=True`, `protect_reduplication=True`).
2. ✅ **Placeholder → empty** — enforced (`-`/dash dropped from arrays, `clean` empties → absent). No residual `-` placeholders found.
3. **Dedup persyaratan/kewajiban** within risk-groups after confirming redundancy, or introduce an authority sub-level. *(Proposed — your call.)*

---

## Observations
1. Schema validation passed with 0 errors; all WARN/INFO items are data-quality matters the schema intentionally does not enforce.
2. Row conservation holds: every one of the 1,392 populated source rows fed an entry/risk-group; none dropped.
3. This was produced by the **general** engine (no domain logic). A domain-tuned run could add an authority (kewenangan) sub-level and the language-aware dehyphenation rule.
