"""Recover data references via matching Thumb PC-relative load instructions."""
import collections,json,struct,sys
from pathlib import Path
from map_emerald_languages import ROOT,BASE,normalized
from build_profiles import lua_symbols

def run(lang):
    path=ROOT/f'build/emerald-{lang}-relocation.json';r=json.loads(path.read_text())
    spec=next(x for x in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms'] if x['language']==lang)
    src=(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba').read_bytes();dst=Path(spec['staged_file']).read_bytes()
    ns,nt=normalized(src,True),normalized(dst,True);maps={int(k):v for k,v in r['mapped'].items()}
    funcs=lua_symbols(ROOT/'build/profile-engine/src/import/gba/syms/emeraldde_funcs.lua')
    candidates=collections.defaultdict(set);proofs=[]
    for off,size in set(funcs.values()):
        for pc in range(off,off+size-1,2):
            ins=struct.unpack_from('<H',src,pc)[0]
            if ins&0xf800!=0x4800:continue
            slot=((pc+4)&~3)+(ins&255)*4
            value=struct.unpack_from('<I',src,slot)[0]-BASE
            if value in maps or not 0<=value<len(src):continue
            if off in maps and ns[off:off+size]==nt[maps[off]:maps[off]+size]:
                tpc=maps[off]+pc-off
                ti=struct.unpack_from('<H',dst,tpc)[0]
                if ti==ins:
                    ts=((tpc+4)&~3)+(ti&255)*4;tv=struct.unpack_from('<I',dst,ts)[0]-BASE
                    if 0<=tv<len(dst):candidates[value].add(tv);proofs.append([value,tv,pc,tpc])
                continue
            for radius in (20,12,8):
                lo=max(off,pc-radius);hi=min(off+size,pc+2+radius);sample=ns[lo:hi]
                if len(sample)<18 or len(set(sample))<7:continue
                start=max(0,lo-4096);end=hi+4096
                hit=nt.find(sample,start,end)
                if hit<0 or nt.find(sample,hit+1,end)>=0:continue
                tpc=hit+pc-lo
                if tpc%2:continue
                ti=struct.unpack_from('<H',dst,tpc)[0]
                if ti!=ins:continue
                ts=((tpc+4)&~3)+(ti&255)*4
                tv=struct.unpack_from('<I',dst,ts)[0]-BASE
                if 0<=tv<len(dst):candidates[value].add(tv);proofs.append([value,tv,pc,tpc])
                break
    added={a:next(iter(v)) for a,v in candidates.items() if len(v)==1}
    maps.update(added);r['mapped']={str(k):v for k,v in maps.items()}
    r['counts']['thumb-literal']=len(added);r['literal_proofs']=proofs
    path.write_text(json.dumps(r));print(lang,'Thumb literal references',len(added))

if __name__=='__main__':run(sys.argv[1])
