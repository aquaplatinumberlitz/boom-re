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

#[test]
fn item_pick_158_and_553_match_fakeserver() {
    let r = pk::parse_item_pick(&unhex("a51c5a5a5a57a569a46996ca470a96ca74855a")).unwrap();
    assert_eq!((r.ctx, r.slot, r.a, r.b, r.index, r.kind, r.key), (0, 0, 0, 13, 0, 256, 10000));
    assert_eq!(pk::item_picked(&r), unhex("a5f75b5a5a5a57a569a4695a"));
    assert_eq!(pk::map_items(&[], &[(0, 13, 0, 1)]), unhex("a74096ca538196ca5c8d96ca539596ca539496cb5e9596ca5395"));
}
