"""Developer-side relocation evidence for the verified European Emerald ROMs.

No guesses are used at runtime. This produces an audit, not an enabled profile.
Exact blocks and relocated pointer slots establish correspondence; unresolved
and conflicting addresses must be handled before a profile is published.
"""
from pathlib import Path
import collections, hashlib, json, re, struct, sys
from build_profiles import lua_symbols

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x08000000

def normalized(data, code=False):
    data = bytearray(data)
    # ROM pointer slots in Thumb code are word aligned. Event bytecode embeds
    # unaligned pointers. All evidence is subsequently checked in both ROMs.
    for m in re.finditer(rb"(?=([\x00-\xff]{3}\x08))", bytes(data)):
        p=m.start()
        if not code or p%4==0: data[p:p+3]=b'\0\0\0'
    if code:
        for m in re.finditer(rb'[\x00-\xff][\xf0-\xf7][\x00-\xff][\xf8-\xff]',bytes(data)):
            p=m.start()
            if p%2==0:struct.pack_into('<HH',data,p,0xf000,0xf800)
    return bytes(data)

def main():
    lang=sys.argv[1]
    inputs=json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())
    spec=next(x for x in inputs['roms'] if x['language']==lang)
    source=(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba').read_bytes()
    target=Path(spec['staged_file']).read_bytes()
    assert hashlib.sha1(source).hexdigest()=='61c2eb2b380b1a75f0c94b767a2d4c26cd7ce4e3'
    assert hashlib.sha1(target).hexdigest()==spec['sha1']
    syms=ROOT/'build/profile-engine/src/import/gba/syms'
    data=lua_symbols(syms/'emeraldde.lua')
    funcs=lua_symbols(syms/'emeraldde_funcs.lua')
    candidates=collections.defaultdict(set); evidence=collections.Counter(); blocks=[]
    extending='--extend' in sys.argv
    if extending:
        old=json.loads((ROOT/f'build/emerald-{lang}-relocation.json').read_text())
        assert old['sha1']==spec['sha1']
        for k,v in old['mapped'].items():candidates[int(k)].add(v)
        for k,v in old['conflicts'].items():
            if int(k) not in candidates:candidates[int(k)].update(v)
        blocks=old['blocks']
    def add(a,b,why):
        if 0<=a<len(source) and 0<=b<len(target):
            candidates[a].add(b);evidence[why]+=1
    # All EU code lives below the first event script data. Normalize both
    # entire images consistently, including the literal pool alignment.
    code_end=max(a+s for a,s in funcs.values())
    for kind,rows in [('code',funcs),('data',data)]:
        ns=normalized(source,kind=='code')
        nt=normalized(target,kind=='code')
        seen=set()
        for name,(off,size) in rows.items():
            if (off,size) in seen or size<16: continue
            seen.add((off,size))
            if extending and len(candidates.get(off,set()))==1:continue
            # Complete symbols, not an arbitrary short prefix.
            sample=ns[off:off+size]
            if len(set(sample))<6:continue
            lo,hi=max(0,off-0x60000),min(len(nt),off+0x60000+size)
            hit=nt.find(sample,lo,hi)
            if hit<0 or nt.find(sample,hit+1,hi)>=0:continue
            # Require matching alignment for code and structured data.
            if kind=='code' and (hit-off)%4:continue
            add(off,hit,kind);blocks.append((off,hit,size,kind))
            for m in re.finditer(rb"(?=([\x00-\xff]{3}\x08))",source[off:off+size]):
                pos=off+m.start()
                if kind=='code' and pos%4:continue
                at=hit+m.start()
                a=struct.unpack_from('<I',source,pos)[0]-BASE
                b=struct.unpack_from('<I',target,at)[0]-BASE
                if target[at+3]==8:add(a,b,'pointer')
    # Pointer-only tables cannot be located by content alone. Once a code
    # reference identifies their base, verify their entire normalized shape
    # and follow their slots (including map headers and event scripts).
    done=set()
    unique_rows=set(data.values())
    for iteration in range(12):
        added=0
        for off,size in unique_rows:
            targets=candidates.get(off,set())
            if len(targets)!=1 or size<4:continue
            hit=next(iter(targets))
            if (off,hit) in done:continue
            done.add((off,hit))
            if ns[off:off+size]!=nt[hit:hit+size]:continue
            for m in re.finditer(rb"(?=([\x00-\xff]{3}\x08))",source[off:off+size]):
                pos=off+m.start();at=hit+m.start()
                a=struct.unpack_from('<I',source,pos)[0]-BASE
                b=struct.unpack_from('<I',target,at)[0]-BASE
                before=len(candidates.get(a,set()))
                if target[at+3]==8:add(a,b,'table-pointer')
                added+=len(candidates.get(a,set()))-before
        if not added:break
    result={'language':lang,'sha1':spec['sha1'],'code_end':code_end,
            'counts':dict(evidence),'blocks':blocks,
            'mapped':{str(k):next(iter(v)) for k,v in candidates.items() if len(v)==1},
            'conflicts':{str(k):sorted(v) for k,v in candidates.items() if len(v)>1}}
    out=ROOT/f'build/emerald-{lang}-relocation.json';out.write_text(json.dumps(result))
    p=json.loads((ROOT/'build/emerald-de-metadata.json').read_text())
    needed={v[0] for v in p['texts'].values()}
    found=needed&{int(k) for k in result['mapped']}
    print(lang,dict(evidence),'unique',len(result['mapped']),'conflicts',len(result['conflicts']),
          'text addresses',len(found),'/',len(needed),'code end',hex(code_end),flush=True)

if __name__=='__main__':main()
