"""Build address-only mod profiles using verified local developer ROMs/symbols.

The distributed profiles contain offsets and identifiers, not ROM payloads.
Runtime users supply their own ROM through Gen1Recomp's mod import panel.
"""
import argparse, json, hashlib, re, subprocess
from source_offsets import recover
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = 0x08000000
SPECS = {
    'sapphire': ('7e6e034f9cdca6d2c4a270fdb50a94def5883d17', '9d816b369343d39b94af9a8b0ce7f63b', 'Pokemon - Saphir-Edition (Germany) (Rev 1).gba'),
    'firered': ('18a3758ceeef2c77b315144be2c3910d6f1f69fe', '6648a0484a56097ca75d6af87ebce225', 'Pokemon - Feuerrote Edition (Germany).gba'),
    'leafgreen': ('0802d1fb185ee3ed48d9a22afb25e66424076dac', '4dd5e72f942a921d3fe53d21a39f4cba', 'Pokemon - Blattgruene Edition (Germany).gba'),
    'ruby': ('1c2a53332382e14dab8815e3a6dd81ad89534050', '1af28ea547d4116dc752c93f7f694239', 'Pokemon - Rubin-Edition (Germany).gba'),
    'emerald': ('61c2eb2b380b1a75f0c94b767a2d4c26cd7ce4e3', 'f793a854654b467211fc32c4062cb183', 'Pokemon - Smaragd-Edition (Germany).gba'),
}

def elf_symbols(path, readelf):
    rows, obj = {}, ''
    for line in subprocess.check_output([readelf, '-sW', str(path)], text=True).splitlines():
        p = line.split()
        if len(p)<8 or not p[0][:-1].isdigit(): continue
        _, addr, size, typ, bind, vis, ndx, name = p[:8]
        if typ == 'FILE': obj=name; continue
        addr = int(addr,16)
        if typ not in ('FUNC','FILE','SECTION') and B <= addr < B+0x1000000 and not name.startswith(('$','.')):
            key = (obj+':' if bind=='LOCAL' else '')+name
            rows[key] = (addr-B, int(size))
    return rows

def lua_symbols(path):
    s=path.read_text()
    objects=re.search(r'objs = \[==\[(.*?)\]==\]',s,re.S)[1].strip().splitlines()
    collisions=set(re.search(r'collide = \[==\[(.*?)\]==\]',s,re.S)[1].strip().splitlines())
    data=re.search(r'data = \[==\[(.*?)\]==\]',s,re.S)[1]
    out={}
    for line in data.splitlines():
        p=line.split()
        if len(p)<3: continue
        name,off,size=p[:3]
        obj=objects[int(p[3])-1] if len(p)>3 else ''
        row=(int(off,16),int(size.lstrip('~'),16))
        if name not in collisions: out[name]=row
        if obj: out[obj+':'+name]=row
    return out

def lua(v):
    if v is None: return 'nil'
    if isinstance(v,bool): return 'true' if v else 'false'
    if isinstance(v,(int,float)): return str(v)
    if isinstance(v,str): return json.dumps(v,ensure_ascii=False)
    if isinstance(v,list): return '{'+','.join(lua(x) for x in v)+'}'
    return '{\n'+''.join('['+lua(k)+']='+lua(x)+',\n' for k,x in sorted(v.items()))+'}'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--engine',type=Path,required=True)
    ap.add_argument('--roms',type=Path,required=True)
    ap.add_argument('--elf-root',type=Path,required=True)
    ap.add_argument('--luajit',required=True)
    ap.add_argument('--readelf',default='/opt/homebrew/bin/arm-none-eabi-readelf')
    ap.add_argument('--games', nargs='+')
    a=ap.parse_args()
    dest=ROOT/'mod'/'profiles';dest.mkdir(parents=True,exist_ok=True)
    build=ROOT/'build';build.mkdir(exist_ok=True)
    for game,(sha,md5,filename) in SPECS.items():
        if a.games and game not in a.games: continue
        rom=(a.roms/filename).read_bytes()
        assert hashlib.sha1(rom).hexdigest()==sha
        assert hashlib.md5(rom).hexdigest()==md5
        meta=build/(game+'.json')
        subprocess.run([a.luajit,str(ROOT/'tools/export_profile.lua'),game,sha,str(meta)],cwd=a.engine,check=True)
        cfg=json.loads(meta.read_text())
        usfile={'firered':'Pokemon - FireRed Version (USA).gba','sapphire':'Pokemon - Sapphire Version (USA).gba','leafgreen':'Pokemon - LeafGreen Version (USA).gba','ruby':'Pokemon - Ruby Version (USA).gba','emerald':'Pokemon - Emerald Version (USA, Europe).gba'}[game]
        usrom=(a.roms/usfile).read_bytes()
        usmeta=build/(game+'-us.json')
        subprocess.run([a.luajit,str(ROOT/'tools/export_profile.lua'),game,hashlib.sha1(usrom).hexdigest(),str(usmeta)],cwd=a.engine,check=True)
        uscfg=json.loads(usmeta.read_text())
        if game in ('leafgreen','firered'):
            us=elf_symbols(a.elf_root/f'poke{game}.elf',a.readelf)
            de=elf_symbols(a.elf_root/f'poke{game}_de.elf',a.readelf)
        else:
            us=lua_symbols(a.engine/f'src/import/gba/syms/{game}.lua')
            de=lua_symbols(a.engine/f'src/import/gba/syms/{game}{'de11' if game=='sapphire' else 'de'}.lua')
            # Names renamed in newer upstream source, with identical roles.
            if game=='emerald':
                for key in us:
                    m=re.fullmatch(r'MatchCall_Text_(.+)_(Preparing|PreparingPostGame|RematchReady|PostRematch)',key)
                    if m:
                        alias='MatchCall_Text_'+m[1]+str(['Preparing','PreparingPostGame','RematchReady','PostRematch'].index(m[2])+1)
                        if alias in de: de[key]=de[alias]
                for key,alias in {'gText_BoostPP':'gText_BoostPp','gText_MoveInterfacePPType':'gText_MoveInterfacePpType',
                                  'sCreditsText_EnglishVersion':'sCreditsText_GermanVersion',
                                  'MtChimney_Text_MeteoriteFittedOnMachine':'MtChimney_Text_MetoriteFittedOnMachine',
                                  'sText_RegistrationCompleted':'sText_RegistraionCompleted'}.items():
                    if alias in de: de[key]=de[alias]
            source=a.elf_root.parent/('pokeruby' if game in ('ruby','sapphire') else 'pokeemerald-german')
            if source.exists():
                missing={k for k in us if k not in de and re.search(r'text|string|description',k,re.I)}
                de.update(recover(source,rom,missing))
        if game=='sapphire':
            # Five source labels became unnamed in this compiler's ELF. Match
            # their complete, terminated DE Ruby strings exactly and uniquely
            # in the verified DE Sapphire ROM; never infer a revision delta.
            reference=(a.roms/'Pokemon - Rubin-Edition (Germany).gba').read_bytes()
            assert hashlib.sha1(reference).hexdigest()==SPECS['ruby'][0]
            rows=(dest/'ruby.lua').read_text()
            for name in ['Category_EnglishVersionCoordinators','Category_NOAProductTesting','Category_Translator','UnknownString_81C40DF','UnknownString_81C6C85']:
                off=int(re.search(r'^'+name+r'\t(\d+)\t',rows,re.M)[1])
                literal=reference[off:reference.index(255,off)+1]
                found=rom.find(literal)
                assert found>=0 and rom.find(literal,found+1)<0, 'Ambiguous shared string: '+name
                de[name]=(found,len(literal))
        texts=cfg['named']
        # Pointer aliases are needed by field-script bytecode. Match exact symbol
        # starts only: byte deltas inside translated strings are not portable.
        candidates={};braille=set()
        for key,(off,size) in us.items():
            if key in de:
                candidates.setdefault(off,set()).add(de[key][0])
                if key not in texts and re.search(r'text|string|description',key,re.I): texts[key]=[de[key][0],False]
                if 'Braille_' in key and not key.startswith('s'): braille.add(off)
        for off,targets in candidates.items():
            if len(targets)==1:
                texts[f'g3:{B+off:08x}']=[next(iter(targets)),False]+([('braille' if game in ('leafgreen','firered') else 'braille_'+game)] if off in braille else [])
        for t in cfg['tables']:
            for i in range(t['count']*t.get('inner',1)):
                if t.get('ids') is not None:
                    ids=cfg['battleIds']; ix=i+t['ids']
                    key=ids[str(ix)] if isinstance(ids,dict) else ids[ix-1]
                elif t.get('inner'):
                    key=f"{t['name']}[{i//t['inner']}][{i%t['inner']}]"
                else: key=f"{t['name']}[{i}]"
                off=t['addr']+i*t['stride']
                if not t.get('inline'): off=int.from_bytes(rom[off:off+4],'little')-B
                if 0<=off<len(rom): texts[key]=[off,bool(t.get('battle') and not t.get('inline'))]
        for i in range(cfg['fields'].get('STD_STRING_COUNT',0)):
            at=cfg['fields']['STD_STRING_PTRS']+4*i
            off=int.from_bytes(rom[at:at+4],'little')-B
            if 0<=off<len(rom): texts[f'stdstring:{i}']=[off,False]
        # Pokedex entries have a stable national index, including when the DE
        # symbol dump is incomplete. Resolve pointers per slot, never by delta.
        usnames={}
        for key,(off,size) in us.items():
            if re.search('description',key,re.I): usnames.setdefault(off,[]).append(key)
        dexmap={}
        for nat in range(387):
            for member in ([16] if game=='emerald' else [16,20]):
                uat=uscfg['fields']['POKEDEX_ENTRIES']+nat*uscfg['fields']['POKEDEX_ENTRY_SIZE']+member
                dat=cfg['fields']['POKEDEX_ENTRIES']+nat*cfg['fields']['POKEDEX_ENTRY_SIZE']+member
                uoff=int.from_bytes(usrom[uat:uat+4],'little')-B
                doff=int.from_bytes(rom[dat:dat+4],'little')-B
                if 0<=uoff<len(usrom) and 0<=doff<len(rom): dexmap.setdefault(uoff,set()).add(doff)
        for uoff,targets in dexmap.items():
            if len(targets)!=1: continue
            doff=next(iter(targets))
            for key in usnames.get(uoff,[]): texts[key]=[doff,False]
            texts[f'g3:{B+uoff:08x}']=[doff,False]
        if game in ('ruby','sapphire'):
            off,size=de['gUnknown_083CC59C']
            texts['gUnknown_083CC59C']=[off,False,'fragment',size]
        profile=dict(game=game,sha1=sha,md5=md5,size=len(rom),fields=cfg['fields'])
        # One data string avoids LuaJIT's 65536-constant limit on large tables.
        rows=''.join(f'{key}\t{v[0]}\t{int(v[1])}\t{v[2] if len(v)>2 else ""}\t{v[3] if len(v)>3 else ""}\n' for key,v in sorted(texts.items()))
        source='-- Generated address metadata; no ROM payload.\nlocal p='+lua(profile)+'\np.texts={}\n'
        source+='local rows=[==[\n'+rows+']==]\n'
        source+='for key,off,battle,kind,len in rows:gmatch("([^\\t\\n]+)\\t(%d+)\\t([01])\\t([^\\t]*)\\t([^\\n]*)\\n") do\n'
        source+=' p.texts[key]={tonumber(off),battle=="1",kind~="" and kind or nil,tonumber(len)}\nend\nreturn p\n'
        (dest/(game+'.lua')).write_text(source)
        print(game,len(texts),'address mappings')

if __name__=='__main__': main()
