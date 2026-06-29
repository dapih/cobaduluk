"""
promote_family.py - bless a finished job as a reusable family (manual promotion).

Creates or extends families/<name>/ with the job's structural fingerprint and a
copy of its schema as the family canonical, so future same-family tables can be
matched (match_profile.py) and warm-started. Deterministic; zero AI tokens.

Medium tier (design/reuse.md):
  - each member stores its own fingerprint; the family match vector is the
    CENTROID (mean) of member vectors, so matching improves as a family grows;
  - the canonical schema is VERSIONED; members record the version they were
    built against; `--evolve` adopts this job's schema as a new canonical version.

Usage:
    python promote_family.py <job-id> --name <family> [--docs docs]
        [--families families] [--force] [--evolve]

  (no flag)  create a new family from this job (canonical = its schema, v1)
  --force    add this job as a member of an existing family (canonical kept)
  --evolve   (with --force) also adopt this job's schema as the new canonical,
             bumping canonical_version

Reads docs/<job-id>/<job-id>.inspect.json and .schema.json.
Exit: 0 = promoted, 2 = usage / IO error.
"""
import argparse
import datetime
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fingerprint import load_report, fingerprint  # noqa: E402


def centroid(vectors):
    """Element-wise mean of equal-length vectors."""
    if not vectors:
        return []
    n, dim = len(vectors), len(vectors[0])
    return [round(sum(v[i] for v in vectors) / n, 6) for i in range(dim)]


def member_vectors(fam, docs_dir):
    """Vectors for every member, backfilling a missing fingerprint from the
    member's inspect.json (older families stored none per-member)."""
    vecs = []
    for m in fam["members"]:
        fp = m.get("fingerprint")
        if not fp:
            insp = os.path.join(docs_dir, m["job_id"], m["job_id"] + ".inspect.json")
            if os.path.isfile(insp):
                fp = fingerprint(load_report(insp))
                m["fingerprint"] = fp  # backfill in place
        if fp:
            vecs.append(fp["vector"])
    return vecs


def main():
    ap = argparse.ArgumentParser(description="Promote a finished job to a reusable family.")
    ap.add_argument("job_id")
    ap.add_argument("--name", required=True, help="family name (kebab-case)")
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--families", default="families")
    ap.add_argument("--force", action="store_true", help="add this job to an existing family")
    ap.add_argument("--evolve", action="store_true",
                    help="with --force: adopt this job's schema as a new canonical version")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    job_dir = os.path.join(args.docs, args.job_id)
    inspect = os.path.join(job_dir, args.job_id + ".inspect.json")
    schema = os.path.join(job_dir, args.job_id + ".schema.json")
    parser = os.path.join(job_dir, args.job_id + ".parser.py")
    for p in (inspect, schema):
        if not os.path.isfile(p):
            print(f"ERROR: missing {p} - run inspect/schema for this job first.", file=sys.stderr)
            return 2

    try:
        fp = fingerprint(load_report(inspect))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    fam_dir = os.path.join(args.families, args.name)
    fam_json = os.path.join(fam_dir, "family.json")
    canonical = os.path.join(fam_dir, "family.schema.json")
    today = datetime.date.today().isoformat()
    # Store member paths relative to the project root (families' parent) so a
    # committed family.json stays portable regardless of how --docs was passed.
    proj_root = os.path.dirname(os.path.abspath(args.families))

    def rel(p):
        return os.path.relpath(os.path.abspath(p), proj_root).replace("\\", "/")

    member = {
        "job_id": args.job_id,
        "schema": rel(schema),
        "parser": rel(parser) if os.path.isfile(parser) else None,
        "added": today,
        "fingerprint": fp,
    }

    if os.path.isfile(fam_json):
        if not args.force:
            print(f"ERROR: family '{args.name}' already exists. Use --force to add this job to it "
                  "(add --evolve to also make it the new canonical).", file=sys.stderr)
            return 2
        with open(fam_json, encoding="utf-8") as f:
            fam = json.load(f)
        if any(m["job_id"] == args.job_id for m in fam["members"]):
            print(f"Job {args.job_id} is already a member of '{args.name}'. Nothing to do.")
            return 0
        if args.evolve:
            fam["canonical_version"] = fam.get("canonical_version", 1) + 1
            fam["canonical_source"] = args.job_id
            shutil.copyfile(schema, canonical)
            member["built_against"] = fam["canonical_version"]
            note = (f"Evolved '{args.name}' canonical to v{fam['canonical_version']} "
                    f"and added {args.job_id}")
        else:
            member["built_against"] = fam.get("canonical_version", 1)
            note = (f"Added {args.job_id} to '{args.name}' "
                    f"(canonical v{fam.get('canonical_version', 1)} unchanged)")
        fam["members"].append(member)
    else:
        if args.evolve:
            print("Note: --evolve ignored when creating a new family (this job IS the v1 canonical).")
        os.makedirs(fam_dir, exist_ok=True)
        member["built_against"] = 1
        fam = {
            "name": args.name,
            "created": today,
            "canonical_version": 1,
            "canonical_source": args.job_id,
            "canonical_schema": "family.schema.json",
            "members": [member],
        }
        shutil.copyfile(schema, canonical)
        note = f"Created family '{args.name}'"

    # Family match vector = centroid of all member vectors (medium tier).
    vecs = member_vectors(fam, args.docs)
    fam["fingerprint"] = {"vector": centroid(vecs), "n_members": len(fam["members"])}

    with open(fam_json, "w", encoding="utf-8") as f:
        json.dump(fam, f, ensure_ascii=False, indent=2)

    print(note)
    print(f"  store:     {fam_dir.replace(chr(92), '/')}/")
    print(f"  canonical: {canonical.replace(chr(92), '/')}  (v{fam['canonical_version']})")
    print(f"  members:   {len(fam['members'])}")
    print(f"  centroid:  {[round(x, 3) for x in fam['fingerprint']['vector']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
