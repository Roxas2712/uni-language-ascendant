"""Bound text runs by verified neighboring script/data symbols, including tails."""
import json,sys,bisect,collections
from pathlib import Path
from map_emerald_languages import ROOT,normalized
from build_profiles import lua_symbols
from chain_emerald_languages import eos

def run(lang,write=False):
 path=ROOT/f'build/emerald-{lang}-relocation.json';r=json.loads(path.read_text());maps={int(k):v for k,v in r['mapped'].items()}
 src=(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba').read_bytes()
 spec=next(x for x in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms'] if x['language']==lang);dst=Path(spec['staged_file']).read_bytes()
 p=json.loads((ROOT/'build/emerald-de-metadata.json').read_text());report=json.loads((ROOT/f'build/emerald-{lang}-profile-report.json').read_text())
 sy=lua_symbols(ROOT/'build/profile-engine/src/import/gba/syms/emeraldde.lua');names=collections.defaultdict(list)
 for k,(off,size) in sy.items():names[off].append(k)
 offsets=sorted(names);index={o:i for i,o in enumerate(offsets)}
 targets={p['texts'][k][0] for k in report['missing'] if k in p['texts'] and p['texts'][k][0] not in maps}
 istext={v[0] for k,v in p['texts'].items() if not k.startswith('g3:')}
 istext.update(o for o,ns in names.items() if any('text' in n.lower() or 'string' in n.lower() or 'description' in n.lower() for n in ns))
 anchors=sorted(o for o in offsets if o in maps);intervals=set();proof=[];added={}
 for a in targets:
  i=bisect.bisect_left(anchors,a)
  if i and i<len(anchors):intervals.add((anchors[i-1],anchors[i]))
 for left,right in sorted(intervals):
  if right-left>8192:continue
  starts=offsets[index[left]:index[right]+1]
  for aligned in [False,True]:
   off=maps[left];pairs=[]
   for a,b in zip(starts,starts[1:]):
    end=eos(src,a)
    if a in istext and end and 0<=b-end<=3 and not any(src[end:b]):
     te=eos(dst,off)
     if te is None:break
     pairs.append((a,off,'text'))
     off=(te+3)&~3 if b-end or aligned and a%4==0 and b%4==0 else te
    else:
     if normalized(src[a:b])!=normalized(dst[off:off+b-a]):break
     pairs.append((a,off,'bytes'));off+=b-a
   else:
    if off==maps[right]:
     for a,b,k in pairs:
      if a in targets:added[a]=b
     proof.append({'left':left,'right':right,'target_left':maps[left],'target_right':maps[right],'rows':pairs});break
 print(lang,'boundary text resolved',len(added))
 for a,b in added.items():print(hex(a),hex(b),names[a][:1])
 (ROOT/f'build/emerald-{lang}-residual-boundary.json').write_text(json.dumps({'added':added,'proof':proof},indent=2))
 if write:
  maps.update(added);r['mapped']={str(a):b for a,b in maps.items()};r['counts']['residual-boundary']=len(added);r['residual_boundary_proof']=proof;path.write_text(json.dumps(r))
if __name__=='__main__':run(sys.argv[1],'--write' in sys.argv)
