#!/usr/bin/env python3
"""Gộp pack của nhiều bản dịch thành một bộ .idd chung, mỗi ngôn ngữ một .idx.

Mỗi bản dịch (l10n_build + l10n_949x convert) có .idd = .idd KR nguyên vẹn + đuôi entry mới.
Công cụ này ghép: .idd chung = KR + đuôi ngôn ngữ 1 + đuôi ngôn ngữ 2 ...; .idx của từng ngôn ngữ
được dời offset các entry nằm trong đuôi của nó. Tiếng Hàn dùng .idx KR gốc (chỉ trỏ vào phần KR).

    python3 tools/l10n_share_pack.py --out OUT vi=DIR_VI en=DIR_EN

Kết quả: OUT/<pack>.idd (chung), OUT/<lang>/<pack>.idx, OUT/ko/<pack>.idx, OUT/share-report.json.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import idf  # noqa: E402
from l10n_build import encrypt_idx  # noqa: E402

CHUNK = 1 << 22


def same_prefix(path, prefix_path):
    n = prefix_path.stat().st_size
    if path.stat().st_size < n:
        return False
    with path.open('rb') as a, prefix_path.open('rb') as b:
        while True:
            x = b.read(CHUNK)
            if not x:
                return True
            if a.read(len(x)) != x:
                return False


def shifted_index(idx_path, base_len, delta):
    data = idx_path.read_bytes()
    key = int.from_bytes(data[:4], 'little')
    plain = bytearray(idf.decrypt_idx(data, key))
    version, entries, end = idf.parse_idx(plain)
    if version is None or end != len(plain):
        raise ValueError(f'index không hỗ trợ: {idx_path}')
    p, moved = 12, 0
    for name, offset, size, _, _ in entries:
        n = struct.unpack_from('<i', plain, p)[0]
        p += 4 + n
        if struct.unpack_from('<I', plain, p)[0] != offset:
            raise ValueError(f'lệch vị trí entry khi đọc index: {name}')
        if offset >= base_len:
            struct.pack_into('<I', plain, p, offset + delta)
            moved += 1
        elif offset + size > base_len:
            raise ValueError(f'entry vắt qua ranh giới KR: {name}')
        p += 16
    out = encrypt_idx(bytes(plain), key)
    if out[:4] != data[:4]:
        raise ValueError('khoá index đổi sau khi mã hoá lại')
    return out, entries, moved


def read_entries(idd, entries):
    with idd.open('rb') as f:
        for name, offset, size, _, _ in entries:
            f.seek(offset)
            yield name, f.read(size)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--kr', type=Path, default=Path('/home/admin/boom/clients/kr-00967'))
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('builds', nargs='+', help='lang=DIR theo thứ tự nối đuôi, ví dụ vi=... en=...')
    a = ap.parse_args()
    kr, out = a.kr.resolve(), a.out.resolve()
    builds = []
    for item in a.builds:
        lang, _, d = item.partition('=')
        if not lang or not d or lang == 'ko':
            raise SystemExit(f'tham số sai: {item}')
        builds.append((lang, Path(d).resolve()))
    for _, d in builds:
        if out == d or d in out.parents or out == kr or kr in out.parents:
            raise SystemExit('OUT không được nằm trong client KR hay thư mục bản dịch')
    out.mkdir(parents=True, exist_ok=True)
    stems = sorted({p.stem for _, d in builds for p in d.glob('*.idx')})
    report = {'kr': str(kr), 'order': [lang for lang, _ in builds], 'packs': {}}
    for stem in stems:
        kr_idd, kr_idx = kr / f'{stem}.idd', kr / f'{stem}.idx'
        if not kr_idd.is_file():
            raise SystemExit(f'không có pack KR: {stem}')
        base_len = kr_idd.stat().st_size
        target = out / f'{stem}.idd'
        tmp = target.with_suffix('.idd.part')
        pack = {'kr_bytes': base_len, 'tails': {}}
        with tmp.open('wb') as w, kr_idd.open('rb') as r:
            while chunk := r.read(CHUNK):
                w.write(chunk)
        (out / 'ko').mkdir(exist_ok=True)
        (out / 'ko' / f'{stem}.idx').write_bytes(kr_idx.read_bytes())
        for lang, d in builds:
            (out / lang).mkdir(exist_ok=True)
            idd, idx = d / f'{stem}.idd', d / f'{stem}.idx'
            if not idx.is_file():
                # Ngôn ngữ này không đổi pack: dùng index KR, chỉ trỏ vào phần KR.
                (out / lang / f'{stem}.idx').write_bytes(kr_idx.read_bytes())
                pack['tails'][lang] = {'bytes': 0, 'moved_entries': 0, 'index': 'kr'}
                continue
            if not same_prefix(idd, kr_idd):
                raise SystemExit(f'{lang}/{stem}.idd không bắt đầu bằng .idd KR nguyên vẹn')
            start = tmp.stat().st_size
            delta = start - base_len
            with tmp.open('ab') as w, idd.open('rb') as r:
                r.seek(base_len)
                while chunk := r.read(CHUNK):
                    w.write(chunk)
            index, entries, moved = shifted_index(idx, base_len, delta)
            (out / lang / f'{stem}.idx').write_bytes(index)
            # Kiểm: mọi entry đọc từ pack chung bằng index mới trùng byte với bản dịch riêng.
            new_entries = idf.parse_idx(idf.decrypt_idx(index, int.from_bytes(index[:4], 'little')))[1]
            for (n1, b1), (n2, b2) in zip(read_entries(idd, entries), read_entries(tmp, new_entries)):
                if n1 != n2 or b1 != b2:
                    raise SystemExit(f'kiểm đọc lại sai: {lang}/{stem}/{n1}')
            pack['tails'][lang] = {'offset': start, 'bytes': idd.stat().st_size - base_len, 'moved_entries': moved}
        tmp.replace(target)
        pack['shared_bytes'] = target.stat().st_size
        report['packs'][stem] = pack
    for lang in ['ko'] + [lang for lang, _ in builds]:
        report.setdefault('index_sha256', {})[lang] = {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out / lang).glob('*.idx'))}
    (out / 'share-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'index_sha256'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
