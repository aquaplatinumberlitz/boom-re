#!/usr/bin/env python3
"""Render the six Vietnamese LoginStage sprites from read-only KR and VN font inputs."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import i16
import l10n_images_review as review


ROOT = Path(__file__).resolve().parents[1]
PACK = 'FxDesktop'
PREFIX = 'LoginStage/'
# Width, height, frame count and SHA-256 of the unpacked KR 00967 entry.
SOURCES = {
    'LO_LogTable00': (456, 157, 1, '111e49e762b7e3618e7a288e6dd36e9c99d5ae255d0203c4e44fca736501c770'),
    'LO_LogTable01': (516, 157, 1, '6b48294fadfd2bb93091fd289c30e3198a229d8d25449aca671d60cbeabc82f6'),
    'LO_SerDre': (95, 120, 5, '9be3f8cd737dae949a5917d95cdeae6c28f073b490fac2d2b5d0e0903a05d462'),
    'LO_SerDre2P': (138, 120, 5, '33bd43f6d4d947ac45a0c666e408cccff0ebc21c9e8873079bcc738bfdfd73dc'),
    'LO_SerHa': (95, 96, 5, 'faef2d48fa4eeec1042b551922cd9ab566dad4b5922cfad9fecd60c9e73c9212'),
    'LO_SerHa2P': (138, 96, 5, 'f941347409ec1b4372126a38b73ff8574d53dbbb9534a66234ef512eedf0847b'),
}
# Rectangles use half-open x, y coordinates; edges of fields/controls lie outside.
TABLES = {
    'LO_LogTable00': ((172, 5, 285, 21), (139, 94, 221, 111), (139, 120, 221, 137)),
    'LO_LogTable01': ((204, 5, 312, 21), (123, 94, 199, 111), (123, 120, 199, 137)),
}
WHITE = (255, 255, 255, 255)
BLUE_STROKE = (0, 60, 119, 255)
GOLD = (255, 224, 0, 255)
BLACK = (0, 0, 0, 255)
TITLE_STROKE = (179, 88, 0, 255)
INACTIVE = (0, 113, 198, 255)
INACTIVE_STROKE = (0, 80, 164, 255)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class BitmapFont:
    def __init__(self, data):
        self.count, self.width, self.height, _, _, stride = struct.unpack_from('<6I', data, 8)
        if (self.width, self.height, stride) != (12, 16, 24) or len(data) < 32 + 25 * self.count:
            raise ValueError('Cần font CxUni VN 12×16')
        self.data = data

    def ink(self, text):
        offsets = [32 + ord(c) * 25 for c in text]
        if any(offset >= 32 + 25 * self.count or not 0 < self.data[offset] <= self.width for offset in offsets):
            raise ValueError(f'Font thiếu glyph cho {text!r}')
        width = sum(self.data[offset] for offset in offsets)
        mask = Image.new('L', (width + self.width, self.height))
        x = 0
        for char, offset in zip(text, offsets):
            bits = int.from_bytes(self.data[offset + 1:offset + 25], 'big')
            if not bits and char != ' ':
                raise ValueError(f'Font thiếu nét của {char!r}')
            for n in range(self.width * self.height):
                if bits & (1 << (self.width * self.height - 1 - n)):
                    y, col = divmod(n, self.width)
                    mask.putpixel((x + col, y), 255)
            x += self.data[offset]
        bbox = mask.getbbox()
        if not bbox:
            raise ValueError('Nhãn không có chữ')
        return mask.crop(bbox)


def label(sprite, rect, text, font, fill, stroke):
    x0, y0, x1, y1 = rect
    if not (0 <= x0 < x1 < sprite.width and 0 <= y0 < y1 <= sprite.height):
        raise ValueError('Vùng nhãn hoặc cột lấy màu nằm ngoài ảnh')
    ink = font.ink(text)
    w, h = x1 - x0, y1 - y0
    if ink.width + 2 > w or ink.height + 2 > h:
        raise ValueError(f'Nhãn {text!r} tràn vùng {rect}')
    pixels = sprite.load()
    # One background sample per row preserves the vertical gradients in KR.
    # The donor column is just to the right of the selected text band.
    for y in range(y0, y1):
        color = pixels[x1, y]
        if color[3] != 255:
            raise ValueError(f'Cột lấy màu có alpha tại {(x1, y)}')
        for x in range(x0, x1):
            pixels[x, y] = color
    centered = Image.new('L', (w, h))
    centered.paste(ink, ((w - ink.width) // 2, (h - ink.height) // 2))
    sprite.paste(stroke, rect, centered.filter(ImageFilter.MaxFilter(3)))
    sprite.paste(fill, rect, centered)


def labels_for(name, state_rows, catalog):
    if name in TABLES:
        title, user, password = TABLES[name]
        # Server heading has no corresponding text key in the KR catalog.
        return [(title, 'CHỌN MÁY CHỦ', WHITE, TITLE_STROKE),
                (user, catalog['UserID'].upper(), WHITE, BLUE_STROKE),
                (password, catalog['Password'].upper(), WHITE, BLUE_STROKE)]
    server = 'DREAM' if name.startswith('LO_SerDre') else 'HAPPY'
    return [((25, i * 24 + 4, 87, i * 24 + 20), server, *(
        (GOLD, BLACK) if i == state_rows - 2 else
        (INACTIVE, INACTIVE_STROKE) if i == state_rows - 1 else
        (WHITE, BLUE_STROKE))) for i in range(state_rows)]


def draw(name, source, font, catalog):
    w, h, count, expected = SOURCES[name]
    parsed = i16.parse(source)
    if sha(source) != expected or parsed['sizes'] != [(h, w)] or parsed['nframes'] != count:
        raise ValueError(f'{name}: không khớp nguồn KR 00967 đã đo')
    rgba, _, _ = i16.decode_image(parsed['images'][0], w, h)
    before = Image.frombytes('RGBA', (w, h), rgba)
    after = before.copy()
    allowed = Image.new('1', (w, h))
    rects = labels_for(name, h // 24, catalog)
    for rect, text, fill, stroke in rects:
        label(after, rect, text, font, fill, stroke)
        allowed.paste(1, rect)
    # The unchanged pixels include every checkbox, field, frame border and alpha.
    if ImageChops.difference(before, after).getbbox(alpha_only=False) is None:
        raise ValueError(f'{name}: không có thay đổi')
    unchanged = before.copy()
    unchanged.paste(after, (0, 0), allowed)
    if unchanged.tobytes() != after.tobytes() or before.getchannel('A').tobytes() != after.getchannel('A').tobytes():
        raise ValueError(f'{name}: đổi pixel ngoài vùng chữ hoặc đổi alpha')
    # Use the same encoder as l10n_build and verify the original frame records.
    rebuilt = i16.parse(i16.encode(source, [after.tobytes()]))
    if rebuilt['frames'] != parsed['frames'] or rebuilt['sizes'] != parsed['sizes']:
        raise ValueError(f'{name}: metadata frame hoặc kích thước đổi')
    if i16.decode_image(rebuilt['images'][0], w, h)[0] != after.tobytes():
        raise ValueError(f'{name}: pixel thay đổi khi encode/decode I16')
    return before, after, [{'rect': rect, 'label': text} for rect, text, _, _ in rects]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kr', type=Path, required=True, help='Client KR 00967 chỉ đọc')
    parser.add_argument('--font', type=Path, required=True, help='CxUni (hoặc CxUniBold) VN 12×16 của gói')
    parser.add_argument('--out', type=Path, required=True, help='Thư mục local mới, không ghi vào client')
    args = parser.parse_args()
    if args.out.resolve().is_relative_to(args.kr.resolve()):
        parser.error('Output không được nằm trong thư mục client')
    font_data = args.font.read_bytes()
    font = BitmapFont(font_data)
    with (ROOT / 'l10n/catalog.csv').open(encoding='utf-8-sig', newline='') as f:
        catalog = {row['id']: row['vi'] for row in csv.DictReader(f) if row['id'] in ('UserID', 'Password')}
    if set(catalog) != {'UserID', 'Password'} or not all(catalog.values()):
        raise ValueError('Catalog thiếu nhãn đăng nhập')
    index = review.index_packs(args.kr, True)
    images = {}
    for name in SOURCES:
        entry = PREFIX + name
        source = review.read_blob(index[PACK, entry], entry)
        images[name] = draw(name, source, font, catalog)

    args.out.mkdir(mode=0o700)
    contact = Image.new('RGB', (1072, 35 + sum(im.height + 24 for im, _, _ in images.values())), '#ebeff2')
    captions = ImageDraw.Draw(contact)
    captions.text((10, 8), 'KR / Before', fill='black')
    captions.text((546, 8), 'VI / After', fill='black')
    y = 30
    entries = {}
    for name, (before, after, regions) in images.items():
        target = args.out / 'drawn' / PACK / PREFIX / name
        target.mkdir(parents=True)
        png = target / '0.png'
        after.save(png)
        for x, sprite in ((10, before), (546, after)):
            captions.text((x, y), name, fill='black')
            contact.paste(sprite, (x, y + 16), sprite)
        y += before.height + 24
        entries[name] = {'source_sha256': SOURCES[name][-1], 'png_sha256': sha(png.read_bytes()),
                         'size': before.size, 'frames': SOURCES[name][2], 'labels': regions}
    contact.save(args.out / 'before-after.png')
    (args.out / 'receipt.json').write_text(json.dumps(
        {'font_sha256': sha(font_data), 'review': 'pending', 'entries': entries}, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(entries)} ảnh; xem {args.out / "before-after.png"} trước khi đóng gói')


if __name__ == '__main__':
    main()
