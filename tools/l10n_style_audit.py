#!/usr/bin/env python3
"""Audit VI (Southern style) and EN quality on catalog.csv / catalog_en.csv,
export targeted shards for polish, and validate candidate shard CSV outputs."""
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

import l10n_extract as L
import l10n_extract_en as EN
import l10n_validate as V

ROOT = Path(__file__).resolve().parent.parent
L10N = ROOT / "l10n"

HANGUL = re.compile(r"[\uac00-\ud7a3\u3131-\u318e]")
EMOTICON_STRIP = re.compile(r"[ㅠㅎㅜㅋㅇㅁ]+")

VI_GUI = re.compile(r"\bgửi\b", re.I)
VI_NGUOI_PR = re.compile(r"\bngươi\b", re.I)
VI_PRONOUN = re.compile(r"\b(cậu|ạ|vâng)\b", re.I)
VI_EN_CHAR = re.compile(
    r"\b(Bazzi|Dao|Marid|Dizni|Diz|Kephi|Ethi|Mos|Uni)\b"
)
VI_ROBOTIC = re.compile(
    r"\b(vui lòng|đã được|tiến hành|thực hiện|sử dụng|người chơi)\b|(?:^|[.!?]\s*)Hãy\b",
    re.I,
)

EN_WRONG_CHAR = re.compile(
    r"\b(Bazzi|Marid|Dizni|Kephi|Ethi|Mos|Uni)\b"
)
EN_LUXURY_CHAR = re.compile(
    r"\bLuxury\s+(Evie|Plunk|Dao|Melvin|Moss|Diz|Sue|Hoou|Ray|Lucy|Marid|Kephi|Ethi|Mos|Dizni)\b"
)
EN_BAD_MT = re.compile(
    r"Destroyed by Power|cosmetic Items|\bWater Bomb\b|\b(?:Luzi|Rucci)\b|(?<!\w) \bitem\b(?=[.!?,\s]|$)",
)
EN_ROBOTIC = re.compile(
    r"(?:^|[.!?]\s*)Please\b|\bPlease try again\b|\bIt is possible\b|\bIt is not possible\b|\bThere is no\b",
    re.I,
)

CORE_SOURCES = {
    "csysstr.ssd",
    "FxDesktop/ClientData/ClientString",
    "csysstr.ssd+FxDesktop/ClientData/ClientString",
    "csysfxmg.ssd",
    "FxDesktop/Help/Help",
    "channel2_001.ssd",
    "multisvr.ssd",
    "fx/ObjectTable/SpeakerTable",
    "design:boom-rs/KR-00967-V1-scope-1",
    "vn-only:fx/ClientData/ClientString",
}


def load_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def has_non_emoticon_hangul(text):
    return bool(HANGUL.search(EMOTICON_STRIP.sub("", text or "")))


def is_core_source(src):
    return (
        src in CORE_SOURCES
        or src.startswith("FxDesktop/Quest/")
        or src.startswith("FxMap/Map/")
        or src.startswith("spcc.ssd")
    )


def vi_reasons(row):
    vi = row.get("vi", "")
    src = row.get("source", "")
    status = row.get("status", "")
    reasons = []
    if V.BAN.search(vi):
        reasons.append(f"ban:{V.BAN.search(vi).group()}")
    if VI_GUI.search(vi):
        reasons.append("gui")
    if VI_NGUOI_PR.search(vi):
        reasons.append("nguoi_pronoun")
    if VI_PRONOUN.search(vi):
        reasons.append(f"pronoun:{VI_PRONOUN.search(vi).group().lower()}")
    if (
        src != "FxStage/StageCredit/Credit"
        and status != "review"
        and not row["id"].startswith("exe:")
        and has_non_emoticon_hangul(vi)
    ):
        reasons.append("hangul_stray")
    if not row["id"].endswith("_CmdMsg") and "/" not in vi and VI_EN_CHAR.search(vi):
        reasons.append(f"en_char:{VI_EN_CHAR.search(vi).group()}")
    if status == "reused":
        reasons.append("reused")
    if VI_ROBOTIC.search(vi):
        reasons.append("robotic")
    return reasons


def en_reasons(row):
    ko = row.get("ko", "")
    en = row.get("en", "")
    src = row.get("source_kr", "")
    st = row.get("en_status", "")
    notes = row.get("en_notes", "")
    reasons = []
    is_particle = row["id"].startswith("q:FindDracula_EndingWord") or row["id"] == "Object"
    if HANGUL.search(ko) and not en.strip():
        if src != "exe:kr-full.exe" and not is_particle and "empty_on_purpose" not in notes:
            reasons.append("en_empty_han")
        return reasons
    if not en.strip():
        return reasons
    if not EN.formatting(ko, en):
        reasons.append("format_err")
    if src != "FxStage/StageCredit/Credit" and src != "exe:kr-full.exe" and has_non_emoticon_hangul(en):
        reasons.append("hangul_stray")
    if not row["id"].endswith("_CmdMsg") and not en.strip().startswith("/") and EN_WRONG_CHAR.search(en):
        reasons.append(f"wrong_char:{EN_WRONG_CHAR.search(en).group()}")
    if EN_LUXURY_CHAR.search(en):
        reasons.append("luxury_char")
    if EN_BAD_MT.search(en):
        reasons.append("bad_mt")
    if st == "machine" and EN_ROBOTIC.search(en):
        reasons.append("robotic_please")
    return reasons


def audit():
    vi_rows = load_rows(L10N / "catalog.csv")
    en_rows = load_rows(L10N / "catalog_en.csv")
    vi_counts = Counter()
    en_counts = Counter()
    for r in vi_rows:
        for tag in vi_reasons(r):
            vi_counts[tag.split(":")[0]] += 1
    for r in en_rows:
        for tag in en_reasons(r):
            en_counts[tag.split(":")[0]] += 1
    return {
        "vi_total": len(vi_rows),
        "vi_issues": dict(sorted(vi_counts.items())),
        "en_total": len(en_rows),
        "en_statuses": dict(Counter(r["en_status"] for r in en_rows)),
        "en_issues": dict(sorted(en_counts.items())),
    }


def write_shard(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id", "source", "ko", "vi", "en", "status", "reason"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def export_shards(out_dir):
    vi_rows = {r["id"]: r for r in load_rows(L10N / "catalog.csv")}
    en_rows = load_rows(L10N / "catalog_en.csv")
    en_by_id = {r["id"]: r for r in en_rows}

    vi_core, vi_quests = [], []
    for r in vi_rows.values():
        if r["source"] == "FxStage/StageCredit/Credit" or r["status"] == "review":
            continue
        reasons = vi_reasons(r)
        if not reasons:
            continue
        en_val = en_by_id.get(r["id"], {}).get("en", "")
        rec = {
            "id": r["id"],
            "source": r["source"],
            "ko": r["ko"],
            "vi": r["vi"],
            "en": en_val,
            "status": r["status"],
            "reason": ";".join(reasons),
        }
        hard = any(
            k.startswith(("ban", "gui", "nguoi_pronoun", "pronoun", "hangul_stray", "en_char"))
            or k == "reused"
            for k in reasons
        )
        if hard or is_core_source(r["source"]):
            vi_core.append(rec)
        else:
            vi_quests.append(rec)

    en_core, en_quests = [], []
    for r in en_rows:
        src = r["source_kr"]
        if src == "FxStage/StageCredit/Credit" or src == "exe:kr-full.exe":
            continue
        reasons = en_reasons(r)
        if not reasons:
            continue
        rec = {
            "id": r["id"],
            "source": src,
            "ko": r["ko"],
            "vi": r["vi"],
            "en": r["en"],
            "status": r["en_status"],
            "reason": ";".join(reasons),
        }
        if is_core_source(src) or "en_empty_han" in reasons or "wrong_char" in ";".join(reasons) or "hangul_stray" in reasons:
            en_core.append(rec)
        else:
            en_quests.append(rec)

    out = Path(out_dir)
    write_shard(out / "vi_core.csv", vi_core)
    write_shard(out / "vi_quests_items.csv", vi_quests)
    write_shard(out / "en_missing_ui.csv", en_core)
    write_shard(out / "en_quests_stock.csv", en_quests)
    print(
        f"Exported shards to {out}: "
        f"vi_core={len(vi_core)}, vi_quests_items={len(vi_quests)}, "
        f"en_missing_ui={len(en_core)}, en_quests_stock={len(en_quests)}"
    )


def validate_candidate(row, vi_map, en_map, exempt_nl):
    i = row.get("id", "")
    lang = row.get("lang", "").strip()
    ko = row.get("ko", "")
    new = row.get("new", "")
    if lang not in ("vi", "en"):
        return f"invalid lang {lang!r}"
    ref_map = vi_map if lang == "vi" else en_map
    ref = ref_map.get(i)
    if not ref:
        return "unknown id"
    if ref["ko"] != ko:
        return "ko mismatch"
    if not new.strip():
        return "empty new translation"
    if lang == "vi":
        if V.BAN.search(new):
            return f"banned word: {V.BAN.search(new).group()}"
        if VI_GUI.search(new):
            return "uses gửi instead of gởi"
        if VI_NGUOI_PR.search(new):
            return "uses ngươi pronoun"
        if VI_PRONOUN.search(new):
            return f"forbidden pronoun/particle: {VI_PRONOUN.search(new).group()}"
        if not i.endswith("_CmdMsg") and "/" not in new and VI_EN_CHAR.search(new):
            return f"stray EN character: {VI_EN_CHAR.search(new).group()}"
        if has_non_emoticon_hangul(new) and ref.get("source") != "FxStage/StageCredit/Credit":
            return "stray Hangul in VI"
        ko_sig, vi_sig = V.reviewed_signature(ko), V.reviewed_signature(new)
        if (i, "vi") in exempt_nl or "quiz_vi_localized" in ref.get("notes", ""):
            ko_sig, vi_sig = ko_sig[:3] + ko_sig[4:], vi_sig[:3] + vi_sig[4:]
        if ko_sig != vi_sig:
            return f"signature mismatch ko={ko_sig} vi={vi_sig}"
    else:
        if not EN.formatting(ko, new):
            return "formatting/placeholder/tag mismatch"
        if has_non_emoticon_hangul(new) and ref.get("source_kr") != "FxStage/StageCredit/Credit":
            return "stray Hangul in EN"
        if not i.endswith("_CmdMsg") and not new.strip().startswith("/") and EN_WRONG_CHAR.search(new):
            return f"non-PopTag char: {EN_WRONG_CHAR.search(new).group()}"
        if EN_LUXURY_CHAR.search(new):
            return "Luxury before PopTag char instead of Posh"
        if "Destroyed by Power" in new or "cosmetic Items" in new or re.search(r"\bWater Bomb\b", new):
            return "known MT error preserved"
    return None


def check_shard(shard_path):
    vi_map = {r["id"]: r for r in load_rows(L10N / "catalog.csv")}
    en_map = {r["id"]: r for r in load_rows(L10N / "catalog_en.csv")}
    exempt_nl = {
        (r["id"], r["lang"])
        for r in load_rows(L10N / "newline_exempt.csv")
    }
    rows = load_rows(Path(shard_path))
    ok = 0
    bad = []
    for idx, r in enumerate(rows, 2):
        err = validate_candidate(r, vi_map, en_map, exempt_nl)
        if err:
            bad.append((idx, r.get("id", ""), err))
        else:
            ok += 1
    print(f"Shard {shard_path}: total={len(rows)}, ok={ok}, rejected={len(bad)}")
    for line_no, rid, err in bad[:20]:
        print(f"  L{line_no} {rid}: {err}")
    return len(bad)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true")
    p.add_argument("--export-shards", type=Path)
    p.add_argument("--check-shard", type=Path)
    args = p.parse_args()
    if args.check_shard:
        rc = check_shard(args.check_shard)
        raise SystemExit(1 if rc else 0)
    summary = audit()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.export_shards:
        export_shards(args.export_shards)


if __name__ == "__main__":
    main()
