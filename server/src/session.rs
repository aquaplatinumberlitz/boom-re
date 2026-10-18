//! One client connection: framing state, opcode dispatch and the scripted match flow (fakeserver.handle()).

use std::sync::Arc;
use std::time::Duration;

use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;
use tokio::sync::mpsc;

use crate::maps::BattleMap;
use crate::packets::{self as pk, HEADER_TYPE};
use crate::proto::{self, SeqState};
use crate::hub::{self, Hub, Member};

/// Server settings; env names match tools/fakeserver.py so the same test recipes work.
#[derive(Clone, Debug)]
pub struct Config {
    pub room_type: u8,
    pub map_index: u32,
    pub auto_start: f64,
    pub turn_start: f64,
    pub turn_mode: u8,
    pub go_start: f64,
    pub begin_start: f64,
    pub begin_op: u16,
    pub play_start: f64,
    /// >0: send 191 (round begin) N s after 189 mode 0 — starts the clock of context 0, the one the match tick reads.
    pub post_play_start: f64,
    /// >0: answer C->S 111 (bomb) with 152 (id) and explode it with 151 after this many seconds; 0 = ignore bombs.
    pub bomb_fuse: f64,
    /// >0: N s after C->S 120 subtype 13 (death) send 146 (round result -> next round).
    pub death_end: f64,
    /// >0: N s after C->S 120 subtype 13 (death) send 173 (match over -> waiting room). Takes precedence over death_end.
    pub match_end: f64,
    /// Number of clients in the room before the server starts the match (AUTO_START seconds after the last one entered).
    pub players: usize,
    /// The 3 ports sent in opcode 15 next to the host (UDP endpoints of the server? env UDP_PORTS="a,b,c").
    pub udp_ports: [u16; 3],
    /// Items placed on the map before each match (S->C 553 list 2): "x,y,kind;..." from env ITEMS.
    pub items: Vec<(u8, u8, u32)>,
    /// Items lying on the floor (553 list 1): env FLOOR_ITEMS.
    pub floor_items: Vec<(u8, u8, u32)>,
    /// Address handed to the client in opcodes 7/15 (must be reachable from the client; 127.0.0.1 for Wine).
    pub server_ip: [u8; 4],
    pub maps: Vec<BattleMap>,
}

impl Config {
    pub fn from_env(maps: Vec<BattleMap>) -> Self {
        fn env<T: std::str::FromStr>(k: &str, d: T) -> T {
            std::env::var(k).ok().and_then(|v| v.parse().ok()).unwrap_or(d)
        }
        Config {
            room_type: env("ROOM_TYPE", 19),
            map_index: env("MAP_INDEX", 0),
            auto_start: env("AUTO_START", 0.0),
            turn_start: env("TURN_START", 0.0),
            turn_mode: env("TURN_MODE", 4),
            go_start: env("GO_START", 0.0),
            begin_start: env("BEGIN_START", 0.0),
            begin_op: env("BEGIN_OP", 191),
            play_start: env("PLAY_START", 0.0),
            post_play_start: env("POST_PLAY_START", 0.0),
            bomb_fuse: env("BOMB_FUSE", 2.5),
            death_end: env("DEATH_END", 0.0),
            match_end: env("MATCH_END", 3.0),
            players: env("PLAYERS", 1usize),
            udp_ports: {
                let v: Vec<u16> = std::env::var("UDP_PORTS").unwrap_or_default().split(',').filter_map(|x| x.trim().parse().ok()).collect();
                [v.first().copied().unwrap_or(0), v.get(1).copied().unwrap_or(0), v.get(2).copied().unwrap_or(0)]
            },
            floor_items: parse_items("FLOOR_ITEMS"),
            items: std::env::var("ITEMS")
                .unwrap_or_default()
                .split(';')
                .filter_map(|e| {
                    let v: Vec<u32> = e.split(',').filter_map(|x| x.trim().parse().ok()).collect();
                    (v.len() == 3).then(|| (v[0] as u8, v[1] as u8, v[2]))
                })
                .collect(),
            server_ip: env::<std::net::Ipv4Addr>("SERVER_IP", std::net::Ipv4Addr::LOCALHOST).octets(),
            maps,
        }
    }
}

pub type Log = Arc<dyn Fn(String) + Send + Sync>;

/// Writer side: owns the client's receive sequence (seq_r) so frames go out in order.
async fn writer_task(mut sock: tokio::net::tcp::OwnedWriteHalf, mut rx: mpsc::UnboundedReceiver<Vec<u8>>, log: Log, port: u16) {
    let mut st = SeqState { header_type: HEADER_TYPE, ..Default::default() };
    st.seq_r += st.dseq_r; // the hello consumed one receive step on the client
    while let Some(body) = rx.recv().await {
        let frame = proto::build(&body, 3, 2, st.recv_seq_byte(), st.seq_r, st.header_type);
        st.seq_r = st.seq_r.wrapping_add(st.dseq_r);
        log(format!("[{port}] S->C opcode {}", proto::get_int(&body, 2, true)));
        if sock.write_all(&frame).await.is_err() {
            break;
        }
    }
}

pub async fn handle(sock: TcpStream, port: u16, cfg: Arc<Config>, log: Log, hub: Arc<Hub>) {
    let peer = sock.peer_addr().map(|a| a.to_string()).unwrap_or_default();
    log(format!("[{port}] connect from {peer}"));
    let (mut rd, mut wr) = sock.into_split();
    if wr.write_all(&pk::hello_packet(HEADER_TYPE, pk::CLIENT_VERSION)).await.is_err() {
        return;
    }
    let (tx, rx) = mpsc::unbounded_channel();
    tokio::spawn(writer_task(wr, rx, log.clone(), port));

    let mut st = SeqState { header_type: HEADER_TYPE, ..Default::default() };
    let mut buf = Vec::new();
    let mut user_id: u32 = 0; // account of this connection (from opcode 1, or found in opcode 6 on the channel connection)
    let mut in_room = false;
    let mut chunk = vec![0u8; 65536];
    loop {
        let n = match tokio::time::timeout(Duration::from_secs(120), rd.read(&mut chunk)).await {
            Ok(Ok(n)) if n > 0 => n,
            Ok(_) => break,
            Err(_) => {
                log(format!("[{port}] idle timeout"));
                break;
            }
        };
        buf.extend_from_slice(&chunk[..n]);
        while let Some(len) = proto::frame_len(&buf, 2, 2) {
            let frame: Vec<u8> = buf.drain(..len).collect();
            let body = match proto::parse(&frame, 2, 2, st.seq_s, st.header_type) {
                Ok(b) => b,
                Err(_) => {
                    log(format!("[{port}] checksum mismatch"));
                    continue;
                }
            };
            st.seq_s = st.seq_s.wrapping_add(st.dseq_s);
            let op = proto::get_int(&body, 2, true) as u16;
            log(format!("[{port}] C->S opcode {op} body {}", hex(&body)));
            if op == 1 {
                user_id = hub.new_user();
                log(format!("[{port}] login -> user {user_id}"));
                let _ = tx.send(pk::login_ok_as(&hub::player_name(user_id), user_id, 1));
                let _ = tx.send(pk::login_net_info(&std::net::Ipv4Addr::from(cfg.server_ip).to_string(), cfg.udp_ports));
            } else if op == 6 {
                // channel login on a new connection: find which account it is (u32 user id somewhere in the body)
                user_id = find_user(&body, hub.known_users()).unwrap_or(1000);
                log(format!("[{port}] channel login user {user_id}"));
                let _ = tx.send(pk::channel_enter_ok(now_utc()));
            } else if op == 395 {
                // lobby entry: same replies as before but with the real room list
                hub.lobby.lock().unwrap().push(tx.clone());
                for r in replies(op, port, &cfg) {
                    let _ = tx.send(if proto::get_int(&r, 2, true) == 88 { hub.room_list(cfg.room_type) } else { r });
                }
            } else if op == 78 {
                // join a room from the lobby list (sub_4CB829: u16 session, u32 room id, str password, ...) -> same answer as create
                log(format!("[{port}] join room request from user {user_id}"));
                let _ = tx.send(pk::create_room_ok(1, cfg.room_type, 0));
            } else if op == 337 {
                in_room = true;
                hub.lobby.lock().unwrap().retain(|t| !t.same_channel(&tx));
                enter_room(&hub, &cfg, &log, port, user_id, &tx);
                hub.push_room_list(cfg.room_type);
            } else {
                for r in replies(op, port, &cfg) {
                    let _ = tx.send(r);
                }
            }
            if op == 117 {
                if let Some(r) = pk::parse_item_pick(&body) {
                    log(format!("[{port}] item pick {r:?} -> 158"));
                    hub.broadcast(&pk::item_picked(&r));
                }
            }
            if op == 111 && cfg.bomb_fuse > 0.0 {
                if let Some(rec) = pk::parse_bomb_record(&body) {
                    let id = hub.next_bomb_id();
                    log(format!("[{port}] bomb {rec:?} -> 152 id {id}, 151 in {}s", cfg.bomb_fuse));
                    hub.broadcast(&pk::bomb_placed(&rec, id));
                    let (hub2, fuse) = (hub.clone(), cfg.bomb_fuse);
                    tokio::spawn(async move {
                        tokio::time::sleep(Duration::from_secs_f64(fuse)).await;
                        hub2.broadcast(&pk::bomb_explode(&[id], 2));
                    });
                }
            }
            if op == 92 && body.len() >= 12 {
                // C->S 92 (CGameStage vf161 0x7027B0, once at match start): u32 ip1, u32 ip2 (sub_9B5552), u16 UDP port (sub_9B555E), ...
                let ip1 = proto::get_int(&body[2..], 4, true) as u32;
                let ip2 = proto::get_int(&body[6..], 4, true) as u32;
                let uport = proto::get_int(&body[10..], 2, true) as u16;
                log(format!("[{port}] udp info user {user_id}: {:08x} {:08x} port {uport}", ip1, ip2));
                if let Some(m) = hub.room.lock().unwrap().members.iter_mut().find(|m| m.user_id == user_id) {
                    m.udp = Some((ip1, ip2, uport));
                }
            }
            if op == 120 && body.len() > 2 {
                // bomber event: u8 subtype (11 trapped, 13 died; oc_e-game.md section 5a-5c)
                let sub = proto::get_int(&body[2..], 1, true) as u8;
                log(format!("[{port}] bomber event 120 subtype {sub}"));
                if sub == 13 && (cfg.match_end > 0.0 || cfg.death_end > 0.0) {
                    let (hub2, cfg2) = (hub.clone(), cfg.clone());
                    tokio::spawn(async move {
                        if cfg2.match_end > 0.0 {
                            tokio::time::sleep(Duration::from_secs_f64(cfg2.match_end)).await;
                            hub2.room.lock().unwrap().started = false;
                            hub2.broadcast(&pk::match_over());
                        } else {
                            tokio::time::sleep(Duration::from_secs_f64(cfg2.death_end)).await;
                            hub2.broadcast(&pk::round_result(0, 10000, (180, 30), 0, (0, 0, 0), &[(0, [(1, 1), (0, 0), (0, 0)])]));
                        }
                    });
                }
            }
        }
    }
    if in_room {
        let mut r = hub.room.lock().unwrap();
        r.members.retain(|m| m.user_id != user_id);
        if r.members.is_empty() {
            r.started = false;
        }
        drop(r);
        hub.push_room_list(cfg.room_type);
    }
    log(format!("[{port}] close {peer}"));
}

fn replies(op: u16, port: u16, cfg: &Config) -> Vec<Vec<u8>> {
    match op {
        0 => pk::login_replies(),
        1 => vec![pk::login_ok("tester", 1), pk::login_net_info(&std::net::Ipv4Addr::from(cfg.server_ip).to_string(), [0, 0, 0])],
        40 => vec![pk::channel_list(&["Kenh 1", "Kenh 2", "Kenh 3", "Kenh 4"], 100), pk::channel_status(&[10, 20, 30, 40])],
        5 => vec![pk::channel_join_ok(cfg.server_ip, port, 10, 0)],
        6 => vec![pk::channel_enter_ok(now_utc())],
        77 => vec![pk::create_room_ok(1, cfg.room_type, 0)],
        337 => vec![
            pk::room_player(0, 1000, "tester", true, 0, 0),
            pk::room_slot_state(0, true, false, 0, 0),
            pk::room_map(cfg.map_index, 0),
        ],
        97 => vec![pk::match_start(&cfg.maps[0], 0, cfg.room_type, 12345, &[(0, 0, 0)])],
        395 => vec![
            pk::square_info(1, "LobbySquare01.map", "Square"),
            pk::square_users(),
            pk::room_list(),
            pk::map_checksums(&cfg.maps),
            pk::dyn_map_info(&cfg.maps),
        ],
        _ => vec![],
    }
}

/// Server-driven match: 501 -> 189 (TURN_MODE) -> 190 -> 191/146 -> 189 mode 0 (docs/oc_e-game.md §5a-3).
async fn match_flow(hub: Arc<Hub>, cfg: Arc<Config>, log: Log, port: u16) {
    let wait = |s: f64| tokio::time::sleep(Duration::from_secs_f64(s));
    let map = &cfg.maps[0];
    wait(cfg.auto_start).await;
    if !cfg.items.is_empty() || !cfg.floor_items.is_empty() {
        // item layout must arrive before 501 (read when the map loads); list 1 = floor, list 2 = hidden in bricks
        let bricks: Vec<(u16, u8, u8, u32)> = cfg.items.iter().enumerate().map(|(i, &(x, y, k))| (i as u16, x, y, k)).collect();
        let n = bricks.len();
        let floor: Vec<(u16, u8, u8, u32)> = cfg.floor_items.iter().enumerate().map(|(i, &(x, y, k))| ((n + i) as u16, x, y, k)).collect();
        hub.broadcast(&pk::map_items(&floor, &bricks));
    }
    let slots: Vec<(u8, u8, u8)> = hub.room.lock().unwrap().members.iter().map(|m| (m.slot, m.slot, 0)).collect();
    hub.broadcast(&pk::match_start(map, 0, cfg.room_type, 12345, &slots));
    log(format!("[{port}] match flow: 501"));
    if cfg.turn_start <= 0.0 {
        return;
    }
    wait(cfg.turn_start).await;
    hub.broadcast(&pk::round_start(map, cfg.turn_mode, 10000, (1, 1, 12345), (hub.slot_mask(), 1)));
    if cfg.go_start <= 0.0 {
        return;
    }
    wait(cfg.go_start).await;
    hub.broadcast(&pk::round_go((120, 30), 0, 0, 0));
    if cfg.begin_start > 0.0 {
        wait(cfg.begin_start).await;
        let r = if cfg.begin_op == 552 {
            crate::packets::Packet::new(552).u32(0).build()
        } else if cfg.begin_op == 146 {
            pk::round_result(0, 1, (180, 30), 0, (0, 0, 0), &[])
        } else {
            pk::round_begin(0, 180_000, 30_000, 0)
        };
        hub.broadcast(&r);
    }
    if cfg.play_start > 0.0 {
        wait(cfg.play_start).await;
        hub.broadcast(&pk::round_start(map, 0, 10000, (1, 1, 12345), (1, 1)));
        if cfg.post_play_start > 0.0 {
            wait(cfg.post_play_start).await;
            // 146 = round begin + UDP peer table (sub_70A647: per slot 3 x (u32 ip, u16 port) -> sub_9B5C5A -> MTUDP HostCreate);
            // fall back to 191 when some client did not report its UDP address (C->S 92)
            let peers: Option<Vec<(usize, [(u32, u16); 3])>> = hub
                .room
                .lock()
                .unwrap()
                .members
                .iter()
                .map(|m| m.udp.map(|(a, b, p)| (m.slot as usize, [(0x7F00_0001, p), (a, p), (b, p)])))
                .collect();
            match peers {
                Some(p) if cfg.players > 1 => {
                    log(format!("[{port}] 146 with UDP peers {p:x?}"));
                    hub.broadcast(&pk::round_result(0, 10000, (180, 30), 0, (0, 0, 0), &p));
                }
                _ => hub.broadcast(&pk::round_begin(0, 180_000, 30_000, 0)),
            }
        }
    }
}

/// UTC wall clock as [y, m, d, h, mi, s] (the client only displays it).
fn now_utc() -> [u16; 6] {
    let secs = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map_or(0, |d| d.as_secs());
    let (days, rem) = ((secs / 86400) as i64, secs % 86400);
    // civil_from_days (H. Hinnant)
    let z = days + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = yoe + era * 400 + (m <= 2) as i64;
    [y as u16, m as u16, d as u16, (rem / 3600) as u16, (rem % 3600 / 60) as u16, (rem % 60) as u16]
}

fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

/// "x,y,kind;..." from an env var.
fn parse_items(var: &str) -> Vec<(u8, u8, u32)> {
    std::env::var(var)
        .unwrap_or_default()
        .split(';')
        .filter_map(|e| {
            let v: Vec<u32> = e.split(',').filter_map(|x| x.trim().parse().ok()).collect();
            (v.len() == 3).then(|| (v[0] as u8, v[1] as u8, v[2]))
        })
        .collect()
}

/// Find a known account id stored as an obfuscated u32 anywhere in a body (opcode 6 carries the id from the login).
fn find_user(body: &[u8], known: std::ops::Range<u32>) -> Option<u32> {
    (2..body.len().saturating_sub(3)).map(|i| proto::get_int(&body[i..], 4, true) as u32).find(|v| known.contains(v))
}

/// Opcode 337 (entering the waiting room): put the user into the shared room, tell everybody, start the match
/// when `PLAYERS` clients are in. Slot 0 = room chief.
fn enter_room(hub: &Arc<Hub>, cfg: &Arc<Config>, log: &Log, port: u16, user_id: u32, tx: &mpsc::UnboundedSender<Vec<u8>>) {
    let (slot, others, start) = {
        let mut r = hub.room.lock().unwrap();
        r.members.retain(|m| m.user_id != user_id);
        let slot = (0..16u8).find(|s| !r.members.iter().any(|m| m.slot == *s)).unwrap_or(0);
        let others: Vec<(u8, u32, String)> = r.members.iter().map(|m| (m.slot, m.user_id, m.name.clone())).collect();
        r.members.push(Member { user_id, name: hub::player_name(user_id), slot, tx: tx.clone(), udp: None });
        let start = !r.started && r.members.len() >= cfg.players && cfg.auto_start > 0.0;
        if start {
            r.started = true;
        }
        (slot, others, start)
    };
    let name = hub::player_name(user_id);
    log(format!("[{port}] user {user_id} enters the room in slot {slot} ({} others)", others.len()));
    // the newcomer: everybody already in the room, then itself
    for (s, id, nm) in &others {
        let _ = tx.send(pk::room_player(*s, *id, nm, *s == 0, 0, 0));
        let _ = tx.send(pk::room_slot_state(*s, *s == 0, false, 0, 0));
    }
    let _ = tx.send(pk::room_player(slot, user_id, &name, slot == 0, 0, 0));
    let _ = tx.send(pk::room_slot_state(slot, slot == 0, false, 0, 0));
    let _ = tx.send(pk::room_map(cfg.map_index, 0));
    // the others: the newcomer
    for m in hub.room.lock().unwrap().members.iter().filter(|m| m.user_id != user_id) {
        let _ = m.tx.send(pk::room_player(slot, user_id, &name, slot == 0, 0, 0));
        let _ = m.tx.send(pk::room_slot_state(slot, slot == 0, false, 0, 0));
    }
    if start {
        tokio::spawn(match_flow(hub.clone(), cfg.clone(), log.clone(), port));
    }
}
