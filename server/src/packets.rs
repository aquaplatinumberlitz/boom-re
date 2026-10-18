//! Server->client packet builders, ported 1:1 from tools/fakeserver.py (field notes and addresses live there and in
//! docs/; each builder names the client handler it feeds).

use crate::maps::{self, BattleMap};
use crate::proto::{self, cp1258, put_int};

pub const CLIENT_VERSION: u16 = 116; // sub_8E2494
pub const HEADER_TYPE: u32 = 0; // row of the opcode substitution table, 0..15

/// Body for formats with checksum mode 1/2: [opcode u16][fields], every int XOR-obfuscated.
pub struct Packet(Vec<u8>);

impl Packet {
    pub fn new(opcode: u16) -> Self {
        let mut v = Vec::new();
        put_int(&mut v, opcode as u64, 2, true);
        Packet(v)
    }
    pub fn u8(mut self, v: u8) -> Self {
        put_int(&mut self.0, v as u64, 1, true);
        self
    }
    pub fn u16(mut self, v: u16) -> Self {
        put_int(&mut self.0, v as u64, 2, true);
        self
    }
    pub fn u32(mut self, v: u32) -> Self {
        put_int(&mut self.0, v as u64, 4, true);
        self
    }
    pub fn u64(mut self, v: u64) -> Self {
        put_int(&mut self.0, v, 8, true);
        self
    }
    pub fn str(mut self, text: &str) -> Self {
        proto::put_str(&mut self.0, &cp1258(text), true);
        self
    }
    pub fn blob(mut self, inner: &[u8]) -> Self {
        proto::put_blob(&mut self.0, inner, true);
        self
    }
    /// RecvPkt__DecodeBuf: run-obfuscated bytes, no length prefix.
    pub fn buf(mut self, raw: &[u8]) -> Self {
        proto::obf_bytes(&mut self.0, raw);
        self
    }
    pub fn build(self) -> Vec<u8> {
        self.0
    }
}

/// Little-endian writer for blob sub-readers (sub_A62F40/sub_A62F70/sub_A62FB0, strings = sub_A63A40: u32 len + bytes).
#[derive(Default)]
pub struct Le(pub Vec<u8>);

impl Le {
    pub fn u8(&mut self, v: u8) -> &mut Self {
        self.0.push(v);
        self
    }
    pub fn u16(&mut self, v: u16) -> &mut Self {
        self.0.extend_from_slice(&v.to_le_bytes());
        self
    }
    pub fn u32(&mut self, v: u32) -> &mut Self {
        self.0.extend_from_slice(&v.to_le_bytes());
        self
    }
    pub fn bytes(&mut self, b: &[u8]) -> &mut Self {
        self.0.extend_from_slice(b);
        self
    }
    pub fn str(&mut self, text: &str) -> &mut Self {
        let b = cp1258(text);
        self.u32(b.len() as u32).bytes(&b)
    }
}

/// First packet on every connection (PatchServer_CheckVersion 0x8E426E / Net_OnHandshake 0x999C02), format (0,0).
pub fn hello_packet(header_type: u32, version: u16) -> Vec<u8> {
    let st = proto::SeqState { header_type, ..Default::default() };
    let mut body = vec![0u8];
    body.extend_from_slice(&0u16.to_be_bytes());
    body.extend_from_slice(&version.to_be_bytes());
    body.extend_from_slice(&header_type.to_be_bytes());
    body.extend_from_slice(&0u16.to_be_bytes());
    body.push(0);
    proto::build(&body, 0, 0, st.recv_seq_byte(), st.seq_r, header_type)
}

/// Login_DoLoginSequence 0x8E2DEC waits for 13, 2, 12, 21, 1, 43; u8 0 = use the local cache.
pub fn login_replies() -> Vec<Vec<u8>> {
    vec![
        Packet::new(13).u8(0).build(), // CStage__On_13: dyn image info
        Packet::new(2).u8(0).build(),  // FxClientString
        Packet::new(12).u8(0).build(), // FxQuestString
        Packet::new(21).u8(0).build(), // FxMessageTable
        Packet::new(1).u8(0).u8(0).build(), // sub_99933B: keep the built-in server list
        Packet::new(43).u8(0).build(), // sub_982A90
    ]
}

/// CLoginStage__On_4 0x8534F3 (fields: tools/fakeserver.py login_ok). Player id = 1000 + i must match opcode 103.
pub fn login_ok(name: &str, players: u8) -> Vec<u8> {
    login_ok_as(name, 1000, players)
}

/// Opcode 4 with the account id `first_id` (+i for 2-player logins); each connected client needs its own id.
pub fn login_ok_as(name: &str, first_id: u32, players: u8) -> Vec<u8> {
    let mut p = Packet::new(4).u8(0).u8(0).u16(0).u8(players).u64(0);
    for i in 0..players as u32 {
        p = p.u32(first_id + i).u32(0).u16(0).u16(0).u32(first_id + i).str(name).u8(0).str(name).str("");
        p = p.u8(0).u32(0).u8(0).u8(0).u16(0).u8(0).u8(0).u32(0).u32(0).u8(0).u8(0).u8(0);
        p = p.u16(0).u16(0).u32(0).u8(0).u8(0).u32(0).u8(0).u8(0).u32(0).u8(0);
    }
    // trailing: u8 x3, u16, u8 = number of channel category tabs (must be > 0), u8 "change password" flag
    p.u8(0).u8(0).u8(0).u16(0).u8(1).u8(0).build()
}

/// CLoginStage__On_15 0x84FE35: blob {str host, u16 x3, u8 mode 0, u16}.
pub fn login_net_info(host: &str, ports: [u16; 3]) -> Vec<u8> {
    let mut b = Le::default();
    let h = host.as_bytes();
    b.u32(h.len() as u32).bytes(h);
    for p in ports {
        b.u16(p);
    }
    b.u8(0).u16(0);
    Packet::new(15).blob(&b.0).build()
}

/// CStage__On_14 -> sub_99489D: channel records (kind 18, type 0, category 0).
pub fn channel_list(names: &[&str], max_users: u32) -> Vec<u8> {
    let mut b = Le::default();
    b.u8(0).u16(names.len() as u16);
    for n in names {
        b.str(n).u32(max_users).bytes(&[0, 18, 0, 0, 0, 0, 0]).u16(0).u16(0).bytes(&[0; 4]).u32(0).u32(0);
    }
    Packet::new(14).u8(1).blob(&b.0).build()
}

/// CSelectServerStage__On_16: per channel u16 current users, u32 state (1 = online).
pub fn channel_status(users: &[u16]) -> Vec<u8> {
    let mut b = Le::default();
    b.u8(0).u16(users.len() as u16);
    for &u in users {
        b.u16(u).u32(1);
    }
    Packet::new(16).blob(&b.0).build()
}

/// CSelectServerStage__On_7 0x8558C4: point the client at the channel server.
pub fn channel_join_ok(ip: [u8; 4], port: u16, kind: u8, index: u32) -> Vec<u8> {
    Packet::new(7).u8(1).u8(kind).u32(index).u32(u32::from_be_bytes(ip)).u16(port).build()
}

/// Opcode 17 -> lobby (stage 11). SYSTEMTIME (8 x u16: y, m, weekday (Sunday = 0), d, h, mi, s, ms), u32, u8 x9,
/// u8 n = 0, u8 x3.
pub fn channel_enter_ok(t: [u16; 6]) -> Vec<u8> {
    let [y, mo, d, h, mi, s] = t;
    let mut p = Packet::new(17);
    for v in [y, mo, weekday(y, mo, d), d, h, mi, s, 0] {
        p = p.u16(v);
    }
    p = p.u32(0);
    for _ in 0..13 {
        p = p.u8(0);
    }
    p.build()
}

/// Day of week, Sunday = 0 (Sakamoto).
fn weekday(y: u16, m: u16, d: u16) -> u16 {
    const T: [i32; 12] = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4];
    let y = y as i32 - (m < 3) as i32;
    ((y + y / 4 - y / 100 + y / 400 + T[m as usize - 1] + d as i32) % 7) as u16
}

/// CLobbySquareStage__On_466 0x4E52B5: area, square objects (none), map file, theme, time offset.
pub fn square_info(area: u32, map_name: &str, theme: &str) -> Vec<u8> {
    let mut b = Le::default();
    b.u8(0).u32(0);
    Packet::new(466).u32(area).blob(&b.0).str(map_name).str(theme).u32(0).build()
}

/// CLobbySquareStage__On_467 0x4E4100: empty user list.
pub fn square_users() -> Vec<u8> {
    Packet::new(467).u16(0).build()
}

/// Opcode 88 -> sub_4D0F56: empty room list (required for the create-room button).
pub fn room_list() -> Vec<u8> {
    Packet::new(88).u16(0).build()
}

/// One room of the lobby list (opcode 88).
pub struct RoomEntry {
    pub session: u16, // room slot in the lobby (< 560), sent back in C->S 78
    pub room_id: u32, // sent back in C->S 78
    pub name: String,
    pub password: bool, // +76: != 0 -> the client asks for a password before joining
    pub playing: bool,  // +104: != 0 -> not joinable
    pub players: u8,    // +128
    pub max_players: u8, // +152: joinable while players < max_players
    pub room_type: u8,  // +88 (guess)
}

/// Opcode 88 (lobby room list, sub_4D0F56): u16 n; blob (tag 0 + little-endian) n x {u16 session, u32 room id, u32 len + name,
/// u8 +76 password, u8 +88, u8 +104 playing, u16 +116, u8 +128 players, u8 +140, u8 +152 max, u8 +92, u32 +176, u8, u8 (sub_97C722),
/// u8 +200, u8 n2 = 0 (sub_6ACA64)} (sub_6ACBB5). Fields without a comment are unknown and sent as 0.
pub fn room_list_with(rooms: &[RoomEntry]) -> Vec<u8> {
    if rooms.is_empty() {
        return room_list();
    }
    let mut b = Le::default();
    b.u8(0);
    for r in rooms {
        let nm = cp1258(&r.name);
        b.u16(r.session).u32(r.room_id).u32(nm.len() as u32).bytes(&nm);
        b.u8(r.password as u8).u8(r.room_type).u8(r.playing as u8).u16(0).u8(r.players).u8(0).u8(r.max_players).u8(0).u32(0);
        b.u8(0).u8(0).u8(0).u8(0);
    }
    Packet::new(88).u16(rooms.len() as u16).blob(&b.0).build()
}

/// CStage__On_234: misc checksums; the dyn-map checksum gates opcode 231.
pub fn map_checksums(maps: &[BattleMap]) -> Vec<u8> {
    let mut b = Le::default();
    b.u8(0).u8(0).u16(0).u32(0).u8(0);
    Packet::new(234).blob(&b.0).u32(maps::adler32_seed0(&maps::dyn_map_blob(maps, 0))).u32(0).u8(0).u32(0).build()
}

/// CStage__On_231: battle map table (sub_6E077C).
pub fn dyn_map_info(maps: &[BattleMap]) -> Vec<u8> {
    Packet::new(231).blob(&maps::dyn_map_blob(maps, 0)).build()
}

/// Opcode 83 (reply to 77) -> waiting room (stage 12).
pub fn create_room_ok(room_no: u16, room_type: u8, team_mode: u8) -> Vec<u8> {
    Packet::new(83).u8(0).u16(room_no).u32(0).u8(team_mode).u8(room_type).u8(0).build()
}

/// Opcode 103: player in a room slot (CSetPlayerPacket sub_573146 + CSlotAccessoryPacket sub_572A05).
pub fn room_player(slot: u8, user_id: u32, name: &str, chief: bool, character: u8, team: u8) -> Vec<u8> {
    // profile blob (sub_679434): str name (u32 length, sub_A63A40) first, then numbers (zeros); the name shown in the room / result
    // window and needed by the kick check (sub_6C9413) comes from here, not from the str field further down
    let mut profile = Le::default();
    profile.u8(0).str(name).bytes(&[0; 256]);
    let mut pad = Le::default();
    pad.u8(0).bytes(&[0; 256]);
    let p = Packet::new(103).u8(slot).u32(user_id).u8(0).u8(0).u8(0).u32(0);
    let p = p.buf(&[if chief { 2 } else { 0 }, character & 0x3F, team & 0x1F]);
    let p = p.blob(&profile.0).u8(0).u8(0).u8(0).str(name).str("").blob(&pad.0).u8(0);
    let p = p.u16(0).u8(0).u8(0).u8(255).u8(0).u32(0).u32(0).u32(0).u8(0);
    p.u32(0).u32(0).u8(0).u32(0).u16(0).str("").build()
}

/// CPrepareStage__On_106 0x6C6BC9: slot state (enables the room buttons for our own slot). Flags byte: bit 0 = slot closed,
/// bit 1 = room master, bits 2-4 = player state (1 = ready; sub_6C31ED / CPrepareStage__vf153), then 6-bit character, 5-bit team.
pub fn room_slot_state(slot: u8, chief: bool, ready: bool, character: u8, team: u8) -> Vec<u8> {
    let st = [(if chief { 2 } else { 0 }) | if ready { 4 } else { 0 }, character & 0x3F, team & 0x1F];
    Packet::new(106).u8(slot).buf(&st).u8(0).build()
}

/// 106 for an empty slot: open / closed by the master (C->S 94).
pub fn slot_closed(slot: u8, closed: bool) -> Vec<u8> {
    Packet::new(106).u8(slot).buf(&[closed as u8, 0, 0]).u8(0).build()
}

/// CPrepareStage__On_113: the room's current map (index into the 231 table).
pub fn room_map(map_index: u32, map_code: u16) -> Vec<u8> {
    Packet::new(113).u16(0).u16(map_code).u32(map_index).build()
}

/// CPrepareStage__On_501 0x6C4978: start the match -> CGameStage. slots: (slot, pos, team).
pub fn match_start(map: &BattleMap, dyn_index: u32, room_type: u8, seed: u32, slots: &[(u8, u8, u8)]) -> Vec<u8> {
    let mut p = Packet::new(501).u8(1).u32(seed).u16(map.idx).str(&map.name).u32(dyn_index);
    p = p.u8(room_type).u8(0).u8(slots.len() as u8);
    for &(slot, pos, team) in slots {
        p = p.u8(slot).u8(pos).u8(team).u32(0).u32(0).u32(0);
    }
    p.u8(0).build()
}

/// Opcode 117 (CPrepareStage__On_117 0x6CCDxx): full match start (the normal-room variant of 501). Unlike 501, which sets
/// every slot's start point (+124 of the room slot record, read by CGameStage__vf44 -> sub_71A9EC -> vf147) to 0, this carries
/// it per slot, so players spawn on different cells. Layout (docs/oc_e-game.md section 5a-7):
/// u8 0 (no per-slot profile list), blob {tag 0; u16x8 SYSTEMTIME; u32 seed; u16 CPlayMapInfoList index; str map name;
/// u32 231-table index; u8 room type; u8 (sub_8E7636); u8 n; u8 x3 (sub_8E7A56); u8 n2 (n2 x u32 item ids);
/// n x {u8 slot, u8 (+84; != 0 hides the player: logs/duo/t13), u8 start point (+124), u8 pos (+96), u8 team (+112), u8, i8 partner slot (-1), u32, u32 (<0: keep),
/// u32, u32, u8 0}}, u8 0 (no 985703 blob), u8 time (x1000 -> room+78*4), u8 event-NPC stage (-1),
/// u8, u16 n3, blob {tag 0} (n3 x records).
pub fn match_start_full(map: &BattleMap, dyn_index: u32, room_type: u8, seed: u32, slots: &[(u8, u8, u8, u8, u8)], time_s: u8) -> Vec<u8> {
    let mut b = Le(vec![0]);
    for _ in 0..8 {
        b.u16(0);
    }
    b.u32(seed).u16(map.idx).str(&map.name).u32(dyn_index).u8(room_type).u8(0).u8(slots.len() as u8).u8(0).u8(0).u8(0).u8(0);
    for &(slot, r84, spawn, pos, team) in slots {
        b.u8(slot).u8(r84).u8(spawn).u8(pos).u8(team).u8(0).u8(0xFF).u32(0).u32(0).u32(0).u32(0).u8(0);
    }
    Packet::new(117).u8(0).blob(&b.0).u8(0).u8(time_s).u8(0xFF).u8(0).u16(0).blob(&[0]).build()
}

/// Opcode 189 (sub_70E5C4): round command. u32 = session key (this[4887]); mode 0 = play (phase 2 -> 3),
/// 1 = load round (+ clock start, client answers 139), 2/4 = other round loads (client answers 140).
pub fn round_start(map: &BattleMap, mode: u8, key: u32, extra2: (u16, u8, u32), extra4: (u16, u8)) -> Vec<u8> {
    let mut p = Packet::new(189).u8(mode).u32(key).u16(map.idx);
    match mode {
        1 => {
            for i in 0..16 {
                p = p.u8((extra4.0 >> i) as u8 & 1); // mode 1: per-slot active flags (bit i of extra4.0)
            }
        }
        2 => p = p.u16(extra2.0).u8(extra2.1).u32(extra2.2),
        4 => p = p.u16(extra4.0).u8(extra4.1).u8(1),
        _ => {}
    }
    p.build()
}

/// Opcode 189 mode 1 with explicit start points: `spawns[slot]` = index into the map's start-point list (8-byte x,y entries,
/// `sub_7223A1`), read by `sub_6EC1DA` when the round loads (vf147 -> sub_715C3A). Same index for two slots = same cell.
pub fn round_load(map: &BattleMap, key: u32, spawns: &[u8; 16]) -> Vec<u8> {
    spawns.iter().fold(Packet::new(189).u8(1).u32(key).u16(map.idx), |p, &v| p.u8(v)).build()
}

/// Opcode 190 (sub_70E7D6): "GO" — phase 2, clock paused, overlay THỜI GIAN.
pub fn round_go(times: (u32, u32), seed: u32, kind: u8, flag: u8) -> Vec<u8> {
    let p = Packet::new(190).u32(seed).u8(kind).u32(times.0).u32(times.1).u8(flag);
    if flag == 0 { p.u8(0) } else { p }.build()
}

/// Opcode 191 (sub_709A38): round begin — clock start (game time), limits in ms, flag.
pub fn round_begin(game_time: u32, limit_ms: u32, t2_ms: u32, flag: u8) -> Vec<u8> {
    Packet::new(191).u32(game_time).u32(limit_ms).u32(t2_ms).u8(flag).build()
}

/// Opcode 146 (sub_70DE4C -> sub_70A647): end of round + per-slot score table (18 slots, 3 x (u32, u16) each).
pub fn round_result(game_time: u32, key: u32, t: (u32, u32), flag: u8, rank: (u32, u16, u8), slots: &[(usize, [(u32, u16); 3])]) -> Vec<u8> {
    let mut p = Packet::new(146).u32(game_time).u32(key).u32(t.0).u32(t.1).u8(flag).u32(rank.0).u16(rank.1).u8(rank.2);
    for i in 0..18 {
        match slots.iter().find(|s| s.0 == i) {
            Some((_, vals)) => {
                p = p.u8(1);
                for &(v, w) in vals {
                    p = p.u32(v).u16(w);
                }
            }
            None => p = p.u8(0),
        }
    }
    p.build()
}

/// C->S 111: bomb record of the CGameMsgCache ring (flushed by vf8 0x6F06ED; docs/oc_e-game.md section 5a-5).
#[derive(Clone, Debug, Default)]
pub struct BombRecord {
    pub key: u32,
    pub ctx: u8,
    pub slot: u8,
    pub serial: u32,
    pub y: u8,
    pub x: u8,
    pub power: u8,
    pub r34: u8,
    pub r38: u8,
    pub r3c: u8,
    pub r18: u8,
    pub r1c: u32,
    pub flag: u8,
    pub extra: Option<(u8, u8, u8, u16)>,
}

/// Parse a C->S 111 body (opcode included).
pub fn parse_bomb_record(body: &[u8]) -> Option<BombRecord> {
    let mut o = 2usize;
    let mut take = |n: usize| -> Option<u64> {
        let v = body.get(o..o + n).map(|b| crate::proto::get_int(b, n, true));
        o += n;
        v
    };
    let mut r = BombRecord {
        key: take(4)? as u32,
        ctx: take(1)? as u8,
        slot: take(1)? as u8,
        serial: take(4)? as u32,
        y: take(1)? as u8,
        x: take(1)? as u8,
        power: take(1)? as u8,
        r34: take(1)? as u8,
        r38: take(1)? as u8,
        r3c: take(1)? as u8,
        r18: take(1)? as u8,
        r1c: take(4)? as u32,
        flag: take(1)? as u8,
        extra: None,
    };
    if r.flag & 3 != 0 {
        r.extra = Some((take(1)? as u8, take(1)? as u8, take(1)? as u8, take(2)? as u16));
    }
    Some(r)
}

/// S->C 152 (CGameStage__On_152 0x7064AC): bomb confirmed -> bomb owner vf20 gives the pooled bomb (serial == desc+0, id -1)
/// the id `bomb_id` and places it. Field order from the disassembly; desc+48/+96/+168 values are guesses (see fakeserver.py).
pub fn bomb_placed(r: &BombRecord, bomb_id: u16) -> Vec<u8> {
    let mut p = Packet::new(152)
        .u8(r.ctx)
        .u8(r.slot)
        .u16(r.slot as u16)
        .u32(r.serial)
        .u32(0)
        .u32(0)
        .u8(r.y)
        .u8(r.x)
        .u8(r.r18)
        .u32(r.r1c)
        .u8(r.flag);
    if r.flag & 3 != 0 {
        let (a, b, c, _) = r.extra.unwrap_or_default();
        p = p.u8(a).u8(b).u8(c);
    }
    p = p.u16(bomb_id).u16(0).u8(r.power).u64(0).u8(r.r34).u8(r.r38);
    if r.r34 == 1 || r.r34 == 2 || (r.r34 == 4 && r.r38 == 4) {
        p = p.u8(0);
    }
    p.build()
}

/// S->C 151 (CGameStage__On_151 0x70205B): u8 n, n x (u16 bomb id, u8 kind, kind == 0: u32) -> ctx sub_6E9994; kind 0 = explode
/// (sub_7324C0). Verified 2026-10-18: after 152 gave the bomb id 1, 151 {1, 0, 2} makes it explode (water blast, player trapped).
pub fn bomb_explode(ids: &[u16], arg: u32) -> Vec<u8> {
    let mut p = Packet::new(151).u8(ids.len() as u8);
    for &id in ids {
        p = p.u16(id).u8(0).u32(arg);
    }
    p.build()
}

/// S->C 173 (CGameStage dispatch case 153 -> vf149 0x7132xx): match over. u8 (sub_8E75D2), u8 0 (no player list) -> the 16 slots are reset and
/// the client changes to stage 12 (waiting room; 11 when sub_8DACD5() says so). Verified 2026-10-18: client goes back to the room, re-sends 337.
pub fn match_over() -> Vec<u8> {
    Packet::new(173).u8(0).u8(0).build()
}

/// C->S 117: item pickup request (CGameMsgCache vf9 0x6F0874; record written by sub_6F2ECE when a bomber steps on an item).
#[derive(Clone, Debug, Default)]
pub struct ItemPick {
    pub ctx: u8,
    pub slot: u8,
    pub a: u8,
    pub b: u8,
    pub index: u16,
    pub kind: u16,
    pub time: u32,
    pub key: u32,
    pub flag: u8,
}

pub fn parse_item_pick(body: &[u8]) -> Option<ItemPick> {
    let mut o = 2usize;
    let mut take = |n: usize| -> Option<u64> {
        let v = body.get(o..o + n).map(|b| crate::proto::get_int(b, n, true));
        o += n;
        v
    };
    Some(ItemPick {
        ctx: take(1)? as u8,
        slot: take(1)? as u8,
        a: take(1)? as u8,
        b: take(1)? as u8,
        index: take(2)? as u16,
        kind: take(2)? as u16,
        time: take(4)? as u32,
        key: take(4)? as u32,
        flag: take(1)? as u8,
    })
}

/// S->C 158 (CGameStage__On_158 0x715E90): pickup confirmed -> sub_6F001E clears the pending 117 record, sub_706E0A applies the item.
/// u8 ok, u8 ctx, u8 slot, u8, u8 (echo of the record's a/b — guessed), u16 index, u16 kind, bool. Verified 2026-10-18 (item stays picked).
pub fn item_picked(r: &ItemPick) -> Vec<u8> {
    Packet::new(158).u8(1).u8(r.ctx).u8(r.slot).u8(r.a).u8(r.b).u16(r.index).u16(r.kind).u8(0).build()
}

/// S->C 553 (CStage__OnPacket -> sub_6A5A5E): item layout of the next map, must arrive before 501. Blob (little-endian inner):
/// u8 reader tag 0, then list 1 (items lying on the floor, sub_71FCFE), list 2 (hidden in the brick at (x, y), sub_5BF485), list 3 empty. Entries {u16 index, u8 x, u8 y, u32 kind}.
pub fn map_items(floor: &[(u16, u8, u8, u32)], placed: &[(u16, u8, u8, u32)]) -> Vec<u8> {
    let mut inner = vec![0u8]; // reader tag 0 = raw copy (sub_A62580)
    for list in [floor, placed] {
        inner.extend_from_slice(&(list.len() as u16).to_le_bytes());
        for &(i, x, y, k) in list {
            inner.extend_from_slice(&i.to_le_bytes());
            inner.push(y); // row first (verified: logs/xvfb/item_kinds4)
            inner.push(x);
            inner.extend_from_slice(&k.to_le_bytes());
        }
    }
    inner.extend_from_slice(&0u16.to_le_bytes());
    Packet::new(553).blob(&inner).build()
}

/// Opcode 28 (CChatStage__OnPacket -> sub_6855DF): one chat/notice line, `str text, u8 kind` (0 = show as is, 1 = text is a
/// string-table key, 2/3 = special formats). The client shows the text in the chat box of the lobby / waiting room.
pub fn chat_line(text: &str) -> Vec<u8> {
    Packet::new(28).str(text).u8(0).build()
}

/// Opcode 168 (CGameStage__OnPacket case 148 -> sub_719D08): match result, shown by the result window (sub_7190C6). One blob:
/// header (sub_6F7C0E) u8, i8, i8 result kind (0 = normal battle), u8, u8, u32 (/30 = delay?), i8 extra (-1 = none, else 7 more u8 per
/// player, sub_976564), i8, u32 (sub_97B206), u8; then 16 slot records (sub_6F7DC1): u8 kind (0 empty, 1 player, 2 AI, 3);
/// player: u32, u8 rank (<= 1 = winner, sub_6F77B5), u8, u8, u8, u8 short (1 = skip the exp/score block), u32 option bits (0),
/// u8, i8, u32, u8, u8.
pub fn game_result(ranks: &[(u8, u8)]) -> Vec<u8> {
    let mut b = Le(vec![0]);
    b.u8(0).u8(0).u8(0).u8(0).u8(0).u32(0).u8(0xFF).u8(0).u32(0).u8(0);
    for slot in 0..16u8 {
        match ranks.iter().find(|r| r.0 == slot) {
            Some(&(_, rank)) => {
                b.u8(1).u32(0).u8(rank).u8(0).u8(0).u8(0).u8(1).u32(0).u8(0).u8(0).u32(0).u8(0).u8(0);
            }
            None => {
                b.u8(0);
            }
        }
    }
    Packet::new(168).blob(&b.0).build()
}

/// Opcode 104 (CSessionStage__OnPacket -> vf143, CPrepareStage__vf143 0x6C6A0B / CSessionStage__vf143): a player left the slot.
/// `u8 slot, u32 user id, u8 by super-master`. When the slot is our own the client shows BannedByLeader and returns to the lobby.
pub fn player_left(slot: u8, user_id: u32) -> Vec<u8> {
    Packet::new(104).u8(slot).u32(user_id).u8(0).build()
}

/// Opcode 23 (CStage vf59 -> sub_9B974A): account state of the players on this PC; it ends with `this+288 = 1`, the flag the
/// SHOP button (global event 6002 -> stage vf65) checks before doing anything (sub_9B73E1). u8 flag, u8 n, n x {u16, u8, u32, u8,
/// u32, u8, u8, u32, u32, u8, u32, u8, u16, u8, str, u8, u8, u32, u8, u8, u8}, n x 4 x u32, blob {flag != 0: n x {u32 k, k x (str,
/// u8, u32)}; flag 0: n x 2 x {u16 k, k x (str, u8)}}. Field meanings: CHƯA KIỂM (zeros).
pub fn account_info(name: &str) -> Vec<u8> {
    let mut p = Packet::new(23).u8(0).u8(1);
    p = p.u16(0).u8(0).u32(0).u8(0).u32(0).u8(0).u8(0).u32(0).u32(0).u8(0).u32(0).u8(0).u16(0).u8(0).str(name);
    p = p.u8(0).u8(0).u32(0).u8(0).u8(0).u8(0);
    p = p.u32(0).u32(0).u32(0).u32(0);
    let mut b = Le(vec![0]);
    b.u16(0).u16(0);
    p.blob(&b.0).build()
}

/// Gold (lucci, VANG) given on shop entry; the client deducts prices itself after a 223 ok.
pub const SHOP_GOLD: u32 = 5000;

/// Opcode 20 (CStage__On_20): shop entry data, the answer to C->S 38. u8 slot, u8, 4 x u32 (?, lucci/VANG sub_9B754B,
/// gcoupon sub_9B6973, capoint/BAC sub_9B6936); [feature 67] u8, 4 x u32, str;
/// [186] bool; [176] u8 n (+ SYSTEMTIME 8 x u16 if n != 0); u32, u32, u32, u8, u32, str, blob {u32 n, n x (u8 idx, u32, str)},
/// u32 count, count x blob. Ends with sub_8F391D(14) when E60884+900 == 14 (the shop stage).
pub fn shop_data() -> Vec<u8> {
    let mut p = Packet::new(20).u8(0).u8(0).u32(0).u32(SHOP_GOLD).u32(0).u32(0);
    p = p.u8(0).u32(0).u32(0).u32(0).u32(0).str("");
    p = p.u8(0).u8(0);
    p = p.u32(0).u32(0).u32(0).u8(0).u32(0).str("");
    let mut b = Le(vec![0]);
    b.u32(0);
    p.blob(&b.0).u32(0).build()
}

/// Shop test catalog: (stock id, item id, stock type, name, icon path, price)
pub const SHOP_ITEMS: &[(u32, u32, u8, &str, &str, u32)] = &[
    (1, 1001, 2, "Test A", "Icon/A02_10_0001icon", 100),
    (2, 1002, 2, "Test B", "Icon/A02_21_0001icon", 200),
];

/// Opcode 51 (CStage__On_51 -> sub_8C0009, item catalog into dword_E60814): blob {u16 n, n x (u32 id, u8 type, str, u32 +60,
/// u32 +72, u32 +84, str, u16, u8)}. The icon path comes from the type (sub_8BBFE8): type 2 -> the str itself, 19 (avatar) ->
/// A{char +60}_{part +72}_{num +84}.
pub fn item_catalog() -> Vec<u8> {
    let mut b = Le(vec![0]);
    b.u16(SHOP_ITEMS.len() as u16);
    for &(_, id, kind, _, icon, _) in SHOP_ITEMS {
        b.u32(id).u8(kind).str(icon).u32(0).u32(0).u32(0).str("").u16(0).u8(0);
    }
    Packet::new(51).blob(&b.0).build()
}

/// Opcode 64 (sub_8B25A2, FxStock.ini): blob {u16 n, n x stock record (sub_8A1190)}.
pub fn shop_stock() -> Vec<u8> {
    let mut b = Le(vec![0]);
    b.u16(SHOP_ITEMS.len() as u16);
    for &(stock, id, kind, name, _, price) in SHOP_ITEMS {
        b.u32(stock).u8(kind).str(name).u32(price).u32(id).u32(1).str("");
        // +248 = currency (sub_8A04EA): 0 cash (XU), 1 lucci (VANG), 2 gcoupon, 5 capoint (BAC)
        b.u32(price).u32(price).u16(0).u8(0).u16(0).u16(0).u32(0).u8(0).u8(1).u32(0).u16(0).u32(0).u32(0).u8(1);
    }
    Packet::new(64).blob(&b.0).build()
}

/// Opcode 225 (sub_8B26FB, StringTable.ini): blob {u16 n, n x (u32 id, str)}.
pub fn shop_strings() -> Vec<u8> {
    let mut b = Le(vec![0]);
    b.u16(0);
    Packet::new(225).blob(&b.0).build()
}

/// Opcode 65 (sub_8B27FB, PackageMap.ini): blob {u16 n, n x (u32 package stock id, u32 member stock id)}.
pub fn shop_packages() -> Vec<u8> {
    let mut b = Le(vec![0]);
    b.u16(0);
    Packet::new(65).blob(&b.0).build()
}

/// Opcode 223 (CStage case 221 -> stage vf84 -> sub_9B691A, E60848+348 = cash / XU): u8 slot, u32 cash. Answer to C->S 260.
pub fn cash_balance(cash: u32) -> Vec<u8> {
    Packet::new(223).u8(0).u32(cash).build()
}

/// Opcode 223 inside the shop stage (sub_803416 -> sub_8AF6B7): purchase result, u8 code. 0 = ok ("BuyItem", item applied
/// locally by sub_8ADBC9), 1/5 ErrorBuying, 24 ErrorBuying2, 40 ProcessOther, 41 ErrorWrongItem, 45 NotRegistered..., 22/23 ignored.
pub fn buy_result(code: u8) -> Vec<u8> {
    Packet::new(223).u8(code).build()
}

/// Opcode 289 (sub_6952A5 -> sub_7EFC2E): answer to C->S 325 (shop button). u8 ok: 1 -> sub_8BE528 + sub_7EFB6A (enter the shop),
/// 0 -> "CannotConnectToShop".
pub fn shop_enter_ok() -> Vec<u8> {
    Packet::new(289).u8(1).build()
}

