"""Verify adjacent ROM asset boundaries, including variable-sized LZ streams."""
import json,sys
from pathlib import Path
from map_emerald_languages import ROOT,normalized
from build_profiles import lua_symbols

def lz_end(data,start):
    if data[start]!=16:return None
    size=int.from_bytes(data[start+1:start+4],'little')
    if not 0<size<=0x40000:return None
    pos=start+4;out=0
    try:
        while out<size:
            flag=data[pos];pos+=1
            for bit in range(7,-1,-1):
                if out>=size:break
                if flag&(1<<bit):
                    value=int.from_bytes(data[pos:pos+2],'big');pos+=2
                    if (value&4095)+1>out:return None
                    out+=(value>>12)+3
                else:pos+=1;out+=1
        return (pos+3)&~3
    except IndexError:return None

def run(lang):
    path=ROOT/f'build/emerald-{lang}-relocation.json';r=json.loads(path.read_text())
    spec=next(x for x in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms'] if x['language']==lang)
    src=(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba').read_bytes();dst=Path(spec['staged_file']).read_bytes()
    ns,nt=normalized(src),normalized(dst);maps={int(k):v for k,v in r['mapped'].items()}
    rows=lua_symbols(ROOT/'build/profile-engine/src/import/gba/syms/emeraldde.lua')
    sizes={a:n for a,n in rows.values()};added={}
    for iteration in range(6):
        changed=0
        for a,size in sizes.items():
            # Backward table boundary: all pointer slots and scalar bytes must
            # agree, and existing relocated targets corroborate slot identity.
            if a not in maps and a+size in maps and size>=8:
                hit=maps[a+size]-size
                if hit>=0 and ns[a:a+size]==nt[hit:hit+size]:
                    import struct,re
                    known=0;valid=True
                    for match in re.finditer(rb'(?=([\x00-\xff]{3}\x08))',src[a:a+size]):
                        x=struct.unpack_from('<I',src,a+match.start())[0]-0x08000000
                        y=struct.unpack_from('<I',dst,hit+match.start())[0]-0x08000000
                        if x in maps:
                            known+=1
                            if maps[x]!=y:valid=False
                    if known and valid:maps[a]=hit;added[a]=hit;changed+=1
            if a not in maps:continue
            b=maps[a];end=a+size
            if end in maps or end not in sizes:continue
            if ns[a:end]!=nt[b:b+size]:continue
            hit=b+size;length=sizes[end]
            if ns[end:end+length]==nt[hit:hit+length]:
                maps[end]=hit;added[end]=hit;changed+=1;continue
            if src[end:end+4]==dst[hit:hit+4] and src[end]==16:
                se,te=lz_end(src,end),lz_end(dst,hit)
                if se is not None and te is not None and maps.get(se)==te:
                    maps[end]=hit;added[end]=hit;changed+=1
        if not changed:break
    r['mapped']={str(k):v for k,v in maps.items()};r['counts']['asset-boundary']=len(added)
    path.write_text(json.dumps(r));print(lang,'asset boundaries',len(added))

if __name__=='__main__':run(sys.argv[1])
