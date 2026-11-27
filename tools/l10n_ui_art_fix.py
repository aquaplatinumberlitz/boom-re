#!/usr/bin/env python3
"""Build bounded VI login JPEG and English UI sprite/background replacements.

Only reads client packs/fonts and writes a disposable image-dir tree under ``--out``
matching the layout consumed by :mod:`l10n_build`.
"""
import argparse
import hashlib
import io
import json
import statistics
import struct
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont

import i16
import l10n_images_review as review

ROOT = Path(__file__).resolve().parents[1]
BOLD_TTF = Path('/usr/share/fonts/TTF/DejaVuSans-Bold.ttf')
CONDENSED_BOLD_TTF = Path('/usr/share/fonts/TTF/DejaVuSansCondensed-Bold.ttf')

LOGIN = ('LO_LogTable00', 'LO_LogTable01', 'LO_SerDre', 'LO_SerDre2P', 'LO_SerHa', 'LO_SerHa2P')
LOGIN_TABLES = {
    'LO_LogTable00': ((172, 5, 285, 21), (139, 94, 221, 111), (139, 120, 221, 137)),
    'LO_LogTable01': ((204, 5, 312, 21), (123, 94, 199, 111), (123, 120, 199, 137)),
}
LOGIN_SOURCES = {
    'LO_LogTable00': (456, 157, 1, '111e49e762b7e3618e7a288e6dd36e9c99d5ae255d0203c4e44fca736501c770'),
    'LO_LogTable01': (516, 157, 1, '6b48294fadfd2bb93091fd289c30e3198a229d8d25449aca671d60cbeabc82f6'),
    'LO_SerDre': (95, 120, 5, '9be3f8cd737dae949a5917d95cdeae6c28f073b490fac2d2b5d0e0903a05d462'),
    'LO_SerDre2P': (138, 120, 5, '33bd43f6d4d947ac45a0c666e408cccff0ebc21c9e8873079bcc738bfdfd73dc'),
    'LO_SerHa': (95, 96, 5, 'faef2d48fa4eeec1042b551922cd9ab566dad4b5922cfad9fecd60c9e73c9212'),
    'LO_SerHa2P': (138, 96, 5, 'f941347409ec1b4372126a38b73ff8574d53dbbb9534a66234ef512eedf0847b'),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class BitmapFont:
    def __init__(self, data: bytes):
        self.count, self.width, self.height, _, _, self.stride = struct.unpack_from('<6I', data, 8)
        self.data = data
        if (self.width, self.height, self.stride) != (12, 16, 24):
            raise ValueError('font must be 12x16 CxUni')

    def ink(self, text: str) -> Image.Image:
        mask = Image.new('L', (self.width * max(1, len(text)) + self.width, self.height))
        x = 0
        for ch in text:
            off = 32 + ord(ch) * 25
            if off + 25 > len(self.data) or not 0 < self.data[off] <= self.width:
                raise ValueError(f'font missing glyph {ch!r}')
            bits = int.from_bytes(self.data[off + 1 : off + 25], 'big')
            for n in range(self.width * self.height):
                if bits & (1 << (self.width * self.height - 1 - n)):
                    y, col = divmod(n, self.width)
                    mask.putpixel((x + col, y), 255)
            x += self.data[off]
        box = mask.getbbox()
        if not box:
            raise ValueError('empty label')
        return mask.crop(box)


def _find_ttf(condensed: bool = True) -> Path | None:
    order = (CONDENSED_BOLD_TTF, BOLD_TTF) if condensed else (BOLD_TTF, CONDENSED_BOLD_TTF)
    for path in order:
        if path.is_file():
            return path
    return None


def _draw_ttf_label(
    im: Image.Image,
    rect: tuple[int, int, int, int],
    text: str,
    size: int,
    fill: tuple[int, int, int],
    stroke: tuple[int, int, int] | None = None,
    stroke_width: int = 1,
    condensed: bool = True,
    bitmap_font: BitmapFont | None = None,
    align: str = 'center',
) -> None:
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    ttf_path = _find_ttf(condensed)
    if ttf_path is not None:
        layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        # Shrink font size automatically until the label fits comfortably with stroke margin.
        cur_size = size
        font = ImageFont.truetype(str(ttf_path), cur_size)
        pad = stroke_width * 2 + 2
        while cur_size > 7:
            bbox = d.multiline_textbbox((0, 0), text, font=font, stroke_width=stroke_width, align='center')
            if (bbox[2] - bbox[0]) <= w - pad and (bbox[3] - bbox[1]) <= h - 1:
                break
            cur_size -= 1
            font = ImageFont.truetype(str(ttf_path), cur_size)
        bbox = d.multiline_textbbox((0, 0), text, font=font, stroke_width=stroke_width, align='center')
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if align == 'right':
            tx = w - tw - 2 - bbox[0]
        elif align == 'left':
            tx = 2 - bbox[0]
        else:
            tx = (w - tw) / 2 - bbox[0]
        ty = (h - th) / 2 - bbox[1]
        kw = {'fill': fill + (255,), 'font': font, 'align': 'center'}
        if stroke is not None and stroke_width > 0:
            kw.update({'stroke_width': stroke_width, 'stroke_fill': stroke + (255,)})
        d.multiline_text((round(tx), round(ty)), text, **kw)
        base_crop = im.crop((x0, y0, x1, y1)).convert('RGBA')
        alpha = base_crop.getchannel('A')
        composited = Image.alpha_composite(base_crop, layer)
        composited.putalpha(alpha)
        im.paste(composited, (x0, y0))
        return

    if bitmap_font is None:
        raise ValueError('no TTF or bitmap font available')
    ink = bitmap_font.ink(text.replace('\n', ' '))
    scale = min((w - 2) / max(1, ink.width), (h - 2) / max(1, ink.height), 1.0)
    if scale < 1.0:
        ink = ink.resize((max(1, int(ink.width * scale)), max(1, int(ink.height * scale))), Image.Resampling.NEAREST)
    ox = x0 + (w - ink.width) // 2
    oy = y0 + (h - ink.height) // 2
    px = im.load()
    for yy in range(ink.height):
        for xx in range(ink.width):
            if ink.getpixel((xx, yy)) >= 128:
                old = px[ox + xx, oy + yy]
                px[ox + xx, oy + yy] = fill + (old[3],)


def _erase_horizontal_median(
    im: Image.Image,
    before: Image.Image,
    rect: tuple[int, int, int, int],
    donor_xs: list[int],
) -> None:
    x0, y0, x1, y1 = rect
    bpx = before.load()
    px = im.load()
    valid_xs = [x for x in donor_xs if 0 <= x < im.width]
    for y in range(y0, y1):
        rs = [bpx[x, y][0] for x in valid_xs if bpx[x, y][3] > 0]
        gs = [bpx[x, y][1] for x in valid_xs if bpx[x, y][3] > 0]
        bs = [bpx[x, y][2] for x in valid_xs if bpx[x, y][3] > 0]
        if not rs:
            c = bpx[valid_xs[0], y][:3]
        else:
            c = (int(statistics.median(rs)), int(statistics.median(gs)), int(statistics.median(bs)))
        for x in range(x0, x1):
            px[x, y] = c + (px[x, y][3],)


def decode_image_at(blob: bytes, index: int = 0) -> tuple[dict, Image.Image]:
    s = i16.parse(blob)
    h, w = s['sizes'][index]
    rgba, _, _ = i16.decode_image(s['images'][index], w, h)
    return s, Image.frombytes('RGBA', (w, h), rgba)


def validate_i16(original: bytes, after: Image.Image, allowed: list[tuple[int, int, int, int]], index: int = 0) -> bytes:
    s, before = decode_image_at(original, index)
    if before.getchannel('A').tobytes() != after.getchannel('A').tobytes():
        raise ValueError('alpha changed')
    diff = ImageChops.difference(before, after).load()
    for y in range(before.height):
        for x in range(before.width):
            if diff[x, y][:3] != (0, 0, 0) or diff[x, y][3] != 0:
                if not any(r[0] <= x < r[2] and r[1] <= y < r[3] for r in allowed):
                    raise ValueError(f'pixel changed outside allowed boxes at {(x, y)}')
    payload = [None] * len(s['images'])
    payload[index] = after.tobytes()
    rebuilt = i16.encode(original, payload)
    rs, decoded = decode_image_at(rebuilt, index)
    if rs['frames'] != s['frames'] or rs['sizes'] != s['sizes'] or decoded.getchannel('A').tobytes() != after.getchannel('A').tobytes():
        raise ValueError('I16 roundtrip failed')
    diff2 = ImageChops.difference(before, decoded).load()
    for y in range(before.height):
        for x in range(before.width):
            if diff2[x, y][:3] != (0, 0, 0) or diff2[x, y][3] != 0:
                if not any(r[0] <= x < r[2] and r[1] <= y < r[3] for r in allowed):
                    raise ValueError(f'roundtrip changed pixel outside allowed boxes at {(x, y)}')
    return rebuilt


def read_entry(idx: dict, pack: str, name: str) -> bytes:
    return review.read_blob(idx[(pack, name)], name)


def render_login(kr: Path, font_data: bytes, out: Path) -> tuple[list, dict]:
    ki = review.index_packs(kr, True)
    bfont = BitmapFont(font_data)
    rendered = []
    receipt = {}
    for name in LOGIN:
        src = read_entry(ki, 'FxDesktop', 'LoginStage/' + name)
        w, h, n, expected = LOGIN_SOURCES[name]
        if sha(src) != expected:
            raise ValueError(f'{name}: KR hash mismatch')
        s, before = decode_image_at(src, 0)
        after = before.copy()
        boxes = []
        if name in LOGIN_TABLES:
            specs = (
                ('SELECT SERVER', 12, (255, 255, 255), (179, 88, 0), True),
                ('ID', 12, (255, 255, 255), (0, 60, 119), False),
                ('PASSWORD', 11, (255, 255, 255), (0, 60, 119), True),
            )
            for rect, (label, sz, fill, stroke, cond) in zip(LOGIN_TABLES[name], specs):
                donor_xs = [min(after.width - 1, rect[2] + k) for k in range(3)]
                _erase_horizontal_median(after, before, rect, donor_xs)
                _draw_ttf_label(after, rect, label, sz, fill, stroke=stroke, stroke_width=1, condensed=cond, bitmap_font=bfont)
                boxes.append(rect)
        else:
            visible = h // 24
            server = 'DREAM' if name.startswith('LO_SerDre') else 'HAPPY'
            for i in range(visible):
                rect = (25, 4 + 24 * i, 87, 20 + 24 * i)
                fill = (255, 224, 0) if i == visible - 2 else ((0, 113, 198) if i == visible - 1 else (255, 255, 255))
                stroke = (0, 0, 0) if i == visible - 2 else ((0, 80, 164) if i == visible - 1 else (0, 60, 119))
                _erase_horizontal_median(after, before, rect, [22, 23, 88, 89])
                _draw_ttf_label(after, rect, server, 12, fill, stroke=stroke, stroke_width=1, condensed=True, bitmap_font=bfont)
                boxes.append(rect)
        rebuilt = validate_i16(src, after, boxes, 0)
        target = out / 'en-drawn' / 'FxDesktop' / 'LoginStage' / name
        target.mkdir(parents=True, exist_ok=True)
        (target / '0.png').write_bytes(i16.png(after.tobytes(), w, h))
        rendered.append(('FxDesktop/LoginStage/' + name, before, after))
        receipt[name] = {'pack': 'FxDesktop', 'entry': 'LoginStage/' + name, 'dims': [w, h], 'frames': n, 'sha256': sha(rebuilt)}
    return rendered, receipt


def fix_vi_background(vn: Path, out: Path) -> dict:
    vi = review.index_packs(vn, False)
    rec = vi.get('LoginStage/CAStage') or vi.get('loginstage/CAStage')
    if rec is None:
        raise ValueError('VN pack has no LoginStage/CAStage')
    src = review.read_blob(rec, 'LoginStage/CAStage')
    before = Image.open(io.BytesIO(src)).convert('RGB')
    after = before.copy()
    px = after.load()
    # Erase only the 4 bottom blue button strips (x=181..619, y=553..592) while preserving
    # the bamboo on the left (x<181) and right/copyright corner (x>=619).
    y_top, y_bot = 553, 591
    for y in range(y_top + 1, y_bot):
        t = (y - y_top) / (y_bot - y_top)
        for x in range(181, 619):
            a = before.getpixel((x, y_top))
            b = before.getpixel((x, y_bot))
            px[x, y] = tuple(round(a[k] * (1.0 - t) + b[k] * t) for k in range(3))
    target = out / 'vi-drawn' / 'FxDesktop' / 'LoginStage'
    target.mkdir(parents=True, exist_ok=True)
    jpg_path = target / 'CAStage.jpg'
    after.save(jpg_path, quality=95)

    sheet = Image.new('RGB', (1600, 900), 'white')
    sheet.paste(before, (0, 0))
    sheet.paste(after, (800, 0))
    sheet.paste(before.crop((0, 520, 800, 600)).resize((800, 160)), (0, 650))
    sheet.paste(after.crop((0, 520, 800, 600)).resize((800, 160)), (800, 650))
    sheet.save(out / 'before-after-vi-login-bg.png')
    return {'pack': 'FxDesktop', 'entry': 'LoginStage/CAStage', 'dims': [800, 600], 'frames': 1, 'sha256': sha(jpg_path.read_bytes())}


def _paint_bt01_to_04(src: bytes, label: str, bfont: BitmapFont) -> tuple[Image.Image, Image.Image, bytes]:
    _, before = decode_image_at(src, 0)
    after = before.copy()
    boxes = []
    # 5 stacked frames of 51x24 each. Preserve bevel border & per-scanline gradient using donor x=4,5,45,46.
    frame_styles = (
        ((255, 255, 255), (0, 53, 137)),   # frame 0 normal
        ((255, 255, 255), (0, 53, 137)),   # frame 1 hover
        ((152, 236, 255), (0, 102, 171)),  # frame 2 disabled
        ((255, 255, 255), (0, 53, 137)),   # frame 3 pressed
        ((255, 255, 255), (0, 53, 137)),   # frame 4 focus/selected
    )
    for f in range(5):
        rect = (6, f * 24 + 4, 45, f * 24 + 20)
        _erase_horizontal_median(after, before, rect, [4, 5, 45, 46])
        fill, stroke = frame_styles[f]
        _draw_ttf_label(after, rect, label, 10, fill, stroke=stroke, stroke_width=1, condensed=True, bitmap_font=bfont)
        boxes.append(rect)
    rebuilt = validate_i16(src, after, boxes, 0)
    return before, after, rebuilt


def _paint_pre_img(src: bytes, bfont: BitmapFont) -> tuple[Image.Image, Image.Image, bytes]:
    _, before = decode_image_at(src, 0)
    after = before.copy()
    rows = (
        (0, 'READY', (115, 165, 215), (0, 32, 65)),   # muted ready
        (1, 'READY', (255, 190, 0), (65, 35, 0)),     # active ready
        (2, 'HOST', (115, 240, 65), (0, 55, 15)),     # active host
        (3, 'SHOP', (105, 235, 150), (0, 55, 35)),    # active shop
    )
    boxes = []
    for r, label, fill, stroke in rows:
        rect = (5, r * 16 + 1, 89, r * 16 + 15)
        _erase_horizontal_median(after, before, rect, [2, 3, 90, 91])
        _draw_ttf_label(after, rect, label, 11, fill, stroke=stroke, stroke_width=1, condensed=True, bitmap_font=bfont)
        boxes.append(rect)
    rebuilt = validate_i16(src, after, boxes, 0)
    return before, after, rebuilt


def _paint_char_banner(src: bytes, title: str, subtitle: str, bfont: BitmapFont) -> tuple[Image.Image, Image.Image, bytes]:
    _, before = decode_image_at(src, 0)
    after = before.copy()
    erase_rect = (137, 8, 274, 77)
    _erase_horizontal_median(after, before, erase_rect, [134, 135, 136, 274, 275])
    _draw_ttf_label(after, (140, 10, 268, 42), title, 22, (255, 245, 130), stroke=(0, 50, 125), stroke_width=2, condensed=False, bitmap_font=bfont, align='right')
    _draw_ttf_label(after, (137, 46, 271, 74), subtitle, 12, (255, 255, 255), stroke=(0, 50, 125), stroke_width=1, condensed=True, bitmap_font=bfont, align='right')
    rebuilt = validate_i16(src, after, [erase_rect], 0)
    return before, after, rebuilt


def _paint_room_char_banner(src: bytes, title: str, subtitle: str, bfont: BitmapFont) -> tuple[Image.Image, Image.Image, bytes]:
    _, before = decode_image_at(src, 0)
    after = before.copy()
    erase_rect = (165, 5, 274, 48)
    _erase_horizontal_median(after, before, erase_rect, [133, 134, 135, 136, 137])
    _draw_ttf_label(after, (175, 4, 270, 27), title, 18, (255, 245, 130), stroke=(0, 50, 125), stroke_width=2, condensed=False, bitmap_font=bfont, align='right')
    _draw_ttf_label(after, (166, 28, 272, 46), subtitle, 11, (255, 255, 255), stroke=(0, 50, 125), stroke_width=1, condensed=True, bitmap_font=bfont, align='right')
    rebuilt = validate_i16(src, after, [erase_rect], 0)
    return before, after, rebuilt


def _paint_game_stage_item_idx(src: bytes, image_index: int, bfont: BitmapFont) -> tuple[Image.Image, Image.Image, bytes]:
    _, before = decode_image_at(src, image_index)
    after = before.copy()
    rect = (12, 6, 82, 28)
    _erase_horizontal_median(after, before, rect, [8, 9, 10, 83, 84])
    _draw_ttf_label(after, rect, 'MY ITEM', 11, (255, 255, 255), stroke=(0, 55, 120), stroke_width=1, condensed=True, bitmap_font=bfont)
    rebuilt = validate_i16(src, after, [rect], image_index)
    return before, after, rebuilt


def _paint_room_bg(src: bytes, bfont: BitmapFont) -> tuple[Image.Image, Image.Image, bytes]:
    before = Image.open(io.BytesIO(src)).convert('RGB')
    after = before.copy()
    rgba = after.convert('RGBA')
    rgba_before = before.convert('RGBA')

    team_box = (480, 255, 542, 276)
    _erase_horizontal_median(rgba, rgba_before, team_box, [544, 546, 548])
    _draw_ttf_label(rgba, team_box, 'TEAM', 11, (0, 62, 135), stroke=None, stroke_width=0, condensed=True, bitmap_font=bfont, align='left')

    map_box = (480, 325, 532, 345)
    _erase_horizontal_median(rgba, rgba_before, map_box, [544, 546, 548])
    _draw_ttf_label(rgba, map_box, 'MAP', 11, (0, 62, 135), stroke=None, stroke_width=0, condensed=True, bitmap_font=bfont, align='left')

    auto_box = (712, 498, 751, 527)
    _erase_horizontal_median(rgba, rgba_before, auto_box, [709, 710, 752])
    _draw_ttf_label(rgba, auto_box, 'AUTO\nREADY', 9, (190, 228, 255), stroke=(0, 48, 100), stroke_width=1, condensed=True, bitmap_font=bfont, align='center')

    after = rgba.convert('RGB')
    buf = io.BytesIO()
    after.save(buf, format='JPEG', quality=95)
    return before, after, buf.getvalue()


def render_ui(kr: Path, font_data: bytes, out: Path) -> list:
    idx = review.index_packs(kr, True)
    bfont = BitmapFont(font_data)
    rendered = []
    receipt = []

    for bt_num, label in ((1, 'ALL'), (2, 'NORMAL'), (3, 'LUXURY'), (4, 'SUPER')):
        pack, entry = 'FxContents', f'CharacterSelectAll/CAStage_CharSetUpDlg_BT0{bt_num}'
        src = read_entry(idx, pack, entry)
        before, after, rebuilt = _paint_bt01_to_04(src, label, bfont)
        d = out / 'en-drawn' / pack / entry
        d.mkdir(parents=True, exist_ok=True)
        (d / '0.png').write_bytes(i16.png(after.tobytes(), after.width, after.height))
        rendered.append((pack + '/' + entry, before, after))
        receipt.append({'pack': pack, 'entry': entry, 'dims': list(after.size), 'frames': 5, 'image_index': 0, 'sha256': sha(rebuilt)})

    for pack, entry, fn, image_index, nframes in (
        ('FxMap', 'Prepare/PRE_Img', lambda s: _paint_pre_img(s, bfont), 0, 29),
        ('FxDesktop', 'Etc/ChaInfo_Char00', lambda s: _paint_char_banner(s, 'DAO', 'Righteous & Loyal!', bfont), 0, 1),
        ('FxContents', 'CharacterSelect/S_Cha00', lambda s: _paint_room_char_banner(s, 'DAO', 'Righteous & Loyal!', bfont), 0, 1),
        ('FxStage', 'Game/GameStageItem', lambda s: _paint_game_stage_item_idx(s, 0, bfont), 0, 41),
        ('FxStage', 'Game/GameStageItem', lambda s: _paint_game_stage_item_idx(s, 2, bfont), 2, 41),
    ):
        src = read_entry(idx, pack, entry)
        before, after, rebuilt = fn(src)
        d = out / 'en-drawn' / pack / entry
        d.mkdir(parents=True, exist_ok=True)
        (d / f'{image_index}.png').write_bytes(i16.png(after.tobytes(), after.width, after.height))
        if before.width > 360:
            rendered.append((f'{pack}/{entry}[{image_index}] (left crop)', before.crop((0, 0, 300, before.height)), after.crop((0, 0, 300, after.height))))
        else:
            rendered.append((f'{pack}/{entry}[{image_index}]', before, after))
        receipt.append({'pack': pack, 'entry': entry, 'dims': list(after.size), 'frames': nframes, 'image_index': image_index, 'sha256': sha(rebuilt)})

    # Room background labels (TEAM, MAP, AUTO READY)
    bg_pack, bg_entry = 'FxMap', 'Prepare/CAStage_Custom'
    bg_src = read_entry(idx, bg_pack, bg_entry)
    bg_before, bg_after, bg_jpg = _paint_room_bg(bg_src, bfont)
    bg_target = out / 'en-drawn' / bg_pack / 'Prepare' / 'CAStage_Custom.jpg'
    bg_target.parent.mkdir(parents=True, exist_ok=True)
    bg_target.write_bytes(bg_jpg)
    crop_box = (475, 250, 760, 560)
    rendered.append((bg_pack + '/' + bg_entry + ' (labels crop)', bg_before.crop(crop_box).convert('RGBA'), bg_after.crop(crop_box).convert('RGBA')))
    receipt.append({'pack': bg_pack, 'entry': bg_entry, 'dims': list(bg_after.size), 'frames': 1, 'image_index': 0, 'sha256': sha(bg_jpg)})

    return rendered, receipt


def build_contact_sheet(items: list[tuple[str, Image.Image, Image.Image]], path: Path) -> None:
    row_h = 190
    col_w = 520
    sheet = Image.new('RGB', (col_w * 2, max(row_h, row_h * len(items))), '#e8edf2')
    d = ImageDraw.Draw(sheet)
    for idx, (name, b, a) in enumerate(items):
        y = idx * row_h
        d.text((8, y + 4), f'{name}  [Original KR]', fill='black')
        d.text((col_w + 8, y + 4), '[Rendered EN]', fill='black')
        max_w, max_h = col_w - 20, row_h - 32
        scale = min(max_w / max(1, b.width), max_h / max(1, b.height))
        if scale > 1.0:
            scale = min(2.0, int(scale)) if scale >= 2.0 else 1.0
        nw, nh = max(1, int(b.width * scale)), max(1, int(b.height * scale))
        resample = Image.Resampling.NEAREST if scale >= 1.0 else Image.Resampling.LANCZOS
        qb = b.convert('RGBA').resize((nw, nh), resample)
        qa = a.convert('RGBA').resize((nw, nh), resample)
        sheet.paste(qb, (8, y + 24), qb)
        sheet.paste(qa, (col_w + 8, y + 24), qa)
    sheet.save(path)


def main(argv=None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--kr', type=Path, required=True)
    p.add_argument('--vn', type=Path, required=True)
    p.add_argument('--font', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(argv)
    out = a.out.resolve()
    if out == a.kr.resolve() or out == a.vn.resolve() or a.kr.resolve() in out.parents or a.vn.resolve() in out.parents:
        p.error('--out must be outside input packs')
    out.mkdir(parents=True, exist_ok=True)
    data = a.font.read_bytes()
    ui_rendered, ui_receipt = render_ui(a.kr, data, out)
    login_rendered, login_receipt = render_login(a.kr, data, out)
    vi = fix_vi_background(a.vn, out)
    build_contact_sheet(login_rendered + ui_rendered, out / 'before-after-en-ui.png')
    receipt = {'entries': ui_receipt + list(login_receipt.values()) + [vi], 'font_sha256': sha(data), 'review': 'pending'}
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'ui_entries': len(ui_receipt), 'login_entries': len(login_receipt), 'vi_background': vi['entry'], 'out': str(out)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
