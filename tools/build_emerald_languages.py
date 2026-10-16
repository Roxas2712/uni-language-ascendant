"""Emit address-only language profiles from audited, exact-ROM relocations."""
import copy,json,sys,struct
from pathlib import Path
from build_profiles import lua
from map_emerald_languages import ROOT

def run(lang):
    audit=json.loads((ROOT/f'build/emerald-{lang}-relocation.json').read_text())
    maps={int(k):v for k,v in audit['mapped'].items()};missing=[]
    def relocate(v,label):
        if v in maps:return maps[v]
        if v&1 and v-1 in maps:return maps[v-1]+1
        missing.append((label,hex(v)));return v
    def tree(value,label):
        if isinstance(value,dict):return {k:tree(v,label+'.'+str(k)) for k,v in value.items()}
        if isinstance(value,list):return [tree(v,label+'.'+str(i)) for i,v in enumerate(value)]
        if isinstance(value,int) and value>65535:return relocate(value,label)
        return value
    src=json.loads((ROOT/'build/emerald-de-metadata.json').read_text())
    p={k:copy.deepcopy(v) for k,v in src.items() if k!='texts'}
    spec=next(x for x in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms'] if x['language']==lang)
    for k in ('sha1','md5','size'):p[k]=spec[k]
    p['fields']=tree(p['fields'],'fields')
    assets=json.loads((ROOT/'build/emerald-de_assets-metadata.json').read_text())
    original_names=copy.deepcopy(assets['symbols']['namesAt'])
    assets['fields']=tree(assets['fields'],'assets.fields')
    for name,v in assets['symbols']['off'].items():v[0]=relocate(v[0],'symbol.'+name)
    for name,size in audit.get('size_overrides',{}).items():assets['symbols']['size'][name]=[size]
    for method in ('namesAt','funcAt'):
        result={}
        for key,v in assets['symbols'][method].items():
            n=int(key);addr=n-0x08000000 if n>=0x08000000 else n
            target=relocate(addr,method+'.'+key)
            result[str(target+(0x08000000 if n>=0x08000000 else 0))]=v
        assets['symbols'][method]=result
    # Pokedex descriptions are indexed by national dex number. In particular,
    # unused/deduplicated pointers need not have a unique relocation alias.
    source_rom=(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba').read_bytes()
    target_rom=Path(spec['staged_file']).read_bytes()
    for nat in range(387):
        a=struct.unpack_from('<I',source_rom,src['fields']['POKEDEX_ENTRIES']+nat*32+16)[0]-0x08000000
        b=struct.unpack_from('<I',target_rom,p['fields']['POKEDEX_ENTRIES']+nat*32+16)[0]-0x08000000
        if str(a) in original_names:assets['symbols']['namesAt'][str(b)]=original_names[str(a)]
    world=json.loads((ROOT/'build/emerald-de_world-metadata.json').read_text())
    world['pairs']=tree(world['pairs'],'world')
    if missing:
        print(lang,'UNRESOLVED ASSETS',len(missing),missing[:30]);raise SystemExit(1)
    base=json.loads((ROOT/'build/emerald-base-texts.json').read_text())
    texts={k:[maps[v[0]],*v[1:]] for k,v in src['texts'].items() if k in base and v[0] in maps}
    for key,off in audit.get('text_overrides',{}).items():
        if key in base and key in src['texts']:texts[key]=[off,*src['texts'][key][1:]]
    omitted=sorted(set(base)-texts.keys())
    # No strings, images, or bytes from a ROM are emitted, only key/offset pairs.
    rows=''.join(f'{key}\t{v[0]}\t{int(v[1])}\t{v[2] if len(v)>2 and v[2] else ""}\t{v[3] if len(v)>3 and v[3] else ""}\n' for key,v in sorted(texts.items()))
    out='-- Generated address metadata; no ROM payload.\nlocal p='+lua(p)+'\np.texts={}\nlocal rows=[==[\n'+rows+']==]\n'
    out+='for key,off,battle,kind,len in rows:gmatch("([^\\t\\n]+)\\t(%d+)\\t([01])\\t([^\\t]*)\\t([^\\n]*)\\n") do\n p.texts[key]={tonumber(off),battle=="1",kind~="" and kind or nil,tonumber(len)}\nend\nreturn p\n'
    dest=ROOT/'mod/profiles';(dest/f'emerald_{lang}.lua').write_text(out)
    (dest/f'emerald_{lang}_assets.lua').write_text('-- Address metadata, no ROM payload.\nreturn '+lua(assets)+'\n')
    (dest/f'emerald_{lang}_world.lua').write_text('-- Address metadata, no ROM payload.\nreturn '+lua(world)+'\n')
    report={'language':lang,'sha1':spec['sha1'],'mapped':len(texts),'total':len(base),'missing':omitted,'evidence':audit['counts']}
    (ROOT/f'build/emerald-{lang}-profile-report.json').write_text(json.dumps(report,indent=2))
    print(lang,'PROFILE',len(texts),'/',len(base),'missing',len(omitted))

if __name__=='__main__':run(sys.argv[1])
