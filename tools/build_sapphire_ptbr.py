"""Build Sapphire PT-BR using exact shared Ruby source identities + authored dex.

The imported translation source is a Ruby PT-BR ROM; the executing game stays
US Sapphire. Original source text, graphics and ROM bytes are never emitted.
"""
import argparse,json,subprocess
from pathlib import Path
from build_profiles import lua
from build_authored import build
from build_plain_supplement import compile_prose, reuse_exact

ROOT=Path(__file__).resolve().parents[1]

def main(a):
    def readlua(path, numeric_fields=False):
        code="local J=require('src.link.Json');local function fix(v) if type(v)~='table' then return v end;local r={};for k,x in pairs(v) do r[tostring(k)]=fix(x) end;return r end;io.write(J.encode(fix(dofile("+lua(str(path))+"))))"
        if not numeric_fields: code="local J=require('src.link.Json');io.write(J.encode(dofile("+lua(str(path))+")))"
        return json.loads(subprocess.check_output([str(a.luajit),'-e',code],cwd=a.engine,text=True))
    ru=json.loads(a.ruby_texts.read_text());sa=json.loads(a.sapphire_texts.read_text())
    profile=readlua(ROOT/'mod/profiles/ruby_ptbr.lua')
    profile['decodeGlyphs']={int(k):v for k,v in profile.get('decodeGlyphs',{}).items()}
    canon=lambda ir:json.dumps(ir,sort_keys=True,ensure_ascii=False)
    lookup={canon(ir):key for key,ir in ru.items()}
    shared={key:lookup[canon(ir)] for key,ir in sa.items() if canon(ir) in lookup}
    unique=set(sa)-set(shared)
    dex={}
    for key in unique:
        if key.startswith('DexDescription_'):
            species=key.rsplit('_',1)[0].removeprefix('DexDescription_');dex.setdefault(species,[]).append(key)
    prose=json.loads((ROOT/'translations/pt-BR/sapphire-dex.json').read_text())
    assert set(dex)==set(prose)
    code="local J=require('src.link.Json');local I=require('src.core.game3.scripting.text_ir');local g=assert(loadfile("+lua(str(ROOT/'mod/latin_glyphs.lua'))+"))('pt-BR');local out={};for k,v in pairs(I.CHARMAP) do out[tostring(k)]=v end;for k,v in pairs(g) do out[tostring(k)]=v end;io.write(J.encode(out))"
    charmap=json.loads(subprocess.check_output([str(a.luajit),'-e',code],cwd=a.engine,text=True))
    reverse={v:int(k) for k,v in charmap.items() if len(v)==1};reverse.update(profile['renderGlyphs'])
    metadata=readlua(ROOT/'mod/profiles/ruby_ptbr_assets.lua', True)
    # Native RS normal text uses font 3, including the Pokédex.
    widths=metadata['fields']['RS_FONT_WIDTHS']['3'];rom=a.source_rom.read_bytes()
    def width(text):
        assert set(text)<=set(reverse),f'Unsupported glyphs {set(text)-set(reverse)}'
        return sum(rom[widths['off']+reverse[ch]] for ch in text)
    def wrap(text):
        lines=[];line=''
        for word in text.split():
            assert width(word)<=208
            if line and width(line+' '+word)>208:lines.append(line);line=word
            else:line=(line+' '+word).strip()
        if line:lines.append(line)
        return lines
    targets={}
    overflow=[]
    for species,keys in sorted(dex.items()):
        keys.sort();lines=wrap(prose[species])
        if len(lines)>3*len(keys):overflow.append((species,len(lines),3*len(keys)));continue
        # Both pages exist; avoid silently leaving the second page empty.
        split=3 if len(lines)>3 else max(1,(len(lines)+1)//2)
        pages=[lines] if len(keys)==1 else [lines[:split],lines[split:]]
        for key,ls in zip(keys,pages):
            ir=[]
            for line in ls:
                if ir:ir.append({'t':'nl'})
                ir.append({'t':'text','s':line})
            targets[key]=ir+[{'t':'eos'}]
    assert not overflow,f'Translations exceed original page capacity: {overflow}'
    for key in unique-set(targets):
        ir=sa[key]
        if key=='Text_Version':
            targets[key]=[dict(seg,s='POKéMON VERSÃO SAFIRA') if seg['t']=='text' else seg for seg in ir]
        else:
            assert key in ('gDefaultBoyName1','gMalePresetNames[1]','gDefaultGirlName1','gFemalePresetNames[1]'),key
            targets[key]=ir # Preserve Sapphire's player-name presets.
    corrections=json.loads((ROOT/'translations/pt-BR/ruby-corrections.json').read_text())
    # Address-derived script keys differ even when the whole source IR is
    # identical. Reuse the reviewed correction by full IR, including controls.
    targets=reuse_exact(sa,ru,corrections,targets)
    ruby_prose=json.loads((ROOT/'translations/pt-BR/ruby-remainders.json').read_text())
    targets=reuse_exact(sa,ru,compile_prose(ru,ruby_prose),targets)
    if a.reference_base:
        reference=json.loads(a.reference_base.read_text())
        extra=json.loads((ROOT/'translations/pt-BR/emerald-remainders.json').read_text())
        targets=reuse_exact(sa,reference,compile_prose(reference,extra),targets)
    authored=build(sa,targets,a.engine,a.luajit)
    mapped={key:profile['texts'][rkey] for key,rkey in shared.items()}
    # Unique entries have authored content, so they require no source pointer.
    profile['texts']=mapped;profile['game']='sapphire';profile['skipWorld']=True
    (ROOT/'mod/profiles/sapphire_ptbr.lua').write_text('-- Shared Ruby PT-BR source; US Sapphire gameplay.\nreturn '+lua(profile)+'\n')
    (ROOT/'mod/profiles/sapphire_ptbr_authored.lua').write_text('-- Authored Sapphire Pokédex and corrections, pinned to US base IR.\nreturn '+lua(authored)+'\n')
    report={'shared_source_keys':len(shared),'authored_keys':len(authored),'unique_base_keys':len(unique),'authored_species':len(dex),'width_limit':208,'lines_per_page':3}
    (ROOT/'build/ptbr-qa/sapphire-profile-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('SAPPHIRE_BUILD_OK',report)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('engine','luajit','ruby-texts','sapphire-texts','source-rom'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--reference-base',type=Path,help='Reuse authored Emerald dialogue only for identical source IR')
    main(p.parse_args())
