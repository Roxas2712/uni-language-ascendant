import importlib.util
import struct
import unittest
import zlib
from pathlib import Path

spec = importlib.util.spec_from_file_location('bps', Path(__file__).resolve().parents[1]/'tools/apply_bps.py')
bps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bps)


def number(n):
    out = bytearray()
    while True:
        byte = n & 127
        n >>= 7
        if not n:
            out.append(byte | 128)
            return bytes(out)
        out.append(byte)
        n -= 1


def patch(source, target, commands):
    body = b'BPS1' + number(len(source)) + number(len(target)) + number(0) + commands
    body += struct.pack('<II', zlib.crc32(source), zlib.crc32(target))
    return body + struct.pack('<I', zlib.crc32(body))


class BpsTests(unittest.TestCase):
    def test_all_actions_and_overlapping_target_copy(self):
        source, target = b'abcdef', b'abefXYXYXY'
        commands = number(4) + number(6) + number(8) + number(5) + b'XY' + number(15) + number(8)
        self.assertEqual(bps.apply(source, patch(source, target, commands)), target)

    def test_source_relative_negative_delta(self):
        source, target = b'abcdef', b'efab'
        commands = number(6) + number(8) + number(6) + number(13)
        self.assertEqual(bps.apply(source, patch(source, target, commands)), target)

    def test_wrong_base(self):
        with self.assertRaisesRegex(ValueError, 'Source ROM CRC'):
            bps.apply(b'wrong!', patch(b'abcdef', b'abcdef', number(20)))

    def test_corrupt_patch(self):
        p = bytearray(patch(b'abc', b'abc', number(8)))
        p[4] ^= 1
        with self.assertRaisesRegex(ValueError, 'Patch CRC'):
            bps.apply(b'abc', bytes(p))

    def test_wrong_output_crc(self):
        with self.assertRaisesRegex(ValueError, 'Target ROM CRC'):
            bps.apply(b'abc', patch(b'abc', b'xyz', number(8)))

    def test_invalid_backreference(self):
        with self.assertRaisesRegex(ValueError, 'target copy overflow'):
            bps.apply(b'abc', patch(b'abc', b'aaa', number(11) + number(0)))

    def test_output_overflow(self):
        with self.assertRaisesRegex(ValueError, 'output overflow'):
            bps.apply(b'abc', patch(b'abc', b'a', number(8)))

    def test_large_varint(self):
        source = b'x' * 20000
        self.assertEqual(bps.apply(source, patch(source, source, number((len(source)-1)*4))), source)


if __name__ == '__main__':
    unittest.main()
