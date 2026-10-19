"""Trích chữ KR + VN của Boom Online → l10n/catalog.csv (UTF-8) cho engine Rust viết lại.

Đọc pack bằng tools/idf.py (không copy code), KR dùng khoá tự thân = 4 byte đầu .idx (boomkr-re/docs/kr.md §16).
Định dạng từng nguồn: l10n/README.md.

  python3 tools/l10n_extract.py sources            # quét nguồn → l10n/.cache/sources.json (chậm, ~1-2 phút)
  python3 tools/l10n_extract.py catalog            # sources + tm.csv → catalog.csv, glossary.csv, stats
  python3 tools/l10n_extract.py todo [-n 300] [--src csysstr] OUT.tsv   # chuỗi Hàn chưa dịch (duy nhất)
  python3 tools/l10n_extract.py import IN.tsv [--status translated]     # gộp bản dịch vào l10n/tm.csv
  python3 tools/l10n_extract.py images             # → l10n/images_todo.csv
  python3 tools/l10n_extract.py stats

Thư mục: --kr (mặc định $BOOMKR_DIR hoặc /home/admin/boom-re/boomKR), --vn (~/Downloads/Boom),
--kr-exe (boomkr-re/out/kr-full.exe, image đã unpack, chỉ đọc), --vn-strings (boom-re/server/src/strings.rs).
"""
import argparse
import csv
import hashlib
import json
import os
import re
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import idf  # noqa: E402  (reader pack của boom-re)

ROOT = HERE.parent
L10N = ROOT / "l10n"
CACHE = L10N / ".cache"
BOOM_RE = Path(os.environ.get("BOOM_RE", "/home/admin/boom-re"))
DEF_KR = Path(os.environ.get("BOOMKR_DIR", BOOM_RE / "boomKR"))
DEF_VN = Path(os.environ.get("BOOM_VN_DIR", Path.home() / "Downloads/Boom"))
DEF_KR_EXE = Path(os.environ.get("BOOMKR_RE", "/home/admin/boomkr-re")) / "out/kr-full.exe"
DEF_VN_STRINGS = BOOM_RE / "server/src/strings.rs"

HANGUL = re.compile("[\uac00-\ud7a3\u3131-\u318e]")
csv.field_size_limit(1 << 26)


# ---------------------------------------------------------------- pack

def iter_pack(root, stem, self_key):
    """(name, blob) của một pack. self_key: KR, khoá = dword đầu .idx; VN: idf.KEYS."""
    root = Path(root)
    data = (root / (stem + ".idx")).read_bytes()
    key = struct.unpack_from("<I", data)[0] if self_key else idf.KEYS[stem]
    _, ents, _ = idf.parse_idx(idf.decrypt_idx(data, key))
    with open(root / (stem + ".idd"), "rb") as f:
        for name, off, size, c, d in ents:
            f.seek(off)
            try:
                blob = idf.unpack_entry(name, f.read(size), c, d)
            except Exception:  # crc/zlib hỏng: bỏ qua entry
                continue
            yield name, blob


def pack_stems(root, kr):
    if kr:
        return sorted(p.stem for p in Path(root).glob("*.idx"))
    return [s for s in idf.KEYS if (Path(root) / (s + ".idx")).exists()]


def read_entries(root, kr, wanted):
    """{(stem, name): blob} cho các entry thoả wanted(stem, name)."""
    out = {}
    for stem in pack_stems(root, kr):
        for name, blob in iter_pack(root, stem, kr):
            if wanted(stem, name):
                out[(stem, name)] = blob
    return out


# ---------------------------------------------------------------- định dạng

def lstr(b, o, enc="cp949"):
    n = struct.unpack_from("<I", b, o)[0]
    return b[o + 4:o + 4 + n].decode(enc), o + 4 + n


def ssd_raw(path):
    """.ssd: 'ssi1', u32 ?, u8 0x18, u32 comp_len, u32 raw_len (offset 14), zlib từ offset 0x12."""
    b = Path(path).read_bytes()
    if b[:4] != b"ssi1":
        raise ValueError("not ssi1: %s" % path)
    raw = zlib.decompress(b[0x12:])
    if len(raw) != struct.unpack_from("<I", b, 14)[0]:
        raise ValueError("raw_len mismatch: %s" % path)
    return raw


def ssd_pairs(raw):
    """csysstr / csysqstr: u16 count, count × (lstr key, lstr value)."""
    n = struct.unpack_from("<H", raw)[0]
    o, out = 2, []
    for _ in range(n):
        k, o = lstr(raw, o)
        v, o = lstr(raw, o)
        out.append((k, v))
    assert o == len(raw), "trailing bytes"
    return out


def ssd_fxmg(raw):
    """csysfxmg: u16 count, count × (u8 kind, lstr text)."""
    n = struct.unpack_from("<H", raw)[0]
    o, out = 2, []
    for _ in range(n):
        kind = raw[o]
        s, o = lstr(raw, o + 1)
        out.append((kind, s))
    return out


def ssd_strlist(raw):
    """spcc: u16 count, count × lstr (câu hỏi bảo mật); phần sau là mật khẩu cấm + URL."""
    n = struct.unpack_from("<H", raw)[0]
    o, out = 2, []
    for _ in range(n):
        s, o = lstr(raw, o)
        out.append(s)
    return out


def ssd_channels(raw):
    """channel2_001: u16 count, count × (lstr name, 27 byte cấu hình)."""
    n = struct.unpack_from("<H", raw)[0]
    o, out = 2, []
    for _ in range(n):
        s, o = lstr(raw, o)
        out.append(s)
        o += 27
    assert o == len(raw)
    return out


def ssd_dynmaps(raw):
    """fxdynmapinfo (= blob opcode 231 không có tag): u16 count, mỗi record
    u32 id, u8 mode, lstr name, lstr display, u8, u8, lstr theme, lstr file, u8, u8, u32 color, u8, u8, u8, u16 idx, u8, u32
    (cùng thứ tự với dyn_map_blob trong server/src/maps.rs)."""
    n = struct.unpack_from("<H", raw)[0]
    o, out = 2, []
    for _ in range(n):
        mid, mode = struct.unpack_from("<IB", raw, o)
        o += 5
        name, o = lstr(raw, o)
        disp, o = lstr(raw, o)
        o += 2
        theme, o = lstr(raw, o)
        file, o = lstr(raw, o)
        o += 2 + 4 + 3 + 2 + 1 + 4
        out.append((mid, mode, name, disp, theme, file))
    assert o == len(raw), (o, len(raw))
    return out


def scan_lstr(raw, enc="cp949"):
    """Dự phòng: mọi lstr (u32 len + chuỗi) có chữ Hàn."""
    out, i = [], 0
    while i + 4 <= len(raw):
        n = struct.unpack_from("<I", raw, i)[0]
        if 0 < n < 4096 and i + 4 + n <= len(raw):
            try:
                s = raw[i + 4:i + 4 + n].decode(enc)
            except UnicodeDecodeError:
                s = None
            if s and HANGUL.search(s) and all(c >= " " or c in "\r\n\t" for c in s):
                out.append((i, s))
                i += 4 + n
                continue
        i += 1
    return out


def xml_elems(text):
    """ClientString: <Elem><LangID/><key/><string/></Elem>."""
    out = []
    for m in re.finditer(r"<Elem>(.*?)</Elem>", text, re.S):
        k = re.search(r"<key>(.*?)</key>", m.group(1), re.S)
        v = re.search(r"<string>(.*?)</string>", m.group(1), re.S)
        if k:
            out.append((xml_unescape(k.group(1)), xml_unescape(v.group(1)) if v else ""))
    return out


def xml_unescape(s):
    return (s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
            .replace("&apos;", "'").replace("&#10;", "\n").replace("&#13;", "\r").replace("&amp;", "&"))


def clientstring_kr(blob):
    """KR: u32 len + XML cp949."""
    return xml_elems(blob[4:].decode("cp949"))


def clientstring_vn(blob):
    """VN: u32 len + BOM FFFE + XML UTF-16LE."""
    i = blob.find(b"\xff\xfe")
    return xml_elems(blob[i + 2:].decode("utf-16-le"))


def excel_rows(blob):
    """Excel 2003 XML (SpeakerTable…): u32 len + UTF-8."""
    s = blob[4:].decode("utf-8", "replace")
    rows = []
    for r in re.findall(r"<Row[^>]*>(.*?)</Row>", s, re.S):
        rows.append([xml_unescape(c) for c in re.findall(r"<Data[^>]*>(.*?)</Data>", r, re.S)])
    return rows


def lua_strings(text):
    """Literal "…" có chữ Hàn trong script quest Lua, bỏ comment '--'."""
    out = []
    for ln, line in enumerate(text.splitlines()):
        code = re.sub(r'--.*$', "", line) if '"' not in line.split("--")[0] else line
        for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', code):
            if HANGUL.search(m.group(1)) and "--" not in line[:m.start()]:
                out.append((ln + 1, m.group(1)))
    return out


SAY_RE = re.compile(r'\b(say\d\d)\s*=\s*"([^"]*)"')


def map_says(blob):
    """<mapscript> trong .map: thuộc tính sayNN của action Say (chữ hiển thị trên bong bóng)."""
    i = blob.find(b"<mapscript")
    if i < 0:
        return []
    s = re.sub(r"<!--.*?-->", "", blob[i:].decode("cp949", "replace"), flags=re.S)
    return [(m.group(1), m.group(2)) for m in SAY_RE.finditer(s)]


EXE_STR = re.compile(rb"(?<=\x00)(?:[\x09\x0a\x0d\x20-\x7e]|[\xa1-\xc8][\xa1-\xfe]){2,}(?=\x00)")
DEV_HINT = re.compile(r"잘못된 |Error|에러|크래쉬|루아|스크립트|액션리스트|ActionList|디버그|테스트|로그|%s\s*$|0x|\.cpp|::|걍")


def exe_strings(path):
    """Chuỗi cp949 kết thúc NUL có ≥3 âm tiết Hàn liền nhau (ngưỡng lọc nhiễu khi đọc code thành chữ)."""
    b = Path(path).read_bytes()
    out, seen = [], set()
    for m in EXE_STR.finditer(b):
        s = m.group(0).decode("cp949", "ignore")
        if len(s) >= 4 and re.search("[\uac00-\ud7a3]{3,}", s) and s not in seen:
            seen.add(s)
            out.append((m.start(), s))
    return out


def vn_strings_rs(path):
    if not Path(path).exists():
        return []
    return re.findall(r'\("([^"]+)",\s*"((?:[^"\\]|\\.)*)"\)', Path(path).read_text("utf-8"))


# ---------------------------------------------------------------- nguồn → rows

def row(id_, source, ko, vi_base="", base_src="", ctx=""):
    return {"id": id_, "source": source, "ko": ko, "vi_base": vi_base, "base_src": base_src, "ctx": ctx}


def collect(a):
    kr, vn = Path(a.kr), Path(a.vn)
    rows = []
    want_kr = lambda st, n: (n in ("ClientData/ClientString", "ObjectTable/SpeakerTable", "Help/Help",
                                   "NoticeImg/Contract", "NoticeImg/Notice2PW", "StageCredit/Credit",
                                   "CustomMap/CustomTileList")
                             or n.startswith("Quest/c") or n.startswith("CustomMap/CustomMap_")
                             or (st == "FxMap" and n.startswith("Map/")))
    want_vn = lambda st, n: n in ("ClientData/ClientString",) or n.startswith("Map/")
    print("đọc pack KR…", file=sys.stderr)
    K = read_entries(kr, True, want_kr)
    print("đọc pack VN…", file=sys.stderr)
    V = read_entries(vn, False, want_vn)
    vnmap = {n: b for (st, n), b in V.items()}

    # VN base: ClientString (lời thoại NPC, VN gốc) + strings.rs (chuỗi UI tự viết của boom-re)
    vn_cs = {}
    for k, v in clientstring_vn(vnmap["ClientData/ClientString"]):
        vn_cs.setdefault(k, v)
    vn_rs = {k: v.replace('\\"', '"').replace("\\n", "\n") for k, v in vn_strings_rs(a.vn_strings) if v}

    def base(key):
        if key in vn_cs:
            return vn_cs[key], "vn:fx/ClientData/ClientString"
        if key in vn_rs:
            return vn_rs[key], "boom-re:server/src/strings.rs"
        return "", ""

    # 1+2. FxClientString: csysstr.ssd (server cache) + FxDesktop/ClientData/ClientString (pack), chung không gian khoá
    sysstr = ssd_pairs(ssd_raw(kr / "csysstr.ssd"))
    cs = {}
    for k, v in clientstring_kr(K[("FxDesktop", "ClientData/ClientString")]):
        cs.setdefault(k, v)
    seen = set()
    for k, v in sysstr:
        if k in seen:
            continue
        seen.add(k)
        src = "csysstr.ssd"
        if k in cs and cs[k] == v:
            src += "+FxDesktop/ClientData/ClientString"
        rows.append(row(k, src, v, *base(k)))
        if k in cs and cs[k] != v:
            rows.append(row(k + "@ClientString", "FxDesktop/ClientData/ClientString", cs[k], *base(k),
                            ctx="dup_key_diff"))
    for k, v in cs.items():
        if k not in seen:
            rows.append(row(k, "FxDesktop/ClientData/ClientString", v, *base(k)))
    # khoá VN không còn trong KR: giữ để không mất bản dịch (ko rỗng)
    for k, v in vn_cs.items():
        if k not in seen and k not in cs:
            rows.append(row(k, "vn-only:fx/ClientData/ClientString", "", v, "vn:fx/ClientData/ClientString",
                            ctx="vn_only"))

    # 3. FxQuestString
    for k, v in ssd_pairs(ssd_raw(kr / "csysqstr.ssd")):
        rows.append(row("q:" + (k.strip() or "<empty>"), "csysqstr.ssd", v))
    # 4. tip (FxMessageTable)
    for i, (kind, s) in enumerate(ssd_fxmg(ssd_raw(kr / "csysfxmg.ssd"))):
        rows.append(row("csysfxmg.ssd:%d" % i, "csysfxmg.ssd", s, ctx="kind=%d" % kind))
    # 5. tên map hiển thị
    seen = set()
    for mid, mode, name, disp, theme, file in ssd_dynmaps(ssd_raw(kr / "fxdynmapinfo.ssd")):
        if name in seen:  # cùng map ở nhiều chế độ
            continue
        seen.add(name)
        rows.append(row("map:" + name, "fxdynmapinfo.ssd", disp, ctx="theme=%s file=%s" % (theme, file)))
    # 6. kênh, 7. server, 8. câu hỏi bảo mật
    for i, s in enumerate(ssd_channels(ssd_raw(kr / "channel2_001.ssd"))):
        rows.append(row("channel2_001.ssd:%d" % i, "channel2_001.ssd", s))
    for off, s in scan_lstr(ssd_raw(kr / "multisvr.ssd")):
        rows.append(row("multisvr.ssd:%d" % off, "multisvr.ssd", s))
    for i, s in enumerate(ssd_strlist(ssd_raw(kr / "spcc.ssd"))):
        rows.append(row("spcc.ssd:%d" % i, "spcc.ssd", s))

    # 9. SpeakerTable: cột Name
    rws = excel_rows(K[("fx", "ObjectTable/SpeakerTable")])
    hdr = rws[0]
    for r in rws[1:]:
        if len(r) > 1 and HANGUL.search(r[1]):
            rows.append(row("fx:ObjectTable/SpeakerTable:%s" % r[0], "fx/ObjectTable/SpeakerTable", r[1], ctx="Name"))
    # 10. Help (từng dòng)
    for i, line in enumerate(K[("FxDesktop", "Help/Help")].decode("cp949").split("\r\n")):
        if HANGUL.search(line):
            rows.append(row("FxDesktop:Help/Help:%d" % i, "FxDesktop/Help/Help", line))
    # 11. Quest Lua
    for (st, n), b in sorted(K.items()):
        if n.startswith("Quest/c"):
            for ln, s in lua_strings(b.decode("cp949", "replace")):
                rows.append(row("%s:%s:%d" % (st, n, ln), "%s/%s" % (st, n), s, ctx="lua"))
    # 12. CustomMap: Desc (UTF-8 XML)
    for (st, n), b in sorted(K.items()):
        if n.startswith("CustomMap/"):
            s = b[4:].decode("utf-8", "replace")
            s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
            for j, m in enumerate(re.finditer(r'\b(Desc|Name|Title)="([^"]*)"', s)):
                if HANGUL.search(m.group(2)):
                    rows.append(row("%s:%s:%s#%d" % (st, n, m.group(1), j), "%s/%s" % (st, n),
                                    xml_unescape(m.group(2)), ctx=m.group(1)))
    # 13. lời thoại trong map script
    for (st, n), b in sorted(K.items()):
        if st == "FxMap" and n.startswith("Map/"):
            vs = map_says(vnmap[n]) if n in vnmap else []
            for j, (attr, s) in enumerate(map_says(b)):
                if not HANGUL.search(s):
                    continue
                vb, vsrc = "", ""
                if j < len(vs) and vs[j][0] == attr and vs[j][1] != s and not HANGUL.search(vs[j][1]):
                    v = vs[j][1]
                    # VN thay chữ bằng khoá ClientString (vd. 'mongolem12default14')
                    k = next((x for x in (v, v.lower()) if x in vn_cs), None) or \
                        next((x for x in vn_cs if x.lower() == v.lower()), None)
                    vb, vsrc = (vn_cs[k], "vn:fx/%s→ClientString:%s" % (n, k)) if k else (v, "vn:fx/" + n)
                rows.append(row("%s:%s:%s#%d" % (st, n, attr, j), "%s/%s" % (st, n), s, vb, vsrc, ctx="say"))
    # 14. văn bản pháp lý: liệt kê, không dịch
    for n in ("NoticeImg/Contract", "NoticeImg/Notice2PW"):
        rows.append(row("FxDesktop:" + n, "FxDesktop/" + n, K[("FxDesktop", n)].decode("cp949"), ctx="legal"))
    # 15. credit
    for i, line in enumerate(K[("FxStage", "StageCredit/Credit")].decode("cp949").split("\r\n")):
        if HANGUL.search(line):
            rows.append(row("FxStage:StageCredit/Credit:%d" % i, "FxStage/StageCredit/Credit", line.strip(), ctx="credit"))
    # 16. exe KR (image đã unpack; chỉ đọc)
    if Path(a.kr_exe).exists():
        for off, s in exe_strings(a.kr_exe):
            rows.append(row("exe:kr-full.exe:0x%x" % off, "exe:" + Path(a.kr_exe).name, s,
                            ctx="dev_debug" if DEV_HINT.search(s) else ""))
    return rows


def cmd_sources(a):
    rows = collect(a)
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "sources.json").write_text(json.dumps(rows, ensure_ascii=False))
    print("%d chuỗi → %s" % (len(rows), CACHE / "sources.json"))


# ---------------------------------------------------------------- translation memory

TM = L10N / "tm.csv"
TM_FIELDS = ["ko", "vi", "status", "notes"]


def load_tm():
    if not TM.exists():
        return {}
    with open(TM, newline="", encoding="utf-8") as f:
        return {r["ko"]: r for r in csv.DictReader(f)}


def save_tm(tm):
    with open(TM, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, TM_FIELDS, lineterminator="\n")
        w.writeheader()
        for k in sorted(tm):
            w.writerow({x: tm[k].get(x, "") for x in TM_FIELDS})


def esc(s):
    return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")


def unesc(s):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            out.append({"t": "\t", "r": "\r", "n": "\n", "\\": "\\"}.get(s[i + 1], "\\" + s[i + 1]))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def load_sources():
    return json.loads((CACHE / "sources.json").read_text())


def needs_translation(r):
    return r["ko"] and not r["vi_base"] and HANGUL.search(r["ko"]) and r["ctx"] != "legal"


def cmd_todo(a):
    tm = load_tm()
    rows = load_sources()
    seen, out = set(), []
    for r in rows:
        if a.src and not r["source"].startswith(a.src) and not r["id"].startswith(a.src):
            continue
        k = r["ko"]
        if needs_translation(r) and k not in tm and k not in seen:
            seen.add(k)
            out.append(k)
    out = out[:a.n]
    with open(a.out, "w", encoding="utf-8") as f:
        for i, k in enumerate(out):
            f.write("%d\t%s\n" % (i, esc(k)))
    print("%d chuỗi → %s" % (len(out), a.out))


def cmd_import(a):
    """IN.tsv: 'n<TAB>vi' (hoặc 'n<TAB>vi<TAB>status<TAB>notes'), n tham chiếu file todo cùng tên bỏ đuôi .vi."""
    tm = load_tm()
    src = Path(a.todo or re.sub(r"\.vi\.tsv$", ".tsv", a.inp))
    ko = {}
    for line in src.read_text("utf-8").splitlines():
        n, s = line.split("\t", 1)
        ko[n] = unesc(s)
    added = 0
    for line in Path(a.inp).read_text("utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        n, vi = parts[0], unesc(parts[1]) if len(parts) > 1 else ""
        st = parts[2] if len(parts) > 2 and parts[2] else a.status
        notes = parts[3] if len(parts) > 3 else ""
        if n not in ko:
            print("bỏ qua n=%s (không có trong %s)" % (n, src), file=sys.stderr)
            continue
        tm[ko[n]] = {"ko": ko[n], "vi": vi, "status": st, "notes": notes}
        added += 1
    save_tm(tm)
    print("+%d → %s (%d mục)" % (added, TM, len(tm)))


# ---------------------------------------------------------------- catalog

PH = re.compile(r"%[-+ #0]*\d*(?:\.\d+)?(?:l|h|I64)?[sdiufxXcp%]|\{[^{}]*\}|<[^<>]+>")
PRINTF = re.compile(r"%[-+ #0]*\d*(?:\.\d+)?(?:l|h|I64)?[sdiufxXcp]")
PH_LINES = re.compile(r"\r?\n|\|")
NUM = re.compile(r"\d+")


def placeholders(s, lines=False):
    """printf, {..}, <tag>; lines=True thêm xuống dòng và '|' (ngắt dòng của multisvr)."""
    return sorted(PH.findall(s)) + (sorted(x.replace("\r", "") for x in PH_LINES.findall(s)) if lines else [])


TM_ID = L10N / "tm_id.csv"   # ghi đè theo id (khoá trùng nhưng nghĩa KR khác bản VN…): id, vi, status, notes


def load_tm_id():
    if not TM_ID.exists():
        return {}
    with open(TM_ID, newline="", encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


NAM_BO = L10N / "nam_bo.csv"   # từ Bắc → Nam (giọng miền Nam), áp lên mọi bản dịch ở bước catalog


def load_nam_bo():
    """[(regex, nam)]: mỗi mục khớp trọn âm tiết, không phân biệt hoa thường; giữ hoa chữ đầu / viết hoa toàn bộ."""
    if not NAM_BO.exists():
        return []
    with open(NAM_BO, newline="", encoding="utf-8") as f:
        return [(re.compile(r"(?<!\w)(?:%s)(?!\w)" % r["bac"], re.I), r["nam"]) for r in csv.DictReader(f)]


def nam_bo(s, lex):
    def keep_case(m, nam):
        w = m.group(0)
        if w.isupper() and len(w) > 1:
            return nam.upper()
        return nam[:1].upper() + nam[1:] if w[:1].isupper() else nam
    for rx, nam in lex:
        s = rx.sub(lambda m: keep_case(m, nam), s)
    return s


def cmd_catalog(a):
    lex = ()
    rows = load_sources()
    tm = load_tm()
    tid = load_tm_id()
    out = []
    for r in rows:
        ko, vb = r["ko"], r["vi_base"]
        notes = [r["ctx"]] if r["ctx"] else []
        if r["id"] in tid:
            t = tid[r["id"]]
            vi, status = t["vi"], t["status"] or "review"
            if vb:
                notes.append("vi_base=" + r["base_src"])
            notes.append(t["notes"] or "override")
        elif vb:
            vi, status = vb, "reused"
            notes.append("vi_base=" + r["base_src"])
            if ko and placeholders(ko) != placeholders(vb):
                status = "review"
                notes.append("kr_changed?")
        elif r["ctx"] == "legal":
            vi, status = "", "review"
            notes.append("not_translated: thay bằng điều khoản của dự án")
        elif not HANGUL.search(ko):
            vi, status = ko, "translated"
            notes.append("no_hangul")
        elif ko in tm and tm[ko]["vi"] != "":
            t = tm[ko]
            vi, status = t["vi"], t["status"] or "translated"
            if t["notes"]:
                notes.append(t["notes"])
            if placeholders(ko, True) != placeholders(vi, True):
                status = "review"
                notes.append("placeholder_mismatch")
            elif PRINTF.findall(ko) != PRINTF.findall(vi):
                status = "review"
                notes.append("placeholder_order")  # printf không có %1$: đổi thứ tự là sai tham số
        else:
            vi, status = "", "review"
            notes.append("untranslated")
        if vi and ko and len(vi) > 1.6 * len(ko) and status != "reused":
            notes.append("too_long?")
        out.append({"id": r["id"], "source": r["source"], "ko": ko, "vi_base": vb, "vi": vi,
                    "status": status, "notes": ";".join(notes)})
    with open(L10N / "catalog.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["id", "source", "ko", "vi_base", "vi", "status", "notes"], lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    write_glossary(out, lex)
    print_stats(out)


GLOSS_FIELDS = ["ko", "vi", "kind", "source", "count"]


def write_glossary(cat, lex=()):
    """Thuật ngữ: cặp ngắn (≤ 12 ký tự Hàn, không dấu câu) đã có bản Việt; cộng l10n/glossary_seed.csv (biên soạn tay)."""
    terms = {}
    seed = L10N / "glossary_seed.csv"
    if seed.exists():
        with open(seed, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                terms[r["ko"]] = {"ko": r["ko"], "vi": nam_bo(r["vi"], lex), "kind": r.get("kind", ""), "source": "seed", "count": 0}
    for r in cat:
        ko, vi = r["ko"].strip(), r["vi"].strip()
        if not ko or not vi or r["status"] == "review" or not HANGUL.search(ko):
            continue
        if len(ko) > 12 or re.search(r"[.!?~%<>{}\n,]", ko):
            continue
        t = terms.setdefault(ko, {"ko": ko, "vi": vi, "kind": "", "source": r["status"], "count": 0})
        t["count"] += 1
    with open(L10N / "glossary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, GLOSS_FIELDS, lineterminator="\n")
        w.writeheader()
        for k in sorted(terms, key=lambda k: (terms[k]["source"] != "seed", -terms[k]["count"], k)):
            w.writerow(terms[k])


def print_stats(cat):
    from collections import Counter
    st = Counter(r["status"] for r in cat)
    src = Counter((r["source"].split("+")[0] if not r["source"].startswith(("FxMap/Map", "FxDesktop/Quest", "fx/CustomMap"))
                   else r["source"].split("/")[0] + "/" + r["source"].split("/")[1]) for r in cat)
    unt = sum(1 for r in cat if "untranslated" in r["notes"])
    print("tổng %d · %s · chưa dịch %d" % (len(cat), dict(st), unt))
    for k, v in src.most_common():
        print("   %-45s %d" % (k, v))


def cmd_stats(a):
    with open(L10N / "catalog.csv", newline="", encoding="utf-8") as f:
        print_stats(list(csv.DictReader(f)))


# ---------------------------------------------------------------- ảnh có chữ

IMG_TOKENS = ["Bt_", "Bt", "Btn", "Button", "Dlg_", "Dlg", "Title", "Tab", "Txt", "Text", "Banner", "Logo",
              "Result", "Notice", "Tooltip", "ToolTip", "Msg", "Popup", "Name", "Word", "Label", "Menu",
              "Rank", "Win", "Lose", "Draw", "Start", "Ready", "Help", "Guide", "Tutorial", "Event", "Font",
              "Num", "Digit", "Info", "Intro", "Mission", "Quest", "Ending", "Clear", "Fail", "Success",
              "Ok", "Cancel", "Close", "Confirm"]
TOKEN_RE = re.compile(r"(?:^|[/_\-])(?:%s)|(?<=[a-z0-9])(?:%s)(?=[A-Z0-9_]|$)" % (
    "|".join(map(re.escape, IMG_TOKENS)), "|".join(map(re.escape, IMG_TOKENS))))


def img_info(blob):
    if blob[:3] == b"\xff\xd8\xff":
        return "jpg", ""
    if len(blob) >= 16 and blob[4:8] == b"\x02\x00\x00\x00":
        nimg = struct.unpack_from("<I", blob, 8)[0]
        if 0 < nimg < 100000 and len(blob) >= 16 + 8:
            h, w = struct.unpack_from("<II", blob, 16)
            return "i16", "%dx%d×%d" % (w, h, nimg)
        return "i16", ""
    return None, ""


def cmd_images(a):
    print("đọc pack VN…", file=sys.stderr)
    vn = {}
    for stem in pack_stems(a.vn, False):
        for name, blob in iter_pack(a.vn, stem, False):
            if img_info(blob)[0]:
                vn[name] = hashlib.sha1(blob).hexdigest()
    print("đọc pack KR…", file=sys.stderr)
    out = []
    for stem in pack_stems(a.kr, True):
        for name, blob in iter_pack(a.kr, stem, True):
            kind, dims = img_info(blob)
            if not kind:
                continue
            reasons = sorted(set(m.group(0).strip("/_-") for m in TOKEN_RE.finditer(name)))
            if HANGUL.search(name):
                reasons.append("hangul_name")
            if kind == "jpg":
                reasons.append("jpg_background")
            if not reasons:
                continue
            h = hashlib.sha1(blob).hexdigest()
            same = "no" if name not in vn else ("same_bytes" if vn[name] == h else "diff_bytes")
            out.append({"pack": stem, "entry": name, "kind": kind, "size": len(blob), "dims": dims,
                        "vn_same_name": same, "reason": "|".join(reasons)})
    with open(L10N / "images_todo.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["pack", "entry", "kind", "size", "dims", "vn_same_name", "reason"], lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    from collections import Counter
    print("%d ảnh → %s · %s" % (len(out), L10N / "images_todo.csv", dict(Counter(r["vn_same_name"] for r in out))))


# ---------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--kr", default=str(DEF_KR))
    p.add_argument("--vn", default=str(DEF_VN))
    p.add_argument("--kr-exe", default=str(DEF_KR_EXE))
    p.add_argument("--vn-strings", default=str(DEF_VN_STRINGS))
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("sources").set_defaults(f=cmd_sources)
    sp.add_parser("catalog").set_defaults(f=cmd_catalog)
    sp.add_parser("stats").set_defaults(f=cmd_stats)
    sp.add_parser("images").set_defaults(f=cmd_images)
    t = sp.add_parser("todo")
    t.add_argument("-n", type=int, default=300)
    t.add_argument("--src", default="")
    t.add_argument("out")
    t.set_defaults(f=cmd_todo)
    i = sp.add_parser("import")
    i.add_argument("inp")
    i.add_argument("--todo")
    i.add_argument("--status", default="translated")
    i.set_defaults(f=cmd_import)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
