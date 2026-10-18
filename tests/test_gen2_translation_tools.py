import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from gen2_ptbr_text import decode
from gen2_engine_strings import literal,keys_in_source,bind_rom_strings
from gb_lz import decompress
from lua_literal import lua

class Gen2TextTests(unittest.TestCase):
 def test_positional_ram_substitutions_preserve_order(self):
  rom=bytes([0,0x80,1,0x73,0xd0,0,0x81,1,0x86,0xd0,0x58])
  recipe,sig,text=decode(rom,0,0,{0x80:'A',0x81:'B'})
  self.assertEqual(sig,[('ram','73d0'),('ram','86d0')])
  self.assertEqual(text,'A{STRBUF}B{STRBUF}{PROMPT}')
  self.assertEqual(recipe['parts'][0],{'off':1,'size':1})
 def test_far_cycle_unknown_glyph_and_truncation_are_not_success(self):
  with self.assertRaisesRegex(ValueError,'cycle'):decode(bytes([0x16,0,0,0]),0,0,{})
  with self.assertRaisesRegex(ValueError,'Undefined glyph'):decode(bytes([0,0x80,0x57]),0,0,{})
  with self.assertRaises(IndexError):decode(bytes([0,0x80]),0,0,{0x80:'A'})
 def test_crystal_player_macro_is_distinct_from_buffer_command(self):
  _,sig,text=decode(bytes([0,0x14,0x58]),0,0,{},True)
  self.assertEqual(sig,[('slot','{PLAYER}')]);self.assertEqual(text,'{PLAYER}{PROMPT}')
  _,sig,text=decode(bytes([0x14,2,0x50]),0,0,{},True)
  self.assertEqual(sig,[('buffer',2)]);self.assertEqual(text,'{STRBUF}')
 def test_ui_harvest_decodes_decimal_utf8_and_combines_literals(self):
  self.assertEqual(literal(r'"PARKBALL\195\151%02d"'),'PARKBALL×%02d')
  code='-- Strings("fake")\nStrings.source("First\\n" .. -- comment\n "second")\nStrings("%s", name)\nStrings("not a key" .. variable)'
  self.assertEqual(list(keys_in_source(code)),['First\nsecond','%s'])
 def test_only_unambiguous_exact_rom_text_is_reused(self):
  review=[dict(key='a',original='Hi!{DONE}',translated='Oi!{DONE}'),dict(key='b',original='Who?{DONE}',translated='Quem?{DONE}'),dict(key='c',original='Who?{DONE}',translated='Onde?{DONE}')]
  recipes={'a':{'parts':[{'off':4,'size':3},{'token':'{DONE}'}]}}
  out,missing=bind_rom_strings(['Hi!','Who?','Hello'],review,recipes,{})
  self.assertEqual(out,{'Hi!':{'parts':[{'off':4,'size':3}]}});self.assertEqual(missing,['Who?','Hello'])
 def test_lua_control_escape_does_not_turn_pause_into_literal_u0001(self):
  self.assertEqual(lua('a\x01b\vb'),'"a\\001b\\011b"')

class Lz3Tests(unittest.TestCase):
 def test_literals_and_overlapping_repeat(self):
  self.assertEqual(decompress(bytes([1,65,66,0x83,0x81,255])),(b'ABABAB',6))
 def test_bad_back_reference_truncation_and_output_limit(self):
  for data in [bytes([0x80,0x80,255]),bytes([2,65]),bytes([0xe0])]:
   with self.assertRaises(ValueError):decompress(data)
  with self.assertRaisesRegex(ValueError,'limit'):decompress(bytes([0x3f,65,255]),limit=8)

class VocabularyTests(unittest.TestCase):
 def test_catalogs_have_complete_ids_and_preserve_format_slots(self):
  root=Path(__file__).resolve().parents[1]/'translations/pt-BR'
  moves=json.loads((root/'move-names.json').read_text())['moves'];abilities=json.loads((root/'ability-names.json').read_text())
  self.assertEqual(set(moves),{str(i) for i in range(1,355)});self.assertEqual(set(abilities),{str(i) for i in range(78)})
  import re
  for path in [root/'gen1-ui.json',root/'gen2-ui.json']:
   for source,target in json.loads(path.read_text()).items():
    pattern=r'%[-+ #0]*\d*\.?\d*[a-zA-Z]|\{[^}]*\}'
    self.assertEqual(re.findall(pattern,source),re.findall(pattern,target),source)
 def test_authored_descriptions_fit_real_two_line_boxes(self):
  root=Path(__file__).resolve().parents[1]/'translations/pt-BR'
  for name in ['gen2-item-descriptions.json','gen2-move-descriptions.json']:
   for key,row in json.loads((root/name).read_text()).items():
    lines=row['text'].split('\n');self.assertLessEqual(len(lines),2,key)
    for line in lines:self.assertLessEqual(len(line),18,key)
    self.assertEqual(len(row['source_sha256']),64,key)
 def test_authored_dex_pages_fit_without_discarding_lines(self):
  root=Path(__file__).resolve().parents[1]/'translations/pt-BR/gen2-dex'
  for game in ['gold','silver']:
   for key,row in json.loads((root/(game+'.json')).read_text()).items():
    self.assertLessEqual(len(row['kind']),11,key)
    for field in ['text','text2']:
     lines=row[field].split('<NEXT>');self.assertLessEqual(len(lines),3,key)
     for line in lines:self.assertLessEqual(len(line),18,key)
    self.assertEqual(len(row['source_sha256']),64,key)
if __name__=='__main__':unittest.main()
