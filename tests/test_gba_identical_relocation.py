import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from gba_identical_relocation import unique_copy


class IdenticalDataTests(unittest.TestCase):
    def test_complete_unique_object_can_move(self):
        block = bytes(range(32))
        self.assertEqual(unique_copy(b'xxx' + block, b'yyyzz' + block, 3, 32), 5)

    def test_duplicate_source_or_target_is_not_identity(self):
        block = bytes(range(32))
        self.assertIsNone(unique_copy(block * 2, block, 0, 32))
        self.assertIsNone(unique_copy(block, block * 2, 0, 32))

    def test_changed_last_byte_is_rejected(self):
        block = bytes(range(32))
        self.assertIsNone(unique_copy(block, block[:-1] + b'X', 0, 32))

    def test_padding_and_truncated_object_are_rejected(self):
        self.assertIsNone(unique_copy(b'0' * 32, b'0' * 32, 0, 32))
        self.assertIsNone(unique_copy(bytes(range(32)), bytes(range(32)), 0, 40))


if __name__ == '__main__':
    unittest.main()
