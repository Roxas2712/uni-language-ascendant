import sys
import struct
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from frlg_tileset_relocation import extract, BASE


class TilesetHeaderTests(unittest.TestCase):
    def fixture(self):
        source, target = bytearray(1024), bytearray(2048)
        symbols = {}
        for prefix, old, new, size in [
            ('gTileset_', 64, 128, 24), ('gTilesetTiles_', 160, 700, 32),
            ('gTilesetPalettes_', 256, 900, 64), ('gMetatiles_', 400, 1100, 32),
            ('gMetatileAttributes_', 512, 1400, 64),
        ]:
            symbols[prefix+'DepartmentStore'] = {'off': old, 'size': size}
            if prefix in ('gTilesetPalettes_', 'gMetatileAttributes_'):
                block = bytes((i*13 + old//8) % 256 for i in range(size))
                source[old:old+size] = target[new:new+size] = block
        struct.pack_into('<6I', source, 64, 0x101, BASE+160, BASE+256, BASE+400, 0, BASE+512)
        struct.pack_into('<6I', target, 128, 0x101, BASE+700, BASE+900, BASE+1100, 0, BASE+1400)
        return source, target, symbols

    def test_two_unique_anchors_recover_translated_art(self):
        src, dst, symbols = self.fixture()
        mapped, proof = extract(src, dst, symbols)
        self.assertEqual(mapped[160], 700)
        self.assertEqual(mapped[400], 1100)
        self.assertEqual(len(proof['independent_anchors']), 2)

    def test_changed_header_callback_is_rejected(self):
        src, dst, symbols = self.fixture()
        struct.pack_into('<I', dst, 128+16, BASE+100)
        with self.assertRaises(AssertionError):
            extract(src, dst, symbols)

    def test_duplicate_anchor_is_rejected(self):
        src, dst, symbols = self.fixture()
        dst[1700:1764] = dst[900:964]
        with self.assertRaises(AssertionError):
            extract(src, dst, symbols)

    def test_duplicate_header_is_rejected(self):
        src, dst, symbols = self.fixture()
        dst[1800:1824] = dst[128:152]
        with self.assertRaises(AssertionError):
            extract(src, dst, symbols)


if __name__ == '__main__':
    unittest.main()
