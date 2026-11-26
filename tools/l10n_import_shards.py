#!/usr/bin/env python3
"""Safely validate and import Codex polish shard CSVs (id,lang,ko,old,new,notes)
into tm_id.csv / review_audit.csv (VI) and en_id.csv (EN), then rebuild & validate."""
import argparse
import csv
import subprocess
import sys
from pathlib import Path

import l10n_style_audit as SA

ROOT = SA.ROOT
L10N = SA.L10N


def read_csv_dict(path, key):
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return list(rows[0].keys()) if rows else [], {r[key]: r for r in rows}


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("shards", nargs="+", type=Path)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-rebuild", action="store_true")
    args = p.parse_args()

    vi_map = {r["id"]: r for r in SA.load_rows(L10N / "catalog.csv")}
    en_map = {r["id"]: r for r in SA.load_rows(L10N / "catalog_en.csv")}
    exempt_nl = {(r["id"], r["lang"]) for r in SA.load_rows(L10N / "newline_exempt.csv")}

    tm_fields, tm_id = read_csv_dict(L10N / "tm_id.csv", "id")
    aud_fields, audit = read_csv_dict(L10N / "review_audit.csv", "id")
    en_fields, en_id = read_csv_dict(L10N / "en_id.csv", "id")
    if not en_fields:
        en_fields = ["id", "en", "notes"]

    accepted_vi = accepted_en = 0
    rejected = []
    for sp in args.shards:
        rows = SA.load_rows(sp)
        for idx, r in enumerate(rows, 2):
            err = SA.validate_candidate(r, vi_map, en_map, exempt_nl)
            if err:
                rejected.append((sp.name, idx, r.get("id", ""), err))
                continue
            rid = r["id"]
            lang = r["lang"].strip()
            new = r["new"]
            note = (r.get("notes") or "").strip() or f"polish-95 ({sp.stem})"
            if lang == "vi":
                cur = vi_map[rid]
                if new == cur["vi"] and cur["status"] == "translated":
                    continue
                prev = tm_id.get(rid)
                prev_notes = prev["notes"] if prev else cur.get("notes", "")
                if "quiz_vi_localized" in prev_notes:
                    note = f"{prev_notes};{note}"
                elif "ko_reviewed" not in note:
                    note = f"ko_reviewed;{note}"
                tm_id[rid] = {
                    "id": rid,
                    "vi": new,
                    "status": "translated",
                    "notes": note,
                }
                if rid in audit:
                    audit[rid]["vi_after"] = new
                    audit[rid]["status"] = "translated"
                accepted_vi += 1
            else:
                cur = en_map[rid]
                if new == cur["en"] and cur["en_status"] == "manual":
                    continue
                en_id[rid] = {"id": rid, "en": new, "notes": note}
                accepted_en += 1

    print(
        f"Summary: accepted_vi={accepted_vi}, accepted_en={accepted_en}, rejected={len(rejected)}"
    )
    for fname, lno, rid, err in rejected[:30]:
        print(f"  REJECT {fname}:L{lno} {rid}: {err}")

    if args.dry_run:
        return 0

    write_csv(L10N / "tm_id.csv", tm_fields, tm_id.values())
    write_csv(L10N / "review_audit.csv", aud_fields, audit.values())
    write_csv(L10N / "en_id.csv", en_fields, en_id.values())

    if not args.no_rebuild:
        for cmd in (
            [sys.executable, "tools/l10n_extract.py", "catalog"],
            [sys.executable, "tools/l10n_extract_en.py"],
            [sys.executable, "tools/l10n_validate.py"],
            [sys.executable, "tools/l10n_style_audit.py"],
        ):
            subprocess.run(cmd, cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
