"""Close relocation gaps only inside equal-shape, two-anchor intervals."""
import bisect,collections,json,re,struct,sys
from pathlib import Path
from map_emerald_languages import ROOT,BASE,normalized
from build_profiles import lua_symbols

def run(lang):
    path=ROOT/f'build/emerald-{lang}-relocation.json';r=json.loads(path.read_text())
    p=json.loads((ROOT/'build/emerald-de-metadata.json').read_text())
    spec=next(x for x in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms'] if x['language']==lang)
    src=(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba').read_bytes();dst=Path(spec['staged_file']).read_bytes()
    ns,nt=normalized(src),normalized(dst)
    maps={int(k):v for k,v in r['mapped'].items()}
    rows=lua_symbols(ROOT/'build/profile-engine/src/import/gba/syms/emeraldde.lua')
    needed={v[0] for v in p['texts'].values()}|{a for a,s in rows.values()}
    stats=collections.Counter();done=set();proofs=[]
    for turn in range(8):
        additions={};anchors=sorted(maps)
        for off in sorted(needed-maps.keys()):
            i=bisect.bisect_left(anchors,off)
            if not 0<i<len(anchors):continue
            a,b=anchors[i-1:i+1];ta,tb=maps[a],maps[b]
            if ta-a!=tb-b or b-a>0x10000:continue
            if ns[a:b]!=nt[ta:tb]:continue
            additions[off]=ta+off-a;stats['interval']+=1
        maps.update(additions)
        candidates=collections.defaultdict(set)
        for off,size in set(rows.values()):
            if off not in maps or (off,maps[off]) in done:continue
            hit=maps[off];done.add((off,hit))
            if ns[off:off+size]!=nt[hit:hit+size]:continue
            for m in re.finditer(rb'(?=([\x00-\xff]{3}\x08))',src[off:off+size]):
                a=struct.unpack_from('<I',src,off+m.start())[0]-BASE
                b=struct.unpack_from('<I',dst,hit+m.start())[0]-BASE
                if 0<=a<len(src) and 0<=b<len(dst) and a not in maps:candidates[a].add(b)
        extra={a:next(iter(v)) for a,v in candidates.items() if len(v)==1}
        maps.update(extra);stats['pointer']+=len(extra)
        if not additions and not extra:break
    r['mapped']={str(k):v for k,v in maps.items()};r['counts']['interval-pass']=dict(stats)
    path.write_text(json.dumps(r));print(lang,dict(stats))

if __name__=='__main__':run(sys.argv[1])
