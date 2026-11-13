#!/usr/bin/env python3
"""Trích chuỗi PopTag 0.7.8, ghép ứng viên theo ID với catalog KR–VI.

Nguồn phải là client đã trích xuất; không đọc hoặc chạy bộ cài. Mọi bản ghép
chỉ là ứng viên, khác phiên bản có thể đổi nghĩa ngay cả khi trùng ID.
"""
import argparse
import csv
import hashlib
import json
import re
import struct
import io
from collections import Counter, defaultdict
from pathlib import Path

import idf
import i16
from PIL import Image
import l10n_extract as base

ROOT = Path(__file__).resolve().parent.parent
PRINTF = re.compile(r'%(?:\d+\$)?[-+#0 ]*\d*(?:\.\d+)?(?:hh|ll|h|l|I64|z)?[diuoxXfFeEgGaAcspn%]')
OTHER = re.compile(r'\{[^{}]+\}|</?[^<>]+>')
HANGUL = re.compile(r'[\uac00-\ud7a3\u3131-\u318e]')


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def pack_entry(root, name, index='fx.idx'):
    idx = root / index
    data = idx.read_bytes()
    _, entries, end = idf.parse_idx(idf.decrypt_idx(data, int.from_bytes(data[:4], 'little')))
    if end != len(data):
        raise ValueError('fx.idx có dữ liệu thừa hoặc index chưa đọc hết')
    found = [e for e in entries if e[0] == name]
    if len(found) != 1:
        raise ValueError(f'cần đúng một entry {name}; có {len(found)}')
    n, offset, size, key, checksum = found[0]
    with idx.with_suffix('.idd').open('rb') as f:
        f.seek(offset)
        payload = f.read(size)
    if len(payload) != size:
        raise ValueError('entry pack bị cắt ngắn')
    return idf.unpack_entry(n, payload, key, checksum)


def stock_names(path):
    """Ứng viên tên stock: quét header id/u8 kind/lstr và kind lặp u16.

    Không khẳng định đã giải toàn bộ record hoặc cùng ID với KR. Từ chối nếu
    số kết quả/ID không khớp count của nguồn PopTag, tránh lặng lẽ bỏ sót.
    """
    raw = base.ssd_raw(path)
    expected = int.from_bytes(raw[:2], 'little')
    found = []
    for offset in range(2, len(raw) - 11):
        item_id = int.from_bytes(raw[offset:offset + 4], 'little')
        kind = raw[offset + 4]
        length = int.from_bytes(raw[offset + 5:offset + 9], 'little')
        end = offset + 9 + length
        if kind > 30 or not 1 <= length <= 150 or end + 2 > len(raw) or not item_id:
            continue
        if raw[end:end + 2] != bytes((kind, 0)):
            continue
        try:
            name = raw[offset + 9:end].decode('cp949')
        except UnicodeDecodeError:
            continue
        if all(ch.isprintable() for ch in name):
            found.append((item_id, name, offset))
    if len(found) != expected or len({item_id for item_id, _, _ in found}) != expected:
        raise ValueError(f'fxstock: {len(found)} tên / count {expected}, hoặc trùng ID')
    return found


def formatting(ko, en):
    # Thứ tự printf quan trọng với các tham số không đánh số; %% không lấy đối số.
    a = [m for m in PRINTF.findall(ko) if m != '%%']
    b = [m for m in PRINTF.findall(en) if m != '%%']
    return a == b and OTHER.findall(ko) == OTHER.findall(en)


def make_rows(kr_rows, records):
    variants = defaultdict(dict)
    for key, value, source in records:
        variants[key].setdefault(value, set()).add(source)
    catalog_ids = {r['id'] for r in kr_rows}
    folded = defaultdict(list)
    for key in variants:
        folded[key.casefold()].append(key)
    result, source_rows = [], []
    for key in sorted(variants):
        for text, sources in sorted(variants[key].items()):
            source_rows.append({'id': key, 'en': text, 'source_en': '+'.join(sorted(sources)),
                                'match_kr_id': 'yes' if key in catalog_ids else 'no',
                                'contains_hangul': 'yes' if HANGUL.search(text) else 'no'})
    for r in kr_rows:
        vals = variants.get(r['id'], {})
        flags = []
        fallback = False
        if not vals:
            matches = folded.get(r['id'].casefold(), [])
            if len(matches) == 1:
                vals = variants[matches[0]]
                fallback = True
                flags.append('poptag_id=' + matches[0])
            elif len(matches) > 1:
                flags.append('poptag_ids=' + ','.join(sorted(matches)))
                vals = {'': set(), '<ambiguous>': set()}
        en = next(iter(vals)) if len(vals) == 1 else ''
        if not vals:
            status = 'missing'
        elif len(vals) > 1:
            status = 'conflicting_variants'
        else:
            status = 'casefold_candidate' if fallback else 'candidate'
            if not r['ko']:
                flags.append('missing_korean_source')
            elif not formatting(r['ko'], en):
                flags.append('format_mismatch')
            if HANGUL.search(en):
                flags.append('contains_hangul')
        result.append({'id': r['id'], 'source_kr': r['source'], 'ko': r['ko'],
                       'vi': r['vi'], 'vi_status': r['status'], 'en': en,
                       'source_en': '+'.join(sorted(next(iter(vals.values())))) if len(vals) == 1 else '',
                       'en_status': status, 'en_notes': ';'.join(flags)})
    return result, source_rows


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def index_tree(root):
    index = defaultdict(list)
    for path in sorted(root.rglob('*.idx')):
        data = path.read_bytes()
        _, entries, end = idf.parse_idx(idf.decrypt_idx(data, int.from_bytes(data[:4], 'little')))
        if end != len(data):
            raise ValueError(f'index không đọc hết: {path}')
        for entry in entries:
            index[entry[0].casefold()].append((path, entry))
    return index


def read_entry(path, entry):
    name, offset, size, key, crc = entry
    with path.with_suffix('.idd').open('rb') as f:
        f.seek(offset)
        data = f.read(size)
    if len(data) != size:
        raise ValueError(f'entry bị cắt: {name}')
    return idf.unpack_entry(name, data, key, crc)


def dimensions(blob):
    if blob.startswith(b'\xff\xd8\xff'):
        with Image.open(io.BytesIO(blob)) as img:
            return [[img.width, img.height]], 1
    parsed = i16.parse(blob)
    return [[w, h] for h, w in parsed['sizes']], parsed['nframes']


def image_candidates(en_root, kr_root, source):
    en_index = index_tree(en_root)
    kr_index = index_tree(kr_root)
    with source.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    out = []
    for row in rows:
        kr_matches = [v for v in kr_index[row['entry'].casefold()] if v[0].stem.casefold() == row['pack'].casefold() and v[1][0] == row['entry']]
        matches = en_index.get(row['entry'].casefold(), [])
        if not matches:
            continue
        if len(kr_matches) != 1:
            raise ValueError(f"Không tìm được entry KR duy nhất {row['pack']}/{row['entry']}")
        kr_blob = read_entry(*kr_matches[0])
        kr_sizes, kr_frames = dimensions(kr_blob)
        details = []
        for path, entry in matches:
            data = read_entry(path, entry)
            try:
                sizes, frames = dimensions(data)
                error = ''
            except (ValueError, IndexError, struct.error, OSError) as exc:
                sizes, frames, error = None, None, type(exc).__name__
            details.append({'pack': str(path.relative_to(en_root)), 'entry': entry[0],
                            'comparison': 'same' if data == kr_blob else 'different',
                            'sizes': sizes, 'frames': frames, 'error': error,
                            'dimensions_match': None if sizes is None else sizes == kr_sizes,
                            'frames_match': None if frames is None else frames == kr_frames})
        out.append({**row, 'poptag_packs': json.dumps([x['pack'] for x in details], ensure_ascii=False),
                    'comparison': 'same' if any(x['comparison'] == 'same' for x in details) else 'different',
                    'kr_sizes': json.dumps(kr_sizes), 'kr_frames': kr_frames,
                    'poptag_details': json.dumps(details, ensure_ascii=False, separators=(',', ':'))})
    return out


def kr_stock(path):
    raw = base.ssd_raw(path)
    count = struct.unpack_from('<I', raw)[0]
    pos, rows = 4, []
    for _ in range(count):
        item, kind, size = struct.unpack_from('<IBI', raw, pos)
        if not 0 < size < 300:
            raise ValueError(f'độ dài tên bất thường trong {path.name}')
        name = raw[pos+9:pos+9+size].decode('cp949')
        q = pos + 9 + size
        icon_len = struct.unpack_from('<I', raw, q+12)[0]
        if not 0 < icon_len < 300:
            raise ValueError(f'độ dài icon bất thường trong {path.name}')
        icon = raw[q+16:q+16+icon_len].decode('cp949')
        rows.append((item, kind, name, icon, pos))
        pos += 129 + size + icon_len
    if pos != len(raw):
        raise ValueError(f'đọc chưa hết {path.name}: {pos}/{len(raw)}')
    return rows


def stock_crosswalk(en_path, kr_root, catalog):
    raw = base.ssd_raw(en_path)
    kr = defaultdict(list)
    for path in sorted(kr_root.glob('fxstock[0-3].ini')):
        for item, kind, name, icon, off in kr_stock(path):
            kr[item].append((kind, name, icon, path.name, off))
    by_icon = defaultdict(list)
    for item, entries in kr.items():
        for kind, name, icon, source, off in entries:
            by_icon[(kind, icon.casefold())].append((item, kind, name, icon, source, off))
    texts = defaultdict(list)
    for row in catalog:
        texts[row['ko']].append(row['id'])
    result = []
    for item, name, off in stock_names(en_path):
        kind = raw[off + 4]
        q = off + 9 + len(name.encode('cp949'))
        icon_len = struct.unpack_from('<I', raw, q+10)[0]
        if icon_len > 300:
            raise ValueError('icon PopTag không hợp lệ')
        icon = raw[q+14:q+14+icon_len].decode('cp949')
        candidates = by_icon.get((kind, icon.casefold()), [])
        names = {v[2] for v in candidates}
        if len(names) != 1:
            continue
        for kr_id, kk, ko, ki, source, ko_off in candidates:
            result.append({'item_id': item, 'en': name, 'en_kind': kind, 'en_icon': icon,
                           'kr_item_id': kr_id, 'ko': ko, 'kr_kind': kk, 'kr_icon': ki,
                           'kr_source': source, 'kr_offset': f'0x{ko_off:x}',
                           'kind_match': 'true', 'icon_match': 'true',
                           'catalog_ko_ids': json.dumps(texts.get(ko, []), ensure_ascii=False),
                           'basis': 'kind;icon;single_kr_name', 'status': 'icon_kind_candidate_review'})
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--client', type=Path, required=True, help='PopTag đã trích xuất')
    ap.add_argument('--catalog', type=Path, default=ROOT / 'l10n/catalog.csv')
    ap.add_argument('--out', type=Path, default=ROOT / 'l10n')
    ap.add_argument('--kr', type=Path, default=Path('/home/admin/boom/clients/kr-00967'))
    args = ap.parse_args()
    paths = {n: args.client / n for n in ('csysstr.ssd', 'fx.idx', 'fx.idd', 'fxdynmapinfo.ssd', 'fxstock.ini', 'channel2_000.ssd')}
    records = [(k, v, 'csysstr.ssd') for k, v in base.ssd_pairs(base.ssd_raw(paths['csysstr.ssd']))]
    blob = pack_entry(args.client, 'ClientData/ClientString')
    if int.from_bytes(blob[:4], 'little') != len(blob) - 4:
        raise ValueError('độ dài ClientString không khớp')
    # Dùng parser có sẵn của repo: XML gốc chứa ký tự không hợp lệ với XML parser chuẩn.
    text = blob[4:].decode('cp949')
    pack_pairs = base.xml_elems(text)
    if len(pack_pairs) != len(re.findall(r'<Elem>', text)):
        raise ValueError('không đọc đủ các Elem trong ClientString')
    records += [(k, v, 'fx/ClientData/ClientString') for k, v in pack_pairs]
    for _mid, _mode, name, display, _theme, _file in base.ssd_dynmaps(base.ssd_raw(paths['fxdynmapinfo.ssd'])):
        records.append(('map:' + name, display, 'fxdynmapinfo.ssd'))
    for item_id, name, offset in stock_names(paths['fxstock.ini']):
        records.append((f'poptag:stock:{item_id}', name, f'fxstock.ini@0x{offset:x}'))
    for index, name in enumerate(base.ssd_channels(base.ssd_raw(paths['channel2_000.ssd']))):
        records.append((f'poptag:channel:{index}', name, 'channel2_000.ssd'))
    swish_path = 'clientextensions/swish/swish.idx'
    effects = json.loads(pack_entry(args.client, 'Swish/Catalog', swish_path).decode('utf-8'))['effects']
    records += [(f"poptag:swish:{e['id']}", e['name'], swish_path + ':Swish/Catalog') for e in effects]
    with args.catalog.open(encoding='utf-8-sig', newline='') as f:
        kr = list(csv.DictReader(f))
    rows, sources = make_rows(kr, records)
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / 'catalog_en.csv', ['id', 'source_kr', 'ko', 'vi', 'vi_status', 'en', 'source_en', 'en_status', 'en_notes'], rows)
    write_csv(args.out / 'english_sources.csv', ['id', 'en', 'source_en', 'match_kr_id', 'contains_hangul'], sources)
    stock = stock_crosswalk(paths['fxstock.ini'], args.kr, kr)
    stock_by_id = defaultdict(list)
    for candidate in stock:
        stock_by_id[str(candidate['kr_item_id'])].append(candidate)
    for r in rows:
        if not r['id'].startswith('stock:') or r['en_status'] != 'missing':
            continue
        candidates = stock_by_id.get(r['id'][6:], [])
        values = {candidate['en'] for candidate in candidates}
        if len(values) == 1:
            r['en'] = next(iter(values))
            r['source_en'] = 'fxstock.ini:kind+icon'
            r['en_status'] = 'stock_icon_candidate'
            r['en_notes'] = 'poptag_ids=' + ','.join(sorted(str(x['item_id']) for x in candidates))
            if not formatting(r['ko'], r['en']):
                r['en_notes'] += ';format_mismatch'
        elif len(values) > 1:
            r['en_status'] = 'conflicting_variants'
            r['en_notes'] = 'stock_icon_multiple_en_values'
    with (ROOT / 'l10n/tm_en.csv').open(encoding='utf-8', newline='') as f:
        english_memory = {r['ko']: r for r in csv.DictReader(f)}
    for r in rows:
        if r['en_status'] != 'missing' or not r['ko']:
            continue
        candidate = english_memory.get(r['ko'])
        if not candidate:
            continue
        flags = []
        if candidate['notes']:
            flags.append(candidate['notes'])
        if not candidate['en']:
            flags.append('empty_translation')
        if not formatting(r['ko'], candidate['en']):
            flags.append('format_mismatch')
        r['en'] = candidate['en']
        r['source_en'] = 'tm_en.csv'
        r['en_status'] = 'machine_review' if flags or candidate['status'] == 'review' else 'machine'
        r['en_notes'] = ';'.join(flags)
    # Ghi lại sau bước đối chiếu stock; không thay các ứng viên nguồn khác.
    write_csv(args.out / 'catalog_en.csv', ['id', 'source_kr', 'ko', 'vi', 'vi_status', 'en', 'source_en', 'en_status', 'en_notes'], rows)
    write_csv(args.out / 'stock_names_en.csv', ['item_id','en','en_kind','en_icon','kr_item_id','ko','kr_kind','kr_icon','kr_source','kr_offset','kind_match','icon_match','catalog_ko_ids','basis','status'], stock)
    images = image_candidates(args.client, args.kr, ROOT / 'l10n/images_todo.csv')
    write_csv(args.out / 'images_en_candidates.csv', ['pack','entry','kind','size','dims','vn_same_name','reason','poptag_packs','comparison','kr_sizes','kr_frames','poptag_details'], images)
    paths[swish_path] = args.client / swish_path
    paths[swish_path.replace('.idx', '.idd')] = args.client / swish_path.replace('.idx', '.idd')
    metadata = {
        'client': 'PopTag 0.7.8', 'matching': 'ID chính xác hoặc casefold duy nhất; tất cả là ứng viên, không chọn biến thể mâu thuẫn',
        'sha256': {name: sha256(path) for name, path in paths.items()},
        'catalog_kr_sha256': sha256(args.catalog),
        'english_raw_records': len(records), 'english_unique_ids': len({r[0] for r in records}),
        'english_variants': len(sources), 'english_only_ids': len({r['id'] for r in sources if r['match_kr_id'] == 'no'}),
        'swish_count': len(effects), 'stock_rows': len(stock), 'stock_status': dict(Counter(r['status'] for r in stock)),
        'stock_unique_poptag_ids': len({r['item_id'] for r in stock}),
        'image_rows': len(images), 'image_comparison': dict(Counter(r['comparison'] for r in images)),
        'kr_stock_sha256': {p.name: sha256(p) for p in sorted(args.kr.glob('fxstock[0-3].ini'))},
        'kr_stock_related_sha256': {n: sha256(args.kr / n) for n in ('fxstovi.ini', 'fxstovs.ini')},
        'images_todo_sha256': sha256(ROOT / 'l10n/images_todo.csv'),
        'catalog_rows': len(rows), 'status': dict(Counter(r['en_status'] for r in rows)),
        'format_mismatch': sum('format_mismatch' in r['en_notes'] for r in rows),
    }
    (args.out / 'english_sources_manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
