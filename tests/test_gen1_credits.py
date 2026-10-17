"""Parser fixtures test data safety, not translation quality or gameplay."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from gen1_ptbr_credits import credits

class NativeCreditsTests(unittest.TestCase):
    def fixture(self, text=b'\x80', command=0xff):
        rom=bytearray(1024)
        rom[32:34]=(128).to_bytes(2,'little')
        rom[64:67]=bytes([0,command,0xfa])
        rom[128]=0xf8 # column 9 - 8 = 1
        rom[129:130+len(text)]=text+b'\x50'
        rom[512:519]=b'\x60\x7f\x62\x50\x61\x7f\x63'
        syms={'CreditsTextPointers':(0,32),'CreditsOrder':(0,64),'TheEndTextString':(0,512)}
        manifest={'screens':[{'fade':True,'mon':'PIKACHU'}]}
        return rom,syms,{0x80:'A',0x81:'B'},manifest

    def test_native_layout_and_accent_compose_without_copying_text(self):
        args=self.fixture(b'\x80\xea\x4e\x81')
        result=credits(*args)
        screen=dict(result['screens']['array'][0]['table'])
        lines=screen['lines']['array']
        self.assertEqual(dict(lines[0]['table'])['text'],{'parts':[{'token':'Ã'}]})
        self.assertEqual(dict(lines[1]['table'])['text'],{'parts':[{'off':132,'size':1}]})
        self.assertEqual(result['pattern'],{'value':[0,-1,1]})
        self.assertEqual(screen['mon'],{'value':'PIKACHU'})

    def test_changed_timing_cannot_be_silently_reused(self):
        with self.assertRaises(AssertionError): credits(*self.fixture(command=0xfc))

    def test_offscreen_and_too_many_rows_rejected(self):
        with self.assertRaises(AssertionError): credits(*self.fixture(b'\x80'*20))
        with self.assertRaises(AssertionError): credits(*self.fixture(b'\x80\x4e'*4+b'\x80'))

    def test_invalid_end_tile_pair_rejected(self):
        args=self.fixture();args[0][516]=0x62
        with self.assertRaises(AssertionError):credits(*args)

    def test_unterminated_page_rejected(self):
        args=self.fixture();args[0][65]=0xfa
        with self.assertRaises(AssertionError):credits(*args)

if __name__=='__main__':unittest.main()
