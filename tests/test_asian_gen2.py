"""Binary/control-flow regression tests; these are not dialogue evidence."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from asian_gen2 import TextReader,japanese_charmap
class JapaneseCharmapScopes(unittest.TestCase):
 def test_mobile_ascii_does_not_replace_voiced_kana(self):
  import tempfile
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'charmap.asm'
   p.write_text('charmap "ゴ", $09\ncharmap "ザ", $0a\ncharmap "ゼ", $0d\npushc\nnewcharmap ascii\ncharmap "\\\\t", $09\ncharmap "\\\\n", $0a\ncharmap "\\\\r", $0d\npopc\n')
   cm=japanese_charmap(p)
  self.assertEqual([cm[str(x)]for x in (9,10,13)],['ゴ','ザ','ゼ'])
  self.assertEqual(TextReader(bytes([0,9,10,13,0x57]),'ja',cm).text(0)[1],'ゴザゼ{DONE}')
class KoreanBoundaries(unittest.TestCase):
 def test_control_valued_second_bytes_are_characters(self):
  cm={'1:80':'가','1:94':'나','1:95':'다','89':'\n'}
  r=TextReader(bytes([0,1,80,89,1,94,1,95,94]),'ko',cm)
  recipe,value=r.text(0)
  self.assertEqual(value,'가\n나다{DONE}')
  self.assertEqual(recipe['parts'][0],{'off':1,'size':7})
 def test_truncated_pair_rejected_even_in_fixed_cell(self):
  with self.assertRaisesRegex(AssertionError,'Truncated'):TextReader(b'\x01','ko',{}).span(0,1,fixed=True)
 def test_missing_mapping_is_not_a_blank(self):
  with self.assertRaisesRegex(AssertionError,'Unknown'):TextReader(b'\x01\x01\x50','ko',{}).span(0)
 def test_fixed_name_can_fill_entire_cell(self):
  self.assertEqual(TextReader(b'\x01\x50','ko',{'1:80':'가'}).span(0,2,fixed=True)[1],'가')
 def test_dex_tokens_only_at_character_boundaries(self):
  r=TextReader(bytes([1,89,89,1,89,80]),'ko',{'1:89':'가','89':'\n'})
  recipe,text,_,_=r.span(0,tokens={89:'<NEXT>'})
  self.assertEqual(text,'가<NEXT>가')
  self.assertEqual(recipe['parts'],[{'off':0,'size':2},{'token':'<NEXT>'},{'off':3,'size':2}])
 def test_one_byte_terminator_unchanged(self):
  r=TextReader(b'\x00\x80\x57','ja',{'128':'ア'})
  self.assertEqual(r.text(0)[1],'ア{DONE}')
class RegionalScriptBoundaries(unittest.TestCase):
 def mapper(self,source,target,target_ops=None):
  from relocate_gen2 import Mapper
  left=bytearray(32768);right=bytearray(32768);left[16384:16384+len(source)]=source;right[16384:16384+len(target)]=target
  ops={'1':{'name':'writetext','size':2},'2':{'name':'end','size':0},'3':{'name':'setval','size':1},'terminators':['end']}
  mapper=Mapper(left,right,{'romSha1':'test'},ops,target_opcodes=target_ops);mapper.pointer((1,0x4000),(1,0x4000));mapper.scripts_walk();return mapper
 def test_default_rejects_shifted_opcode(self):
  self.assertTrue(self.mapper(bytes([1,0,0x41,2]),bytes([7,0,0x42,2])).failures)
 def test_explicit_opcode_map_preserves_text_pointer(self):
  m=self.mapper(bytes([1,0,0x41,2]),bytes([7,0,0x42,8]),{7:'writetext',8:'end'})
  self.assertFalse(m.failures);self.assertEqual(m.texts,{'01:4100':[1,0x4200]})
 def test_near_far_text_pair_keeps_native_bank(self):
  m=self.mapper(bytes([1,0,0x41,2]),bytes([7,2,0,0x43,8]),{7:'farwritetext',8:'end'})
  self.assertFalse(m.failures);self.assertEqual(m.texts,{'01:4100':[2,0x4300]})
 def test_different_gameplay_operands_still_rejected(self):
  m=self.mapper(bytes([3,10,2]),bytes([9,11,8]),{9:'setval',8:'end'})
  self.assertTrue(m.failures)


class InlineAsmFragments(unittest.TestCase):
 def test_only_explicit_boundary_can_stop_before_asm(self):
  r=TextReader(bytes([0,128,80,8,201]),'ja',{'128':'ア'})
  with self.assertRaisesRegex(ValueError,'Unsupported text command'):r.text(0)
  self.assertEqual(r.text(0,stop_at=3)[1],'ア')
  with self.assertRaisesRegex(AssertionError,'crossed'):r.text(0,stop_at=2)
 def test_fields_keep_identity_before_reviewed_asm(self):
  from asian_text_arguments import fields
  r=TextReader(bytes([1,0,208,8]),'ja',{})
  self.assertEqual(fields(r,0,3),[('STRBUF',1,0xd000)])
  with self.assertRaises(ValueError):fields(r,0)
class NativeArgumentIdentity(unittest.TestCase):
 def test_unrelated_banked_ram_alias_does_not_hide_sentence_roles(self):
  from asian_text_arguments import argument_orders
  src=TextReader(bytes([9,0,208,0,1,1,208,9,2,208,0,80]),'en',{})
  native=TextReader(bytes([1,3,208,9,4,208,0,9,5,208,0,80]),'ko',{})
  source_sy={'sale':(0,0),'item':(0,0xd001),'quantity':(1,0xd000),'money':(0,0xd002),'mail':(7,0xc000)}
  native_sy={'item':(1,0xd003),'quantity':(1,0xd004),'money':(0,0xd005),'mail':(7,0xd003)}
  self.assertEqual(argument_orders(src,source_sy,native,{'sale':0},native_symbols=native_sy),{'sale':{'value':[2,1,3]}})



class AuthoredUiFields(unittest.TestCase):
 def test_format_arguments_and_script_tokens_are_preserved(self):
  import re,collections
  from asian_engine_ui import entries,unescape
  from asian_engine_extra import ROWS as extra
  from asian_engine_fields import ROWS as fields
  rows=list(entries())+[line.split('|')for line in (extra+'\n'+fields).splitlines()if line]
  fmt=lambda t:collections.Counter(re.findall(r'%(?!%)[-+ #0-9.]*([a-zA-Z])',t))
  args=lambda t:collections.Counter(re.findall(r'\{(?:PLAYER|RIVAL|MOM|STRBUF|NUM|USER|TARGET)\}',t))
  for row in rows:
   self.assertEqual(len(row),3,row)
   source=unescape(row[0])
   for value in row[1:]:
    self.assertEqual(fmt(source),fmt(unescape(value)),row[0])
    self.assertEqual(args(source),args(unescape(value)),row[0])

if __name__=='__main__':unittest.main()
