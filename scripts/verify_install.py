"""
verify_install.py - end-to-end install verification for excel-to-json.

Usage:
    python scripts/verify_install.py [--root PATH]

Checks:
  1. Python >= 3.9
  2. Dependencies (openpyxl, jsonschema)
  3. resolve_plugin_root.py
  4. validate_marketplace.py
  5. Sample job artifacts (inspect.json + schema validate)
  6. learnings.py --lint gate (format smoke)

Exit: 0 all pass, 1 failure.
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

SAMPLE_JOB = "table-20260628-1"
LINT_PROBE = """\
## [tooling] install verification probe
- Context: running verify_install.py after clone or release prep
- Insight: the learnings lint gate accepts well-formed entries with engine source
- Source: engine
"""


def plugin_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    return Path(__file__).resolve().parent.parent


def run_script(python: str, script: Path, *args: str) -> None:
    proc = subprocess.run(
        [python, str(script), *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout, end="")
        print(proc.stderr, file=sys.stderr, end="")
        raise RuntimeError(f"{script.name} exited {proc.returncode}")


def check_python() -> None:
    if sys.version_info < (3, 9):
        raise RuntimeError(f"Python 3.9+ required; got {sys.version.split()[0]}")


def check_deps() -> None:
    for name in ("openpyxl", "jsonschema"):
        if importlib.util.find_spec(name) is None:
            raise RuntimeError(f"missing dependency: {name} (pip install -r requirements.txt)")


def check_sample_job(root: Path) -> None:
    job_dir = root / "docs" / SAMPLE_JOB
    inspect_json = job_dir / f"{SAMPLE_JOB}.inspect.json"
    schema = job_dir / f"{SAMPLE_JOB}.schema.json"
    instance = job_dir / f"{SAMPLE_JOB}.json"
    xlsx = job_dir / f"{SAMPLE_JOB}.xlsx"

    if not inspect_json.is_file():
        raise RuntimeError(f"missing sample inspect json: {inspect_json}")

    if xlsx.is_file():
        out_prefix = job_dir / f"{SAMPLE_JOB}.verify"
        run_script(
            sys.executable,
            root / "scripts" / "inspect_xlsx.py",
            str(xlsx),
            "--out",
            str(out_prefix),
        )
        generated = Path(f"{out_prefix}.inspect.json")
        if not generated.is_file():
            raise RuntimeError("inspect_xlsx.py did not produce .inspect.json")
        generated.unlink(missing_ok=True)
        Path(f"{out_prefix}.inspect.md").unlink(missing_ok=True)
    else:
        print(f"  note: no {xlsx.name}; using committed inspect.json only")

    if not schema.is_file() or not instance.is_file():
        raise RuntimeError("sample job missing schema.json or instance.json")

    run_script(
        sys.executable,
        root / "scripts" / "validate_json.py",
        str(schema),
        str(instance),
        "--counts",
    )


def check_learnings_lint(root: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "learnings.py"),
            "--lint",
            "--entry",
            LINT_PROBE,
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout, end="")
        print(proc.stderr, file=sys.stderr, end="")
        raise RuntimeError("learnings.py --lint probe failed")
    if "LINT: FAIL" in proc.stdout:
        raise RuntimeError("learnings lint probe returned FAIL")


def verify(root: Path, project_root: Path | None = None) -> None:
    check_python()
    print("OK  Python", sys.version.split()[0])
    check_deps()
    print("OK  dependencies")
    run_script(sys.executable, root / "scripts" / "resolve_plugin_root.py")
    print("OK  resolve_plugin_root.py")
    validate_args = [sys.executable, str(root / "scripts" / "validate_marketplace.py"), "--root", str(root)]
    if project_root is not None:
        validate_args.extend(["--project-root", str(project_root)])
    proc = subprocess.run(validate_args, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout, end="")
        print(proc.stderr, file=sys.stderr, end="")
        raise RuntimeError("validate_marketplace.py exited {}".format(proc.returncode))
    print(proc.stdout, end="")
    print("OK  validate_marketplace.py")
    check_sample_job(root)
    print(f"OK  sample job {SAMPLE_JOB}")
    check_learnings_lint(root)
    print("OK  learnings.py --lint probe")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify excel-to-json install.")
    parser.add_argument("--root", help="Plugin root (default: parent of scripts/)")
    parser.add_argument("--project-root", help="User project root (nested install)")
    args = parser.parse_args()
    root = plugin_root(args.root)
    proj = Path(args.project_root).resolve() if args.project_root else None
    try:
        verify(root, proj)
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
    print("OK: install verification passed")


if __name__ == "__main__":
    main()
