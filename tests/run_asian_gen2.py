"""Isolated QA. Profiles are staged only in this disposable save identity."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from asian_gen2 import TextReader,korean_charmap,japanese_charmap,symbols,offset
from build_european_gb import lua
IDENTITY='ula-asian-gen2-qa';QA=Path.home()/'Library/Application Support/LOVE'/IDENTITY
ENGINE=ROOT/'build/upstream-engine';OUT=ROOT/'build/asian-gen2/live'

def run(game,mode):
    lang='ja' if game=='crystal' else 'ko'
    suffix='_'+lang
    QA.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True,parents=True)
    if not (QA/game).exists():
        subprocess.run(['cp','-cR',str(QA.parent/f'german-rom-mod-ptbr-gen1-qa/{game}'),str(QA/game)],check=True)
    dest=QA/'mods/german_rom_source';shutil.copytree(ROOT/'mod',dest,dirs_exist_ok=True)
    source=(ROOT.parent/'Pocket Monsters - Crystal Version (Japan).gbc') if lang=='ja' else ROOT/f'build/pokegold-kr/poke{game}.gbc';rom=source.read_bytes()
    imports=dest/'baseroms';imports.mkdir(exist_ok=True);shutil.copyfile(source,imports/(game+suffix+'.gbc'))
    if mode!='switch-english':(imports/'.uni-language-profile').write_text('ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt='+lang+'\npreferences/'+game+'.txt='+lang+'\n')
    (QA/'options.lua').write_text('return {mods={german_rom_source=true},modOptions={german_rom_source={language="auto",showPicker=false}}}\n')
    if lang=='ko':
        reader=TextReader(rom,'ko',korean_charmap(ROOT/'build/pokegold-kr'));sy=symbols(ROOT/f'build/pokegold-kr/poke{game}.sym')
    else:
        reference=ROOT.parent/'Uni-Language-Ascendant-Europe/build/pokecrystal'
        reader=TextReader(rom,'ja',japanese_charmap(reference/'constants/charmap.asm'));sy=symbols(reference/'pokecrystal.sym');graph=json.loads((ROOT/'tools/asian_gen2_refs/crystal.json').read_text());mapping=graph['mapped']
        sy={k:((int(mapping[str(offset(*v))])//16384,int(mapping[str(offset(*v))])%16384+16384)if v[0]<128 and v[1]<0x8000 and str(offset(*v))in mapping else v)for k,v in sy.items()}
    labels=('NurseMornText','NurseDayText','NurseNiteText','NurseAskHealText','NurseTakePokemonText','NurseReturnPokemonText','NurseGoodbyeText','_MartFinalPriceText','_OakText1','_OakText2','_OakText4','_OakText5','_OakText6')
    expected={k:reader.text(0x607c,stop_at=0x60bc)[1]if lang=='ja'and k=='_OakText2'else reader.text(offset(*sy[k]))[1] for k in ('NurseMornText','NurseDayText','NurseNiteText','NurseAskHealText','NurseTakePokemonText','NurseReturnPokemonText','NurseGoodbyeText','_MartFinalPriceText','_OakText1','_OakText2','_OakText4','_OakText5','_OakText6')}
    if lang=='ja':
        from asian_gen2_refs.crystal_ja_compat import TEXT
        expected.update({k:v for k,v in TEXT.items()if k.startswith('18:')})
    (OUT/(game+'-expected.json')).write_text(json.dumps(expected,ensure_ascii=False))
    if mode=='cold-verify':
        # Disposable indexes in this test identity only; payloads are retained.
        for index in (QA/'mod_cache/german_rom_source/compiled').glob('*/index.lua'):index.unlink()
    log=OUT/(game+'-'+mode+'.log')
    driver='asian_gen2_switch.lua' if mode.startswith('switch-') else 'performance.lua' if mode.startswith('perf-') else 'asian_gen2_live.lua'
    qa_language='en' if mode=='perf-en' else lang
    if mode.startswith('perf-'):(imports/'.uni-language-profile').write_text('ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt=en\npreferences/'+game+'.txt='+qa_language+'\n')
    runtime=hashlib.sha256()
    for path in sorted((ROOT/'mod').rglob('*')):
        if path.is_file() and path.suffix.lower() not in ('.md','.html','.txt') and not path.name.endswith('QA.json'):
            runtime.update(str(path.relative_to(ROOT/'mod')).encode());runtime.update(path.read_bytes())
    with log.open('w') as f:
        result=subprocess.run([os.environ.get('LOVE','love'),str(ENGINE)],env=dict(os.environ,POKEPORT_IDENTITY=IDENTITY,POKEPORT_VERSION=game,POKEPORT_DRIVER=str(ROOT/'tests'/driver),QA_MODE=mode,QA_LANGUAGE=qa_language,SHOT_DIR=str(OUT),GERMAN_MOD_ROOT=str(ROOT)),stdout=f,stderr=subprocess.STDOUT,timeout=240)
    marker='ASIAN_SWITCH_REQUEST_OK' if mode=='switch-request' else 'ASIAN_SWITCH_ENGLISH_OK' if mode=='switch-english' else 'PERFORMANCE_JSON' if mode.startswith('perf-') else 'ASIAN_GEN2_LIVE_OK'
    print('ASIAN_PROCESS_EXIT',game,mode,result.returncode);print(log.read_text()[-10000:]);assert result.returncode==0 and marker in log.read_text() and 'FAILED' not in log.read_text(),log
    proof={'game':game,'language':lang,'mode':mode,'passed':True,'runtimePayloadSha256':runtime.hexdigest(),'log':log.name,'logSha256':hashlib.sha256(log.read_bytes()).hexdigest(),'driver':driver,'driverSha256':hashlib.sha256((ROOT/'tests'/driver).read_bytes()).hexdigest(),'helpersSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'tests').glob('asian_gen2_*.lua'))}}
    (OUT/(game+'-'+mode+'.evidence.json')).write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('game',choices=['gold','silver','crystal']);p.add_argument('--mode',default='live');args=p.parse_args();run(args.game,args.mode)
