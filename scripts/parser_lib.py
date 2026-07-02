"""
parser_lib.py - reusable, domain-agnostic helpers for Excel->JSON parsers.

A per-table parser (generated into a job folder) imports these helpers instead
of reinventing text cleaning, placeholder handling, hierarchy nesting, and JSON
output. Every function is deterministic and uses zero AI tokens.

Import from a generated parser:

    import sys; sys.path.insert(0, r"<plugin-root>/scripts")
    from parser_lib import clean, nest_by_pattern, dedupe, write_json

Design rules:
  * Conservative by default. Transformations that could damage legitimate data
    (e.g. merging every hyphen) are opt-in, never automatic.
  * Pure functions. No global state, no I/O except load_json / write_json.
"""
from __future__ import annotations

import json
import re
import datetime
from typing import Any, Iterable, Optional

# --- text cleaning ----------------------------------------------------------

# Strip zero-width space (200b), ZWNJ (200c), ZWJ (200d), and BOM (feff).
_ZERO_WIDTH = {0x200B: None, 0x200C: None, 0x200D: None, 0xFEFF: None}


def clean(val: Any, *, empty_to_none: bool = True) -> Optional[str]:
    """Normalize a cell value to a clean string.

    - None stays None.
    - Non-strings are stringified.
    - Non-breaking spaces -> normal spaces; zero-width characters removed.
    - Runs of whitespace collapse to a single space, then stripped.
    - Empty result -> None (unless empty_to_none=False, which returns "").
    """
    if val is None:
        return None
    s = str(val).replace("\xa0", " ").translate(_ZERO_WIDTH)
    s = re.sub(r"\s+", " ", s).strip()
    if not s and empty_to_none:
        return None
    return s


_LINEBREAK_HYPHEN = re.compile(r"(\w)-\s+(\w)")
_WORD_HYPHEN_WORD = re.compile(r"(\w+)-(\w+)")


def _is_reduplication(a: str, b: str) -> bool:
    """Heuristic: do `a` and `b` form a reduplication (e.g. Indonesian/Malay
    'undang-undang', 'sehari-hari', 'berlari-lari') rather than a line-break
    split of one word? Used to protect reduplications from being merged."""
    a_, b_ = a.lower(), b.lower()
    if a_ == b_:
        return True
    if len(a_) >= 3 and len(b_) >= 3 and (
        a_.endswith(b_) or b_.endswith(a_) or a_.startswith(b_) or b_.startswith(a_)
    ):
        return True
    return False


def dehyphenate(
    s: Optional[str],
    *,
    merge_no_space: bool = False,
    protect_reduplication: bool = True,
) -> Optional[str]:
    """Repair hyphenation artifacts from PDF/Excel line wrapping.

    Always merges 'word- word' (hyphen followed by whitespace) — almost always a
    broken line-break hyphenation.

    With merge_no_space=True, also merges intra-word 'wo-rd' (hyphen, no space),
    catching splits like 'pe-nangkap' -> 'penangkap'. This is riskier, so by
    default protect_reduplication=True keeps reduplications such as
    'undang-undang' / 'sehari-hari' (common in Indonesian/Malay) intact. Set
    protect_reduplication=False to merge every intra-word hyphen unconditionally
    (may damage legitimate hyphenated terms like 'e-commerce').
    """
    if not s:
        return s
    s = _LINEBREAK_HYPHEN.sub(r"\1\2", s)
    if merge_no_space:
        if protect_reduplication:
            def _repl(m):
                a, b = m.group(1), m.group(2)
                return m.group(0) if _is_reduplication(a, b) else a + b
            s = _WORD_HYPHEN_WORD.sub(_repl, s)
        else:
            s = _WORD_HYPHEN_WORD.sub(r"\1\2", s)
    return s


def strip_trailing_words(s: Optional[str], words: Iterable[str]) -> Optional[str]:
    """Remove a trailing conjunction (e.g. 'dan' / 'atau' / 'and' / 'or')."""
    if not s:
        return s
    pat = r"\s+(?:%s)\s*$" % "|".join(re.escape(w) for w in words)
    out = re.sub(pat, "", s, flags=re.IGNORECASE).rstrip()
    return out or None


def is_placeholder(val: Any, tokens: Iterable[str]) -> bool:
    """True if the cleaned value is empty or a bare placeholder (e.g. '-', 'N/A')."""
    s = clean(val)
    if s is None:
        return True
    return s in set(tokens)


def as_int_str(val: Any) -> Optional[str]:
    """Stringify a numeric code without a trailing '.0' (e.g. 3111.0 -> '3111').

    Cannot restore leading zeros Excel already dropped; keep such codes as text
    in the source, or zfill at the call site.
    """
    if val is None:
        return None
    if isinstance(val, bool):
        return str(val)
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    s = str(val).strip()
    return s or None


# --- hierarchy nesting ------------------------------------------------------


def nest_by_pattern(
    items: Iterable[Any],
    levels: list,
    *,
    text_key: str = "teks",
    child_key: str = "sub",
    drop: Optional[Iterable[str]] = None,
    orphan: str = "attach",
) -> list:
    r"""Build a nested tree from a flat list using ordered numbering patterns.

    `levels` is an ordered list of (name, regex) from outermost to innermost,
    e.g. [("num", r"^\d+\."), ("alpha", r"^[a-z]\."), ("paren", r"^\d+\)")].
    Each item is assigned to the deepest level whose regex matches its start.

    `orphan` controls items that match no pattern:
      - "attach": append under the deepest currently-open node (continuation text)
      - "group":  start a new top-level group header that following items nest into
      - "root":   append at the root level

    `drop` lists exact (cleaned) strings to discard before nesting (e.g. "-").
    Returns a list of dicts shaped {text_key: str, child_key: [...]}.
    """
    compiled = [(name, re.compile(p) if isinstance(p, str) else p) for name, p in levels]
    drop_set = set(drop or ())
    cleaned = [
        i for i in (clean(x, empty_to_none=False) for x in items)
        if i and i not in drop_set
    ]

    root: list = []
    open_nodes: list = [None] * len(compiled)  # current node at each level
    group = None  # active group header when orphan == "group"

    def level_of(item: str) -> int:
        for k, (_name, rx) in enumerate(compiled):
            if rx.match(item):
                return k
        return -1

    def deepest_open():
        for n in reversed(open_nodes):
            if n is not None:
                return n
        return None

    for item in cleaned:
        k = level_of(item)
        node = {text_key: item}

        if k == -1:
            if orphan == "group":
                group = node
                open_nodes = [None] * len(compiled)
                root.append(node)
            elif orphan == "root":
                root.append(node)
            else:  # "attach"
                parent = deepest_open() or group
                if parent is None:
                    root.append(node)
                else:
                    parent.setdefault(child_key, []).append(node)
            continue

        # matched a level: record it and reset deeper levels
        open_nodes[k] = node
        for j in range(k + 1, len(open_nodes)):
            open_nodes[j] = None

        parent = None
        for j in range(k - 1, -1, -1):
            if open_nodes[j] is not None:
                parent = open_nodes[j]
                break
        if parent is None:
            parent = group  # may still be None -> root

        if parent is None:
            root.append(node)
        else:
            parent.setdefault(child_key, []).append(node)

    return root


def dedupe(arr: Iterable[Any]) -> list:
    """Order-preserving de-duplication; handles dicts/lists by value."""
    seen = set()
    out: list = []
    for x in arr:
        key = json.dumps(x, sort_keys=True, ensure_ascii=False) if isinstance(x, (dict, list)) else x
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out


# --- type helpers -----------------------------------------------------------


def cell_type(v: Any) -> Optional[str]:
    """Classify a raw openpyxl cell value into a coarse type name."""
    if v is None:
        return None
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, (datetime.datetime, datetime.date)):
        return "date"
    return "str"


# --- I/O --------------------------------------------------------------------


def load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(obj: Any, path: str, *, indent: int = 2) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)


def load_rules(path: str) -> dict:
    """Load a JSON rules file; returns {} if the path is missing/empty."""
    import os
    if not path or not os.path.exists(path):
        return {}
    return load_json(path)
