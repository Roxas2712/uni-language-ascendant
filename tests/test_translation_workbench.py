import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('workbench',Path(__file__).resolve().parents[1]/'tools/translation_workbench.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)

class WorkbenchTests(unittest.TestCase):
    def test_reuse_never_approves_automatically(self):
        rows=w.prepare({'a':'Hello {PLAYER}','alias':'Hello {PLAYER}'},[({'old':'Hello {PLAYER}'},{'old':'Olá {PLAYER}'})])
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['keys'],['a','alias'])
        self.assertEqual(rows[0]['candidate'],'Olá {PLAYER}')
        with self.assertRaisesRegex(ValueError,'not approved'):w.validate(rows[0])

    def test_conflicting_candidates_are_left_untranslated(self):
        rows=w.prepare({'a':'Hello'},[({'a':'Hello','b':'Hello'},{'a':'Olá','b':'Oi'})])
        self.assertIsNone(rows[0]['candidate'])

    def test_lost_placeholder_is_rejected(self):
        row=w.prepare({'a':[{'t':'text','s':'Hello '},{'t':'player'},{'t':'eos'}]})[0]
        row.update(status='approved',target=[{'t':'text','s':'Olá'},{'t':'eos'}])
        with self.assertRaisesRegex(ValueError,'control tokens'):w.validate(row)

    def test_changed_source_requires_new_review(self):
        row=w.prepare({'a':'Hello {PLAYER}'})[0]
        row.update(status='approved',target='Olá {PLAYER}',source='Goodbye {PLAYER}')
        with self.assertRaisesRegex(ValueError,'Source changed'):w.validate(row)

    def test_missing_terminator_is_rejected(self):
        row=w.prepare({'a':[{'t':'text','s':'Hello'},{'t':'eos'}]})[0]
        row.update(status='approved',target=[{'t':'text','s':'Olá'}])
        with self.assertRaisesRegex(ValueError,'EOS'):w.validate(row)

if __name__=='__main__':unittest.main()
