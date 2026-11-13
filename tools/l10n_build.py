#!/usr/bin/env python3
"""Bản dựng thử offline: file cache + ClientString, chưa được client nạp thử."""
import argparse
import csv
import json
import re
import shutil
import struct
import zlib
from pathlib import Path
from xml.sax.saxutils import escape

import idf
import l10n_extract as L
import l10n_extract_en as EN


def u32(n):
    return struct.pack('<I', n)


def packed(data):
    return u32(len(data)) + data


def encodable(ch, encoding):
    try:
        ch.encode(encoding)
        return True
    except UnicodeEncodeError:
        return False


def get_text(key, old, catalog, language, stats, encoding):
    row = catalog.get(key)
    new = ''
    if language != 'ko' and row and row['ko'] == old:
        if language == 'vi' and row.get('vi_status', row.get('status')) in ('translated', 'reused'):
            new = row['vi']
        if language == 'en' and row.get('en_status') in ('candidate', 'casefold_candidate', 'machine'):
            new = row['en']
    if new and not EN.formatting(old, new):
        stats['format_rejected'] += 1
        new = ''
    if new:
        bad = [ch for ch in new if not encodable(ch, encoding)]
        if bad:
            stats['encoding_rejected'] = stats.get('encoding_rejected', 0) + 1
            chars = stats.setdefault('unencodable_characters', {})
            for ch in sorted(set(bad)):
                chars[ch] = chars.get(ch, 0) + 1
            new = ''
    value = new or old
    stats['replaced' if new and new != old else 'retained'] += 1
    if EN.HANGUL.search(value):
        stats['hangul'] += 1
    return value


def pair_file(raw, name, catalog, lang, encoding, stats):
    n = struct.unpack_from('<H', raw)[0]
    out, pos = bytearray(raw[:2]), 2
    for _ in range(n):
        start = pos
        key, pos = L.lstr(raw, pos)
        key_bytes = raw[start:pos]
        stats['non_ascii_keys'] = stats.get('non_ascii_keys', 0) + any(b >= 128 for b in key_bytes[4:])
        val, pos = L.lstr(raw, pos)
        idx = ('q:' + (key.strip() or '<empty>')) if name == 'csysqstr.ssd' else key
        out += key_bytes + packed(get_text(idx, val, catalog, lang, stats, encoding).encode(encoding))
    if pos != len(raw):
        raise ValueError('pair file có dữ liệu thừa')
    return bytes(out)


def maps(raw, catalog, lang, encoding, stats):
    count = struct.unpack_from('<H', raw)[0]
    out, p = bytearray(raw[:2]), 2
    for _ in range(count):
        out += raw[p:p+5]; p += 5
        start = p
        name, p = L.lstr(raw, p)
        name_bytes = raw[start:p]
        stats['non_ascii_map_names'] = stats.get('non_ascii_map_names', 0) + any(b >= 128 for b in name_bytes[4:])
        display, p = L.lstr(raw, p)
        out += name_bytes
        out += packed(get_text('map:' + name, display, catalog, lang, stats, encoding).encode(encoding))
        out += raw[p:p+2]; p += 2
        for _ in range(2):
            start = p
            text, p = L.lstr(raw, p)
            identifier = raw[start:p]
            stats['non_ascii_map_paths'] = stats.get('non_ascii_map_paths', 0) + any(b >= 128 for b in identifier[4:])
            out += identifier
        out += raw[p:p+16]; p += 16
    if p != len(raw):
        raise ValueError(f'map parse chưa hết {p}/{len(raw)}')
    return bytes(out)


def stock(raw, catalog, lang, encoding, stats):
    count = struct.unpack_from('<I', raw)[0]
    out, p = bytearray(raw[:4]), 4
    for _ in range(count):
        item = struct.unpack_from('<I', raw, p)[0]
        n = struct.unpack_from('<I', raw, p+5)[0]
        old = raw[p+9:p+9+n].decode('cp949')
        q = p+9+n
        iconlen = struct.unpack_from('<I', raw, q+12)[0]
        end = p + 129 + n + iconlen
        if end > len(raw):
            raise ValueError('stock bị cắt')
        out += raw[p:p+5] + packed(get_text(f'stock:{item}', old, catalog, lang, stats, encoding).encode(encoding)) + raw[q:end]
        p = end
    if p != len(raw):
        raise ValueError('stock parse chưa hết')
    return bytes(out)


def write_ssi(original, raw):
    if original[:4] != b'ssi1' or original[8] != 0x18 or original[13] != 1:
        raise ValueError('header SSI không hỗ trợ')
    compressed = zlib.compress(raw, 9)
    header = bytearray(original[:18])
    header[9:13] = u32(len(compressed) + 5)
    header[14:18] = u32(len(raw))
    output = bytes(header) + compressed
    checksum = zlib.adler32(output[8:], 0) & 0xffffffff
    return output[:4] + u32(checksum) + output[8:]


def encrypt_idx(plain, key):
    count, tail = divmod(len(plain), 4)
    words = struct.unpack_from('<%dI' % count, plain)
    cipher = [words[0] ^ key] + [words[i] ^ words[i-1] for i in range(1, count)] if count else []
    out = bytearray(struct.pack('<%dI' % count, *cipher))
    last = words[-1] if words else key
    for i in range(tail):
        out.append(plain[4*count+i] ^ ((last >> (8*i)) & 255))
    return bytes(out)


def pack_build(root, out, catalog, lang, encoding, stats):
    index = root/'FxDesktop.idx'; data = index.read_bytes(); key = int.from_bytes(data[:4], 'little')
    plain = bytearray(idf.decrypt_idx(data, key)); version, entries, end = idf.parse_idx(plain)
    if end != len(plain) or version is None:
        raise ValueError('index không hỗ trợ')
    entries = [e for e in entries if e[0] == 'ClientData/ClientString']
    if len(entries) != 1 or entries[0][3] != 0:
        raise ValueError('ClientString không có đúng một entry không mã hóa')
    _, offset, size, _, _ = entries[0]
    idd = root/'FxDesktop.idd'
    with idd.open('rb') as f:
        f.seek(offset); blob = f.read(size)
    if int.from_bytes(blob[:4], 'little') != len(blob)-4:
        raise ValueError('độ dài ClientString sai')
    text = blob[4:]
    pattern = re.compile(rb'(<Elem>)(.*?)(</Elem>)', re.S)
    def edit(match):
        block = match.group(2)
        k = re.search(rb'<key>(.*?)</key>', block, re.S)
        v = re.search(rb'<string>(.*?)</string>', block, re.S)
        if not k or not v:
            return match.group(0)
        key_bytes = k.group(1)
        stats['non_ascii_keys'] = stats.get('non_ascii_keys', 0) + any(b >= 128 for b in key_bytes)
        name = L.xml_unescape(key_bytes.decode('cp949')); old = L.xml_unescape(v.group(1).decode('cp949'))
        # duplicate @ClientString bảo toàn giá trị gốc riêng
        row = catalog.get(name+'@ClientString')
        identity = name+'@ClientString' if row and row['ko'] == old else name
        new = get_text(identity, old, catalog, lang, stats, encoding)
        if new == old and encoding == 'cp949':
            return match.group(0)
        value = escape(new, {'"':'&quot;', "'":'&apos;'}).encode(encoding)
        return match.group(1) + block[:v.start(1)] + value + block[v.end(1):] + match.group(3)
    replaced = pattern.sub(edit, text)
    newblob = packed(replaced)
    # Append-only: mọi byte entry khác giữ nguyên. Cập nhật offset/size trong index.
    p = 12
    for _ in range(struct.unpack_from('<I', plain, 8)[0]):
        n = struct.unpack_from('<i', plain, p)[0]; p += 4
        name = bytes(plain[p:p+n]).decode('cp949'); p += n
        if name == 'ClientData/ClientString':
            struct.pack_into('<II', plain, p, idd.stat().st_size, len(newblob))
        p += 16
    shutil.copyfile(idd, out/'FxDesktop.idd')
    with (out/'FxDesktop.idd').open('ab') as f: f.write(newblob)
    (out/'FxDesktop.idx').write_bytes(encrypt_idx(plain, key))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kr',type=Path,default=Path('/home/admin/boom/clients/kr-00967'))
    parser.add_argument('--catalog',type=Path,default=L.L10N/'catalog_en.csv')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--lang',choices=('ko','vi','en'),required=True)
    parser.add_argument('--encoding',choices=('cp949','utf-8'),required=True)
    a=parser.parse_args(); root=a.kr.resolve(); out=a.out.resolve()
    if out == root or root in out.parents:
        raise ValueError('Không ghi vào client nguồn')
    out.mkdir(parents=True,exist_ok=True)
    with a.catalog.open(encoding='utf-8',newline='') as f: catalog={r['id']:r for r in csv.DictReader(f)}
    check_names = ['csysstr.ssd','csysqstr.ssd','fxdynmapinfo.ssd'] + [f'fxstock{i}.ini' for i in range(4)] + ['csysfxmg.ssd','channel2_001.ssd','spcc.ssd','multisvr.ssd','fxstovi.ini','filterstr.ssd']
    for name in check_names:
        data = (root/name).read_bytes()
        assert int.from_bytes(data[4:8], 'little') == (zlib.adler32(data[8:], 0) & 0xffffffff), f'checksum gốc sai: {name}'
    names=['csysstr.ssd','csysqstr.ssd','fxdynmapinfo.ssd']+[f'fxstock{i}.ini' for i in range(4)]
    results={}
    for name in names:
        stats={'replaced':0,'retained':0,'hangul':0,'format_rejected':0,'encoding_rejected':0,'unencodable_characters':{}}
        path=root/name; original=path.read_bytes(); raw=L.ssd_raw(path)
        if a.lang=='ko' and a.encoding=='cp949':
            if name.startswith('fxstock'): rebuilt=stock(raw,catalog,a.lang,a.encoding,stats)
            elif name=='fxdynmapinfo.ssd': rebuilt=maps(raw,catalog,a.lang,a.encoding,stats)
            else: rebuilt=pair_file(raw,name,catalog,a.lang,a.encoding,stats)
            assert rebuilt==raw
            built=write_ssi(original, rebuilt)
            (out/name).write_bytes(built)
            assert L.ssd_raw(out/name)==raw
            stats['roundtrip']='byte-identical' if built == original else 'decompressed-identical'
            stats['first_difference']=next((i for i,(x,y) in enumerate(zip(original,built)) if x != y), None)
            stats['original_bytes']=len(original); stats['written_bytes']=len(built)
        else:
            if name.startswith('fxstock'): rebuilt=stock(raw,catalog,a.lang,a.encoding,stats)
            elif name=='fxdynmapinfo.ssd': rebuilt=maps(raw,catalog,a.lang,a.encoding,stats)
            else: rebuilt=pair_file(raw,name,catalog,a.lang,a.encoding,stats)
            (out/name).write_bytes(write_ssi(original,rebuilt))
            assert L.ssd_raw(out/name)==rebuilt
            stats['roundtrip']='decompressed-bytes'
        results[name]=stats
    if a.lang=='ko' and a.encoding=='cp949':
        idx = (root/'FxDesktop.idx').read_bytes()
        key = int.from_bytes(idx[:4], 'little')
        decoded = idf.decrypt_idx(idx, key)
        _, entries, end = idf.parse_idx(decoded)
        assert end == len(idx) and encrypt_idx(decoded, key) == idx
        entry = next(e for e in entries if e[0] == 'ClientData/ClientString')
        with (root/'FxDesktop.idd').open('rb') as src:
            src.seek(entry[1]); blob = src.read(entry[2])
        assert int.from_bytes(blob[:4], 'little') == len(blob)-4
        blob[4:].decode('cp949')
        for name in ('FxDesktop.idx','FxDesktop.idd'): shutil.copyfile(root/name,out/name)
        results['FxDesktop']={'roundtrip':'index read and re-encoded identical; unchanged IDD copied'}
    else:
        stats={'replaced':0,'retained':0,'hangul':0,'format_rejected':0,'encoding_rejected':0,'unencodable_characters':{}}
        pack_build(root,out,catalog,a.lang,a.encoding,stats); results['FxDesktop']=stats
    (out/'build-report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__ == '__main__': main()
