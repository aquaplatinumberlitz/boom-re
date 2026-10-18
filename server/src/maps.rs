//! Battle map table (opcode 231 / 234), ported from tools/fakeserver.py + tools/idf.py.

use std::path::Path;

use crate::packets::Le;

/// (display name, theme folder, map file, index in the client's CPlayMapInfoList = position among Map/* in fx.idx)
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BattleMap {
    pub name: String,
    pub theme: String,
    pub file: String,
    pub idx: u16,
}

impl BattleMap {
    pub fn new(name: &str, theme: &str, file: &str, idx: u16) -> Self {
        BattleMap { name: name.into(), theme: theme.into(), file: file.into(), idx }
    }
}

/// The three hand-made maps (dyn index 0..2), as in fakeserver BATTLE_MAPS.
pub fn default_maps() -> Vec<BattleMap> {
    vec![
        BattleMap::new("Village01", "Village", "Village01.map", 954),
        BattleMap::new("Forest01", "Forest", "Forest01.map", 223),
        BattleMap::new("Camp01", "Camp", "Camp01.map", 104),
    ]
}

/// Inner bytes (tag 0 + data) of the opcode 231 blob, parsed by sub_6E077C into 128-byte CDynamicMapMan records
/// (field list: fakeserver.dyn_map_blob).
pub fn dyn_map_blob(maps: &[BattleMap], mode: u8) -> Vec<u8> {
    let mut b = Le::default();
    b.u8(0).u16(maps.len() as u16);
    for (i, m) in maps.iter().enumerate() {
        b.u32(i as u32 + 1).u8(mode).str(&m.name).str(&m.name).u8(0).u8(1).str(&m.theme).str(&m.file);
        b.u8(0).u8(1).u32(0x00FF_FFFF).u8(0).u8(1).u8(0).u16(m.idx).u8(0).u32(0);
    }
    b.0
}

/// zlib.adler32(data, 0): Adler-32 seeded with 0 (sub_A0E1E0).
pub fn adler32_seed0(data: &[u8]) -> u32 {
    let (mut a, mut b) = (0u32, 0u32);
    for &x in data {
        a = (a + x as u32) % 65521;
        b = (b + a) % 65521;
    }
    (b << 16) | a
}

const FX_KEY: u32 = 1_906_092_848;

/// PackFS__DecryptIdx 0xA355B0
fn decrypt_idx(data: &[u8], key: u32) -> Vec<u8> {
    let n = data.len() / 4;
    let mut out = Vec::with_capacity(data.len());
    let mut prev = key;
    for i in 0..n {
        let x = u32::from_le_bytes(data[4 * i..4 * i + 4].try_into().unwrap());
        prev = if i == 0 { x ^ key } else { prev ^ x };
        out.extend_from_slice(&prev.to_le_bytes());
    }
    for (j, &b) in data[4 * n..].iter().enumerate() {
        out.push(b ^ (prev >> (8 * j)) as u8);
    }
    out
}

/// Entry names of a decrypted .idx (PackFS__AttachIdf 0xA388C0).
fn idx_names(buf: &[u8]) -> Vec<String> {
    let rd = |o: usize| u32::from_le_bytes(buf[o..o + 4].try_into().unwrap());
    let (count, mut off, extra) = if rd(0) == 0 { (rd(8), 12, true) } else { (rd(0), 4, false) };
    let mut names = Vec::with_capacity(count as usize);
    for _ in 0..count {
        let nl = rd(off) as usize;
        off += 4;
        names.push(String::from_utf8_lossy(&buf[off..off + nl]).into_owned());
        off += nl + 12 + if extra { 4 } else { 0 };
    }
    names
}

/// Every Map/* entry of fx.idx (1019); the 3 hand-made maps keep dyn index 0..2, the rest follow in idx order.
/// Theme = longest Theme/* folder prefixing the name (after NXCL_/WS_/WinningStreak_), else "ThemeDefault".
pub fn all_battle_maps(boom_dir: &Path) -> std::io::Result<Vec<BattleMap>> {
    let names = idx_names(&decrypt_idx(&std::fs::read(boom_dir.join("fx.idx"))?, FX_KEY));
    let set: std::collections::BTreeSet<&str> =
        names.iter().filter_map(|n| n.strip_prefix("Theme/")?.split('/').next()).collect();
    let mut themes: Vec<&str> = set.into_iter().collect();
    themes.sort_by_key(|t| std::cmp::Reverse(t.len()));
    let theme = |name: &str| -> String {
        let base = ["NXCL_", "WS_", "WinningStreak_"].iter().find_map(|p| name.strip_prefix(p)).unwrap_or(name);
        let base = base.to_lowercase();
        themes.iter().find(|t| base.starts_with(&t.to_lowercase())).map_or("ThemeDefault".into(), |t| t.to_string())
    };
    let mut out = default_maps();
    let first: Vec<String> = out.iter().map(|m| m.name.clone()).collect();
    for (i, n) in names.iter().filter_map(|n| n.strip_prefix("Map/")).enumerate() {
        if !first.iter().any(|f| f == n) {
            out.push(BattleMap::new(n, &theme(n), &format!("{n}.map"), i as u16));
        }
    }
    Ok(out)
}
