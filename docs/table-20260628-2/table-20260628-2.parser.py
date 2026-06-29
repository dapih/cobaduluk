"""
table-20260628-2.parser.py
Parse table-20260628-2.xlsx (Sheet1) into table-20260628-2.json.

Row state-machine:
  - Blank row (all cells empty) -> skip
  - Col A matches ^[IVX]+\\.   -> section header, start new section wrapper
  - Col A matches ^\\d+\\.     -> item boundary, start new entry
  - Col A empty                -> continuation, accumulate C/E/G into current entry
                                  or start a new tier if tier-divider detected

Tier detection (continuation rows only):
  A continuation row starts a new tier when ANY of:
    (a) Col C has non-empty text that does NOT match a numbered label
    (b) Col G has non-empty text that does NOT match a numbered label
    (c) Col H is non-empty (same kewenangan repeating also counts; we use H
        presence to signal a new authority block)
  The tier_label is the unnumbered C text (preferred) or unnumbered G text.
  If both C and G have unnumbered text at the same row they should match;
  use C. If only H signals the boundary, tier_label is null (single-implicit
  tier label not extracted from a heading row).

Fixes applied (2026-06-28):
  P1-A: tier sub-array (schema change + parser rewrite)
  P1-B: recover full nama_pb_umku for entry no=10 (split across two B cells)
  P2-A: 8 residual wrap hyphens fixed in post-clean pass
  P2-B: 4 source typos fixed with targeted replacements
  P3-C: kbli_note parens stripped
"""
import sys
import re

import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # docs/<job>/ -> plugin root
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from parser_lib import clean, dehyphenate, nest_by_pattern, write_json

import openpyxl

# ---------------------------------------------------------------------------
# Paths (resolved from this file, like the table-20260628-1 parser)
# ---------------------------------------------------------------------------
SRC = os.path.join(HERE, "table-20260628-2.xlsx")
OUT = os.path.join(HERE, "table-20260628-2.json")

DATA_START_ROW = 4  # row 1=title, row 2=header, row 3=blank, row 4=first data

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------
RE_SECTION = re.compile(r"^([IVX]+)\.\s+(.+)$")
RE_ITEM = re.compile(r"^\d+\.$")
RE_KBLI_NOTE = re.compile(r"^\(\*(.+?)\)$", re.IGNORECASE)

# A "numbered label" at the start of a string means it's a list item, not a heading
RE_NUMBERED = re.compile(r"^(\d+\.|[a-z]\.|[A-Z]\.|\d+\))")

# Levels for nest_by_pattern (C, E, G)
LEVELS = [
    ("num",   r"^\d+\."),
    ("alpha", r"^[a-z]\."),
    ("paren", r"^\d+\)"),
]

# ---------------------------------------------------------------------------
# P2-A: residual wrap-hyphen fixes (targeted, after dehyphenate)
# ---------------------------------------------------------------------------
_HYPHEN_FIXES = [
    ("administra-si",      "administrasi"),
    ("bersangku-tan",      "bersangkutan"),
    ("bersangkut-an",      "bersangkutan"),
    ("bersang-kutan",      "bersangkutan"),
    ("Pelabuh-an",         "Pelabuhan"),
    ("pelabuh-an",         "pelabuhan"),
    ("penangkap-an",       "penangkapan"),
    ("penang-kapan",       "penangkapan"),
    ("Penyerta-an",        "Penyertaan"),
    ("penyerta-an",        "penyertaan"),
]

# P2-B: source typos
_TYPO_FIXES = [
    ("Mnyampaikan",    "Menyampaikan"),
    ("pembokaran",     "pembongkaran"),
    ("peMuat",         "pemuat"),
    ("pemeriksaaan",   "pemeriksaan"),
]


def apply_text_fixes(s: str) -> str:
    """Apply P2-A residual hyphen fixes and P2-B typo fixes."""
    if not s:
        return s
    for bad, good in _HYPHEN_FIXES:
        s = s.replace(bad, good)
    for bad, good in _TYPO_FIXES:
        s = s.replace(bad, good)
    return s


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_kewenangan(v):
    """Normalize authority string; fix case variant."""
    if v is None:
        return None
    s = clean(v)
    if s is None:
        return None
    s = re.sub(r"Kepala\s+badan", "Kepala Badan", s)
    return s


def clean_and_fix(v) -> str | None:
    """clean() + dehyphenate (with merge_no_space) + targeted fixes."""
    s = clean(v)
    if s is None:
        return None
    s = dehyphenate(s, merge_no_space=True)
    s = apply_text_fixes(s)
    return s


def is_numbered_text(s: str) -> bool:
    """True if s starts with a numbered label (list item, not heading)."""
    return bool(RE_NUMBERED.match(s))


def parse_kbli_note(raw: str) -> str:
    """Strip (*...) wrapper → plain text. e.g. '(*berlaku untuk seluruh KBLI)' → 'berlaku untuk seluruh KBLI'."""
    m = RE_KBLI_NOTE.match(raw.strip())
    if m:
        return m.group(1).strip()
    return raw.strip()


def build_list(flat: list) -> list:
    """Build a nested Item ({teks, sub}) array from a flat list of raw strings,
    using the family-canonical recursive idiom directly (see families/kkp-licensing)."""
    if not flat:
        return []
    return nest_by_pattern(
        flat,
        levels=LEVELS,
        drop=["-"],
        orphan="attach",
        text_key="teks",
        child_key="sub",
    )


def parse_col_b(raw_b):
    """
    Parse Col B value.
    Returns (nama_pb_umku, applies_to_all_kbli, kbli_note_plain).
    kbli_note_plain is plain text (parens stripped) per P3-C.
    """
    s = clean(raw_b)
    if s is None:
        return None, False, None

    # Pure kbli note row: "(*berlaku untuk seluruh KBLI)"
    if RE_KBLI_NOTE.match(s):
        return None, False, parse_kbli_note(s)

    # Star-prefixed: "*Surat Izin ..." -> applies_to_all_kbli=True
    applies = False
    if s.startswith("*"):
        applies = True
        s = s[1:].strip()

    return s, applies, None


# ---------------------------------------------------------------------------
# Tier helpers
# ---------------------------------------------------------------------------

def new_tier(tier_label=None):
    """Create an empty tier accumulator."""
    return {
        "tier_label": tier_label,
        "_c_flat": [],
        "_e_flat": [],
        "_g_flat": [],
    }


def finalize_tier(t: dict) -> dict:
    """Convert a tier accumulator to the schema Tier shape."""
    return {
        "tier_label": t["tier_label"],
        "persyaratan": build_list(t["_c_flat"]),
        "kewajiban":   build_list(t["_e_flat"]),
        "parameter":   build_list(t["_g_flat"]),
    }


def is_heading_text(s: str) -> bool:
    """
    True if s looks like a section/tier heading (unnumbered, not a parenthetical note).
    Parenthetical continuations like '(khusus Provinsi Aceh...)' start with '(' and
    are NOT headings — they are orphan continuations of the previous list item.
    """
    if not s:
        return False
    if is_numbered_text(s):
        return False
    # Parenthetical notes/clarifications are not headings
    if s.startswith("("):
        return False
    return True


def is_tier_divider_row(c_val, g_val, h_val) -> tuple:
    """
    Returns (is_divider: bool, tier_label: str|None).
    A continuation row starts a new tier when:
      (a) Col C has heading text (unnumbered, not parenthetical) — C is the
          primary column for tier-scope labels, OR
      (b) Col H is non-empty (new authority block signals a new tier)
    Col G heading text does NOT trigger a tier break — in some entries (e.g.
    entry no=2) G transitions to a new scope block independently of C, so we
    leave G heading text to be treated as orphan/group items within the
    current tier's parameter list.
    tier_label is the C heading text, or None when only H signals the break.
    """
    c = clean(c_val)
    h = normalize_kewenangan(h_val)

    c_is_heading = is_heading_text(c) if c else False

    if c_is_heading or h:
        label = None
        if c_is_heading:
            label = dehyphenate(c, merge_no_space=True)
            label = apply_text_fixes(label)
        return True, label
    return False, None


# ---------------------------------------------------------------------------
# Entry helpers
# ---------------------------------------------------------------------------

def new_entry(a_val, b_val, c_val, d_val, e_val, f_val, g_val, h_val):
    """Create a fresh entry dict for an item boundary row."""
    no = clean(a_val)
    nama, applies, kbli_note = parse_col_b(b_val)
    jangka = clean(d_val)
    masa = dehyphenate(clean(f_val), merge_no_space=True)
    if masa:
        masa = apply_text_fixes(masa)
    kewenangan = normalize_kewenangan(h_val)

    c = clean_and_fix(c_val)
    e = clean_and_fix(e_val)
    g = clean_and_fix(g_val)

    # Determine tier_label for the first tier.
    # If C is a heading (unnumbered, not parenthetical) on the boundary row itself,
    # use it as tier_label. G headings do NOT trigger a tier_label (see is_tier_divider_row).
    first_tier_label = None
    c_is_heading = is_heading_text(c) if c else False

    if c_is_heading:
        first_tier_label = c
        c = None  # consumed as tier_label

    first_tier = new_tier(tier_label=first_tier_label)
    if c:
        first_tier["_c_flat"].append(c)
    if e:
        first_tier["_e_flat"].append(e)
    if g:
        first_tier["_g_flat"].append(g)

    return {
        "no": no,
        "nama_pb_umku": nama,
        "applies_to_all_kbli": applies,
        "kbli_note": kbli_note,
        "jangka_waktu_penerbitan": jangka,
        "masa_berlaku": masa,
        "kewenangan": kewenangan,
        "_tiers": [first_tier],
    }


def accumulate(cur, b_val, c_val, e_val, g_val, h_val, rows_seen):
    """Accumulate a continuation row into the current entry, handling tier breaks."""
    # Col B: may carry kbli_note or continuation of nama_pb_umku
    b = clean(b_val)
    if b is not None:
        if RE_KBLI_NOTE.match(b):
            if cur["kbli_note"] is None:
                cur["kbli_note"] = parse_kbli_note(b)
        elif cur["nama_pb_umku"] is None:
            nama, applies, note = parse_col_b(b_val)
            if nama:
                # P1-B: concatenate with any partial name already accumulated
                cur["nama_pb_umku"] = nama
                cur["applies_to_all_kbli"] = applies
            if note:
                cur["kbli_note"] = note
        elif not cur["nama_pb_umku"].strip():
            # Safety: empty string → try to fill
            nama, applies, note = parse_col_b(b_val)
            if nama:
                cur["nama_pb_umku"] = nama

    c = clean_and_fix(c_val)
    e = clean_and_fix(e_val)
    g = clean_and_fix(g_val)
    h = normalize_kewenangan(h_val)

    # Determine if this row is a tier divider
    is_div, tier_label = is_tier_divider_row(c_val, g_val, h_val)

    if is_div:
        # Start a new tier
        cur["_tiers"].append(new_tier(tier_label=tier_label))
        # Col H: set entry-level kewenangan from first occurrence only
        if cur["kewenangan"] is None and h:
            cur["kewenangan"] = h
        # Add non-heading items to the new tier
        cur_tier = cur["_tiers"][-1]
        c_is_heading = c and not is_numbered_text(c)
        g_is_heading = g and not is_numbered_text(g)
        if c and not c_is_heading:
            cur_tier["_c_flat"].append(c)
        if e:
            cur_tier["_e_flat"].append(e)
        if g and not g_is_heading:
            cur_tier["_g_flat"].append(g)
    else:
        # Regular continuation: accumulate into current (last) tier
        cur_tier = cur["_tiers"][-1]
        if c:
            cur_tier["_c_flat"].append(c)
        if e:
            cur_tier["_e_flat"].append(e)
        if g:
            cur_tier["_g_flat"].append(g)
        # Col H: set entry-level kewenangan from first occurrence only
        if cur["kewenangan"] is None and h:
            cur["kewenangan"] = h


def finalize(cur):
    """Convert accumulated raw entry to final schema shape."""
    # P1-B: handle split nama_pb_umku (e.g. "Sertifikasi" + "Cara Pembenihan Ikan yang Baik")
    nama = cur["nama_pb_umku"] or ""
    # If nama looks like it's only the first word of a multi-word name,
    # the second part would have been accumulated via accumulate() already.
    # But the current design: boundary row sets nama from B; continuation row
    # checks if nama is None/empty and fills it. So if boundary row had partial
    # value like "Sertifikasi" and next row B has "Cara Pembenihan...", the
    # accumulate() logic only fills if nama_pb_umku is None.
    # P1-B fix: we need to detect the split and join them.
    # This is handled in accumulate() via the _nama_continuation flag set below.
    nama = cur.get("_nama_full") or nama

    tiers = [finalize_tier(t) for t in cur["_tiers"]]

    entry = {
        "no": cur["no"],
        "nama_pb_umku": nama.strip() if nama else "",
        "applies_to_all_kbli": cur["applies_to_all_kbli"],
        "kbli_note": cur["kbli_note"],
        "jangka_waktu_penerbitan": cur["jangka_waktu_penerbitan"] or "",
        "masa_berlaku": cur["masa_berlaku"] or "",
        "kewenangan": cur["kewenangan"] or "",
        "tiers": tiers,
    }
    return entry


# ---------------------------------------------------------------------------
# Main parse loop
# ---------------------------------------------------------------------------

def parse():
    wb = openpyxl.load_workbook(SRC, data_only=True)
    ws = wb["Sheet1"]

    sections = []
    cur_section = None
    cur_entry = None
    rows_seen = 0
    entries_total = 0
    details_total = 0  # continuation rows
    # Track if previous boundary row had a partial B value (P1-B)
    prev_b_partial = False

    for row in ws.iter_rows(min_row=DATA_START_ROW, values_only=True):
        row = list(row) + [None] * max(0, 8 - len(row))
        A, B, C, D, E, F, G, H = row[:8]

        # Blank row check
        if all(v is None or str(v).strip() == "" for v in row[:8]):
            continue

        rows_seen += 1
        a_clean = clean(A)

        # ── Section header ──
        if a_clean is not None:
            m = RE_SECTION.match(a_clean)
            if m:
                if cur_entry is not None:
                    if cur_section is not None:
                        cur_section["items"].append(finalize(cur_entry))
                    entries_total += 1
                    cur_entry = None
                cur_section = {
                    "section_id": m.group(1),
                    "section_title": m.group(2).strip(),
                    "items": [],
                }
                sections.append(cur_section)
                continue

            # ── Item boundary (Col A matches digit number) ──
            if RE_ITEM.match(a_clean):
                if cur_entry is not None:
                    if cur_section is not None:
                        cur_section["items"].append(finalize(cur_entry))
                    entries_total += 1
                cur_entry = new_entry(A, B, C, D, E, F, G, H)
                # P1-B: detect partial B (no space after meaningful text, short word)
                # "Sertifikasi" alone looks truncated; flag for next row
                b_clean = clean(B)
                # If B ends without closing bracket and looks like a partial name
                # (e.g., it has no spaces among common stop chars), we note it.
                # We'll handle it in the accumulate step using the _nama_continuation key.
                prev_b_partial = (b_clean is not None and
                                  cur_entry["nama_pb_umku"] is not None and
                                  len(cur_entry["nama_pb_umku"].split()) == 1 and
                                  not cur_entry["nama_pb_umku"].endswith(")"))
                if prev_b_partial:
                    cur_entry["_nama_partial"] = cur_entry["nama_pb_umku"]
                continue

            # Col A has unrecognized non-empty value — treat as continuation
            print(f"WARNING: unrecognized Col A value '{a_clean}' — treating as continuation")
            if cur_entry is not None:
                accumulate(cur_entry, B, C, E, G, H, rows_seen)
                details_total += 1
            else:
                print(f"  WARNING: no current entry to attach to, skipping row")
            continue

        # ── Continuation row (Col A empty) ──
        if cur_entry is not None:
            # P1-B: if previous boundary row had a single-word B that looks partial,
            # and this row has a non-empty B that is not a kbli_note,
            # concatenate them as the full name.
            b_clean = clean(B)
            if prev_b_partial and b_clean and not RE_KBLI_NOTE.match(b_clean):
                partial = cur_entry.get("_nama_partial", cur_entry["nama_pb_umku"] or "")
                cur_entry["nama_pb_umku"] = (partial + " " + b_clean).strip()
                cur_entry["_nama_full"] = cur_entry["nama_pb_umku"]
                prev_b_partial = False
                # Don't consume B as a regular accumulation; continue accumulating C/E/G
                accumulate(cur_entry, None, C, E, G, H, rows_seen)
            else:
                prev_b_partial = False
                accumulate(cur_entry, B, C, E, G, H, rows_seen)
            details_total += 1
        else:
            print(f"WARNING: continuation row with no current entry (rows_seen={rows_seen}), skipping")

    # Finalize last entry
    if cur_entry is not None:
        if cur_section is not None:
            cur_section["items"].append(finalize(cur_entry))
        entries_total += 1

    # Count total tiers across all entries
    tiers_total = sum(
        len(entry["tiers"])
        for section in sections
        for entry in section["items"]
    )

    print(f"rows_seen={rows_seen} entries={entries_total} details={details_total}")
    print(f"sections={len(sections)} tiers_total={tiers_total}")

    write_json(sections, OUT)
    print(f"Written: {OUT}")


if __name__ == "__main__":
    parse()
