"""Resolve residual text references using unique instruction/script contexts.
Only references to known text/table symbols are considered, never arbitrary
pointer-looking bytes found in graphics. Emit audit evidence for every match.
"""
import json,sys,struct,collections,re,bisect
from pathlib import Path
from map_emerald_languages import ROOT,BASE,normalized
from build_profiles import lua_symbols
from chain_emerald_languages import eos

def run(lang,write=False):
 path=ROOT/f'build/emerald-{lang}-relocation.json';r=json.loads(path.read_text());maps={int(k):v for k,v in r['mapped'].items()}
 src=(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba').read_bytes()
 spec=next(x for x in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms'] if x['language']==lang);dst=Path(spec['staged_file']).read_bytes()
 p=json.loads((ROOT/'build/emerald-de-metadata.json').read_text());report=json.loads((ROOT/f'build/emerald-{lang}-profile-report.json').read_text())
 sy=lua_symbols(ROOT/'build/profile-engine/src/import/gba/syms/emeraldde.lua')
 names=collections.defaultdict(list)
 for k,(off,size) in sy.items():names[off].append(k)
 offsets=sorted(names)
 targets={p['texts'][k][0] for k in report['missing'] if k in p['texts']}
 targets.update(sy[k][0] for k in ['gTextTable_Players','sCantTradeMonTexts','sDoYouWantModeTexts'])
 ns,nt=normalized(src,False),normalized(dst,False)
 cand=collections.defaultdict(set);proof=[]
 for a in sorted(targets):
  needle=struct.pack('<I',BASE+a);ref=src.find(needle)
  while ref>=0:
   # Exclude graphics, and record the source script/code owner for review.
   if ref<0x300000:
    owner=offsets[bisect.bisect_right(offsets,ref)-1]
    for radius in [48,32,24,16,12]:
     lo=max(0,ref-radius);hi=ref+4+radius;sample=ns[lo:hi]
     if len(set(sample))<8:continue
     hit=nt.find(sample,max(0,lo-0x40000),hi+0x40000)
     if hit<0 or nt.find(sample,hit+1,hi+0x40000)>=0:continue
     slot=hit+ref-lo;b=struct.unpack_from('<I',dst,slot)[0]-BASE
     if 0<=b<len(dst):cand[a].add(b);proof.append(dict(source=a,target=b,source_slot=ref,target_slot=slot,radius=radius,owner=names[owner]))
     break
   ref=src.find(needle,ref+1)
 added={a:next(iter(bs)) for a,bs in cand.items() if len(bs)==1}
 print(lang,'resolved',len(added),'ambiguous',[(hex(a),list(map(hex,bs))) for a,bs in cand.items() if len(bs)>1])
 for a,b in added.items():print(hex(a),hex(b),names[a][:1])
 out={'added':{str(a):b for a,b in added.items()},'proof':proof}
 (ROOT/f'build/emerald-{lang}-residual-context.json').write_text(json.dumps(out,indent=2))
 if write:
  maps.update(added);r['mapped']={str(a):b for a,b in maps.items()};r['counts']['residual-context']=len(added);r['residual_context_proof']=proof;path.write_text(json.dumps(r))
if __name__=='__main__':run(sys.argv[1],'--write' in sys.argv)
