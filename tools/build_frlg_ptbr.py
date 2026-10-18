"""Build private FRLG language recipes from typed relocation evidence.

This does not enable a public profile. Missing, ambiguous or structurally
unverified strings remain explicit in the report for review and real-game QA.
"""
import argparse,collections,hashlib,json,struct
from pathlib import Path
from build_profiles import elf_symbols
from lua_literal import lua
from frlg_gender import extract as gender_recipes
BASE=0x08000000

def build(a):
 root=Path(__file__).resolve().parents[1];engine=a.engine
 us=a.base.read_bytes();pt=a.target.read_bytes();meta=json.loads(a.metadata.read_text());keys=json.loads(a.texts.read_text())
 audit=json.loads((a.evidence/'texts.json').read_text());structures=json.loads((a.evidence/'structures.json').read_text());maps={int(k):v for k,v in audit['mapped'].items()}
 assert hashlib.sha1(pt).hexdigest()==audit['target_sha1']
 expected={'firered':'41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc','leafgreen':'574fa542ffebb14be69902d1d36f1ec0a4afd71e'}
 assert hashlib.sha1(us).hexdigest()==expected[a.game], 'Unexpected US base revision'
 s0=elf_symbols(a.elf,'/opt/homebrew/bin/arm-none-eabi-readelf')
 rows=json.loads((a.evidence/'symbols.json').read_text());s1=collections.defaultdict(set)
 for r in rows:
  s1[r['name']].add(r['off'])
  if r['object']:s1[r['object']+':'+r['name']].add(r['off'])
 bridge=collections.defaultdict(set)
 for name,(off,size) in s0.items():
  if len(s1[name])==1:bridge[off].update(s1[name])
 def source1(off):
  vals=bridge.get(off,set());assert len(vals)==1,('Revision symbol identity',hex(off),vals)
  return next(iter(vals))
 def target(off):return maps.get(source1(off))
 fields={k:target(v) if isinstance(v,int) and v>0x10000 else v for k,v in meta['fields'].items()}
 fields.update(structures['fields'])
 assert all(v is not None for v in fields.values()),{k:v for k,v in fields.items() if v is None}
 source={k:list(v) for k,v in meta['named'].items() if k in keys};translated={};missing_tables=[]
 def pointer(data,at):
  value=struct.unpack_from('<I',data,at)[0]-BASE;assert 0<=value<len(data),(hex(at),hex(value))
  return value
 for k in keys:
  if k.startswith('g3:'):source[k]=[int(k[3:],16)-BASE,False]
  elif k not in source and k in s0:source[k]=[s0[k][0],False]
 for table in meta['tables']:
  old=table['addr'];new=target(old)
  if new is None:missing_tables.append(table['name'])
  stride=table['stride']
  if table['name']=='gTrainerClassNames':stride=fields['TRAINER_CLASS_NAME_STRIDE']
  elif table['name']=='gTypeNames' and new is not None:
   possible=[]
   for width in range(7,19):
    for i in range(18):
     data=pt[new+i*width:new+(i+1)*width]
     if 255 not in data or any(x not in (0,255) for x in data[data.index(255)+1:]):break
    else:possible.append(width)
   assert len(possible)==1,('Type width',possible);stride=possible[0]
  for i in range(table['count']*table.get('inner',1)):
   if table.get('ids') is not None:
    ids=meta['battleIds'];ix=i+table['ids'];key=ids[str(ix)] if isinstance(ids,dict) else ids[ix-1]
   elif table.get('inner'):key=f"{table['name']}[{i//table['inner']}][{i%table['inner']}]"
   else:key=f"{table['name']}[{i}]"
   if key not in keys:continue
   source[key]=[old+i*table['stride'] if table.get('inline') else pointer(us,old+i*table['stride']),bool(table.get('battle') and not table.get('inline'))]
   if new is not None:translated[key]=[new+i*stride if table.get('inline') else pointer(pt,new+i*stride),source[key][1]]
 for i in range(fields['STD_STRING_COUNT']):
  source[f'stdstring:{i}']=[pointer(us,meta['fields']['STD_STRING_PTRS']+i*4),False]
  translated[f'stdstring:{i}']=[pointer(pt,fields['STD_STRING_PTRS']+i*4),False]
 no_symbol=[];ambiguous=[]
 for key,row in source.items():
  if key in translated:continue
  try:new=target(row[0])
  except AssertionError:no_symbol.append(key);continue
  if new is not None:translated[key]=[new,row[1]]
 # A table slot and a named alias must share their exact source address.
 aliases=collections.defaultdict(set)
 for key,row in translated.items():aliases[source[key][0]].add(tuple(row))
 for key,row in source.items():
  if key not in translated and len(aliases[row[0]])==1:translated[key]=list(next(iter(aliases[row[0]])))
 # Braille reads retain the engine's separate alphabet decoder.
 braille={off for name,(off,_) in s0.items() if 'Braille_' in name}
 for key,row in translated.items():
  if source[key][0] in braille:row.append('braille')
 missing=sorted(set(keys)-translated.keys())
 assert len(s1['GetExpandedPlaceholder'])==1
 gender=gender_recipes(pt,maps[next(iter(s1['GetExpandedPlaceholder']))])
 profile=dict(genderPlaceholders=gender,game=a.game,sha1=audit['target_sha1'],md5=hashlib.md5(pt).hexdigest(),size=len(pt),fields=fields,metricUnits=True,
  renderGlyphs={'Ã':0xF1,'Õ':0xF2,'ã':0xF4,'õ':0xF5,'Í':0x5A,'í':0x6F},decodeGlyphs={0x0C:'Ï',0x21:'ï'})
 a.output.mkdir(parents=True,exist_ok=True)
 data=''.join(f'{k}\t{v[0]}\t{int(v[1])}\t{v[2] if len(v)>2 else "-"}\n' for k,v in sorted(translated.items()))
 text='-- Private address recipes; requires linguistic and live-game QA.\nlocal p='+lua(profile)+'\np.texts={}\nlocal rows=[==[\n'+data+']==]\n'
 text+='for k,o,b,t in rows:gmatch("([^\\t\\n]+)\\t(%d+)\\t([01])\\t([^\\n]+)\\n") do p.texts[k]={tonumber(o),b=="1",t~="-" and t or nil} end\nreturn p\n'
 (a.output/'profile.lua').write_text(text)
 report=dict(game=a.game,total=len(keys),mapped=len(translated),missing=missing,missing_tables=missing_tables,no_symbol=no_symbol,runtime_enabled=False,complete=False)
 (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 (a.output/'private-addresses.json').write_text(json.dumps({'source':source,'target':translated}))
 print(a.game,'mapped',len(translated),'missing',len(missing),'missing tables',missing_tables,'no symbol',len(no_symbol))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game',choices=['firered','leafgreen'],required=True)
 for key in ['base','target','elf','engine','metadata','texts','evidence','output']:p.add_argument('--'+key,type=Path,required=True)
 build(p.parse_args())
