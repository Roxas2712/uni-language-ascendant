"""Verify cartridge text-dictionary dispatch and localize macro expansions.

Each CP token / JP Z handler / LD DE name chain is proved unique in ROM bank 0.
Only the small charmap lexemes (PC, MT/CT, ENTREN./DRESSEUR/ALLEN., ROCKET) are
stored as decoder metadata; full cartridge text remains address-based.
"""
import hashlib,json,re
from pathlib import Path
from build_european_gb import ROOT,lua
from build_gb_profiles import export
PAIRS=[('red','es'),('yellow','es'),('gold','es'),('gold','fr'),('gold','it'),('silver','es'),('silver','fr'),('crystal','es'),('crystal','it')]
def run(game,lang):
 folder=ROOT/f'mod/gb/profiles/{game}_{lang}'
 profile=export(folder/'profile.lua')
 row=next(x for x in json.loads((ROOT/'build/european-inputs.json').read_text()) if x.get('game')==game and x.get('language')==lang)
 rom=Path(row['file']).read_bytes();assert hashlib.sha1(rom).hexdigest()==profile['sha1']
 proof={}
 expected={0x5b:'PC',0x5c:'CT' if lang=='fr' else 'MT',0x5d:{'es':'ENTREN.','fr':'DRESSEUR','it':'ALLEN.'}[lang],0x5e:'ROCKET'}
 for code,want in expected.items():
  hits=[]
  for match in re.finditer(re.escape(bytes([0xfe,code,0xca])),rom[:16384]):
   handler=int.from_bytes(rom[match.start()+3:match.start()+5],'little')
   if not 0<=handler<16384:continue
   at=handler+(rom[handler]==0xd5)
   if rom[at]!=0x11:continue
   ptr=int.from_bytes(rom[at+1:at+3],'little')
   if not 0<=ptr<16384:continue
   end=rom.find(b'\x50',ptr,ptr+20)
   if end<=ptr or not all(c>=0x80 or c in (0x54,0x7f)for c in rom[ptr:end]):continue
   value=''.join(profile['charmap'][str(c)] for c in rom[ptr:end])
   hits.append({'dispatch':match.start(),'handler':handler,'off':ptr,'size':end-ptr,'value':value})
  assert len(hits)==1 and hits[0]['value']==want,(game,lang,code,hits)
  profile['charmap'][str(code)]=want;proof[str(code)]=hits[0]
 (folder/'profile.lua').write_text('return '+lua(profile)+'\n')
 (ROOT/f'build/{game}-{lang}-text-macros.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
 print('EU_NATIVE_TEXT_MACROS',game,lang,expected[0x5c],expected[0x5d],flush=True)
if __name__=='__main__':
 for pair in PAIRS:run(*pair)
