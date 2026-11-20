from collections import Counter
import struct
import unittest

from PIL import Image

from l10n_login_art_vi import BitmapFont, SOURCES, labels_for, label


class LoginArt(unittest.TestCase):
    def font(self):
        count = ord('A') + 1
        data = bytearray(32 + 25 * count)
        struct.pack_into('<6I', data, 8, count, 12, 16, 13, 3, 24)
        offset = 32 + 25 * ord('A')
        data[offset] = 6
        # A horizontal stroke placed at x=1..4, y=2 and a vertical pixel at (1, 3).
        data[offset + 1:offset + 25] = ((0b011110000000 << (13 * 12)) |
                                       (0b010000000000 << (12 * 12))).to_bytes(24, 'big')
        return BitmapFont(data)

    def test_draw_is_bounded_and_preserves_each_row_background(self):
        sprite = Image.new('RGBA', (20, 20))
        for y in range(sprite.height):
            sprite.paste((y, 80, 120, 255), (0, y, sprite.width, y + 1))
        original = sprite.copy()
        allowed = (3, 4, 17, 16)
        sprite.paste((0, 0, 0, 255), (4, 5, 16, 15))  # old opaque text
        ink, stroke = (255, 255, 255, 255), (255, 204, 0, 255)
        label(sprite, allowed, 'A', self.font(), ink, stroke)
        for y in range(sprite.height):
            for x in range(sprite.width):
                color = sprite.getpixel((x, y))
                bg = original.getpixel((x, y))
                if 3 <= x < 17 and 4 <= y < 16:
                    self.assertIn(color, (ink, stroke, bg))
                else:
                    self.assertEqual(color, bg)
        self.assertEqual(Counter(sprite.getpixel((x, y)) for y in range(sprite.height) for x in range(sprite.width))[ink], 5)
        self.assertGreater(Counter(sprite.getpixel((x, y)) for y in range(sprite.height) for x in range(sprite.width))[stroke], 0)

    def test_bad_font_and_label_overflow_are_rejected(self):
        sprite = Image.new('RGBA', (20, 20), 'white')
        before = sprite.tobytes()
        with self.assertRaisesRegex(ValueError, 'tràn vùng'):
            label(sprite, (2, 2, 7, 16), 'AA', self.font(), 'white', 'black')
        self.assertEqual(sprite.tobytes(), before)
        with self.assertRaisesRegex(ValueError, 'thiếu glyph'):
            self.font().ink('Ế')

    def test_atlases_use_one_label_per_visible_state_not_per_frame_record(self):
        names = {'LO_SerDre': 5, 'LO_SerDre2P': 5, 'LO_SerHa': 4, 'LO_SerHa2P': 4}
        for name, visible in names.items():
            with self.subTest(name=name):
                _, height, frames, _ = SOURCES[name]
                self.assertEqual(frames, 5)
                regions = labels_for(name, height // 24, {})
                self.assertEqual(len(regions), visible)
                self.assertEqual([rect[1] for rect, *_ in regions], [4 + 24 * i for i in range(visible)])


if __name__ == '__main__':
    unittest.main()
