#!/usr/bin/env python3
"""Ước lượng tĩnh bề rộng chữ của bản dịch so với câu Hàn, theo bảng bề rộng ký tự trong file font .fft.

Chỉ là xếp hạng nguy cơ tràn khung: không biết bề rộng khung thật của từng nhãn, không biết nhãn nào
dùng font nào (ở đây dùng CxUni.fft), chưa đo trên client. Bản chính thức (chữ PopTag cho tiếng Anh,
chữ bản VN cho tiếng Việt) được in riêng để làm mốc so.

  python3 tools/l10n_width.py --vi-font /duong/dan/font/VN/CxUni.fft [--out width.csv]
"""
import argparse
import collections
import csv
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = re.compile(r'</?font\b[^<>]*>', re.I)


class Font:
    """.fft: header 32 byte (u16 mã đầu, u16 mã cuối, rồi tại offset 8: số ô, rộng, cao, hai trường
    chưa rõ nghĩa, số byte bitmap mỗi ô); mỗi ô là 1 byte bề rộng bước rồi bitmap."""

    def __init__(self, path):
        self.data = Path(path).read_bytes()
        self.count, self.w, self.h, _, _, bitmap = struct.unpack_from('<6I', self.data, 8)
        self.size = bitmap + 1
        if 32 + self.count * self.size > len(self.data):
            raise ValueError(f'font ngắn hơn header mô tả: {path}')

    def width(self, text):
        best = 0
        for line in TAG.sub('', text).replace('\r', '').split('\n'):
            best = max(best, sum(self.data[32 + ord(ch) * self.size] for ch in line if ord(ch) < self.count))
        return best


def percentiles(values):
    values = sorted(values)
    return {p: round(values[min(len(values) - 1, len(values) * p // 100)], 2) for p in (50, 75, 90, 95, 99)} if values else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', type=Path, default=ROOT / 'l10n/catalog_en.csv')
    parser.add_argument('--kr-font', type=Path, default=Path('/home/admin/boom/clients/kr-00967/CxUni.fft'))
    parser.add_argument('--vi-font', type=Path, required=True, help='CxUni.fft của bộ font VN')
    parser.add_argument('--out', type=Path)
    a = parser.parse_args()
    kr, vn = Font(a.kr_font), Font(a.vi_font)
    with a.catalog.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    out, groups = [], collections.defaultdict(list)
    for r in rows:
        ko_px = kr.width(r['ko'])
        if not ko_px:
            continue
        vi_px = vn.width(r['vi']) if r['vi_status'] in ('translated', 'reused') and r['vi'] else 0
        en_px = kr.width(r['en']) if r['en_status'] in ('candidate', 'casefold_candidate', 'machine') and r['en'] else 0
        out.append({'id': r['id'], 'ko_px': ko_px, 'vi_px': vi_px, 'en_px': en_px,
                    'vi_ratio': f'{vi_px / ko_px:.2f}' if vi_px else '', 'en_ratio': f'{en_px / ko_px:.2f}' if en_px else ''})
        if r['id'].startswith('stock:'):
            continue
        length = 'ngắn (≤ 72 px)' if ko_px <= 72 else 'dài'
        if vi_px:
            groups['vi', 'chính thức' if r['vi_status'] == 'reused' else 'dịch máy', length].append(vi_px / ko_px)
        if en_px:
            official = r['en_status'] != 'machine'
            groups['en', 'chính thức' if official else 'dịch máy', length].append(en_px / ko_px)
    for key in sorted(groups):
        print(*key, len(groups[key]), percentiles(groups[key]), 'max', round(max(groups[key]), 2))
    if a.out:
        with a.out.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, list(out[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(out)


if __name__ == '__main__':
    main()
