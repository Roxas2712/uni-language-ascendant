"""Extend relocations through bounded, byte-verified pointer contexts."""
from pathlib import Path
import bisect, collections, hashlib, json, re, struct, sys
from build_profiles import lua_symbols
from map_emerald_languages import ROOT, BASE, normalized

def run(lang):
    path=ROOT/f'build/emerald-{lang}-relocation.json'
    audit=json.loads(path.read_text())
    spec=next(x for x in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms'] if x['language']==lang)
    src=(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba').read_bytes()
    dst=Path(spec['staged_file']).read_bytes()
    assert hashlib.sha1(dst).hexdigest()==audit['sha1']
    maps={int(k):v for k,v in audit['mapped'].items()}
    conflicts={int(k):set(v) for k,v in audit['conflicts'].items()}
    rows=lua_symbols(ROOT/'build/profile-engine/src/import/gba/syms/emeraldde.lua')
    profile=json.loads((ROOT/'build/emerald-de-metadata.json').read_text())
    needed={v[0] for v in profile['texts'].values()}
    needed.update(off for off,size in rows.values())
    ptrs=collections.defaultdict(list)
    for m in re.finditer(rb'(?=([\x00-\xff]{3}\x08))',src):
        pos=m.start();ptrs[struct.unpack_from('<I',src,pos)[0]-BASE].append(pos)
    ns,nt=normalized(src),normalized(dst)
    additions={}
    # A pointer's surrounding bytecode/data must match uniquely on both sides.
    # Values are obtained from the corresponding target pointer slot.
    for off in sorted(needed-maps.keys()-conflicts.keys()):
        hits=set()
        for pos in ptrs.get(off,[]):
            for radius in (20,12):
                lo=max(0,pos-radius);hi=pos+4+radius
                sample=ns[lo:hi]
                if len(set(sample))<7:continue
                start=max(0,lo-0x60000);end=min(len(dst),hi+0x60000)
                hit=nt.find(sample,start,end)
                if hit<0 or nt.find(sample,hit+1,end)>=0:continue
                at=hit+pos-lo
                if dst[at+3]==8:
                    value=struct.unpack_from('<I',dst,at)[0]-BASE
                    if 0<=value<len(dst):hits.add(value)
                break
        if len(hits)==1:additions[off]=next(iter(hits))
    maps.update(additions)
    audit['counts']['context-pointer']=len(additions)
    # Text-pointer tables with an identified start are indexed by their
    # semantic slot, even if localized strings differ in size.
    cfg=json.loads((ROOT/'build/emerald.json').read_text())
    def ptr(data,at):
        v=int.from_bytes(data[at:at+4],'little')-BASE
        return v if 0<=v<len(data) else None
    indexed=0
    for table in cfg['tables']:
        a=table['addr'];b=maps.get(a)
        if b is None:continue
        for i in range(table['count']*table.get('inner',1)):
            aa=a+i*table['stride'];bb=b+i*table['stride']
            if not table.get('inline'):aa,bb=ptr(src,aa),ptr(dst,bb)
            if aa is not None and bb is not None and aa not in conflicts:
                if aa in maps and maps[aa]!=bb:continue
                maps[aa]=bb;indexed+=1
    for field,count,stride,member in [('ITEMS',377,44,20),('POKEDEX_ENTRIES',387,32,16),('ABILITY_DESCRIPTIONS',78,4,0),('MOVE_DESCRIPTIONS',354,4,0)]:
        a=profile['fields'][field];b=maps.get(a)
        assert b is not None,field
        for i in range(count):
            aa,bb=ptr(src,a+i*stride+member),ptr(dst,b+i*stride+member)
            if aa is not None and bb is not None and aa not in conflicts:
                if aa in maps and maps[aa]!=bb:continue
                maps[aa]=bb;indexed+=1
    audit['counts']['indexed-text']=indexed
    audit['mapped']={str(k):v for k,v in maps.items()}
    path.write_text(json.dumps(audit))
    base=json.loads((ROOT/'build/emerald-base-texts.json').read_text())
    missing=[k for k in base if k in profile['texts'] and profile['texts'][k][0] not in maps]
    (ROOT/f'build/emerald-{lang}-missing.json').write_text(json.dumps(missing,indent=2))
    print(lang,'refined',len(additions),'indexed',indexed,'missing registry',len(missing),missing[:15],flush=True)

if __name__=='__main__':run(sys.argv[1])
