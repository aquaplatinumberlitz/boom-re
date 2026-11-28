import struct
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image, ImageChops, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i16
import l10n_ui_art_fix as art


def make_i16(image, frames):
    w, h = image.size
    template = struct.pack('<6I', frames, 2, 1, 0, h, w) + bytes(48 * frames)
    return i16.encode(template + b'\x01\x00\x00\x00\xc1', [image.tobytes()])


class LoginArt(unittest.TestCase):
    def test_vi_render_preserves_sprite_and_fits_outlined_diacritics(self):
        # Pillow discovers the installed font by name; no client or font path fixture.
        font_path = ImageFont.truetype('DejaVuSansCondensed-Bold.ttf', 12).path
        name = 'LO_LogTable00'
        entry = 'LoginStage/' + name
        base_rects = art.LOGIN_TABLES[name]
        rects = art.VI_LOGIN_TABLES[name]
        background = (17, 29, 43, 255)
        original = Image.new('RGBA', (456, 157), background)
        original.putpixel((0, 0), (20, 40, 60, 128))
        for rect in base_rects:
            x0, y0, x1, y1 = rect
            original.paste((0, 60, 119, 255), (x0 + 1, y0 + 1, x1 - 1, y1 - 1))
        blob = make_i16(original, 1)

        with (
            TemporaryDirectory() as tmp,
            patch.object(art, 'LOGIN', (name,)),
            patch.dict(art.LOGIN_SOURCES, {name: (*original.size, 1, art.sha(blob))}),
            patch.object(art.review, 'index_packs', return_value={('FxDesktop', entry): None}),
            patch.object(art.review, 'read_blob', return_value=blob),
            patch.object(art, '_find_ttf', return_value=font_path),
        ):
            out = Path(tmp)
            [(_, before, after)], receipt = art.render_login(out, None, out, lang='vi')
            with Image.open(out / 'vi-drawn' / 'FxDesktop' / entry / '0.png') as png:
                self.assertEqual(png.tobytes(), after.tobytes())

        self.assertEqual(after.getchannel('A').tobytes(), before.getchannel('A').tobytes())
        for rect in rects:
            before.paste(background, rect)
        labels = receipt[name]['labels']
        self.assertEqual([item['text'] for item in labels], ['CHỌN MÁY CHỦ', 'ID', 'MẬT KHẨU'])
        self.assertEqual([item['rect'] for item in labels], [list(rect) for rect in rects])
        self.assertEqual(labels[0]['size'], 12)
        self.assertEqual(labels[2]['size'], 11)
        self.assertEqual(labels[0]['rect'], [172, 3, 285, 23])
        self.assertEqual(labels[2]['rect'], [139, 117, 221, 137])
        for item in (labels[0], labels[2]):
            self.assertTrue(item['extension_evidence'])
            self.assertTrue(all(row['plain'] for row in item['extension_evidence']))
            self.assertLessEqual(max(row['max_deviation'] for row in item['extension_evidence']), 2)
        diff = ImageChops.difference(before.convert('RGB'), after.convert('RGB'))
        for label, rect in zip(labels, rects):
            with self.subTest(text=label['text']):
                x0, y0, x1, y1 = rect
                bbox = diff.crop(rect).getbbox()
                self.assertIsNotNone(bbox)
                left, top, right, bottom = bbox
                self.assertTrue(0 < left < right < x1 - x0)
                self.assertTrue(0 < top < bottom < y1 - y0)
                # Compare with the complete stroked ink on a canvas with room to spare.
                ref = Image.new('L', (256, 64))
                font = ImageFont.truetype(font_path, label['size'])
                ImageDraw.Draw(ref).text((16, 16), label['text'], font=font, fill=255, stroke_width=1)
                ref_l, ref_t, ref_r, ref_b = ref.getbbox()
                self.assertEqual((right - left, bottom - top), (ref_r - ref_l, ref_b - ref_t))
                diff.paste(0, rect)
        self.assertIsNone(diff.getbbox())

    def test_vi_rect_extension_fails_closed_on_non_plain_row(self):
        image = Image.new('RGBA', (32, 24), (20, 40, 60, 255))
        image.putpixel((10, 4), (255, 0, 0, 255))
        with self.assertRaisesRegex(ValueError, 'not plain background'):
            art._plain_row_evidence(image, (5, 5, 20, 10), (5, 4, 20, 11), [20, 21, 22])
        with self.assertRaisesRegex(ValueError, 'exceeds three rows'):
            art._plain_row_evidence(image, (5, 5, 20, 10), (5, 1, 20, 11), [20, 21, 22])
        abrupt = Image.new('RGBA', (32, 24), (20, 40, 60, 255))
        for x in (20, 21, 22):
            abrupt.putpixel((x, 4), (240, 240, 240, 255))
        with self.assertRaisesRegex(ValueError, 'not plain background'):
            art._plain_row_evidence(abrupt, (5, 5, 20, 10), (5, 4, 20, 11), [20, 21, 22])

    def test_vi_server_states_match_en_and_keep_frame_records(self):
        font_path = ImageFont.truetype('DejaVuSansCondensed-Bold.ttf', 12).path
        name = 'LO_SerHa'
        entry = 'LoginStage/' + name
        original = Image.new('RGBA', (95, 96), (20, 40, 60, 255))
        blob = make_i16(original, 5)
        with (
            TemporaryDirectory() as tmp,
            patch.object(art, 'LOGIN', (name,)),
            patch.dict(art.LOGIN_SOURCES, {name: (*original.size, 5, art.sha(blob))}),
            patch.object(art.review, 'index_packs', return_value={('FxDesktop', entry): None}),
            patch.object(art.review, 'read_blob', return_value=blob),
            patch.object(art, '_find_ttf', return_value=font_path),
        ):
            out = Path(tmp)
            [(_, _, vi)], receipt = art.render_login(out, None, out, lang='vi')
            [(_, _, en)], _ = art.render_login(out, None, out)
        self.assertEqual(vi.tobytes(), en.tobytes())
        self.assertEqual(receipt[name]['frames'], 5)
        labels = receipt[name]['labels']
        self.assertEqual([item['text'] for item in labels], ['HAPPY'] * 4)
        colors = ((255, 255, 255), (255, 255, 255), (255, 224, 0), (0, 113, 198))
        for row, color in enumerate(colors):
            state = vi.crop((0, row * 24, 95, (row + 1) * 24))
            self.assertIn(color + (255,), {pixel for _, pixel in state.getcolors(95 * 24)})


if __name__ == '__main__':
    unittest.main()
