"""
validate_json.py - validate a JSON instance against a JSON Schema (Draft 2020-12).

Usage:
    python validate_json.py <schema.json> <instance.json>
        [--max-errors N] [--counts] [--json]

Exit code: 0 = valid, 1 = validation errors, 2 = usage / IO error.
Zero AI tokens - pure jsonschema.
"""
import argparse
import json
import sys


def _counts(doc):
    """Best-effort structural counts for a quick sanity check."""
    out = {}
    if isinstance(doc, list):
        out["root[]"] = len(doc)
    elif isinstance(doc, dict):
        for k, v in doc.items():
            if isinstance(v, list):
                out[k] = len(v)
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Validate a JSON instance against a Draft 2020-12 schema."
    )
    ap.add_argument("schema")
    ap.add_argument("instance")
    ap.add_argument("--max-errors", type=int, default=50)
    ap.add_argument("--counts", action="store_true", help="print top-level array counts")
    ap.add_argument("--json", action="store_true", dest="as_json", help="machine-readable output")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("ERROR: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
        return 2

    try:
        with open(args.schema, encoding="utf-8") as f:
            schema = json.load(f)
        with open(args.instance, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    # Validate the schema itself is well-formed before using it.
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as e:
        print(f"ERROR: schema is not a valid Draft 2020-12 schema: {e}", file=sys.stderr)
        return 2

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))

    result = {
        "schema": args.schema,
        "instance": args.instance,
        "valid": len(errors) == 0,
        "error_count": len(errors),
        "errors": [
            {
                "path": "/" + "/".join(str(p) for p in e.absolute_path),
                "message": e.message,
            }
            for e in errors[: args.max_errors]
        ],
    }
    if args.counts:
        result["counts"] = _counts(doc)

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Schema:   {args.schema}")
        print(f"Instance: {args.instance}")
        print(f"Valid: {result['valid']}  (errors: {result['error_count']})")
        for e in result["errors"]:
            print(f"  [{e['path']}] {e['message'][:160]}")
        if len(errors) > args.max_errors:
            print(f"  ... and {len(errors) - args.max_errors} more")
        if args.counts:
            print("Counts:")
            for k, v in result["counts"].items():
                print(f"  {k}: {v}")

    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
