import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from gen1_ptbr_dialogue import recipe,offset,charmap
import tempfile


class Gen1DialogueTests(unittest.TestCase):
    def test_literal_recipe_has_no_embedded_source_text(self):
        row=recipe(bytes([0,0x80,0x81,0x57]),(0,0),[],{},{0x80:'A',0x81:'B'})
        self.assertEqual(row,{'parts':[{'off':1,'size':2},{'token':'{DONE}'}]})

    def test_dynamic_ram_identity_cannot_be_guessed(self):
        rom=bytes([1,0x23,0xc1,0x50])
        dynamic=[(1,'{RAM:wNameBuffer}')]
        result=recipe(rom,(0,0),dynamic,{'wNameBuffer':(0,0xc123)},{})
        self.assertEqual(result['parts'][0],{'token':'{RAM:wNameBuffer}'})
        with self.assertRaises(ValueError):recipe(rom,(0,0),dynamic,{'wNameBuffer':(0,0xc124)},{})

    def test_far_cycle_and_unknown_glyph_fail(self):
        with self.assertRaises(ValueError):recipe(bytes([0x17,0,0,0]),(0,0),[],{},{})
        with self.assertRaises(ValueError):recipe(bytes([0,0x80,0x57]),(0,0),[],{},{})
        with self.assertRaises(ValueError):offset(2,0xc000)

    def test_latin_alphabet_is_not_overwritten_by_unused_kana_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'charmap.asm'
            path.write_text('charmap "A", $80\ncharmap "B", $81\ncharmap "ア", $80\ncharmap "イ", $81\n')
            self.assertEqual((charmap(path)[0x80],charmap(path)[0x81]),('A','B'))

    def test_reordered_dynamic_values_cannot_swap_engine_positional_arguments(self):
        rom=bytes([1,0x24,0xc1,1,0x23,0xc1,0x50])
        dynamic=[(1,'{RAM:name}'),(1,'{RAM:stat}')]
        syms={'name':(0,0xc123),'stat':(0,0xc124)}
        with self.assertRaisesRegex(ValueError,'Changed dynamic operand order'):
            recipe(rom,(0,0),dynamic,syms,{})
        with self.assertRaises(ValueError):
            recipe(bytes([1,0x23,0xc1,1,0x23,0xc1,0x50]),(0,0),dynamic,syms,{})

if __name__=='__main__':unittest.main()
