#!/usr/bin/env python3
"""Bản dựng thử offline: file cache + ClientString, chưa được client nạp thử."""
import unicodedata
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
import i16
import io
from PIL import Image
import l10n_images_review as IR
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


FALLBACK = {'—': '-', '–': '-', '‘': "'", '’': "'", '“': '"', '”': '"', '…': '...'}
# Bản dựng UTF-8 chuyển cả khoá có chữ Hàn sang UTF-8 để file chỉ mang một bảng mã.
# Quét exe, 13 file ssi1 và mọi entry pack KR 00967 không thấy nơi nào tham chiếu các khoá này
# bằng byte CP949. `--keep-key-bytes` giữ byte gốc.
KEEP_KEY_BYTES = False
PARTICLES = {'이', '가', '을', '를', '은', '는'}


def get_text(key, old, catalog, language, stats, encoding):
    row = catalog.get(key)
    new = ''
    empty = False  # trợ từ Hàn đứng riêng (을/를…): bản dịch cố ý rỗng
    if language != 'ko' and row and row['ko'] == old:
        if language == 'vi' and row.get('vi_status', row.get('status')) in ('translated', 'reused'):
            new = row['vi']
            empty = not new and old in PARTICLES
        if language == 'en' and row.get('en_status') in ('candidate', 'casefold_candidate', 'machine', 'manual'):
            new = row['en']
            empty = not new and 'empty_on_purpose' in row.get('en_notes', '')
    if empty:
        stats['replaced'] += 1
        stats['emptied'] = stats.get('emptied', 0) + 1
        return ''
    if new and not EN.formatting(old, new):
        stats['format_rejected'] += 1
        new = ''
    if new and encoding == 'cp949':
        # Chữ Latin có dấu và gạch dài không có trong bảng mã Hàn: hạ về ký tự gần nhất.
        new = ''.join(ch if encodable(ch, encoding) else FALLBACK.get(ch) or
                      unicodedata.normalize('NFKD', ch).encode('ascii', 'ignore').decode() or ch for ch in new)
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
        if encoding == 'utf-8' and not KEEP_KEY_BYTES and any(b >= 128 for b in key_bytes[4:]):
            key_bytes = packed(key_bytes[4:].decode('cp949').encode('utf-8'))
            stats['keys_reencoded'] = stats.get('keys_reencoded', 0) + 1
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


def fxmg(raw, catalog, lang, encoding, stats):
    """csysfxmg: u16 count, count × (u8 kind, lstr text); id theo thứ tự như l10n_extract."""
    count = struct.unpack_from('<H', raw)[0]
    out, p = bytearray(raw[:2]), 2
    for i in range(count):
        out += raw[p:p+1]; p += 1
        text, p = L.lstr(raw, p)
        out += packed(get_text(f'csysfxmg.ssd:{i}', text, catalog, lang, stats, encoding).encode(encoding))
    if p != len(raw):
        raise ValueError('csysfxmg parse chưa hết')
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


def pack_build(root, out, catalog, lang, encoding, stats, images=None):
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
        parts = [(v.start(1), v.end(1), value)]
        if encoding == 'utf-8' and not KEEP_KEY_BYTES and any(b >= 128 for b in key_bytes):
            parts.append((k.start(1), k.end(1), key_bytes.decode('cp949').encode('utf-8')))
            stats['keys_reencoded'] = stats.get('keys_reencoded', 0) + 1
        for start, end, data in sorted(parts, reverse=True):
            block = block[:start] + data + block[end:]
        return match.group(1) + block + match.group(3)
    replaced = pattern.sub(edit, text)
    newblob = packed(replaced)
    replacements = [('ClientData/ClientString', newblob)] + (images or [])
    write_pack(index, out, replacements)


def write_pack(index, out, replacements):
    """Append plaintext entries to a copied KR pack and update its index once."""
    data = index.read_bytes()
    key = int.from_bytes(data[:4], 'little')
    plain = bytearray(idf.decrypt_idx(data, key))
    version, entries, end = idf.parse_idx(plain)
    if version is None or end != len(plain):
        raise ValueError(f'index không hỗ trợ: {index}')
    changes = dict(replacements)
    if len(changes) != len(replacements):
        raise ValueError('entry thay thế bị lặp')
    positions = {}
    p = 12
    for name, offset, size, entry_key, crc in entries:
        n = struct.unpack_from('<i', plain, p)[0]
        p += 4 + n
        if name in changes:
            if name in positions:
                raise ValueError(f'entry trùng tên: {name}')
            positions[name] = (p, entry_key, crc)
        p += 16
    if set(changes) != set(positions):
        raise ValueError(f'entry không tồn tại: {set(changes) - set(positions)}')
    idd = index.with_suffix('.idd')
    shutil.copyfile(idd, out / idd.name)
    with (out / idd.name).open('ab') as f:
        for name, blob in replacements:
            pos, entry_key, crc = positions[name]
            if entry_key:
                if crc not in (0, 1):
                    struct.pack_into('<I', plain, pos + 12, idf._crc32(entry_key, blob))
                blob = idf.encrypt_entry(blob, entry_key)
            elif '_mm' in name:
                compressed = zlib.compress(blob)
                blob = struct.pack('<II', len(compressed), len(blob)) + compressed
            struct.pack_into('<II', plain, pos, f.tell(), len(blob))
            f.write(blob)
    (out / index.name).write_bytes(encrypt_idx(plain, key))


def image_shape(blob):
    if blob.startswith(b'\xff\xd8\xff'):
        with Image.open(io.BytesIO(blob)) as im:
            return ('jpg', 1, 1, (im.size,))
    s = i16.parse(blob)
    return ('i16', len(s['images']), s['nframes'], tuple(s['sizes']))


def image_changes(root, lang, decisions, image_dir, allow_shape_change, vn, en):
    if image_dir and not image_dir.is_dir():
        raise ValueError(f'thư mục ảnh không tồn tại: {image_dir}')
    kr = IR.index_packs(root, True)
    source = IR.index_packs(vn, False) if decisions and lang == 'vi' else {}
    en_index = EN.index_tree(en) if decisions and lang == 'en' else {}
    changes, skipped = {}, []
    if decisions:
        with decisions.open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
    else:
        rows = []
    selected = {(r['pack'], r['entry']): r for r in rows
                if r.get('status_en' if lang == 'en' else 'status') == 'translated' and lang != 'ko'}
    if image_dir:
        names = {(pack, name.replace('\\', '/')) for pack, name in kr}
        for path in image_dir.rglob('*'):
            if not path.is_file() or path.suffix.lower() not in ('.png', '.jpg'):
                continue
            parts = path.relative_to(image_dir).parts
            if len(parts) < (3 if path.suffix.lower() == '.png' else 2):
                skipped.append({'pack': parts[0], 'entry': '/'.join(parts[1:]),
                                'reason': 'đường dẫn ảnh không đúng quy ước'})
                continue
            if path.suffix not in ('.png', '.jpg'):
                skipped.append({'pack': parts[0], 'entry': '/'.join(parts[1:]),
                                'reason': 'đuôi file phải là .png hoặc .jpg'})
                continue
            entry = '/'.join(parts[1:-1]) if path.suffix.lower() == '.png' else '/'.join(parts[1:])[:-4]
            if (parts[0], entry) not in names:
                skipped.append({'pack': parts[0], 'entry': entry, 'reason': 'không có entry KR'})
        for pack, name in kr:
            base = image_dir / pack / name.replace('\\', '/')
            if base.is_dir() and any(base.glob('*.png')) or base.with_suffix(base.suffix + '.jpg').is_file():
                selected.setdefault((pack, name), None)
    for (pack, name), row in selected.items():
        try:
            record = kr.get((pack, name))
            if record is None:
                raise ValueError('không có entry KR')
            original = IR.read_blob(record, name)
            blob = original
            if row is not None:
                if lang == 'vi':
                    if name not in source:
                        raise ValueError('không có entry VN cùng tên')
                    blob = IR.read_blob(source[name], name)
                else:
                    matches = en_index.get(name.casefold(), [])
                    exact = [(p, e) for p, e in matches if e[0] == name]
                    if len(exact) != 1:
                        raise ValueError(f'cần đúng một entry Bắc Mỹ cùng tên, có {len(exact)}')
                    blob = EN.read_entry(*exact[0])
                if not allow_shape_change and image_shape(blob) != image_shape(original):
                    raise ValueError('số ảnh, kích thước, số frame hoặc loại ảnh khác KR')
            if image_dir:
                base = image_dir / pack / name.replace('\\', '/')
                jpg = base.with_suffix(base.suffix + '.jpg')
                if jpg.is_file():
                    replacement = jpg.read_bytes()
                    if image_shape(original)[0] != 'jpg' or image_shape(replacement)[0] != 'jpg':
                        raise ValueError('file thay thế không phải JPEG')
                    if not allow_shape_change and image_shape(replacement) != image_shape(original):
                        raise ValueError('kích thước JPEG khác KR')
                    blob = replacement
                if base.is_dir() and any(base.glob('*.png')):
                    s = i16.parse(original)
                    rgba = []
                    known = set()
                    for i, (h, w) in enumerate(s['sizes']):
                        paths = [p for p in base.glob('*.png') if p.stem.isdigit() and int(p.stem) == i]
                        if len(paths) > 1:
                            raise ValueError(f'ảnh con {i} có nhiều PNG')
                        if not paths:
                            rgba.append(None); continue
                        known.add(paths[0])
                        with Image.open(paths[0]) as im:
                            if im.size != (w, h):
                                raise ValueError(f'ảnh con {i} sai kích thước')
                            rgba.append(im.convert('RGBA').tobytes())
                    if set(base.glob('*.png')) != known:
                        raise ValueError('tên PNG hoặc chỉ số ảnh con không hợp lệ')
                    blob = i16.encode(original, rgba)
            changes.setdefault(pack, []).append((name, blob))
        except (ValueError, OSError, struct.error, IndexError, EOFError, zlib.error) as exc:
            skipped.append({'pack': pack, 'entry': name, 'reason': str(exc)})
    unique = {}
    for item in skipped:
        key = (item['pack'], item['entry'])
        if key not in unique:
            unique[key] = item
        elif item['reason'] not in unique[key]['reason']:
            unique[key]['reason'] += '; ' + item['reason']
    return changes, list(unique.values())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kr',type=Path,default=Path('/home/admin/boom/clients/kr-00967'))
    parser.add_argument('--catalog',type=Path,default=L.L10N/'catalog_en.csv')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--lang',choices=('ko','vi','en'),required=True)
    parser.add_argument('--encoding',choices=('cp949','utf-8'),required=True)
    parser.add_argument('--keep-key-bytes',action='store_true',help='bản UTF-8 vẫn giữ khoá theo byte CP949 gốc')
    parser.add_argument('--images', type=Path, nargs='?', const=L.L10N/'images_review.csv')
    parser.add_argument('--image-dir', type=Path)
    parser.add_argument('--allow-shape-change', action='store_true')
    parser.add_argument('--vn', type=Path, default=Path('/home/admin/Downloads/Boom'))
    parser.add_argument('--en', type=Path, default=L.L10N/'.cache/poptag-client')
    a=parser.parse_args(); root=a.kr.resolve(); out=a.out.resolve()
    global KEEP_KEY_BYTES
    KEEP_KEY_BYTES = a.keep_key_bytes
    if out == root or root in out.parents:
        raise ValueError('Không ghi vào client nguồn')
    for source in (a.vn.resolve(), a.en.resolve()):
        if out == source or source in out.parents:
            raise ValueError('Không ghi vào client nguồn')
    if (a.images or a.image_dir) and (L.ROOT.resolve() in out.parents or out == L.ROOT.resolve()):
        # Pack dựng ra là dữ liệu game: trong repo chỉ được ghi vào thư mục cache bị Git bỏ qua.
        cache = (L.L10N / '.cache').resolve()
        if out == cache or cache not in out.parents:
            raise ValueError('trong repo, bản dựng ảnh phải nằm trong l10n/.cache/')
    out.mkdir(parents=True,exist_ok=True)
    with a.catalog.open(encoding='utf-8',newline='') as f: catalog={r['id']:r for r in csv.DictReader(f)}
    check_names = ['csysstr.ssd','csysqstr.ssd','fxdynmapinfo.ssd'] + [f'fxstock{i}.ini' for i in range(4)] + ['csysfxmg.ssd','channel2_001.ssd','spcc.ssd','multisvr.ssd','fxstovi.ini','filterstr.ssd']
    for name in check_names:
        data = (root/name).read_bytes()
        assert int.from_bytes(data[4:8], 'little') == (zlib.adler32(data[8:], 0) & 0xffffffff), f'checksum gốc sai: {name}'
    names=['csysstr.ssd','csysqstr.ssd','fxdynmapinfo.ssd','csysfxmg.ssd']+[f'fxstock{i}.ini' for i in range(4)]
    results={}
    for name in names:
        stats={'replaced':0,'retained':0,'hangul':0,'format_rejected':0,'encoding_rejected':0,'unencodable_characters':{}}
        path=root/name; original=path.read_bytes(); raw=L.ssd_raw(path)
        if a.lang=='ko' and a.encoding=='cp949':
            if name.startswith('fxstock'): rebuilt=stock(raw,catalog,a.lang,a.encoding,stats)
            elif name=='fxdynmapinfo.ssd': rebuilt=maps(raw,catalog,a.lang,a.encoding,stats)
            elif name=='csysfxmg.ssd': rebuilt=fxmg(raw,catalog,a.lang,a.encoding,stats)
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
            elif name=='csysfxmg.ssd': rebuilt=fxmg(raw,catalog,a.lang,a.encoding,stats)
            else: rebuilt=pair_file(raw,name,catalog,a.lang,a.encoding,stats)
            (out/name).write_bytes(write_ssi(original,rebuilt))
            assert L.ssd_raw(out/name)==rebuilt
            stats['roundtrip']='decompressed-bytes'
        results[name]=stats
    changes, skipped = image_changes(root, a.lang, a.images, a.image_dir, a.allow_shape_change, a.vn, a.en) if a.images or a.image_dir else ({}, [])
    image_count = sum(len(v) for v in changes.values())
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
        if 'FxDesktop' in changes:
            write_pack(root/'FxDesktop.idx', out, changes.pop('FxDesktop'))
            results['FxDesktop']['roundtrip'] = 'index read and re-encoded identical; image entries appended'
    else:
        stats={'replaced':0,'retained':0,'hangul':0,'format_rejected':0,'encoding_rejected':0,'unencodable_characters':{}}
        pack_build(root,out,catalog,a.lang,a.encoding,stats,changes.pop('FxDesktop', [])); results['FxDesktop']=stats
    if a.images or a.image_dir:
        for pack, replacements in changes.items():
            write_pack(root/(pack+'.idx'), out, replacements)
        results['images'] = {'replaced': image_count, 'skipped': len(skipped), 'reasons': skipped}
    (out/'build-report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__ == '__main__': main()
