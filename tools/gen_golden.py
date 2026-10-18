"""Golden vectors for the Rust server (server/tests/golden.txt): every S->C builder of tools/fakeserver.py plus a few
framed packets, as `name hex` lines. The Rust tests rebuild the same packets and must match byte for byte.

usage: python3 tools/gen_golden.py > server/tests/golden.txt
"""
import datetime, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import boomproto as bp
import fakeserver as fs

FIXED_NOW = datetime.datetime(2026, 10, 18, 10, 20, 30)


def main():
    out = []

    def add(name, data):
        out.append(f"{name} {bytes(data).hex()}")

    add("hello", fs.hello_packet())
    for i, r in enumerate(fs.login_replies()):
        add(f"login_reply_{i}", r)
    add("login_ok", fs.login_ok())
    add("login_net_info", fs.login_net_info())
    add("channel_list", fs.channel_list())
    add("channel_status", fs.channel_status())
    add("channel_join_ok", fs.channel_join_ok(port=4848))
    add("channel_enter_ok", fs.channel_enter_ok(now=FIXED_NOW))
    add("square_info", fs.square_info())
    add("square_users", fs.square_users())
    add("room_list", fs.room_list())
    add("map_checksums", fs.map_checksums())
    add("dyn_map_info", fs.dyn_map_info())
    add("create_room_ok", fs.create_room_ok(room_type=19))
    add("room_player", fs.room_player())
    add("room_slot_state", fs.room_slot_state())
    add("room_map", fs.room_map(0))
    add("match_start", fs.match_start())
    for m in (0, 1, 2, 4):
        add(f"round_start_{m}", fs.round_start(mode=m))
    add("round_go", fs.round_go())
    add("round_begin", fs.round_begin())
    add("round_result", fs.round_result(slots={0: [(1, 2), (3, 4), (5, 6)]}))
    # framing: server->client frames of a fresh session (hello consumed one recv step)
    sess = fs.Session()
    sess.st.seq_r += sess.st.dseq_r
    add("frame_0", sess.send(fs.login_replies()[0]))
    add("frame_1", sess.send(fs.login_ok()))
    # client->server frame (format (2,2), key seq_s) for the parse direction
    st = bp.SeqState()
    body = fs.obf_body(1, ("u8", 1), ("str", "tester"), ("str", "1234"))
    seq_byte = ((st.header_type + st.modif) ^ (st.base_s + st.seq_s)) & 0xFF
    add("c2s_body", body)
    add("c2s_frame", bp.build(body, 2, 2, seq_byte, st.seq_s, st.header_type))
    print("\n".join(out))


if __name__ == "__main__":
    main()
