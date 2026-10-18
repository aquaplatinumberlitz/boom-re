// C->S 111 parse + S->C 152 must match tools/fakeserver.py byte for byte (sample from logs/xvfb/place1).
use boom_server::packets as pk;

fn unhex(s: &str) -> Vec<u8> {
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect()
}

#[test]
fn bomb_record_and_152_match_fakeserver() {
    let body = unhex("a50696ca74855a5a96ca53955a545b5a5a5a5b96ca53945a");
    let r = pk::parse_bomb_record(&body).unwrap();
    assert_eq!((r.key, r.ctx, r.slot, r.serial, r.y, r.x, r.power, r.r18, r.r1c, r.flag), (10000, 0, 0, 0, 0, 14, 1, 1, 1, 0));
    let p = pk::bomb_placed(&r, 1);
    let want = unhex("a5f15a5aa56996ca539596ca539596ca53955a545b96ca53945aa568a5695b0000000071b185895a5a");
    assert_eq!(&p[..], &want[..], "152 body differs");
}
