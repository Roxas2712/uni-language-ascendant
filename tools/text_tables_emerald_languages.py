"""Resolve text by semantic table slots, overriding incidental byte matches."""
import collections,json,struct,sys
from pathlib import Path
from map_emerald_languages import ROOT,BASE
from build_profiles import lua_symbols
from chain_emerald_languages import eos

def run(lang):
    path=ROOT/f'build/emerald-{lang}-relocation.json';r=json.loads(path.read_text())
    spec=next(x for x in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms'] if x['language']==lang)
    src=(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba').read_bytes();dst=Path(spec['staged_file']).read_bytes()
    p=json.loads((ROOT/'build/emerald-de-metadata.json').read_text());cfg=json.loads((ROOT/'build/emerald.json').read_text())
    maps={int(k):v for k,v in r['mapped'].items()}
    # Random bytes in identical compressed graphics are not text references.
    # A stationary text address must actually hold the same string.
    removed=[]
    base=json.loads((ROOT/'build/emerald-base-texts.json').read_text())
    for a in {v[0] for k,v in p['texts'].items() if k in base}:
        if maps.get(a)==a and src[a:eos(src,a)]!=dst[a:eos(dst,a)]:removed.append(a);del maps[a]
    rows=lua_symbols(ROOT/'build/profile-engine/src/import/gba/syms/emeraldde.lua')
    pairs=collections.defaultdict(set);overrides={}
    def ptr(data,at):
        n=struct.unpack_from('<I',data,at)[0]-BASE
        return n if 0<=n<len(data) else None
    def add(a,b):
        if a is not None and b is not None:pairs[a].add(b)
    for table in cfg['tables']:
        a=table['addr'];b=maps.get(a)
        if b is None:continue
        for i in range(table['count']*table.get('inner',1)):
            aa=a+i*table['stride'];bb=b+i*table['stride']
            if not table.get('inline'):aa,bb=ptr(src,aa),ptr(dst,bb)
            if aa is None or bb is None:continue
            add(aa,bb)
            if table.get('ids') is not None:
                ids=cfg['battleIds'];ix=i+table['ids'];key=ids[str(ix)] if isinstance(ids,dict) else ids[ix-1]
            elif table.get('inner'):key=f"{table['name']}[{i//table['inner']}][{i%table['inner']}]"
            else:key=f"{table['name']}[{i}]"
            overrides[key]=bb
    for field,count,stride,member in [('ITEMS',377,44,20),('POKEDEX_ENTRIES',387,32,16),('ABILITY_DESCRIPTIONS',78,4,0),('MOVE_DESCRIPTIONS',354,4,0)]:
        a=p['fields'][field];b=maps[a]
        for i in range(count):add(ptr(src,a+i*stride+member),ptr(dst,b+i*stride+member))
    for name,field,count,stride in [('gTypeNames','TYPE_NAMES',18,7),('gSpeciesNames','SPECIES_NAMES',412,11),('gMoveNames','MOVE_NAMES',355,13),('gAbilityNames','ABILITY_NAMES',78,13)]:
        a=p['fields'][field];b=maps[a]
        for i in range(count):add(a+i*stride,b+i*stride);overrides[f'{name}[{i}]']=b+i*stride
    # Storyteller records: stat ID/flags followed by title, action and story.
    a,size=rows['sStorytellerStories'];b=maps[a]
    assert size==36*16
    for i in range(36):
        assert src[a+i*16:a+i*16+4]==dst[b+i*16:b+i*16+4]
        for j in (4,8,12):add(ptr(src,a+i*16+j),ptr(dst,b+i*16+j))
    fixed=0
    for a,targets in pairs.items():
        strings={dst[b:eos(dst,b)] for b in targets}
        if len(strings)==1:
            b=min(targets)
            fixed+=maps.get(a)!=b;maps[a]=b
    r['mapped']={str(k):v for k,v in maps.items()};r['text_overrides']=overrides
    r['counts']['text-schema']={'removed_incidental':len(removed),'resolved':fixed,'direct_keys':len(overrides)}
    path.write_text(json.dumps(r));print(lang,'TEXT_SCHEMA',len(removed),'incidental removed;',fixed,'resolved')

if __name__=='__main__':run(sys.argv[1])
