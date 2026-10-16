import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_plain_supplement import plain_ir,template_ir,reuse_exact
from build_authored import controls


class PlainSupplementTests(unittest.TestCase):
    def test_explicit_menu_newline_is_not_collapsed(self):
        self.assertIn({'t':'nl'},plain_ir([{'t':'eos'}],'SIM\nNÃO'))
        self.assertIn({'t':'nl'},template_ir([{'t':'ext','cmd':'color','args':[1]},{'t':'eos'}],'{0}SIM\nNÃO'))

    def test_reuse_requires_identical_controls_and_respects_edition_corrections(self):
        original=[{'t':'strvar','n':1},{'t':'text','s':' has arrived.'},{'t':'eos'}]
        other=[{'t':'strvar','n':2},{'t':'text','s':' has arrived.'},{'t':'eos'}]
        reference={'old':original}
        source={'new':original,'alias':original,'different_operand':other}
        target=template_ir(original,'{0} chegou.')
        self.assertEqual(set(reuse_exact(source,reference,{'old':target})),{'new','alias'})
        override=template_ir(original,'{0} já chegou.')
        result=reuse_exact(source,reference,{'old':target},{'new':override})
        self.assertEqual(result,{'new':override,'alias':override})

    def test_template_preserves_operands_and_layout(self):
        source=[{'t':'player'},{'t':'strvar','n':1},{'t':'eos'}]
        result=template_ir(source,'Olá, {0}! Você ganhou {1}!')
        self.assertEqual(controls(result),controls(source))
        for invalid in ('Olá!','{1} {0}','{0} {0}','{0} {1} {2}'):
            with self.assertRaises(ValueError):template_ir(source,invalid)

    def test_rejects_lost_player_or_control(self):
        for control in ({'t':'player'},{'t':'strvar','n':1},{'t':'ext','cmd':'pause','args':[5]}):
            with self.assertRaises(ValueError):
                plain_ir([control,{'t':'eos'}],'Olá!')

    def test_scroll_and_paragraph_keep_dialogue_readable(self):
        result=plain_ir([{'t':'eos'}], 'Uma frase bastante longa para ocupar várias linhas na caixa de diálogo.\n\nAté logo!')
        self.assertIn({'t':'scroll'},result)
        self.assertIn({'t':'para'},result)
        self.assertEqual(result[-1],{'t':'eos'})
        self.assertTrue(all(len(s['s'])<=26 for s in result if s['t']=='text'))

    def test_preserves_fragment_separator(self):
        self.assertEqual(plain_ir([{'t':'eos'}],' não tem FRUTAS.')[0]['s'],' não tem FRUTAS.')

    def test_rejects_blank_or_embedded_control(self):
        for text in ('','   ','{PLAYER} chegou.'):
            with self.assertRaises(ValueError):plain_ir([{'t':'eos'}],text)


if __name__=='__main__':unittest.main()
