import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from frlg_gender import extract,BASE,PREFIX,SUFFIX

class GenderDecoderTests(unittest.TestCase):
 def fixture(self):
  rom=bytearray(4096);dispatch=0;table=64
  rom[:14]=bytes.fromhex('00b5202808d80349800040180068');rom[18:20]=bytes.fromhex('02e0');struct.pack_into('<I',rom,20,BASE+table)
  for code in range(14,33):
   at=256+(code-14)*36;struct.pack_into('<I',rom,table+code*4,BASE+at+1)
   rom[at:at+16]=PREFIX;struct.pack_into('<I',rom,at+16,0x0300500c)
   rom[at+24:at+32]=SUFFIX
   struct.pack_into('<I',rom,at+20,BASE+2000+code*4);struct.pack_into('<I',rom,at+32,BASE+2002+code*4)
   rom[2000+code*4:2004+code*4]=bytes([0xd5,255,0xe3,255])
  return rom
 def test_follows_verified_gender_branch_with_female_and_male_preserved(self):
  rows=extract(self.fixture(),0);self.assertEqual(set(rows),set(range(14,33)))
  for code,row in rows.items():self.assertEqual(row,{'female':2000+code*4,'male':2002+code*4})
 def test_rejects_changed_gender_field_or_branch(self):
  for rel in [6,8,10,12,24]:
   rom=self.fixture();rom[256+rel]^=1
   with self.assertRaises(AssertionError):extract(rom,0)
 def test_rejects_non_thumb_out_of_bounds_or_dynamic_choice(self):
  rom=self.fixture();struct.pack_into('<I',rom,64+14*4,BASE+256)
  with self.assertRaises(AssertionError):extract(rom,0)
  rom=self.fixture();struct.pack_into('<I',rom,256+20,BASE+9999)
  with self.assertRaises(AssertionError):extract(rom,0)
  rom=self.fixture();rom[2000+14*4]=0xfd
  with self.assertRaises(AssertionError):extract(rom,0)
if __name__=='__main__':unittest.main()
