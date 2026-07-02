"""
learnings.py - read / lint the cross-job learnings store (memory/learnings.md).

Two deterministic, token-frugal jobs:
  --tags T1,T2  print only entries tagged [T1]/[T2] - an agent's relevant slice
                so it doesn't have to read the whole file.
  --lint        check a PROPOSED entry (--entry "..." or stdin) for the
                generalize-and-confirm gate: format, instance-markers (column
                letters, data-file names, job ids), and near-duplicates vs
                existing entries. Advisory - the model still decides whether the
                insight is genuinely generalizable and domain-agnostic.

Usage:
    python learnings.py --tags structure,tooling [--file PATH]
    python learnings.py --lint --entry "## [schema] ..." [--file PATH]
    cat entry.md | python learnings.py --lint

Store defaults to <plugin>/skills/excel-to-json/memory/learnings.md (resolved from this file).
Exit: 0 ok, 1 hard format error (lint), 2 IO error.
"""
import argparse
import os
import re
import sys

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = os.path.join(_SKILL_ROOT, "memory", "learnings.md")
TAGS = {"structure", "schema", "normalization", "dq", "tooling"}
HEAD = re.compile(r"^##\s*\[(\w+)\]\s*(.*)$")

# Instance-markers: things a *generalizable* entry should not contain.
MARKERS = [
    (re.compile(r"\b[Cc]ol(?:umn)?s?\.?\s+[A-Z]\b"), "column-letter reference"),
    (re.compile(r"\b[A-Za-z0-9_-]+\.(?:xlsx|xlsm|csv)\b"), "data-file name"),
    (re.compile(r"\btable-\d{6,8}\b"), "job id"),
]


def parse(text):
    """Return [(tag, title, [body_lines]), ...]."""
    entries, cur = [], None
    for line in text.splitlines():
        m = HEAD.match(line)
        if m:
            if cur:
                entries.append(cur)
            cur = [m.group(1).lower(), m.group(2).strip(), []]
        elif cur is not None:
            cur[2].append(line)
    if cur:
        entries.append(cur)
    return entries


def words(s):
    return set(re.findall(r"[a-z0-9]{3,}", s.lower()))


def jaccard(a, b):
    return len(a & b) / len(a | b) if (a | b) else 0.0


def cmd_tags(entries, tags):
    sel = [e for e in entries if not tags or e[0] in tags]
    if not sel:
        print(f"(no learnings for tags: {', '.join(sorted(tags)) or 'all'})")
        return 0
    for tag, title, body in sel:
        print(f"## [{tag}] {title}")
        for ln in body:
            if ln.strip():
                print(ln)
        print()
    return 0


def cmd_lint(entries, entry):
    lines = entry.strip().splitlines()
    m = HEAD.match(lines[0]) if lines else None
    if not m:
        print("LINT: FAIL")
        print("  format: missing a '## [tag] Title' heading on the first line")
        return 1

    fmt = []
    tag = m.group(1).lower()
    if tag not in TAGS:
        fmt.append(f"unknown tag [{tag}] (use {sorted(TAGS)})")
    for key in ("Context", "Insight", "Source"):
        if not re.search(rf"^-\s*{key}:", entry, re.M):
            fmt.append(f"missing '- {key}:' line")

    markers = [f"{label}: '{mm.group(0)}'" for rx, label in MARKERS for mm in rx.finditer(entry)]

    bw = words(entry)
    best = (0.0, None)
    for _, title, body in entries:
        sim = jaccard(bw, words(title + " " + " ".join(body)))
        if sim > best[0]:
            best = (sim, title)

    status = "PASS" if not fmt and not markers and best[0] < 0.4 else "WARN"
    print(f"LINT: {status}")
    print(f"  format: {'ok' if not fmt else '; '.join(fmt)}")
    print(f"  instance-markers: {'none' if not markers else '; '.join(markers)}")
    print(f"  nearest existing: " + (f'"{best[1]}" (similarity {best[0]:.2f})' if best[1] else "none"))
    if markers:
        print("  -> strip the instance-specific bits above; keep only the transferable rule.")
    if best[0] >= 0.4:
        print("  -> likely overlaps an existing entry; merge rather than add.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Read or lint the cross-job learnings store.")
    ap.add_argument("--tags", help="comma-separated tags to print")
    ap.add_argument("--lint", action="store_true")
    ap.add_argument("--entry", help="proposed entry text (else read stdin)")
    ap.add_argument("--file", default=DEFAULT)
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    try:
        with open(args.file, encoding="utf-8") as f:
            entries = parse(f.read())
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.lint:
        entry = args.entry if args.entry is not None else sys.stdin.read()
        return cmd_lint(entries, entry)
    tags = {t.strip().lower() for t in args.tags.split(",")} if args.tags else set()
    return cmd_tags(entries, tags)


if __name__ == "__main__":
    sys.exit(main())
