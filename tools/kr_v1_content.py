"""Fingerprint selected V1 resources and probe Village00 metadata, without running KR.

This is not a complete map loader or a transitive render dependency resolver.
"""
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

import idf


REQUIRED = {
    "map": "FxMap/Map/Village00",
    "preview": "FxMap/Etc/Village00_mm",
    "theme": "FxMap/Theme/Village",
    "music": "FxSound/MP3/Village",
    "character_attr": "FxContents/Attr/BomberAttr",
    "item_attr": "FxContents/Attr/ItemAttr",
    "bomb_item": "fx/Item/Bomb",
    "fire_item": "fx/Item/Fire",
    "speed_item": "fx/Item/Roller",
    "bomb_art": "FxDesktop/Bomb/Bomb00",
    "explosion_art": "FxDesktop/Bomb/BombExplosion001",
    "room_create": "FxStage/Lobby/LB_Bt_T_Create-NM",
    "room_create_dialog": "FxStage/Lobby/Dlg_LB-NMCreate",
    "ready": "FxMap/Prepare/PRE_Bt_Ready",
    "start": "FxMap/Prepare/PRE_Bt_Start",
}


def main():
    root = Path(sys.argv[1])
    out = Path(sys.argv[2])
    selected, raw_map = [], None
    seen = set()
    character = re.compile(r"^FxCharacter/Character/C0[01]-")
    for path in sorted(root.glob("*.idx")):
        raw = path.read_bytes()
        _, records, end = idf.parse_idx(idf.decrypt_idx(raw, struct.unpack_from("<I", raw)[0]))
        if end != len(raw):
            raise ValueError(f"index tail: {path}")
        with path.with_suffix(".idd").open("rb") as stream:
            for name, offset, size, key, crc in records:
                entry = path.stem + "/" + name.replace("\\", "/")
                if entry not in REQUIRED.values() and not character.search(entry):
                    continue
                stream.seek(offset)
                blob = idf.unpack_entry(name, stream.read(size), key, crc)
                seen.add(entry)
                selected.append(dict(entry=entry, bytes=len(blob),
                                     sha256=hashlib.sha256(blob).hexdigest(),
                                     role=next((k for k, v in REQUIRED.items() if v == entry),
                                               "character_family_resource")))
                if entry == REQUIRED["map"]:
                    raw_map = blob
    missing = set(REQUIRED.values()) - seen
    for char in ("C00", "C01"):
        for direction in ("Up", "Down", "Left", "Right"):
            for layer in ("Static", "Adjust"):
                name = f"FxCharacter/Character/{char}-Walk{direction}_ALayer{layer}"
                if name not in seen:
                    missing.add(name)
    if missing:
        raise ValueError(f"missing selected resources: {sorted(missing)}")
    version, _, _, width, height, spawn_count = struct.unpack_from("<6I", raw_map)
    spawns = [list(struct.unpack_from("<2I", raw_map, 80 + i * 8)) for i in range(spawn_count)]
    if version != 1000 or (width, height, spawn_count) != (15, 13, 4):
        raise ValueError("unexpected Village00 header")
    if len({tuple(p) for p in spawns}) != 4 or any(x >= width or y >= height for x, y in spawns):
        raise ValueError("invalid selected map spawn coordinates")
    off = 80 + spawn_count * 8
    rect_count = struct.unpack_from("<I", raw_map, off)[0]
    if rect_count:
        raise ValueError("unexpected Village00 rect metadata")
    off += 4 + width * height * 8
    count = struct.unpack_from("<I", raw_map, off)[0]
    off += 4
    drops = []
    for _ in range(count):
        size = struct.unpack_from("<I", raw_map, off)[0]
        off += 4
        name = raw_map[off:off + size].decode("cp949")
        off += size
        weight = struct.unpack_from("<I", raw_map, off)[0]
        off += 4
        drops.append(dict(name=name, weight=weight))
    tail = list(struct.unpack("<" + "I" * ((len(raw_map) - off) // 4), raw_map[off:]))
    result = dict(schema=1, baseline="KR-00967-V1-scope-1", required=REQUIRED,
                  selected_resources=selected,
                  map_probe=dict(version=version, width=width, height=height,
                                 coordinate_offset=80, spawn_coordinates=spawns,
                                 native_drop_table=drops, trailing_dwords=tail,
                                 contains_mapscript_marker=b"<mapscript" in raw_map.lower()),
                  policy=dict(mode="battle_ffa", player_min=2, player_max=4,
                              characters=["C00", "C01"], item_allowlist=["Bomb", "Fire", "Roller"],
                              drop_source="DESIGN_V1_OVERRIDE_NOT_NATIVE_VILLAGE00"),
                  limitations=["Metadata probe only; tile/object collision and script consumer unresolved.",
                               "Dependencies not transitively resolved; not a shippable asset bundle.",
                               "Character family includes unused states; selection does not enable them.",
                               "Native coin drop table is preserved as evidence; V1 drops deliberately differ."])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(selected)} selected resources fingerprinted; Village00 metadata and required walks validated")


if __name__ == "__main__":
    main()
