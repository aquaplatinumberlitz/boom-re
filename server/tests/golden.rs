//! Byte-for-byte check against tools/fakeserver.py (regenerate: python3 tools/gen_golden.py > server/tests/golden.txt).

use std::collections::HashMap;

use boom_server::maps::default_maps;
use boom_server::packets as pk;
use boom_server::proto::{self, SeqState};

fn golden() -> HashMap<String, Vec<u8>> {
    include_str!("golden.txt")
        .lines()
        .filter_map(|l| l.split_once(' '))
        .map(|(k, h)| (k.to_string(), (0..h.len()).step_by(2).map(|i| u8::from_str_radix(&h[i..i + 2], 16).unwrap()).collect()))
        .collect()
}

#[test]
fn builders_match_fakeserver() {
    let g = golden();
    let maps = default_maps();
    let mut ours: Vec<(String, Vec<u8>)> = vec![
        ("hello".into(), pk::hello_packet(0, 116)),
        ("login_ok".into(), pk::login_ok("tester", 1)),
        ("login_net_info".into(), pk::login_net_info("127.0.0.1", [0, 0, 0])),
        ("channel_list".into(), pk::channel_list(&["Kenh 1", "Kenh 2", "Kenh 3", "Kenh 4"], 100)),
        ("channel_status".into(), pk::channel_status(&[10, 20, 30, 40])),
        ("channel_join_ok".into(), pk::channel_join_ok([127, 0, 0, 1], 4848, 10, 0)),
        ("channel_enter_ok".into(), pk::channel_enter_ok([2026, 10, 18, 10, 20, 30])),
        ("square_info".into(), pk::square_info(1, "LobbySquare01", "Square")),
        ("square_users".into(), pk::square_users()),
        ("room_list".into(), pk::room_list()),
        ("map_checksums".into(), pk::map_checksums(&maps)),
        ("dyn_map_info".into(), pk::dyn_map_info(&maps)),
        ("create_room_ok".into(), pk::create_room_ok(1, 19, 0)),
        ("room_player".into(), pk::room_player(0, 1000, "tester", true, 0, 0)),
        ("room_slot_state".into(), pk::room_slot_state(0, true, false, 0, 0)),
        ("room_map".into(), pk::room_map(0, 0)),
        ("match_start".into(), pk::match_start(&maps[0], 0, 19, 12345, &[(0, 0, 0)])),
        ("round_go".into(), pk::round_go((120, 30), 0, 0, 0)),
        ("round_begin".into(), pk::round_begin(0, 180_000, 30_000, 0)),
        ("round_result".into(), pk::round_result(0, 1, (180, 30), 0, (0, 0, 0), &[(0, [(1, 2), (3, 4), (5, 6)])])),
    ];
    for m in [0u8, 1, 2, 4] {
        ours.push((format!("round_start_{m}"), pk::round_start(&maps[0], m, 10000, (1, 1, 12345), (1, 1))));
    }
    for (i, r) in pk::login_replies().into_iter().enumerate() {
        ours.push((format!("login_reply_{i}"), r));
    }
    for (name, bytes) in &ours {
        assert_eq!(Some(bytes), g.get(name), "{name}");
    }
}

#[test]
fn framing_matches_fakeserver() {
    let g = golden();
    let mut st = SeqState::default();
    st.seq_r += st.dseq_r;
    for (name, body) in [("frame_0", pk::login_replies().remove(0)), ("frame_1", pk::login_ok("tester", 1))] {
        let f = proto::build(&body, 3, 2, st.recv_seq_byte(), st.seq_r, st.header_type);
        st.seq_r += st.dseq_r;
        assert_eq!(&f, &g[name], "{name}");
    }
    // client -> server: parse the Python-built frame back to its body
    let st = SeqState::default();
    let frame = &g["c2s_frame"];
    assert_eq!(proto::frame_len(frame, 2, 2), Some(frame.len()));
    assert_eq!(proto::parse(frame, 2, 2, st.seq_s, 0).unwrap(), g["c2s_body"]);
    assert_eq!(frame[0], st.send_seq_byte());
}

/// Full fx.idx map list (needs the client files; skipped when absent). Expected values from
/// `ALL_MAPS=1` tools/fakeserver.py: 1019 maps, adler32(dyn_map_blob, 0) below.
#[test]
fn all_maps_match_fakeserver() {
    let dir = std::path::PathBuf::from(std::env::var_os("HOME").unwrap_or_default()).join("Downloads/Boom");
    if !dir.join("fx.idx").exists() {
        return;
    }
    let maps = boom_server::maps::all_battle_maps(&dir).unwrap();
    assert_eq!(maps.len(), 1019);
    assert_eq!(boom_server::maps::adler32_seed0(&boom_server::maps::dyn_map_blob(&maps, 0)), 2_017_163_367);
}
