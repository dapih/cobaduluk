# Data-Quality Report: table-20260628-2

**Instance:** `output/table-20260628-2/table-20260628-2.json`
**Schema:** `output/table-20260628-2/table-20260628-2.schema.json`
**Top-level entries:** 22 entries across 3 sections
**Schema validation:** PASSED (0 errors)
**Source rows accounted for:** 266 rows in -> 22 entries out (0 rows dropped)
**Generated:** 2026-06-28
**DQ script run:** YES — `dq_check.py` (automated) + manual spot-check

---

## Summary

| Severity | Check | Issues | Scope | Status |
|---|---|---|---|---|
| P1 WARN | Flat-concatenated multi-tier content (duplicate items) | 34 duplicated ListItems across 3 entries | `[0].items[0-2]` persyaratan / kewajiban | FAIL — parser did not split Gubernur vs Menteri tiers |
| P1 WARN | Truncated `nama_pb_umku` | 1 entry | `[1].items[3]` (no=10.) | FAIL — source value incomplete |
| P2 WARN | Residual wrap hyphens | 8 occurrences in 6 text values | parameter of items no=2, 3, 5, 21 | WARN — cleanup needed |
| P2 WARN | Typographic errors in source text | 4 occurrences | kewajiban / persyaratan of items no=5, 12, 17, 2 | WARN — source typos carried through |
| P3 INFO | Trailing conjunction `dan`/`atau` on last list item | 76 occurrences across all entries | persyaratan / kewajiban / parameter arrays | INFO — source characteristic; last item in each numbered block ends with a conjunction |
| P3 INFO | Orphan text fragments (label=null) | 29 occurrences | persyaratan / kewajiban / parameter across many entries | INFO — mostly legitimate unlabelled items (section dividers, singleton values) |
| P3 INFO | `kbli_note` retains raw asterisk prefix | 5 entries | items no=4,5,6,20,22 | INFO — cosmetic; value is `(*berlaku untuk seluruh KBLI)` not a clean string |

---

## Open Issues

### P1-A — Flat-concatenated multi-tier content produces duplicate ListItems (34 duplicates)

**Where:** `[0].items[0].persyaratan`, `[0].items[0].kewajiban`, `[0].items[1].persyaratan`, `[0].items[1].kewajiban`, `[0].items[2].persyaratan`, `[0].items[2].kewajiban`

**Root cause:** Entries no=1 (Surat Izin Penangkapan Ikan), no=2 (Surat Izin Kapal Pengangkut Ikan), and no=3 (Surat Izin Kapal Pendukung Operasi Penangkapan Ikan) each contain requirements and obligations for **two authority tiers** (Gubernur scope and Menteri scope), which in the source Excel are separate sub-blocks within the same row group. The parser accumulated all rows linearly without detecting the tier boundary, causing the first tier's items to be re-emitted when the second tier's numbering restarts at `1.`. The `parameter` array similarly restarts at `1.` twice (or three times for no=2) representing Gubernur / Menteri / Foreign tiers.

The duplicated `[4]` through `[7]` in `no=1.persyaratan` are not exact duplicates of `[0]–[3]` — there are slight textual differences (e.g., `[1]="Memiliki Buku Kapal Perikanan"` vs `[5]="Memiliki Buku Kapal Perikanan dan"`; `[2]` vs `[6]` differ in wording), meaning the two tiers have *similar but not identical* requirements. The `dq_check.py` flagged 34 items as exact duplicates — these are the subset where text happened to match exactly.

**Example:**
```
[0].items[0].persyaratan[0]: { "label": "1.", "text": "Memiliki alokasi usaha kapal penangkap ikan yang tercantum dalam perizinan berusaha" }
[0].items[0].persyaratan[4]: { "label": "1.", "text": "Memiliki alokasi usaha kapal penangkap ikan yang tercantum dalam perizinan berusaha" }
```
Both label and text are identical. Similarly, `kewajiban[0]` == `kewajiban[11]`, etc.

**Recommended fix (P1):** The parser must detect the tier-reset boundary — where numbered items restart at `1.` within the same entry's array after a preceding orphan-text separator row (e.g., `"Untuk Angkutan Laut Dalam Negeri untuk Barang Khusus"` with label=null). For entries no=1–3, the recommended output structure is to introduce a `tiers` sub-array (or sub-keyed object) keyed by authority scope. Alternatively, if the schema must remain flat, de-duplicate by keeping unique items and attaching tier labels. This requires parser change — do not apply without user confirmation of preferred output structure.

---

### P1-B — Truncated `nama_pb_umku` for entry no=10

**Where:** `[1].items[3].nama_pb_umku`

**Root cause:** The value is `"Sertifikasi"` (11 chars). All other entries in Section II are `"Sertifikat <something>"` or `"Sertifikasi <something>"`. Based on context (persyaratan cover pembenihan ikan / fish hatchery), the full intended value is likely `"Sertifikasi Cara Pembenihan Ikan yang Baik (CPIB)"` or similar. The source cell in the Excel was likely truncated or merged incorrectly.

**Example:**
```json
{ "no": "10.", "nama_pb_umku": "Sertifikasi", ... }
```

**Recommended fix (P1):** Inspect the source Excel cell B for row corresponding to no=10 to recover the full name. Do not guess — source inspection required before correction.

---

### P2-A — Residual wrap hyphens in `parameter` text values

**Where:**
- `[0].items[1].parameter[1].children[0].text` — `"administra-si"`
- `[0].items[1].parameter[1].children[1].text` — `"bersangku-tan"`
- `[0].items[1].parameter[3].children[0].text` — `"Pelabuh-an"` (appears twice)
- `[0].items[1].parameter[3].children[1].text` — `"Pelabuh-an"`
- `[0].items[2].parameter[1].text` — `"bersangkut-an"`
- `[0].items[2].parameter[2].text` — `"penangkap-an"`
- `[0].items[4].parameter[3].children[3].text` — `"Penyerta-an Modal Asing"`
- `[2].items[3].parameter[3].children[3].text` — `"Penyerta-an Modal Asing"`

**Root cause:** These are PDF/Excel column-wrap artifacts. Words were split across lines in the source with a hyphen. Dehyphenation was applied to F/G columns per the log, but these instances in the `parameter` (Col G) text were not caught — likely because the hyphen occurs mid-value within a nested child node that the dehyphenation pass did not traverse deeply, or the `Penyerta-an` pattern was not covered.

**Examples:**
```
"administra-si" → "administrasi"
"bersangku-tan" → "bersangkutan"
"Pelabuh-an" → "Pelabuhan"
"penangkap-an" → "penangkapan"
"Penyerta-an Modal Asing" → "Penyertaan Modal Asing"
```

**Recommended fix (P2):** Apply `dehyphenate()` recursively to all string values in `parameter` children. Safe transform — these are clearly broken syllabications.

---

### P2-B — Typographic errors carried from source

**Where:**

| Path | Found | Should be |
|---|---|---|
| `[1].items[5].kewajiban[1].text` | `"Mnyampaikan laporan kegiatan usaha"` | `"Menyampaikan laporan kegiatan usaha"` |
| `[0].items[4].kewajiban[0].text` | `"Laporan pelaksanaan pembokaran Bangunan..."` | `"Laporan pelaksanaan pembongkaran Bangunan..."` |
| `[0].items[1].persyaratan[12].children[1].text` | `"Pelabuhan peMuat"` | `"Pelabuhan Muat"` |
| `[1].items[10].persyaratan[2].children[3].text` | `"Formulir d (pemeriksaaan bahan baku obat ikan)"` | `"Formulir d (pemeriksaan bahan baku obat ikan)"` |

**Root cause:** Source document contains typographic errors. The parser faithfully transcribed them.

- `"Mnyampaikan"` — missing `"e"`, in no=12 (HACCP certificate) `kewajiban[1]`
- `"pembokaran"` — should be `"pembongkaran"` (demolition), in no=5 (demolition permit) `kewajiban[0]`; ironically the word appears correctly in the `nama_pb_umku` (`"Membongkar"`)
- `"peMuat"` — mid-word capital M in no=2 `persyaratan[12].children[1]`; likely OCR or copy-paste artifact
- `"pemeriksaaan"` — triple-a, in no=17 `persyaratan[2].children[3]`

**Recommended fix (P2):** Apply targeted string replacements. Each is unambiguous. Confirm with user before applying.

---

### P3-A — Trailing conjunction `dan`/`atau` on list items (76 occurrences)

**Where:** Widespread across all entries — persyaratan, kewajiban, parameter arrays.

**Root cause:** This is a **source characteristic**, not a parser error. The source regulation document uses `dan` (and) or `atau` (or) at the end of every item except the last in a numbered list, following Indonesian legislative drafting convention. The last item in each *authority-tier block* within an entry ends without a conjunction. The 76 instances reflect the structural pattern of the source; stripping the trailing conjunction would alter the legal text.

**Example:**
```
[0].items[0].persyaratan[2].children[1].text: "Pelabuhan Pangkalan dan"
[0].items[0].kewajiban[9].text: "Memiliki Surat Izin Penempatan Rumpon, bagi yang menempatkan rumpon dan"
```

**Recommended fix (P3):** No action recommended for the text values. However, note that `dan` at the end of the very last item in an array (i.e., the final item of the final tier) may be a genuine artifact — the last item of a complete list should not have a trailing conjunction. Spot-checking confirms this: many final items in persyaratan/kewajiban arrays do end with `dan`, suggesting the tier-boundary problem (P1-A) is causing the "last item" detection to be unreliable. Defer assessment until P1-A is resolved.

---

### P3-B — Orphan text fragments with `label=null` (29 occurrences)

**Where:** Various persyaratan, kewajiban, parameter nodes across entries no=1–6, 7–17, 18, 19, 20, 21, 22.

**Root cause:** These fall into three distinct sub-cases:

1. **Legitimate unlabelled singleton items** — entries where the entire field contains only one item with no enumeration label. Examples: `[0].items[3].kewajiban[0]` ("Laporan pelaksanaan pembangunan..."), `[0].items[5].persyaratan[0]` ("Surat Izin Membangun..."), all Section II `parameter` entries ("Seluruh"). These are correctly modelled as label=null because the source has no `1.` prefix.

2. **Section-divider text within an array** — e.g., `[0].items[1].persyaratan[0]` ("Untuk Angkutan Laut Dalam Negeri untuk Barang Khusus") and similar. These are sub-heading rows that introduce a tier block; they carry no number in the source. Correctly captured but the tier split (P1-A) means they should ideally be `tier_label` fields rather than list items.

3. **Parenthetical qualifier nodes** — e.g., `[0].items[0].parameter[0].children[0]` ("(khusus Provinsi Aceh ukuran kapal penangkap ikan sesuai...)"). These are asides attached to the preceding numbered item as a child; label=null is structurally correct.

**Example:**
```json
{ "label": null, "text": "Seluruh", "children": [] }
```

**Recommended fix (P3):** No structural change required for sub-cases 1 and 3. Sub-case 2 (tier-divider rows) will be resolved by the P1-A parser fix.

---

### P3-C — `kbli_note` retains raw asterisk prefix (5 entries)

**Where:** `[0].items[3,4,5].kbli_note`, `[2].items[2,4].kbli_note`

**Root cause:** The value stored is `"(*berlaku untuk seluruh KBLI)"` — with parentheses and asterisk still present. The asterisk stripping was applied to `nama_pb_umku` per the log, but the note field retains the raw source format.

**Example:**
```json
{ "kbli_note": "(*berlaku untuk seluruh KBLI)" }
```

**Recommended fix (P3):** Normalize to `"berlaku untuk seluruh KBLI"` (strip leading `(*` and trailing `)`), or to an empty string if `applies_to_all_kbli` boolean alone is sufficient. Low priority since the boolean flag is the machine-readable signal; the string is human-readable annotation.

---

## Recommendations (proposed — apply only after confirmation)

Ordered by severity:

1. **[P1] Fix parser: split multi-tier content for entries no=1, 2, 3.** The parser must detect tier-boundary sentinel rows (orphan text with label=null that introduces a new numbered block) and either (a) structure a `tiers` array with sub-entries keyed by tier label, or (b) deduplicate by omitting the second block if it is genuinely redundant. Requires user decision on preferred output shape before implementation.

2. **[P1] Recover full `nama_pb_umku` for entry no=10.** Inspect source Excel row for no=10 and supply the complete value. Current value `"Sertifikasi"` is incomplete.

3. **[P2] Apply dehyphenation to all parameter/children string values.** Fix: `"administra-si"` → `"administrasi"`, `"bersangku-tan"` → `"bersangkutan"`, `"Pelabuh-an"` → `"Pelabuhan"`, `"bersangkut-an"` → `"bersangkutan"`, `"penangkap-an"` → `"penangkapan"`, `"Penyerta-an"` → `"Penyertaan"`. Safe transform — extend the dehyphenation pass to recurse into all children nodes.

4. **[P2] Correct four typographic errors.** Targeted replacements: `"Mnyampaikan"` → `"Menyampaikan"`, `"pembokaran"` → `"pembongkaran"`, `"peMuat"` → `"Muat"`, `"pemeriksaaan"` → `"pemeriksaan"`. All are unambiguous and confirmed against context.

5. **[P3] Strip asterisk/parentheses from `kbli_note`.** Replace `"(*berlaku untuk seluruh KBLI)"` with `"berlaku untuk seluruh KBLI"` across all 5 instances. Cosmetic only.

6. **[P3] Trailing conjunctions — no action on text values.** Defer assessment until P1-A is resolved; the tier-concatenation inflates counts and obscures which `dan` instances are genuinely terminal artifacts.

7. **[Standing recommendation] `-` / blank → empty-string / empty-array.** No `-` placeholder values were detected in this instance. The empty-array check passed. This recommendation is moot for this job.

---

## Resolved since last run

No previous DQ run for this job. First run.

---

## Observations

1. The automated DQ script (`dq_check.py`) correctly flagged the 34 duplicate array items (WARN) and 76 trailing conjunctions (INFO). It did not flag typos, wrap hyphens, or the truncated `nama_pb_umku` — these required manual inspection.

2. The core structural issue (P1-A, 34 duplicates) is not a typo or formatting artifact: it reflects a genuine ambiguity in the source table layout where two authority-scope variants of the same permit type share a single numbered entry. The parser treated all rows within entry no=1/2/3 as belonging to one flat list, whereas they should be structured as two separate requirement/obligation blocks (one per authority scope).

3. Entry no=10 `"Sertifikasi"` is likely `"Sertifikasi Cara Pembenihan Ikan yang Baik (CPIB)"` based on its kewajiban/persyaratan content, but this must be confirmed against the source.

4. The `kewenangan` field is clean: only two values present (`"Gubernur"`, `"Menteri/ Kepala Badan"`), consistent with the schema enum. No case-normalization issues remain.

5. `jangka_waktu_penerbitan` has 6 distinct values (not 7 as listed in the mapping log — `"4 Hari"` is absent from this instance). This is not an error; it may not appear in the covered entries.
