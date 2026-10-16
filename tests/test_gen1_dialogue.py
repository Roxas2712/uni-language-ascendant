import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from gen1_ptbr_dialogue import recipe,offset


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

if __name__=='__main__':unittest.main()
