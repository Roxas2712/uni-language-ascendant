import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_authored as A

class AuthoredTests(unittest.TestCase):
    def test_controls_are_not_lost_or_changed(self):
        original=[{'t':'text','s':'Original'},{'t':'tag','name':'PLAYER'},{'t':'eos'}]
        for target in [[{'t':'text','s':'Texto'},{'t':'eos'}],
                       [{'t':'tag','name':'RIVAL'},{'t':'eos'}]]:
            with self.assertRaisesRegex(AssertionError,'Control operands'):
                A.build({'x':original},{'x':target},None,None)
    def test_layout_may_change_but_hash_uses_original(self):
        original=[{'t':'text','s':'Original'},{'t':'eos'}]
        target=[{'t':'text','s':'Texto'},{'t':'nl'},{'t':'text','s':'novo'},{'t':'eos'}]
        with patch.object(A,'fingerprints',return_value={'x':'abc'}) as fingerprint:
            out=A.build({'x':original},{'x':target},None,None)
        fingerprint.assert_called_once_with({'x':original},None,None)
        self.assertEqual(out['x'],{'sourceSha256':'abc','target':target})
    def test_address_alias_gets_the_same_correction(self):
        ir=[{'t':'text','s':'Original'},{'t':'eos'}]
        target=[{'t':'text','s':'Corrigido'},{'t':'eos'}]
        with patch.object(A,'fingerprints',return_value={'symbol':'one','g3:08123456':'two'}):
            out=A.build({'symbol':ir,'g3:08123456':ir},{'symbol':target},None,None)
        self.assertEqual(out['g3:08123456']['target'],target)
        self.assertEqual(out['g3:08123456']['sourceSha256'],'two')

    def test_incomplete_and_missing_entries_rejected(self):
        with self.assertRaisesRegex(AssertionError,'Missing EOS'):
            A.build({'x':[]},{'x':[{'t':'text','s':'x'}]},None,None)
        with self.assertRaisesRegex(AssertionError,'Missing base key'):
            A.build({},{'x':[{'t':'eos'}]},None,None)

if __name__=='__main__':unittest.main()
