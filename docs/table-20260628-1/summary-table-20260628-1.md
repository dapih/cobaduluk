# Summary: table-20260628-1

**Source:** table-20260628-1.xlsx (sheet `KKP1`)
**Schema:** table-20260628-1.schema.json
**Instance:** table-20260628-1.json
**Validation:** PASSED (0 errors)
**Generated:** 2026-06-28

---

## What this table is
A regulatory licensing annex: one row-block per business-classification entry, each carrying its risk level(s), licensing type, issuing authority, business scales, processing time, and nested requirements/obligations. The sheet is denormalized — a single entry spans many physical rows, with header cells filled only on the entry's first row.

## Schema in brief
A 3-level structure: `entri[]` (one per business classification) → `tingkat_risiko[]` (risk-group) → `kewenangan[]` (authority group). Each authority group carries its own `skala_usaha`, `jangka_waktu_penerbitan` (scalar), `persyaratan`, `kewajiban`, `parameter`, `pb_umku`. `persyaratan` and `kewajiban` are recursive `{teks, sub[]}` trees; codes are strings; absent fields are null; present-but-empty are `[]`.

## Structure (hierarchy)
```
{ judul_lampiran, entri[ {
    no, kode_kbli, judul_kbli, ruang_lingkup,
    tingkat_risiko[ {
      nilai, perizinan_berusaha,
      kewenangan[ {
        nilai, skala_usaha[],
        jangka_waktu_penerbitan,       ← scalar (string|null)
        persyaratan[ Item ], kewajiban[ Item ],
        parameter[], pb_umku[]
      } ]
    } ]
} ] }
Item = { teks, sub[ Item ] }
```

## Field ↔ column mapping
| JSON field | Excel col | Role | Transform |
|---|---|---|---|
| `entri[].no` | A | entry boundary (int) | as-is |
| `entri[].kode_kbli` | B | header | `as_int_str` → string |
| `entri[].judul_kbli` | C | header | clean + dehyphenate |
| `entri[].ruang_lingkup` | D | header | clean + dehyphenate |
| `tingkat_risiko[].nilai` | F | sub-group key | clean + dehyphenate |
| `tingkat_risiko[].perizinan_berusaha` | G | sub-group attr | clean + dehyphenate |
| `kewenangan[].nilai` | M | 3rd-level key | `norm_kew()` → canonical form |
| `kewenangan[].skala_usaha[]` | E | per-authority (unique) | clean, strip `- ` marker |
| `kewenangan[].jangka_waktu_penerbitan` | I | per-authority scalar | clean + dehyphenate |
| `kewenangan[].persyaratan[]` | H | per-authority (nested) | clean + `nest_by_pattern` |
| `kewenangan[].kewajiban[]` | J | per-authority (nested) | clean + `nest_by_pattern` |
| `kewenangan[].parameter[]` | L | per-authority (dedup) | clean + dehyphenate |
| `kewenangan[].pb_umku[]` | K | per-authority (dedup) | clean, strip `- ` bullet |

Numbering levels for nesting: `1.` → `a.` → `1)`.

## Statistics
| Metric | Value |
|---|---|
| Source rows (non-empty) | 1392 |
| Top-level entries | 94 |
| Risk-groups | 145 |
| Kewenangan groups | 243 |
| Schema validation errors | 0 |
| Structural mismatches vs reference | 0 |

## Data-quality headlines
- 0 schema errors; 1,392 rows → 94 entries → 145 risk-groups → 243 authority groups, none dropped.
- Reduplication-safe dehyphenation applied: `pe-nangkap`→`penangkap`, `undang-undang` preserved (verified in output).
- `kode_kbli` intentionally string; mixed 4-/5-digit lengths noted.

## Files in this job
- `table-20260628-1.xlsx` — source table
- `table-20260628-1.schema.json` — JSON Schema (Draft 2020-12)
- `table-20260628-1.json` — generated instance
- `table-20260628-1.parser.py` — generated parser (reproduces the instance)
- `table-20260628-1.inspect.md/.json` · `table-20260628-1.dq.md/.json`
- `log-table-20260628-1.md` · `data-quality-table-20260628-1.md` · `summary-table-20260628-1.md`
