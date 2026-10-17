import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_language_remainders import audit


def text(s):return [{'t':'text','s':s},{'t':'eos'}]


class RemainderAuditTests(unittest.TestCase):
    def test_short_non_ascii_and_aliases_are_not_silently_skipped(self):
        base={'short':text('YES'),'unicode':text('POKéMON cannot enter.'),'alias':text('POKéMON cannot enter.'),'name':text('PIKACHU')}
        result=audit(base,base,{})
        self.assertEqual(result['unchanged_unique_candidates'],3)
        self.assertEqual(result['unchanged_keys'],4)
        self.assertFalse(result['completeness_proven'])

    def test_effective_translation_and_missing_input(self):
        base={'translated':text('Wait.'),'missing':text('Ready?')}
        result=audit(base,{}, {'translated':text('Espere.')})
        self.assertEqual(result['unchanged_unique_candidates'],0)
        self.assertEqual(result['missing_decoded_keys'],['missing'])

    def test_layout_changes_do_not_hide_english(self):
        base={'a':[{'t':'text','s':'Please'},{'t':'nl'},{'t':'text','s':'wait.'},{'t':'eos'}]}
        self.assertEqual(audit(base,{'a':text('Please wait.')},{})['unchanged_unique_candidates'],1)

if __name__=='__main__':unittest.main()
