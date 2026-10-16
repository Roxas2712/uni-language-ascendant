"""Verify ordered text pools between independently relocated string anchors."""
import json,sys
from pathlib import Path
from map_emerald_languages import ROOT
from build_profiles import lua_symbols

EXT={1:1,2:1,3:1,4:3,5:1,6:1,8:1,11:2,12:1,13:1,14:1,16:2,17:1,18:1,19:1,20:1}
def eos(data,start):
    p=start
    while p<min(start+16384,len(data)):
        c=data[p]
        if c==255:return p+1
        if c==252:p+=2+EXT.get(data[p+1],0)
        elif c in (253,247,248,249):p+=2
        else:p+=1
    return None

def run(lang):
    path=ROOT/f'build/emerald-{lang}-relocation.json';r=json.loads(path.read_text())
    p=json.loads((ROOT/'build/emerald-de-metadata.json').read_text())
    spec=next(x for x in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms'] if x['language']==lang)
    src=(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba').read_bytes();dst=Path(spec['staged_file']).read_bytes()
    maps={int(k):v for k,v in r['mapped'].items()}
    # Exclude address aliases for code/data: only named text entries establish
    # text pool boundaries. Offsets inside another string split the chain.
    rows=lua_symbols(ROOT/'build/profile-engine/src/import/gba/syms/emeraldde.lua')
    starts={v[0] for k,v in p['texts'].items() if not k.startswith('g3:')}
    for name,(off,size) in rows.items():
        if not any(x in name.lower() for x in ('text','string','description')):continue
        end=eos(src,off)
        if end is not None and 0<=off+size-end<=3 and not any(src[end:off+size]):starts.add(off)
    starts=sorted(starts)
    chain=[];chains=[]
    for off in starts:
        if chain:
            end=eos(src,chain[-1])
            if end is None or not 0<=off-end<=3 or any(src[end:off]):
                chains.append(chain);chain=[]
        chain.append(off)
    if chain:chains.append(chain)
    added={};proof=[]
    for chain in chains:
        anchors=[i for i,a in enumerate(chain) if a in maps]
        for lo,hi in zip(anchors,anchors[1:]):
            if hi-lo<2:continue
            modes=[False,True] if all(a%4==0 for a in chain[lo:hi+1]) else [False]
            for align in modes:
                off=maps[chain[lo]];pairs=[]
                for i in range(lo,hi):
                    a=chain[i];pairs.append((a,off));end=eos(dst,off)
                    if end is None:break
                    gap=chain[i+1]-eos(src,a)
                    off=(end+3)&~3 if gap or align else end
                else:
                    if off==maps[chain[hi]]:
                        added.update(pairs[1:]);proof.append([chain[lo],chain[hi],len(pairs)-1]);break
    maps.update(added)
    r['counts']['anchored-text-pool']=len(added);r['text_pool_proofs']=proof
    r['mapped']={str(k):v for k,v in maps.items()};path.write_text(json.dumps(r))
    base=json.loads((ROOT/'build/emerald-base-texts.json').read_text())
    missing=[k for k in base if k in p['texts'] and p['texts'][k][0] not in maps]
    (ROOT/f'build/emerald-{lang}-missing.json').write_text(json.dumps(missing,indent=2))
    print(lang,'text pool',len(added),'missing',len(missing),missing[:20])

if __name__=='__main__':run(sys.argv[1])
