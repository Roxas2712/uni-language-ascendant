"""Validate and normalize the offline EU interface translation catalog."""
import json,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TOKENS=re.compile(r'\{[^{}]*\}|<[^>]*>|%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[a-zA-Z%]')

def normalize(text,lang):
 text=text.replace('\xa0',' ').replace('’',"'").replace('‘',"'").replace('“','"').replace('”','"').replace('…','...').replace('–','-').replace('—','-')
 if lang=='fr':
  text=text.replace('Œ','OE').replace('œ','oe')
  for accented in 'ÀÁÂÃÈÉÊËÌÍÎÏÒÓÔÕÙÚÛŸÇ':text=text.replace(accented,unicodedata.normalize('NFD',accented)[0])
 return text

def run(draft=None):
 p=ROOT/'translations/european/gb-ui.json'
 data=json.loads(Path(draft).read_text()) if draft else json.loads(p.read_text())
 for line in (ROOT/'translations/european/gb-ui-overrides.tsv').read_text().splitlines():
  if not line or line.startswith('#'):continue
  cells=line.split('|');assert len(cells)==4,line
  key,*values=[s.replace('\\n','\n').replace('\\f','\f').replace('\\v','\v').replace('\\001','\1') for s in cells]
  data[key]=values
 for key,values in data.items():
  assert len(values)==3,key
  for i,lang in enumerate(('es','fr','it')):
   text=normalize(values[i],lang)
   left=len(key)-len(key.lstrip(' '));right=len(key)-len(key.rstrip(' '))
   if left:text=' '*left+text.lstrip(' ')
   if right:text=text.rstrip(' ')+' '*right
   # Drafts can translate the NEXT markup as a word. Treat markup
   # identity as a build invariant, including the two font ligature tokens.
   text=text.replace('<SIGUIENTE>','<NEXT>')
   assert sorted(TOKENS.findall(key))==sorted(TOKENS.findall(text)),(key,lang,text)
   assert text.strip() and 'ZXQ' not in text,(key,lang,text)
   values[i]=text
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print('EU_UI_CATALOG',len(data),'keys x 3 languages; format and control identities valid')
if __name__=='__main__':
 import sys;run(sys.argv[1] if len(sys.argv)>1 else None)
