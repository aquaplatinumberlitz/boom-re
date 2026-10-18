//! One client connection: framing state, opcode dispatch and the scripted match flow (fakeserver.handle()).

use std::sync::Arc;
use std::time::Duration;

use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;
use tokio::sync::mpsc;

use crate::maps::BattleMap;
use crate::packets::{self as pk, HEADER_TYPE};
use crate::proto::{self, SeqState};

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

pub async fn handle(sock: TcpStream, port: u16, cfg: Arc<Config>, log: Log) {
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
            for r in replies(op, port, &cfg) {
                let _ = tx.send(r);
            }
            if op == 337 && cfg.auto_start > 0.0 {
                tokio::spawn(match_flow(tx.clone(), cfg.clone(), log.clone(), port));
            }
        }
    }
    log(format!("[{port}] close {peer}"));
}

fn replies(op: u16, port: u16, cfg: &Config) -> Vec<Vec<u8>> {
    match op {
        0 => pk::login_replies(),
        1 => vec![pk::login_ok("tester", 1), pk::login_net_info("127.0.0.1", [0, 0, 0])],
        40 => vec![pk::channel_list(&["Kenh 1", "Kenh 2", "Kenh 3", "Kenh 4"], 100), pk::channel_status(&[10, 20, 30, 40])],
        5 => vec![pk::channel_join_ok([127, 0, 0, 1], port, 10, 0)],
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
async fn match_flow(tx: mpsc::UnboundedSender<Vec<u8>>, cfg: Arc<Config>, log: Log, port: u16) {
    let wait = |s: f64| tokio::time::sleep(Duration::from_secs_f64(s));
    let map = &cfg.maps[0];
    wait(cfg.auto_start).await;
    let _ = tx.send(pk::match_start(map, 0, cfg.room_type, 12345, &[(0, 0, 0)]));
    log(format!("[{port}] match flow: 501"));
    if cfg.turn_start <= 0.0 {
        return;
    }
    wait(cfg.turn_start).await;
    let _ = tx.send(pk::round_start(map, cfg.turn_mode, 10000, (1, 1, 12345), (1, 1)));
    if cfg.go_start <= 0.0 {
        return;
    }
    wait(cfg.go_start).await;
    let _ = tx.send(pk::round_go((120, 30), 0, 0, 0));
    if cfg.begin_start > 0.0 {
        wait(cfg.begin_start).await;
        let r = if cfg.begin_op == 146 {
            pk::round_result(0, 1, (180, 30), 0, (0, 0, 0), &[])
        } else {
            pk::round_begin(0, 180_000, 30_000, 0)
        };
        let _ = tx.send(r);
    }
    if cfg.play_start > 0.0 {
        wait(cfg.play_start).await;
        let _ = tx.send(pk::round_start(map, 0, 10000, (1, 1, 12345), (1, 1)));
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
