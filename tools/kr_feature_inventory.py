"""Build a provisional KR feature index from pack entry names, without running CA.exe.

Name matches are resource signals, not proof of implemented/reachable functionality.
Uses the existing idf reader; does not decrypt payloads or decompile executable code.
"""
import argparse
import csv
import hashlib
import json
import re
import struct
from collections import Counter
from pathlib import Path

import idf


# ID, question/group, regex over pack/entry, next verification question.
GROUPS = [
    ("KR-F001", "Đăng nhập/chọn server", r"/LoginStage/|/SelectServerStage/|/MultiServer/|/SpecialLogin/", "Luồng login KR và phần nào được thay bằng auth mới?"),
    ("KR-F002", "Sảnh/quảng trường", r"/LobbySquare/|/TileLobbySquare/|/Square/", "Màn nào truy cập được, state và thao tác gì?"),
    ("KR-F003", "Ghép trận/phòng", r"/UXMatching/|/Prepare/", "Create/join/ready/start, quyền chủ phòng và giới hạn người?"),
    ("KR-F004", "Trận Battle/bom", r"/Bomb/|/Game/.*(?:Bomb|Battle)", "Di chuyển, va chạm, fuse, nổ dây chuyền và điều kiện kết thúc?"),
    ("KR-F005", "Chọn nhân vật", r"/CharacterSelect(?:All)?/", "Danh sách nhân vật, chỉ số và điều kiện mở khóa?"),
    ("KR-F006", "Shop", r"^FxStage/Shop/", "Mua/tặng/thử, tiền tệ và transaction server?"),
    ("KR-F007", "Hồ sơ/túi đồ", r"/MyInfo/|/RPGMyInfo/", "Tách hồ sơ khỏi inventory và quy tắc equip?"),
    ("KR-F008", "Chat/whisper", r"/Chatting/|/WhisperLog/|/Speaker/", "Kênh chat, whisper, lọc và quyền gửi?"),
    ("KR-F009", "Guild", r"/Guild/", "Thành lập, thành viên, quyền và hoạt động guild?"),
    ("KR-F010", "Couple/bạn bè", r"/CoupleWnd_|/NM/|/MyInfo/.*Friend", "Phân biệt messenger, couple và friend; server giữ gì?"),
    ("KR-F011", "Quest/nhiệm vụ ngày", r"/Quest/|/DailyMission/", "Trigger, tiến độ, reset và phát thưởng?"),
    ("KR-F012", "CAPass", r"/CAPass/", "Tên hệ thống thực, nhiệm vụ và reward track của build này?"),
    ("KR-F013", "Ladder/rating", r"/WeeklyLadder/|/Ladder/|/UXCAJJangRatingMark/", "Tách các ladder, matchmaking và quy tắc điểm?"),
    ("KR-F014", "Magic Market", r"/MagicMarket/|/Dialog/Mix_", "Recipe/probability theo build; liên hệ với Alchemist có được xác nhận?"),
    ("KR-F015", "Câu cá", r"/FishingDeco/|/FishTrade/|/Icon/Fishing", "Bait/rod, xác suất, trao đổi và phần thưởng?"),
    ("KR-F016", "Pet", r"/Pet/|/PetRandomTable", "Định dạng bảng và tác dụng pet trong từng mode?"),
    ("KR-F017", "Tutorial", r"^FxStage/Tutorial/", "Bài hướng dẫn và điều kiện hoàn thành?"),
    ("KR-F018", "HiddenCatch", r"^FxHiddenCatch/", "Thế hệ mode, luật và map nào còn hoạt động?"),
    ("KR-F019", "AI Battle", r"/AIBattle/|/Game/AIBattle", "AI, difficulty, điều kiện thắng và reward?"),
    ("KR-F020", "Airplane", r"/Bonus/Airplane|/Game/Airplane", "Bonus hay mode độc lập; input/va chạm/thắng?"),
    ("KR-F021", "Baseball", r"/.*Baseball", "State bóng, ghi điểm, respawn và luật đội?"),
    ("KR-F022", "BigBattle", r"/.*BigBattle", "Số người, ghép trận, bản đồ và luật riêng?"),
    ("KR-F023", "RPG/CAHero", r"/RPG/|/CAHero/|/Map/CAhero", "Tách mode, nghề, tiến trình và map scripts?"),
    ("KR-F024", "Monster/campaign", r"^FxMonster/|/Map/Mon|/MapScriptTemplate/MonInfo", "AI, collision, spawn, stage clear và reward server?"),
    ("KR-F025", "SandBox", r"/SandBox/", "Chức năng thực: tạo/chia sẻ map, giới hạn và moderation?"),
    ("KR-F026", "DIYBomb", r"/DIYBomb/", "Chức năng thực và dữ liệu tùy biến bom?"),
    ("KR-F027", "ConfusedFight", r"/ConfusedFight/", "Tên hiển thị, luật, ranking và khác biệt Battle?"),
    ("KR-F028", "IamBoss", r"/IamBoss/", "State boss/player, luật và quyền server?"),
    ("KR-F029", "SnowyChamp/Antarctic", r"/SnowyChamp/|/Antarctic/", "Có cùng SnowBall nguồn web không; luật từng nhóm?"),
    ("KR-F030", "MineExplore/IamWriggle", r"/MineExplore/|/IamWriggle/", "Có phải mode độc lập và còn được bật không?"),
    ("KR-F031", "ItemCollection", r"/ItemCollection/", "Điều kiện sưu tập và thưởng?"),
    ("KR-F032", "Event/reward", r"/TakeCareOfEvent/|/InstanceReward/|/LuckyCard/", "Event còn bật, lịch và điều kiện phát thưởng?"),
    ("KR-F033", "Trang phục/trang trí", r"/AvatarDeco/|/CharDeco/|/BombDeco/|/IDDeco/|/Slot/", "Quy tắc layer, equip, ownership và giới hạn từng slot?"),
    ("KR-F034", "Emote/fanfare", r"/Emoticon/|/Fanfare/", "Trigger biểu cảm/hiệu ứng và quyền sở hữu?"),
    ("KR-F035", "Exchange", r"/Exchange/", "UI trao đổi gì; xác nhận, hủy và transaction?"),
    ("KR-F036", "DTT/season shop", r"/DTT/|/DTT_seasonShop/", "Tên hiển thị, pool, tỷ lệ và lịch mùa?"),
    ("KR-F037", "CustomMap/TileCustom", r"/CustomMap/|/TileCustom/|/TileConv/", "Format map tùy biến, chia sẻ và quan hệ với SandBox?"),
    ("KR-F038", "MonWars", r"/MonWars/", "Mode hay event, luật và điều kiện truy cập?"),
    ("KR-F039", "Partners", r"/Partners/|/TilePartners(?:_Ground)?/", "Đối tác/NPC/theme hay mode độc lập?"),
    ("KR-F040", "GreenPC", r"/GreenPC/", "Tín hiệu/trạng thái bảo mật nào; phần nào còn cần cho sản phẩm mới?"),
    ("KR-F041", "PC-room benefits", r"/PCRoomBenefit/", "Điều kiện cấp quyền/lợi ích; không suy từ client thành xác thực server?"),
    ("KR-F042", "MissionPong/CAMission/GrowSprout", r"/MissionPong/|/CAMission/|/GrowSprout/", "Tách từng event và luật/tiến độ/reset?"),
    ("KR-F043", "Tùy chọn/help/notice", r"/GlobalUI/|/Help/|/NoticeImg/|/Dialog/.*(?:Option|Setting)", "Chức năng nào bắt buộc V1; văn bản nào phải thay cho dự án?"),
    ("KR-F044", "Kết quả/vòng đời trận", r"/StageClear/|/StageCredit/|/Game/.*(?:Result|Win|Lose|Draw|Time)", "Kết quả, chuyển màn, reset và phần thưởng do đâu quyết?"),
    ("KR-F045", "Mount/trạng thái đặc biệt", r"/Character/.*Ride|/Item/(?:Turtle|Airship|Owl|Skeleton|MoonWalk|Punch|Shoe)", "Mỗi mount/effect thay collision/input/thời gian ra sao?"),
    ("KR-F046", "Nội dung chiến dịch khác", r"/Captain2/|/WhiteAngel/|/Retro/|/RetroWriggle/|/HoneyButterChip/|/FullMoon/|/bnbolympic/", "Phân loại tutorial, event, theme và mode; không tự coi mọi folder là mode?"),
]


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("client", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--hash-payloads", action="store_true", help="also SHA-256 every .idd")
    args = parser.parse_args()
    root = args.client.resolve()
    packs, entries, top = [], [], Counter()
    for idx in sorted(root.glob("*.idx")):
        raw = idx.read_bytes()
        plain = idf.decrypt_idx(raw, struct.unpack_from("<I", raw)[0])
        version, records, end = idf.parse_idx(plain)
        if end != len(plain):
            raise ValueError(f"unparsed index tail: {idx.name}: {end}/{len(plain)}")
        idd = idx.with_suffix(".idd")
        idd_size = idd.stat().st_size
        for name, off, size, _, _ in records:
            if off + size > idd_size:
                raise ValueError(f"entry out of bounds: {idx.name}/{name}")
            name = name.replace("\\", "/")
            entries.append(f"{idx.stem}/{name}")
            top[(idx.stem, name.split("/")[0])] += 1
        packs.append(dict(pack=idx.stem, index_sha256=digest(idx), version=version,
                          entries=len(records), idd_bytes=idd_size,
                          idd_sha256=digest(idd) if args.hash_payloads else None))
    if not packs:
        raise ValueError("no .idx packs found")
    rows, covered = [], set()
    for feature_id, label, pattern, question in GROUPS:
        regex = re.compile(pattern, re.I)
        matches = sorted(e for e in entries if regex.search(e))
        covered.update(matches)
        rows.append(dict(feature_id=feature_id, feature_group=label,
                         evidence_status="asset_signal" if matches else "no_name_match",
                         match_count=len(matches), evidence_examples=" | ".join(matches[:5]),
                         matcher=pattern, runtime_status="not_verified", next_question=question))
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "kr_feature_candidates.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with (args.out / "kr_asset_groups.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["pack", "top_level_group", "entry_count"])
        writer.writerows((p, g, n) for (p, g), n in sorted(top.items()))
    exe = root / "CA.exe"
    manifest = dict(schema=1, client_exe_sha256=digest(exe) if exe.exists() else None,
                    packs=packs, total_entries=len(entries), candidate_groups=len(rows),
                    matched_entry_paths=len(covered), unmatched_entry_paths=len(set(entries)-covered),
                    limitations=["Name signals only; groups overlap; not feature completeness.",
                                 "Payloads not decoded; IDD hashes only when --hash-payloads is supplied.",
                                 "No executable code analysis or runtime verification."])
    (args.out / "kr_feature_inventory.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ["total_entries", "candidate_groups",
                                             "matched_entry_paths", "unmatched_entry_paths"]}))
    print("groups without matches:", [r["feature_id"] for r in rows if not r["match_count"]])


if __name__ == "__main__":
    main()
