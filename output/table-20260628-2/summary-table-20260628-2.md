<!--
TEMPLATE: job summary. Copy to output/<job-id>/summary-<job-id>.md and fill in.
The single document a reader opens first. MUST include the field<->column mapping
(workflow guideline #7) and plain-language descriptions of both the table and the
schema.
-->
# Summary: table-20260628-2

**Source:** kkp2.xlsx (sheet `Sheet1`)
**Schema:** table-20260628-2.schema.json
**Instance:** table-20260628-2.json
**Validation:** 0 errors (clean)
**Generated:** 2026-06-28

---

## What this table is

This table lists the **Perizinan Berusaha Untuk Menunjang Kegiatan Usaha (PB UMKU)** — operational business licences in Indonesia's fisheries sector — organized into three regulatory categories (sections). For each licence type it specifies: the application requirements (Persyaratan), issuance timeline (Jangka Waktu Penerbitan), ongoing obligations (Kewajiban), validity period (Masa Berlaku), applicability parameters (Parameter), and the issuing authority (Kewenangan). Several licence types have two authority-scoped tiers (Gubernur vs. Menteri/Kepala Badan), each with distinct requirement and obligation lists.

## Schema in brief

The root is an **array of Section objects** (one per Roman-numeral category). Each Section contains an `items` array of **Entry objects**. Each Entry has scalar fields for the licence name, timeline, validity, and authority, plus a `tiers` array. Each **Tier** holds `persyaratan`, `kewajiban`, and `parameter` as arrays of **Item** objects — the `kkp-licensing` family-canonical recursive `{ teks, sub }` idiom, where `teks` holds the full line (numbering prefix included) and `sub` nests up to three numbering levels (`1.` / `a.` / `1)`).

## Structure (hierarchy)

```
root  (array)
└── Section
    ├── section_id      "I" | "II" | "III"
    ├── section_title   e.g. "KELAYAKAN OPERASI (B)"
    └── items  (array)
        └── Entry
            ├── no                        "1." … "22."
            ├── nama_pb_umku              licence name
            ├── applies_to_all_kbli       boolean
            ├── kbli_note                 string | null
            ├── jangka_waktu_penerbitan   enum string
            ├── masa_berlaku              string
            ├── kewenangan                enum string
            └── tiers  (array)
                └── Tier
                    ├── tier_label        string | null
                    ├── persyaratan       Item[]
                    ├── kewajiban         Item[]
                    └── parameter         Item[]
                        └── Item
                            ├── teks      string
                            └── sub       Item[]  (recursive, optional)
```

## Field ↔ column mapping

| JSON field (path) | Excel column | Group | Transform | Notes |
|---|---|---|---|---|
| `[].section_id` | A | Section | Strip trailing `.`; extract Roman numeral | Only on rows matching `^[IVX]+\.` with B–H empty |
| `[].section_title` | A | Section | Strip `section_id + ". "` prefix | Same row as section_id |
| `[].items[].no` | A | Entry | As-is | Only on rows matching `^\d+\.` |
| `[].items[].nama_pb_umku` | B | Entry | Strip leading `*` | Asterisk → `applies_to_all_kbli: true` |
| `[].items[].applies_to_all_kbli` | B | Entry | Boolean from `*` prefix | Default `false` |
| `[].items[].kbli_note` | B | Entry | Strip `(*` … `)` parens | Only when B value matches `(*…*)` pattern; else `null` |
| `[].items[].jangka_waktu_penerbitan` | D | Entry | As-is (enum) | Closed enum: 4–30 Hari |
| `[].items[].masa_berlaku` | F | Entry | Dehyphenate syllable-break hyphens | Open string |
| `[].items[].kewenangan` | H | Entry | Take first non-empty; normalize case | Enum: `Menteri/ Kepala Badan`, `Gubernur` |
| `[].items[].tiers[].tier_label` | C or H | Tier | Text of tier-divider row | `null` for single-tier entries |
| `[].items[].tiers[].persyaratan` | C | Tier | `nest_by_pattern` (3 levels) | Accumulated across continuation rows |
| `[].items[].tiers[].kewajiban` | E | Tier | `nest_by_pattern` (3 levels) | Accumulated across continuation rows |
| `[].items[].tiers[].parameter` | G | Tier | `nest_by_pattern` (3 levels); always array | Singletons → `{teks: …}` (family `Item` idiom) |

## Statistics

| Metric | Value |
|---|---|
| Source rows (non-blank) | 266 |
| Sections | 3 |
| Entries (licence types) | 22 |
| Tiers total | 33 |
| Multi-tier entries | 10 |
| Schema validation errors | 0 |

## Data-quality headlines

- P1-A resolved: 10 entries restructured into authority-scoped tiers (Gubernur / Menteri); 34 previously duplicated ListItems eliminated.
- P1-B resolved: `nama_pb_umku` for entry no=10 recovered from source (`"Sertifikasi Cara Pembenihan Ikan yang Baik"`).
- P2-A: 10 syllable-break hyphens removed from `parameter` and `masa_berlaku` text.
- P2-B: 4 source typos corrected (`Mnyampaikan`, `pembokaran`, `peMuat`, `pemeriksaaan`).
- P3-C: `kbli_note` parens stripped; 5 entries now carry plain-text note.
- See [data-quality-table-20260628-2.md](data-quality-table-20260628-2.md) for the full report.

## Files in this job

- `table-20260628-2.xlsx` — source table (copy of kkp2.xlsx)
- `table-20260628-2.schema.json` — JSON Schema (Draft 2020-12)
- `table-20260628-2.json` — generated instance
- `table-20260628-2.parser.py` — the generated parser (reproduces the instance)
- `table-20260628-2.inspect.md` / `.inspect.json` — structural inspection report
- `log-table-20260628-2.md` · `data-quality-table-20260628-2.md` · `summary-table-20260628-2.md`
