"""Rebase recorded stock extractor reads using verified FRLG symbol identity.

Unknown reads fail the build; unchanged unique complete binary objects can
supply additional witnesses. No source image or ROM bytes are emitted.
"""
import argparse,bisect,collections,hashlib,json,subprocess,re
from pathlib import Path
from build_profiles import elf_symbols
from lua_literal import lua

def run(a):
 src=a.base.read_bytes();dst=a.target.read_bytes();audit=json.loads((a.evidence/'texts.json').read_text());maps={int(k):v for k,v in audit['mapped'].items()}
 assert hashlib.sha1(dst).hexdigest()==audit['target_sha1']
 assert hashlib.sha1(src).hexdigest() in ('41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc','574fa542ffebb14be69902d1d36f1ec0a4afd71e')
 s0=elf_symbols(a.elf,'/opt/homebrew/bin/arm-none-eabi-readelf');rows=json.loads((a.evidence/'symbols.json').read_text());s1=collections.defaultdict(set)
 for r in rows:
  s1[r['name']].add(r['off'])
  if r['object']:s1[r['object']+':'+r['name']].add(r['off'])
 by_off=collections.defaultdict(list)
 for name,(off,size) in s0.items():by_off[off].append((name,size))
 starts=sorted(by_off);resolved={};missing={};proof=[]
 def relocate(off):
  if not isinstance(off,int) or off<=0x10000 or off>=len(src):return off
  if off in resolved:return resolved[off]
  index=bisect.bisect_right(starts,off)-1;origin=starts[index];aliases=by_off[origin];delta=off-origin
  candidates=set();names=[]
  for name,size in aliases:
   if delta>=max(size,1):continue
   names.append(name)
   if len(s1[name])==1 and next(iter(s1[name])) in maps:
    candidates.add(maps[next(iter(s1[name]))]+delta)
  if not candidates:
   for name,size in aliases:
    if size<3 or delta>=size:continue
    block=src[origin:origin+size];hit=dst.find(block)
    pure=re.search(r'Gfx|GFX|Tiles|Tilemap|_Pal$|Pal$|Palette$|YDelta_',name) is not None
    if hit>=0 and (pure or dst.find(block,hit+1)<0):
     candidates.add(hit+delta);proof.append(['unique-complete-object',name,origin,hit,size])
  if len(candidates)!=1:
   missing[hex(off)]=dict(aliases=names,delta=delta,candidates=sorted(candidates));return off
  value=next(iter(candidates));resolved[off]=value;return value
 def move(value):
  if isinstance(value,dict):return {int(k) if k.isdigit() else k:move(v) for k,v in value.items()}
  if isinstance(value,list):return [move(v) for v in value]
  return relocate(value)
 def export(path):return json.loads(subprocess.check_output([a.luajit,str(a.engine/'tools/lua_to_json.lua'),str(path)]))
 metadata=export(a.assets);metadata['symbols']=metadata['symbols'] or {}
 # The extractor explicitly selects only this edition's staff heading. Some
 # patches remove the other edition's unused text; omit that unread field.
 unused='staff_firered' if src[0xac:0xb0]==b'BPGE' else 'staff_leafgreen'
 if 'CREDITS' in metadata['fields']:metadata['fields']['CREDITS'].pop(unused,None)
 metadata['fields']=move(metadata['fields'])
 for method,values in metadata['calls'].items():
  if method in ['address','sym']:metadata['calls'][method]={k:[relocate(v[0])] for k,v in values.items()}
 for method,values in metadata['symbols'].items():
  if method=='off':metadata['symbols'][method]={k:[relocate(v[0])] for k,v in values.items()}
  elif method in ['namesAt','at','nameAt']:metadata['symbols'][method]={str(relocate(int(k))):v for k,v in values.items()}
 struct=json.loads((a.evidence/'structures.json').read_text())['fields'];height=struct['POKEDEX_HEIGHT_OFFSET']
 metadata['fields']['ULA_POKEDEX_ENTRY']=dict(size=struct['POKEDEX_ENTRY_SIZE'],category=0,categoryLen=struct['POKEDEX_NAME_LENGTH'],height=height,weight=height+2,desc=height+4,desc2=height+8,pokemonScale=height+14,pokemonOffset=height+16,trainerScale=height+18,trainerOffset=height+20)
 # These are verified ROM records, not the stock field-width defaults.
 for key in ['POKEDEX_ENTRY_SIZE','SPECIES_NAME_LENGTH','MOVE_NAME_LENGTH','ABILITY_NAME_LENGTH','ITEM_STRIDE','ITEM_NAME_LENGTH']:
  if key in metadata['fields']:metadata['fields'][key]=struct[key]
 world=move(export(a.world))
 a.output.mkdir(exist_ok=True,parents=True)
 report=dict(missing=missing,proof=proof,resolved=resolved)
 (a.output/'asset-report.json').write_text(json.dumps(report,indent=2)+'\n')
 if missing:
  print('UNRESOLVED_ASSETS',len(missing));print(json.dumps(missing,indent=2));return
 (a.output/'assets.lua').write_text('return '+lua(metadata)+'\n')
 (a.output/'world.lua').write_text('return '+lua(world)+'\n')
 print('FRLG_ASSETS_READY',len(resolved))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for key in ['base','target','elf','evidence','assets','world','engine','output']:p.add_argument('--'+key,type=Path,required=True)
 p.add_argument('--luajit',required=True);run(p.parse_args())
