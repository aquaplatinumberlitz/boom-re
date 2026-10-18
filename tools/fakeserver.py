"""Logging fake server for Boom Online. Stage 0: accept, log everything, optionally send a canned reply.

usage: python3 tools/fakeserver.py [--ports 3838,4848,5858,6868] [--log logs/fakeserver.log]
"""
import argparse, asyncio, datetime, pathlib, struct, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import boomproto as bp

CLIENT_VERSION = 116  # sub_8E2494
HEADER_TYPE = 0       # row of the opcode substitution table, 0..15
ROOM_TYPE = int(__import__('os').environ.get('ROOM_TYPE', '19'))
MAP_INDEX = int(__import__('os').environ.get('MAP_INDEX', '0'))
AUTO_START = float(__import__('os').environ.get('AUTO_START', '0'))  # >0: send opcode 501 N s after entering a room  # room_map(); index into the client's map table  # see create_room_ok(); 14 = 1-player start allowed
TURN_START = float(__import__('os').environ.get('TURN_START', '0'))  # >0: send opcode 189 N s after 501 (TURN_START counts from the 501 moment)
TURN_MODE = int(__import__('os').environ.get('TURN_MODE', '4'))      # mode field of opcode 189 (1/2/4, see oc_e-game.md §5a)
GO_START = float(__import__('os').environ.get('GO_START', '0'))      # >0: send opcode 190 ("GO", sub_70E7D6, sets phase this[5402]=2) N s after 189
BEGIN_START = float(__import__('os').environ.get('BEGIN_START', '0'))  # >0: send opcode BEGIN_OP (191 round begin / 146 round + scores) N s after 190
BEGIN_OP = int(__import__('os').environ.get('BEGIN_OP', '191'))
FLOOR_ITEMS = __import__('os').environ.get('FLOOR_ITEMS', '')  # 'x,y,kind;...' -> 553 list 1 (items lying on the floor)
ITEM_ACK = int(__import__('os').environ.get('ITEM_ACK', '0'))  # 1: answer C->S 117 (item pickup) with S->C 158
ITEMS = __import__('os').environ.get('ITEMS', '')  # 'x,y,kind;...' -> S->C 553 list 2 before 501 (items hidden in bricks)
MATCH_END = float(__import__('os').environ.get('MATCH_END', '0'))  # >0: N s after C->S 120 subtype 13 send 173 (match over -> waiting room)
DEATH_END = float(__import__('os').environ.get('DEATH_END', '0'))  # >0: N s after C->S 120 subtype 13 (death) send 146 (round result)
BOMB_PLACE = int(__import__('os').environ.get('BOMB_PLACE', '0'))  # 1: answer C->S 111 with S->C 152 (bomb confirmed + id)
BOMB_ECHO = float(__import__('os').environ.get('BOMB_ECHO', '0'))  # >0: N s after C->S 111 send S->C 151 (explode) for bomb ids 0..BOMB_IDS-1
BOMB_IDS = int(__import__('os').environ.get('BOMB_IDS', '32'))
BOMB_ARG = int(__import__('os').environ.get('BOMB_ARG', '2'))
POST_PLAY_START = float(__import__('os').environ.get('POST_PLAY_START', '0'))  # >0: send 191 (round begin) N s after 189 mode 0 (ctx0 clock start)
PLAY_START = float(__import__('os').environ.get('PLAY_START', '0'))  # >0: send opcode 189 mode 0 (sub_70E511: phase 3 + resume clock) N s after 190


def hello_packet(header_type=HEADER_TYPE, version=CLIENT_VERSION):
    """First packet from server on every connection (PatchServer_CheckVersion 0x8E426E / Net_OnHandshake 0x999C02).
    Format (0,0): [seq][len u16][type u8 (substituted)][u16 ?][u16 version][u32 header_type][str][u8 flag]."""
    st = bp.SeqState()
    st.header_type = header_type
    seq_byte = ((header_type + st.modif) ^ (st.base_r + st.seq_r)) & 0xFF  # decoded by CheckSeqByte 0xA66030
    body = bytes([0]) + struct.pack(">HHI", 0, version, header_type) + struct.pack(">H", 0) + bytes([0])
    return bp.build(body, hdr_mode=0, cks_mode=0, seq_byte=seq_byte, seq=st.seq_r, header_type=header_type)

SIZES = {"u8": 1, "u16": 2, "u32": 4, "u64": 8}


def obf_body(opcode, *fields):
    """Body for formats with checksum mode 1/2: [opcode u16][fields], every int XOR-obfuscated (put_int obf=True).
    fields: ('u8'|'u16'|'u32'|'u64', value), ('str', text), ('blob', inner) or ('buf', raw bytes: RecvPkt__DecodeBuf,
    same 4/2/1-byte run obfuscation as strings, no length prefix)"""
    out = bp.put_int(opcode, 2, True)
    for kind, v in fields:
        if kind == "str":
            out += bp.put_str(v, True)
        elif kind == "blob":
            out += bp.put_blob(v, True)
        elif kind == "buf":
            out += bp.obf_bytes(bytes(v))
        else:
            out += bp.put_int(v, SIZES[kind], True)
    return out


def login_net_info(host="127.0.0.1", ports=(0, 0, 0)):
    """CLoginStage__On_15 0x84FE35: blob {str host, u16 x3 (-> sub_8E289C), u8 mode (0 none / 1: 2 str / 2: u16), u16}.
    Moves CWaitForLoginDlg from state 2 (set by login_ok) to 1; 10 ticks later the dialog ends with 3 ->
    sub_84FABC -> stage 10 (SelectServer)."""
    h = host.encode()
    inner = struct.pack("<I", len(h)) + h + struct.pack("<HHH", *ports) + bytes([0]) + struct.pack("<H", 0)
    return obf_body(15, ("blob", inner))


def channel_list(names=("Kenh 1", "Kenh 2", "Kenh 3", "Kenh 4"), max_users=100):
    """CStage__On_14 -> sub_99489D: u8 1 = new data (cached by the client), blob {u8 tag, u16 n, n records
    (sub_994663): str name, u32, u8 x7, u16 x2, u8 x4, u32 x2}. tag selects sub_A62580 decoding: 0 = raw copy,
    1 = sub_A0B480-encoded; anything else leaves the sub-reader empty and the client overruns CChannelCache
    (crash in sub_414059).

    sub_994663 stores the record at rec = info + 0x18 + 232*i (S = offset in rec); the getters sub_994xxx read
    info + 232*i + G, so G = S + 0x18. Map (verified in IDA + live gdb on the slot builder sub_85718D):
      u32     S=0x1C G=0x34 sub_994D38  MAX USERS (renderer/sub_857458: channel usable while cur < max)
      u8[0]   S=0x28 G=0x40 sub_994D51  channel type (join sub_856BAC: 0x80/0x82/0xC8; builder mode 0 needs != 0xC8;
                                        renderer: 50..65|70 adds an extra sub_66F4E4 check)
      u8[1]   S=0x34 G=0x4C sub_994A5A  kind: 18 -> reads as 10; builder + click need 10/18
      u8[2]   S=0xD0 G=0xE8 sub_994A9F  category: must == selected tab (0)
      u8[3..6], u16 x2, u8x4[0..2]      not read by the channel screen as far as known
      u8x4[3] S=0xAC G=0xC4 sub_994C91  must be 0 for builder/click
      u32 x2  S=0xB8/0xC4 G=0xD0/0xDC  unknown"""
    inner = b"\x00" + struct.pack("<H", len(names))
    for n in names:
        u8x7 = bytes([0, 18, 0, 0, 0, 0, 0])  # type 0, kind 18, category 0
        inner += _lstr(n) + struct.pack("<I", max_users) + u8x7 + struct.pack("<HH", 0, 0) + bytes(4) + struct.pack("<II", 0, 0)
    return obf_body(14, ("u8", 1), ("blob", inner))


def channel_status(users=(10, 20, 30, 40)):
    """CSelectServerStage__On_16: u8 tag (sub_A62580: 0 = raw) + blob {u16 n, n x (u16, u32)} -> sub_9949C6(i, ..):
    entry i (implicit loop index) = u16 CURRENT USERS -> info+0x3A018+12i (sub_994D7E), u32 STATE -> info+0x3D018+12i
    (sub_994DA3): 1 = online (renderer sub_854E1D draws name + load gauge, else greyed; join check sub_67051F rejects
    0, and 3 is a special refusal). Without the tag the sub-reader stays empty and the client overruns."""
    inner = b"\x00" + struct.pack("<H", len(users))
    for u in users:
        inner += struct.pack("<HI", u, 1)
    return obf_body(16, ("blob", inner))


def channel_join_ok(ip="127.0.0.1", port=3838, kind=10, index=0):
    """Reply to opcode 5 (channel join request from sub_856BAC: bool, u32 index-within-kind sub_994F71).
    CSelectServerStage__On_7 0x8558C4: u8 result (0 = ErrCannotConnect, 2/4/5/11..31 = error strings, 26 = shutdown;
    any other value = success) then u8 kind, u32 channel index within kind, u32 ip, u16 port; ip and port both != 0.
    Stored at stage+0x640C..0x6418; sub_855717 copies them into the connection info (sub_999702), reconnects
    (sub_8F6D35, ip/port in host order -> htonl/htons inside) and sends opcode 6 on the new connection."""
    return obf_body(7, ("u8", 1), ("u8", kind), ("u32", index),
                    ("u32", struct.unpack(">I", bytes(map(int, ip.split("."))))[0]), ("u16", port))


def channel_enter_ok(now=None):
    """Reply to opcode 6 (channel-server login, sub_999FE6). Opcode 17 -> CStage__OnPacket case 15 -> stage vf55;
    CSelectServerStage__vf55 (only when [5915]==2 i.e. after the reconnect) -> CHiddenCatchPrepareStage__vf55 0x69A5F0:
    parse (sub_69A420 / sub_4D7963) then sub_8F391D(.., 11) = LOBBY (20 = square if sub_8DB058).
    Body: SYSTEMTIME (8 x u16), u32, u8 x9, u8 n (<= 6), n x (u32, u32), u8, u8, u8. Meanings mostly unknown."""
    t = now or datetime.datetime.now()
    st = [t.year, t.month, (t.weekday() + 1) % 7, t.day, t.hour, t.minute, t.second, 0]
    f = [("u16", v) for v in st] + [("u32", 0)] + [("u8", 0)] * 9 + [("u8", 0)] + [("u8", 0)] * 3
    return obf_body(17, *f)


def square_info(area=1, map_name="LobbySquare01.map", theme="Square"):
    """Reply to opcode 395 (empty, sent by CLobbySquareStage__vf44 via sub_4D5C25). Opcode 466
    (CLobbySquareStage__On_466 0x4E52B5): u32 area id (stage+5541; -1 = use the channel name only, else title
    "LobbySquare_AreaName%02d"), blob {u8 tag 0, u32 n, n x {u32 m, m x 5 x u32}} (square objects, sub_4E4EFD/sub_4E134C),
    str map file incl. extension (loaded as "Map/%s", assets/fx/Map/; sub_4E1FBE -> sub_4BECBE builds the map object
    at stage+22152, which gates 467/476/477 via sub_4D82DE),
    str theme ("Theme/" + theme, assets/fx/Theme/<theme>), u32 (time offset for the map object, sub_6E2054)."""
    blob = b"\x00" + struct.pack("<I", 0)
    return obf_body(466, ("u32", area), ("blob", blob), ("str", map_name), ("str", theme), ("u32", 0))


def square_users(users=()):
    """Opcode 467 (CLobbySquareStage__On_467 0x4E4100, "OnSquareUserList"): u16 n, n x sub_4E3F29 (u16 slot, then
    sub_4E2D7E user record). At the end the stage sets this[4775] = 1 (square loaded) and sends opcode 396."""
    if users:
        raise NotImplementedError("user record sub_4E2D7E not mapped yet")
    return obf_body(467, ("u16", 0))


def room_list(rooms=()):
    """Opcode 88 (lobby room-list packets dispatched by sub_4D24BB, from CLobbySquareStage__OnPacket /
    CLobbyStage__OnPacket) -> sub_4D0F56: u16 n; if n != 0: blob {n x (u16 session idx, u32 ...) -> sub_6ACBB5}.
    It sets CLobbyRoomUIWnd[+0x4585C] = 1 ("room list received"); without it the TẠO PHÒNG button (id 2011 ->
    sub_4CB4C3) and most room buttons silently do nothing."""
    if rooms:
        raise NotImplementedError("room record (sub_6ACBB5) not mapped yet")
    return obf_body(88, ("u16", 0))


def parse_create_room(body):
    """Opcode 77 (client, create-room dialog "XÁC NHẬN"; senders sub_4DD17B / sub_6B6441 / ...). Captured with the
    default dialog: str title "DefaultRoomTitle<n>", str password "", u32 x7 = 0,1,5,19,0,0,0, u32 -1, u32 0, u8 0
    (meanings not mapped yet). Returns the decoded fields (best effort)."""
    p = 2
    title, n = bp.get_str(body[p:], True); p += n
    pw, n = bp.get_str(body[p:], True); p += n
    ints = []
    while p + 4 <= len(body) - 1:
        ints.append(bp.get_int(body[p:], 4, True)); p += 4
    return title.decode("cp1258", "replace"), pw.decode("cp1258", "replace"), ints


def create_room_ok(room_no=1, room_type=0, team_mode=0):
    """Reply to opcode 77. Opcode 83 -> sub_4D24BB -> sub_4CE9FC: u8 result (0 = OK; 1 SameRoomExist, 2 NoEmptySlot,
    3 CantCreateRoom, 4 NoAuthority, 5..19 other errors). On 0 the rest goes to the lobby strategy object
    (CLobbyRoomUIWnd[+252], vt_CNormalLobbyStrategy) vf11 0x6B7B55: u16 room no (sub_8E8E3B), u32 (sub_8E75F1),
    u8 team mode (sub_8E75D2, <=2; read back by sub_8E75EA), u8 ROOM TYPE (sub_8E78CB, read by sub_8E78DB),
    u8 (sub_8E7626) -> sub_8F391D(12) = waiting-room stage.
    Room type decides the Start pre-check (sub_6C0990 -> vf155 -> sub_988F2D): min players / min teams = 2/2 by
    default, 1/1 for types 14, 16, 17, 19, 22, 32, 33 (or map game types 96, 107, 116, ...). team mode 2 -> 1 team."""
    return obf_body(83, ("u8", 0), ("u16", room_no), ("u32", 0), ("u8", team_mode), ("u8", room_type), ("u8", 0))


def room_player(slot=0, user_id=1000, name="tester", chief=True, character=0, team=0):
    """Opcode 103 (CSessionStage__OnPacket -> stage vf141; CPrepareStage: 0x692446 builds CSetPlayerOnPreparePacket
    (sub_57343E) = CSetPlayerPacket sub_573146 + CSlotAccessoryPacket sub_572A05, then vf149 + sub_691E66).
    sub_573146: u8 slot, u32 user id, u8 (+16; 0 forces the next u32 to -1), u8, u8, u32, 3 bytes bitfield
    (byte0 bit0 = ready (On_106), bit1 = room chief (sub_8EA9B0 checks it for our own slot), byte1 & 0x3F = character,
    byte2 & 0x1F = team), blob profile (sub_679434: str, u8,
    u8, u32, u8, u32, u16, u32, u32, u32, u32, u8, u32, str, u16 ...), u8, u8 (<=1), u8, str, str, blob, u8 flag
    (!= 0 -> blob). sub_572A05: u16, u8 n x (u8, u16), u8 m x (u32 x3), u8 (<=22 / 101..102 / 255), u8, u32 x3,
    u8 k x (u32 x3), u32 x2, bool, u32, u16, str. Meanings mostly unmapped (CHƯA KIỂM); blobs are padded with zeros so
    sub-readers never run dry. Opcode 104 (vf143) = player leaves (u8 slot)."""
    nm = name.encode("cp1258")
    profile = b"\x00" + struct.pack("<H", len(nm)) + nm + bytes(256)
    pad = b"\x00" + bytes(256)
    f = [("u8", slot), ("u32", user_id), ("u8", 0), ("u8", 0), ("u8", 0), ("u32", 0),
         ("buf", bytes([0x02 if chief else 0, character & 0x3F, team & 0x1F])),
         ("blob", profile), ("u8", 0), ("u8", 0), ("u8", 0), ("str", name), ("str", ""), ("blob", pad), ("u8", 0),
         ("u16", 0), ("u8", 0), ("u8", 0), ("u8", 255), ("u8", 0), ("u32", 0), ("u32", 0), ("u32", 0), ("u8", 0),
         ("u32", 0), ("u32", 0), ("u8", 0), ("u32", 0), ("u16", 0), ("str", "")]
    return obf_body(103, *f)


def room_slot_state(slot=0, chief=True, ready=False, character=0, team=0):
    """Opcode 106 (CPrepareStage__On_106 0x6C6BC9): u8 slot, 3 bytes state (DecodeBuf; byte0 bit0 ready, bit1 chief,
    byte1 & 0x3F character, byte2 & 0x1F team), u8 (sub_8E8E68(slot, v)). For our own slot with the ready bit unchanged
    the client calls stage vf153(this, 1) (CPrepareStage__vf153): enables the room buttons (sub_A7195B) and shows
    PRE_Bt_Start when we are chief (PRE_Bt_Ready otherwise). Without it the buttons stay disabled."""
    st = bytes([(0x02 if chief else 0) | (0x01 if ready else 0), character & 0x3F, team & 0x1F])
    return obf_body(106, ("u8", slot), ("buf", st), ("u8", 0))


def room_map(map_index=0, map_code=0):
    """Opcode 113 (CPrepareStage__On_113): u16 result (0 = ok; 1 = "MapSelectPlayer" error + u8), then u16 (sub_8E8E59,
    map code?), u32 map index -> sub_6DBFBE(dword_E60930, index) = the room's current map (sub_6DC01D), used by the Start
    checks (sub_6C0990 / sub_6DF9FB: without a map -> "SmallMapPlayer2"). Also calls stage vf153 + strategy vf18."""
    return obf_body(113, ("u16", 0), ("u16", map_code), ("u32", map_index))


# Battle maps offered by the fake server: (display name, theme folder, pack map name, index in CPlayMapInfoList).
# CPlayMapInfoList (dword_E60A10, filled by sub_7376D3 at start-up) holds every "Map/*" entry of fx.idx in idx order
# (== alphabetical, 1019 entries); a map record's u16 at +112 is an index into it (max players come from the .map file,
# sub_6DD119 -> sub_736E92). Indices from tools/idf.py over ~/Downloads/Boom/fx.idx.
BATTLE_MAPS = [("Village01", "Village", "Village01.map", 954),
               ("Forest01", "Forest", "Forest01.map", 223),
               ("Camp01", "Camp", "Camp01.map", 104)]


def all_battle_maps(boom_dir=None):
    """Every Map/* entry of fx.idx (1019) as BATTLE_MAPS tuples; the CPlayMapInfoList index is the position among the
    Map/* entries in idx order. The 3 hand-made maps keep dyn index 0..2 (room_map/match_start defaults), the rest
    follow in idx order. Theme = longest Theme/* folder name prefixing the map name (after dropping NXCL_/WS_/
    WinningStreak_), else "ThemeDefault" (code 138 in the 231 parser)."""
    import os, re
    import idf
    boom_dir = pathlib.Path(boom_dir or os.environ.get("BOOM_DIR", pathlib.Path.home() / "Downloads" / "Boom"))
    _, ents, _ = idf.parse_idx(idf.decrypt_idx((boom_dir / "fx.idx").read_bytes(), idf.KEYS["fx"]))
    names = [e[0] for e in ents]
    themes = sorted({n.split("/")[1] for n in names if n.startswith("Theme/")}, key=len, reverse=True)
    maps = [n[4:] for n in names if n.startswith("Map/")]

    def theme(name):
        base = re.sub(r"^(NXCL_|WS_|WinningStreak_)", "", name).lower()
        return next((t for t in themes if base.startswith(t.lower())), "ThemeDefault")

    first = [m[0] for m in BATTLE_MAPS]
    out = list(BATTLE_MAPS)
    out += [(n, theme(n), n + ".map", i) for i, n in enumerate(maps) if n not in first]
    return out


if __import__('os').environ.get('ALL_MAPS') == '1':
    BATTLE_MAPS = all_battle_maps()


def _sstr(text):
    """String inside a blob sub-reader (sub_A63A40): u32 LE length + bytes."""
    b = text.encode("cp1258")
    return struct.pack("<I", len(b)) + b


def dyn_map_blob(maps=BATTLE_MAPS, mode=0):
    """Inner bytes (tag 0 + data) of the opcode 231 blob, parsed by sub_6E077C into 128-byte CDynamicMapMan records:
    u16 n, then per map: u32 id (+0), u8 mode (+4; must equal CDynamicMapMan[27], set by sub_4D6FC6: 0 normal channel,
    9 if sub_8DAF47, 3/2/1/5/6/7/8 other channel kinds), str name (+8), str name2 (+24), u8 special (+40; 0 = normal),
    u8 game type (+41; 1 = not in any special list), str theme (+44), str map file (+72), u8 (+100), u8 (+101; default
    mode filter needs != 0), u32 RGB (+104), u8 (+108; 2/3 excluded, /10==1 sets +120), u8 (+109; != 2), u8 (+110),
    u16 CPlayMapInfoList index (+112), u8 (+114), u32 (+116). Categories are derived from the maps (sub_6E048D, enabled)."""
    out = struct.pack("<H", len(maps))
    for i, (name, theme, mapfile, idx) in enumerate(maps):
        out += struct.pack("<IB", i + 1, mode) + _sstr(name) + _sstr(name) + bytes([0, 1]) + _sstr(theme) + _sstr(mapfile)
        out += bytes([0, 1]) + struct.pack("<I", 0x00FFFFFF) + bytes([0, 1, 0]) + struct.pack("<HBI", idx, 0, 0)
    return b"\x00" + out


def dyn_map_info():
    """Opcode 231 (CStage__On_231): blob -> sub_6E077C; only accepted if the blob checksum (sub_A0E1E0 = adler32 seeded
    with 0, over tag+data, stored by sub_A62580) equals CDynamicMapMan[3], which opcode 234 sets. Saved to
    fxdynmapinfo.ssd. This is the client's battle-map table: empty -> empty map dialog, "SmallMapPlayer2" on Start."""
    return obf_body(231, ("blob", dyn_map_blob()))


def map_checksums():
    """Opcode 234 (CStage__On_234): blob {u8 (sub_A90B40), u16 (dword_EA7878), u32 (dword_EA787C), u8 n, n x u8}, then
    u32 dyn-map checksum (sub_6E0F64 -> CDynamicMapMan[3], then reloads fxdynmapinfo.ssd), u32 (sub_6ABA21, stage-map
    checksum), u8 flag, u32 (sub_9C24BA if flag)."""
    import zlib
    return obf_body(234, ("blob", b"\x00" + struct.pack("<BHIB", 0, 0, 0, 0)),
                    ("u32", zlib.adler32(dyn_map_blob(), 0)), ("u32", 0), ("u8", 0), ("u32", 0))


def match_start(map_entry=BATTLE_MAPS[0], dyn_index=0, room_type=None, seed=12345, slots=((0, 0, 0),)):
    """Opcode 501 (CPrepareStage__On_501 0x6C4978) = start the match -> sub_8F391D(13) (CGameStage). Server-driven: the
    handler does not require a prior opcode 97, so the server can start the match itself.
    u8 result (1 = ok, else "CannotLaunchAs"); [per-slot block only on special channel kinds sub_8DAB40/8DAD87/8DAD95];
    u32 seed (sub_8E77E4, sub_65412D(3, seed)); u16 CPlayMapInfoList index (sub_8EAB95); str map name — must be a prefix
    match of that CPlayMapInfoList entry (sub_736FE3), else "InvalidMapReturn"; u32 CDynamicMapMan index (sub_6DE36E);
    u8 room type (sub_8E78CB); u8 (sub_8E7636); u8 n; n x (u8 slot, u8 (+96 of the 580-byte slot record, sub_8E76A3;
    a slot with a player needs it != -1), u8 (sub_8E8EBB), u32 (>=0 -> sub_67900E), u32 (sub_67901A), u32 (sub_9B69F7 for
    our own slot)); then every slot 0..15 must pass sub_6BE6D0, else the client goes back (stage [15141]) + opcode 81;
    then u8 flag (!= 0 -> sub_985703 extra data) -> CGameStage."""
    name, _theme, _file, idx = map_entry
    f = [("u8", 1), ("u32", seed), ("u16", idx), ("str", name), ("u32", dyn_index),
         ("u8", ROOM_TYPE if room_type is None else room_type), ("u8", 0), ("u8", len(slots))]
    for slot, pos, team in slots:
        f += [("u8", slot), ("u8", pos), ("u8", team), ("u32", 0), ("u32", 0), ("u32", 0)]
    f += [("u8", 0)]
    return obf_body(501, *f)


def round_start(map_entry=BATTLE_MAPS[0], mode=4, turn_ms=10000, extra2=None, extra4=(1, 1)):
    """Opcode 189 (S->C `sub_70E5C4` 0x70E5C4) = the round/turn command, per oc_e-game.md section 5a:
    u8 mode (Decode1); u32 -> this[4887] (CHUA KIE: looks like per-turn time limit); u16 map_id (Decode2,
    sub_8EAB95-usable); then per mode (static decompile of the handler):
      mode 1: u8 x16 (per-slot state, built client-side into Block)          -> sub_70E357: vf147(map_id, Block)
              + spawns 1 bomber (malloc 0xA18 sub_5862A5) + sends C->S 139 {bool 1}
      mode 2: u16 a4 + u8 a5 + u32 a6                        -> sub_70DF00: sub_70A385(a4, a5, a6) + vf147(map, Block)
              + sends C->S 140 {bool 1}
      mode 4: u16 a4 + u8 a5 + u8 a6(u8)                     -> sub_70DFF9: needs a4 == (*(*this+608))(this, 4)
              (else sub_708FFE(5,0) = silently dropped!) + vf147 + 12-bomber block copy (vt+732) + C->S 140.
    TURN_A2/TURN_A3/TURN_A4 env vars override the mode-2 fields (defaults 1 / 1 / 12345)."""
    import os
    if extra2 is None:
        extra2 = (int(os.environ.get('TURN_A2', '1')), int(os.environ.get('TURN_A3', '1')),
                  int(os.environ.get('TURN_A4', '12345')))
    name, _theme, _file, idx = map_entry
    f = [("u8", mode), ("u32", turn_ms), ("u16", idx)]
    if mode == 1:
        f += [("u8", 1 if i == 0 else 0) for i in range(16)]
    elif mode == 2:
        f += [("u16", extra2[0]), ("u8", extra2[1]), ("u32", extra2[2])]
    elif mode == 4:
        f += [("u16", extra4[0]), ("u8", extra4[1]), ("u8", 1)]
    return obf_body(189, *f)


def round_go(times=(120, 30), seed=0, kind=0, flag=0):
    """Opcode 190 (S->C sub_70E7D6, CGameStage__OnPacket case 190) = "GO" command: sets the round phase
    this[5402] = 2 (via sub_70C5DC). Field order (recv order): u32 (seed/turn no., v27), u8 (kind, v28),
    u32 t1 + u32 t2 (seconds; client stores this[19736] = 1000*t1, this[19740] = 1000*t2), u8 flag (then
    per-flag extras: flag != 0 -> per 2P pairing over bombers (no extra bytes), else u8 n + n x u8).
    Values beyond t1/t2 are CHUA KIE, guessed 0."""
    f = [("u32", seed), ("u8", kind), ("u32", times[0]), ("u32", times[1]), ("u8", flag)]
    if flag == 0:
        f += [("u8", 0)]
    return obf_body(190, *f)


def round_begin(game_time=0, limit_ms=180000, t2_ms=30000, flag=0):
    """Opcode 191 (S->C sub_709A38, CGameStage__OnPacket case 191) = round begin: this[19700] = 1; u32 game_time ->
    sub_6E2054 = CGameClock start (sub_6E1AF7: T[5] = game_time, T[4] = now - ping/2, started); u32 limit_ms ->
    this[19736] and u32 t2_ms -> this[19740] (milliseconds as-is, unlike 190 which multiplies seconds by 1000);
    u8 flag -> box this+19652. Also clock flag T[3] = 1, bombers sub_592ADE(1) + [vt+424](24, 9860), vf155(1) when no
    strategy object claims it, shield item timers (sub_7074E0)."""
    return obf_body(191, ("u32", game_time), ("u32", limit_ms), ("u32", t2_ms), ("u8", flag))


def round_result(game_time=0, key=1, t1=180, t2=30, flag=0, rank_key=0, rank_extra=0, rank_flag=0, slots=None):
    """Opcode 146 (S->C sub_70DE4C -> sub_70A647; field order checked in IDA 2026-10-18). Same head as 191 plus the
    per-slot score table: u32 game_time -> CGameClock start (sub_6E2054); u32 key -> this[4887] (session key, low byte
    prefixes every in-game C->S message); u32 t1, u32 t2 (seconds, x1000 -> this[4934]/[4935]); u8 flag -> box;
    then u32 rank_key (!= 0 -> htonl -> sub_9B54FE(key, u16)), u16 rank_extra, u8 rank_flag (sub_9B5989);
    18 x {u8 on; if on: 3 x (u32, u16) -> sub_9B5C5A(slot, ...)}. slots: dict slot -> [(u32, u16)] * 3."""
    f = [("u32", game_time), ("u32", key), ("u32", t1), ("u32", t2), ("u8", flag),
         ("u32", rank_key), ("u16", rank_extra), ("u8", rank_flag)]
    slots = slots or {}
    for i in range(18):
        if i in slots:
            f += [("u8", 1)]
            for v, w in slots[i]:
                f += [("u32", v), ("u16", w)]
        else:
            f += [("u8", 0)]
    return obf_body(146, *f)


def login_ok(name="tester", players=1):
    """CLoginStage__On_4 0x8534F3: u8 result 0 = success -> sub_852BCA 0x852BCA (field order from the decompile;
    meaning of most fields still unknown, zeros are accepted). `players` must equal the 1P/2P count
    (CLobbyStage__On_218(dword_E60880))."""
    f = [("u8", 0),                                   # result: 0 ok, 1 not registered, ...
         ("u8", 0), ("u16", 0), ("u8", players), ("u64", 0)]
    for i in range(players):
        f += [("u32", 1000 + i), ("u32", 0), ("u16", 0), ("u16", 0),   # sub_9B698F, sub_9B69AB
              ("u32", 1000 + i), ("str", name), ("u8", 0),             # sub_99A71D = PLAYER ID (must match the
              # user id in room opcode 103, else the client does not treat that slot as ours), sub_99A746 = name
              ("str", name), ("str", ""),                              # sub_99A817, sub_99A783
              ("u8", 0), ("u32", 0), ("u8", 0), ("u8", 0), ("u16", 0), ("u8", 0), ("u8", 0),
              ("u32", 0), ("u32", 0), ("u8", 0), ("u8", 0), ("u8", 0),
              ("u16", 0), ("u16", 0),                                  # only if !Feature_IsDisabled(6): stub -> always
              ("u32", 0),                                              # sub_99AC6C
              ("u8", 0), ("u8", 0), ("u32", 0), ("u8", 0), ("u8", 0),
              ("u32", 0),                                              # count of (u32, u32) pairs
              ("u8", 0)]
    # trailing: u8 sub_99C3A7, u8 sub_99C99F, u8 sub_99C3BE, u16 sub_99C42A,
    #   u8 sub_99C4CB = SỐ TAB CATEGORY (CShareContext+456, sub_854A7D) — PHẢI > 0 thì màn chọn kênh mới có tab
    #   để dựng danh sách ô (channel category +0xD0 phải < số tab này). 0 = không tab -> ô kênh trống.
    f += [("u8", 0), ("u8", 0), ("u8", 0), ("u16", 0), ("u8", 1),
          ("u8", 0)]                                  # u8=1 tab; cuối = cờ "đổi mật khẩu"
    return obf_body(4, *f)


class Session:
    """Per-connection crypto state as seen from the server (mirror of CClientSocket fields)."""

    def __init__(self):
        self.st = bp.SeqState()
        self.st.header_type = HEADER_TYPE
        self.recv_buf = b""

    def send(self, body, hdr_mode=3, cks_mode=2):
        """Server->client after handshake: client recv format (2,3), key = client's seq_r."""
        st = self.st
        seq_byte = ((st.header_type + st.modif) ^ (st.base_r + st.seq_r)) & 0xFF
        frame = bp.build(body, hdr_mode, cks_mode, seq_byte, st.seq_r, st.header_type)
        st.seq_r += st.dseq_r
        return frame

    def feed(self, data, hdr_mode=2, cks_mode=2):
        """Client->server frames (format (2,2), key = client's seq_s). Yields plaintext bodies."""
        self.recv_buf += data
        a, b, c, _ = bp.layout(hdr_mode)
        while len(self.recv_buf) >= a + b:
            n = bp.get_int(self.recv_buf[a:], b, cks_mode in (1, 2)) - c
            total = a + b + c + n + (4 if cks_mode == 1 else 1 if cks_mode == 2 else 0)
            if len(self.recv_buf) < total:
                break
            frame, self.recv_buf = self.recv_buf[:total], self.recv_buf[total:]
            body = bp.parse(frame, hdr_mode, cks_mode, self.st.seq_s, self.st.header_type)
            self.st.seq_s += self.st.dseq_s
            yield body


def _lstr(text):
    """string inside a blob sub-reader (0xA63A40): u32 LE length + bytes"""
    b = text.encode("cp1258", errors="replace")
    return struct.pack("<I", len(b)) + b


DEFAULT_ENDPOINTS = tuple(("127.0.0.1", p, 1) for p in (3838, 4848, 5858, 6868))


def multisvr_blob(servers=(("Boom", "Fake server", 0),), endpoints=DEFAULT_ENDPOINTS, flag=0):
    """sub_998CCF 0x998CCF (cached as multisvr.ssd): u8 n {str, str, u32} (sub_9986F3), u16 m {u32 in_addr, u16 port, u8}
    (sub_998760), u8 flag (CMultiServer+0x3C). Built-in defaults (CMultiServer__ctor / CMultiServer__AddDefaultServers):
    one group {"Default Server List", "This is built in ...", 0}, endpoints {ip, 3838/4848/5858/6868, 1}."""
    out = bytes([len(servers)])
    for a, b, v in servers:
        out += _lstr(a) + _lstr(b) + struct.pack("<I", v)
    out += struct.pack("<H", len(endpoints))
    for ip, port, g in endpoints:
        out += bytes(int(x) for x in ip.split(".")) + struct.pack("<HB", port, g)
    return out + bytes([flag])


def multisvrn_blob(entries=((1, "Kenh 1", ""),)):
    """sub_998EA0 0x998EA0 (cached as multisvrn.ssd): u8 n {u8, str, str} (sub_998690)."""
    out = bytes([len(entries)])
    for i, a, b in entries:
        out += bytes([i]) + _lstr(a) + _lstr(b)
    return out


def login_replies():
    """Login_DoLoginSequence 0x8E2DEC waits for 13, 2, 12, 21, 1, 43 in this order.
    Each starts with a u8 'have new data' flag; 0 = use local cache."""
    return [
        obf_body(13, ("u8", 0)),           # CStage__On_13: dyn image info
        obf_body(2, ("u8", 0)),            # FxClientString
        obf_body(12, ("u8", 0)),           # FxQuestString
        obf_body(21, ("u8", 0)),           # FxMessageTable
        obf_body(1, ("u8", 0), ("u8", 0)),  # sub_99933B: 0 = keep built-in list; 1 + multisvr_blob() breaks the
                                            # main connection (ErrCannotLogin) - endpoint fields not fully known yet
        obf_body(43, ("u8", 0)),           # sub_982A90
    ]


def hexdump(b, width=16):
    out = []
    for i in range(0, len(b), width):
        chunk = b[i:i + width]
        out.append(f"  {i:04x}  {chunk.hex(' '):<{width * 3}} {''.join(chr(c) if 32 <= c < 127 else '.' for c in chunk)}")
    return "\n".join(out)


class Logger:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, msg):
        line = f"{datetime.datetime.now():%H:%M:%S.%f} {msg}"
        print(line, flush=True)
        with self.path.open("a") as f:
            f.write(line + "\n")



def parse_bomb_record(body):
    """C->S 111 (CGameMsgCache ring record flushed by vf8 0x6F06ED, oc_e-game.md section 5a-5) -> dict.
    Order: u16 op, u32 key, u8 ctx, u8 slot, u32 serial (bomb box +280), u8 y (rec+0x10), u8 x (rec+0x14),
    u8 power (rec+0x30), u8 r34, u8 r38, u8 r3c, u8 r18, u32 r1c, u8 flag (rec+0x40) [+ u8,u8,u8,u16 if flag & 3]."""
    o = 2
    def take(n):
        nonlocal o
        v = bp.get_int(body[o:], n, True); o += n
        return v
    r = {}
    for k, n in (("key", 4), ("ctx", 1), ("slot", 1), ("serial", 4), ("y", 1), ("x", 1), ("power", 1), ("r34", 1),
                 ("r38", 1), ("r3c", 1), ("r18", 1), ("r1c", 4), ("flag", 1)):
        r[k] = take(n)
    if r["flag"] & 3:
        r.update(r20=take(1), r24=take(1), r28=take(1), r2c=take(2))
    return r


def bomb_placed(rec, bomb_id):
    """S->C 152 (CGameStage__On_152 0x7064AC): server confirmation of a bomb -> ctx sub_6E9AF9 -> bomb owner vf20(desc):
    finds the pooled bomb with serial (box +280) == desc+0 and id == -1, gives it id desc+12 and places it (CGOGameBomb vf37).
    Field order (decode order, desc offsets from the disassembly of On_152):
      u8 ctx (== context index), u8 slot, u16 a3 (-> desc+176), u32 desc+0 serial, u32 a4, u32 a5 (owner vf23, no-op for heroes),
      u8 desc+24 (bomb +428, = rec y), u8 desc+36 (bomb +440, = rec x), u8 desc+48 (bomb +180), u32 desc+60 (bomb +192 = rec r1c),
      u8 desc+72 flags (&3 -> 3 extra u8), u16 desc+12 = NEW BOMB ID, u16 desc+96, u8 desc+156 (power), u64 desc+168,
      u8 desc+108 kind (bomb +328 = rec r34), u8 desc+120 (bomb +340 = rec r38), [u8 desc+132 / desc+144 by kind].
    Mapping from the 111 record is inferred from CGOGameBomb vf37 + the bomb getters; desc+48/+96/+168 values are guesses."""
    f = [("u8", rec["ctx"]), ("u8", rec["slot"]), ("u16", rec["slot"]), ("u32", rec["serial"]), ("u32", 0), ("u32", 0),
         ("u8", rec["y"]), ("u8", rec["x"]), ("u8", rec["r18"]), ("u32", rec["r1c"]), ("u8", rec["flag"])]
    if rec["flag"] & 3:
        f += [("u8", rec.get("r20", 0)), ("u8", rec.get("r24", 0)), ("u8", rec.get("r28", 0))]
    f += [("u16", bomb_id), ("u16", 0), ("u8", rec["power"]), ("u64", 0), ("u8", rec["r34"]), ("u8", rec["r38"])]
    if rec["r34"] in (1, 2) or (rec["r34"] == 4 and rec["r38"] == 4):
        f += [("u8", 0)]
    return obf_body(152, *f)


def map_items(brick_items=(), floor_items=()):
    """S->C 553 (CStage__OnPacket -> sub_6A5A5E 0x6A5A5E): item layout of the next map, stored in the room context
    (dword_E60884 vectors +339/+343/+347) and consumed by CGamePlayMap__Load (sub_729F44): blob, inner little-endian:
      u16 n1, n1 x {u16 index, u8 y(row), u8 x(col), u32 kind}  -- item lying on the floor (room ctx +339 -> sub_729F44 2nd loop, sub_71FCFE)
      u16 n2, n2 x {u16 index, u8 y(row), u8 x(col), u32 kind}  -- item hidden in the brick at (x, y) (+343 -> sub_5BF485(tile, kind, index))
      u16 n3, n3 x {u16, u32, u32}                     -- CHUA KIEM
    index < 1000 = slot in the item table (sub_89AEA3), kind != 0 makes the broken brick spawn the item (sub_5B6578)."""
    import struct
    # order checked with gdb (logs/xvfb/item2): CGamePlayMap__Load calls sub_729F44(list +339, list +343) and sub_729F44
    # treats its SECOND argument as the brick list -> the first list in the packet is the floor list, the second the bricks
    # the blob inner starts with the u8 reader tag (0 = raw copy, sub_A62580) like every other blob (protocol.md); without it the
    # reader is shifted by one byte (gdb logs/xvfb/item_kinds2: counts 0x3200, indexes n<<8)
    inner = b"\x00" + struct.pack("<H", len(floor_items)) + b"".join(struct.pack("<HBBI", i, y, x, k) for i, x, y, k in floor_items)
    inner += struct.pack("<H", len(brick_items)) + b"".join(struct.pack("<HBBI", i, y, x, k) for i, x, y, k in brick_items)
    inner += struct.pack("<H", 0)
    return obf_body(553, ("blob", inner))


def parse_item_pick(body):
    """C->S 117 (CGameMsgCache vf9 0x6F0874, table 21 record written by sub_6F2ECE when a bomber steps on an item, sub_5B098A):
    u8 ctx, u8 slot, u8 rec+12 (a5[1]), u8 rec+16 (a5[0]), u16 item index (sub_5B61A9), u16 item kind (sub_5B61B4),
    u32 time (sub_6EFBB8), u32 session key (sub_6EFBCA), u8 rec+36."""
    o = 2
    out = {}
    for k, n in (("ctx", 1), ("slot", 1), ("a", 1), ("b", 1), ("index", 2), ("kind", 2), ("time", 4), ("key", 4), ("flag", 1)):
        out[k] = bp.get_int(body[o:], n, True); o += n
    return out


def item_picked(r):
    """S->C 158 (CGameStage__On_158 0x715E90): server confirms the pickup -> sub_6F001E clears the pending 117 record (ctx, index),
    then applies the item to the player. Order: u8 ok, u8 ctx (== context index), u8 slot, u8, u8, u16 index, u16 kind, bool.
    The two middle u8 are guessed to be the record's a/b (position?)."""
    return obf_body(158, ("u8", 1), ("u8", r["ctx"]), ("u8", r["slot"]), ("u8", r["a"]), ("u8", r["b"]),
                    ("u16", r["index"]), ("u16", r["kind"]), ("u8", 0))

async def handle(reader, writer, port, log):
    peer = writer.get_extra_info("peername")
    log(f"[{port}] connect from {peer}")
    pkt = hello_packet()
    writer.write(pkt)
    await writer.drain()
    log(f"[{port}] S->C hello {len(pkt)} bytes\n{hexdump(pkt)}")
    sess = Session()
    sess.st.seq_r += sess.st.dseq_r  # hello consumed one recv sequence step on the client
    try:
        while True:
            data = await asyncio.wait_for(reader.read(65536), timeout=120)
            if not data:
                break
            log(f"[{port}] C->S {len(data)} bytes\n{hexdump(data)}")
            try:
                bodies = list(sess.feed(data))
            except Exception as e:
                log(f"[{port}] decode error: {e!r}")
                continue
            for body in bodies:
                op = bp.get_int(body, 2, True)
                log(f"[{port}] C->S opcode {op} body {body.hex()}")
                replies = []
                if op == 1:  # login request (u8 players, str id, str password: both encrypted, accepted as is)
                    replies = [login_ok(), login_net_info()]
                if op == 40:  # sent on entering the channel screen; the channel cache file name
                    # (channel2_%03d%s.ssd, sub_993EF4) only exists from now on -> channel list must come after it
                    replies = [channel_list(), channel_status()]
                if op == 5:  # channel join request -> point the client at a "channel server" (ourselves, same port)
                    replies = [channel_join_ok(port=port)]
                if op == 6:  # login on the channel server -> enter the lobby (stage 11)
                    replies = [channel_enter_ok()]
                if op == 77:  # create room (dialog XÁC NHẬN) -> opcode 83 success -> waiting room (stage 12)
                    log(f"[{port}] create room {parse_create_room(body)}")
                    replies = [create_room_ok(room_type=ROOM_TYPE)]
                if op == 120 and len(body) > 2:  # bomber event (group packet: u8 subtype written by bomber vf112)
                    sub = bp.get_int(body[2:], 1, True)
                    log(f"[{port}] bomber event 120 subtype {sub}")
                    if sub == 13 and MATCH_END:  # EXPERIMENT: 173 = CGameStage vf149 -> slots reset, ChangeStage 12 (or 11)
                        async def _over(delay=MATCH_END):
                            await asyncio.sleep(delay)
                            writer.write(sess.send(obf_body(173, ("u8", 0), ("u8", 0))))
                            await writer.drain()
                            log(f"[{port}] S->C opcode 173 (match over)")
                        asyncio.ensure_future(_over())
                    if sub == 13 and DEATH_END:  # CGameStage vf150 = player died -> EXPERIMENT: end the round with 146
                        async def _end(delay=DEATH_END):
                            await asyncio.sleep(delay)
                            writer.write(sess.send(round_result(key=10000, slots={0: [(1, 1), (0, 0), (0, 0)]})))
                            await writer.drain()
                            log(f"[{port}] S->C opcode 146 (round result after death)")
                        asyncio.ensure_future(_end())
                if op == 117 and ITEM_ACK:  # item pickup request -> confirm with 158
                    r = parse_item_pick(body)
                    log(f"[{port}] item pick {r} -> 158")
                    replies = [item_picked(r)]
                if op == 111 and BOMB_PLACE:  # bomb record -> server confirmation 152 with a fresh bomb id
                    rec = parse_bomb_record(body)
                    sess.bomb_id = getattr(sess, "bomb_id", 0) + 1
                    log(f"[{port}] bomb record {rec} -> 152 id {sess.bomb_id}")
                    replies = [bomb_placed(rec, sess.bomb_id)]
                if op == 111 and BOMB_ECHO:  # bomb record (CGameMsgCache ring) -> EXPERIMENT: explode via 151 {n, n x (u16 id, u8 0, u32 arg)}
                    async def _boom(delay=BOMB_ECHO):
                        await asyncio.sleep(delay)
                        f = [("u8", BOMB_IDS)]
                        for i in range(BOMB_IDS):
                            f += [("u16", i), ("u8", 0), ("u32", BOMB_ARG)]
                        writer.write(sess.send(obf_body(151, *f)))
                        await writer.drain()
                        log(f"[{port}] S->C opcode 151 (explode ids 0..{BOMB_IDS - 1}, arg {BOMB_ARG})")
                    asyncio.ensure_future(_boom())
                if op == 337:  # sent on entering the waiting room (stage 12) -> put ourselves into slot 0
                    replies = [room_player(), room_slot_state(), room_map(MAP_INDEX)]
                    if AUTO_START:  # server-driven match start (opcode 501) a few seconds later
                        async def _start(delay=AUTO_START):
                            await asyncio.sleep(delay)
                            if ITEMS or FLOOR_ITEMS:  # item layout must arrive before the map is loaded (stage 13 OnEnter)
                                its = [tuple(int(v) for v in e.split(",")) for e in ITEMS.split(";") if e]
                                fls = [tuple(int(v) for v in e.split(",")) for e in FLOOR_ITEMS.split(";") if e]
                                writer.write(sess.send(map_items(
                                    brick_items=[(n, x, y, k) for n, (x, y, k) in enumerate(its)],
                                    floor_items=[(len(its) + n, x, y, k) for n, (x, y, k) in enumerate(fls)])))
                                await writer.drain()
                                log(f"[{port}] S->C opcode 553 (bricks {its}, floor {fls})")
                            r = match_start()
                            writer.write(sess.send(r))
                            await writer.drain()
                            log(f"[{port}] S->C opcode 501 (auto start)")
                            if TURN_START:  # round/turn command (opcode 189) after the match starts
                                await asyncio.sleep(TURN_START)
                                r = round_start(mode=TURN_MODE)
                                writer.write(sess.send(r))
                                await writer.drain()
                                log(f"[{port}] S->C opcode 189 (mode {TURN_MODE})")
                                if GO_START:  # "GO" command (opcode 190, sets phase this[5402] = 2)
                                    await asyncio.sleep(GO_START)
                                    r = round_go()
                                    writer.write(sess.send(r))
                                    await writer.drain()
                                    log(f"[{port}] S->C opcode 190 (GO)")
                                    if BEGIN_START:  # 191 round begin: starts CGameClock with a real base + time limit
                                        await asyncio.sleep(BEGIN_START)
                                        r = round_result() if BEGIN_OP == 146 else (obf_body(552, ("u32", 0)) if BEGIN_OP == 552 else round_begin())
                                        writer.write(sess.send(r))
                                        await writer.drain()
                                        log(f"[{port}] S->C opcode {BEGIN_OP} (round begin)")
                                    if PLAY_START:  # 189 mode 0 while phase == 2 -> sub_70E511: phase 3, clock runs
                                        await asyncio.sleep(PLAY_START)
                                        r = round_start(mode=0)
                                        writer.write(sess.send(r))
                                        await writer.drain()
                                        log(f"[{port}] S->C opcode 189 (mode 0, play)")
                                        if POST_PLAY_START:  # 191 after the switch back to ctx 0 -> starts the clock the tick reads
                                            await asyncio.sleep(POST_PLAY_START)
                                            writer.write(sess.send(round_begin()))
                                            await writer.drain()
                                            log(f"[{port}] S->C opcode 191 (round begin, post-play)")
                        asyncio.ensure_future(_start())
                if op == 97:  # client Start (passed its own checks) -> start the match
                    replies = [match_start()]
                if op == 395:  # lobby square: request square info -> area/map/theme, then the user list
                    replies = [square_info(), square_users(), room_list(), map_checksums(), dyn_map_info()]
                if op == 0:
                    replies = login_replies()
                if replies:
                    for r in replies:
                        frame = sess.send(r)
                        writer.write(frame)
                        log(f"[{port}] S->C opcode {bp.get_int(r, 2, True)} {frame.hex()}")
                    await writer.drain()
    except asyncio.TimeoutError:
        log(f"[{port}] idle timeout")
    except ConnectionError as e:
        log(f"[{port}] {e!r}")
    finally:
        log(f"[{port}] close {peer}")
        writer.close()


async def main(ports, logpath):
    log = Logger(logpath)
    servers = []
    for p in ports:
        srv = await asyncio.start_server(lambda r, w, p=p: handle(r, w, p, log), "0.0.0.0", p)
        servers.append(srv)
        log(f"listening on {p}")
    await asyncio.gather(*(s.serve_forever() for s in servers))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ports", default="3838,4848,5858,6868")
    ap.add_argument("--log", default=str(pathlib.Path(__file__).resolve().parent.parent / "logs" / "fakeserver.log"))
    a = ap.parse_args()
    asyncio.run(main([int(x) for x in a.ports.split(",")], a.log))
