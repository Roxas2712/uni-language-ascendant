"""Run PT-BR QA in an isolated LÖVE save identity (never the player's profile)."""
import argparse
import hashlib
import json
import os
import shutil
import sys
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
IDENTITY='german-rom-mod-ptbr-qa'


def run(args):
    if args.mode=='dialogues' and args.game!='emerald':
        raise SystemExit('The field-dialogue fixtures currently target Emerald only.')
    if args.mode=='battle-dialogues' and args.game not in ('emerald','ruby','sapphire'):
        raise SystemExit('The battle-dialogue fixtures target Ruby/Sapphire/Emerald only.')
    identity=args.identity
    assert identity.startswith('german-rom-mod-ptbr-') and '/' not in identity and '\\' not in identity, 'QA identity must remain isolated'
    qa=Path.home()/'Library/Application Support/LOVE'/identity
    qa.mkdir(parents=True,exist_ok=True)
    if not (qa/args.game).exists():
        if args.base_cache is None:
            raise SystemExit('Provide --base-cache pointing to an already imported US Emerald cache directory.')
        shutil.copytree(args.base_cache,qa/args.game)
    shutil.copytree(args.mod_root or ROOT/'mod',qa/'mods/german_rom_source',dirs_exist_ok=True)
    imports=qa/'mods/german_rom_source/baseroms'
    imports.mkdir(exist_ok=True)
    source_id='ruby_ptbr' if args.game=='sapphire' else args.game+'_ptbr'
    if args.rom:
        shutil.copyfile(args.rom,imports/(source_id+'.gba'))
    if not (imports/(source_id+'.gba')).exists():
        raise SystemExit('Provide --rom with the exact locally patched Emerald PT-BR ROM.')
    if args.private_profile:
        assert args.game in ('firered','leafgreen'), 'Private Gen3 fixtures currently cover FRLG'
        installed=qa/'mods/german_rom_source'
        profile_id=args.game+'_ptbr'
        relative='profiles/'+profile_id+'_qa'
        for file in ('profile.lua','assets.lua','world.lua','authored.lua'):
            if file=='authored.lua' and not (args.private_profile/file).exists():continue
            dest=installed/relative/file;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(args.private_profile/file,dest)
        raw=(imports/(source_id+'.gba')).read_bytes()
        manifest=json.loads((installed/'manifest.json').read_text())
        manifest['optional_imports']=[r for r in manifest['optional_imports'] if r['id']!=profile_id]
        manifest['optional_imports'].append({'id':profile_id,'name':args.game+' PT-BR private QA',
            'file':profile_id+'.gba','md5':hashlib.md5(raw).hexdigest(),'size':len(raw)})
        (installed/'manifest.json').write_text(json.dumps(manifest))
        row=" {id='%s',game='%s',language='pt-BR',name='Português (Brasil)',code='%s',revision=%d,profile='%s/profile.lua',assets='%s/assets.lua',world='%s/world.lua',glyphsPath='latin_glyphs.lua'},\n" % (profile_id,args.game,raw[0xac:0xb0].decode('ascii'),raw[0xbc],relative,relative,relative)
        if (args.private_profile/'authored.lua').exists():row=row.replace("glyphsPath=","authored='"+relative+"/authored.lua',glyphsPath=")
        catalog='\n'.join(line for line in (installed/'catalog.lua').read_text().splitlines() if "id='"+profile_id+"'" not in line)
        (installed/'catalog.lua').write_text(catalog.replace('return {','return {\n'+row,1))
    language='en' if args.mode=='menu' else args.language
    (imports/'.uni-language-profile').write_text('ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt=pt-BR\npreferences/'+args.game+'.txt='+language+'\n')
    picker='true' if args.mode in ('menu','picker') else 'false'
    (qa/'options.lua').write_text('return {mods={german_rom_source=true},modOptions={german_rom_source={language="auto",showPicker='+picker+'}}}\n')
    out=ROOT/'build/ptbr-qa';out.mkdir(parents=True,exist_ok=True)
    driver={'snapshot':'cache_snapshot.lua','hatch':'ptbr_hatch_live.lua','easy-chat':'ptbr_easy_chat_live.lua','reference':'ptbr_reference_live.lua','minigames':'ptbr_minigames_live.lua','frontier':'ptbr_frontier_live.lua','side-menus':'ptbr_side_menus_live.lua','uitour':'ptbr_ui_tour.lua','gender':'frlg_gender_live.lua','braille':'ptbr_braille_live.lua','panels':'ptbr_panels_live.lua','vocabulary':'ptbr_vocabulary_live.lua','endings':'ptbr_endings_live.lua','battle-dialogues':'ptbr_battle_dialogues.lua','performance':'performance.lua','menu':'ptbr_menu_live.lua','picker':'emerald_release_ui.lua'}.get(args.mode,'languages_live.lua' if args.game=='emerald' else ('frlg_ptbr_live.lua' if args.game in ('firered','leafgreen') else 'gen3_ptbr_live.lua'))
    env=dict(os.environ,POKEPORT_IDENTITY=identity,POKEPORT_VERSION=args.game,
             POKEPORT_DRIVER=str(ROOT/'tests'/driver),QA_LANGUAGE=language,QA_MODE=args.mode,
             QA_FRAMES='360',SHOT_DIR=str(out),GERMAN_MOD_ROOT=str(ROOT),QA_CHOICES=str(args.choices),QA_GAME=args.game)
    log=out/f'{args.game+"-" if args.game!="emerald" else ""}{language}-{args.label or args.mode}.log'
    installed=qa/'mods/german_rom_source'
    before={p.name:p.stat().st_mtime_ns for p in out.glob('*.png')}
    evidence={'game':args.game,'language':language,'mode':args.mode,'passed':False,
              'identity':identity,'driver':driver,
              'test_options':{k:v for k,v in env.items() if k in ('QA_CONTEST_FULL','QA_CONTEST_ONLY','QA_NAV_ONLY','QA_SIDE_DECOR_ONLY','QA_FRONTIER_SAMPLE')},
              'runtime_sha256':{str(p.relative_to(installed)):hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(installed.rglob('*.lua')) if 'baseroms' not in p.parts},
              'driver_sha256':hashlib.sha256((ROOT/'tests'/driver).read_bytes()).hexdigest(),
              'helpers_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(list((ROOT/'tests').glob('ptbr_*.lua'))+list((ROOT/'tests').glob('frlg_*.lua'))+list((ROOT/'tests').glob('rs_ptbr_*.lua')))}}
    with log.open('w') as stream:
        process=subprocess.run([args.love,str(args.engine)],env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=args.timeout)
    # Peak resident process memory is separate from the Lua heap sampled by the driver.
    if sys.platform in ('darwin','linux'):
        import resource
        evidence['peak_process_rss_bytes']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    marker={'snapshot':'CACHE_SNAPSHOT_OK','hatch':'LANGUAGE_HATCH_OK','easy-chat':'LANGUAGE_EASY_CHAT_OK','reference':'LANGUAGE_REFERENCE_OK','minigames':'LANGUAGE_MINIGAMES_OK','frontier':'LANGUAGE_FRONTIER_OK','side-menus':'LANGUAGE_SIDE_MENUS_OK','uitour':'LANGUAGE_UI_TOUR_OK','gender':'LANGUAGE_GENDER_OK','braille':'LANGUAGE_BRAILLE_OK','panels':'LANGUAGE_PANELS_OK','load':'LANGUAGE_LOAD ','live':'LANGUAGE_LIVE_OK','smoke':'LANGUAGE_LIVE_OK','dialogues':'LANGUAGE_DIALOGUES_OK','battle-dialogues':'LANGUAGE_BATTLE_DIALOGUES_OK','menu':'PTBR_MENU_OK','picker':'RELEASE_UI_OK','performance':'PERFORMANCE_JSON ','endings':'LANGUAGE_ENDINGS_OK','vocabulary':'LANGUAGE_VOCABULARY_OK'}[args.mode]
    lines=log.read_text().splitlines()
    evidence['runtime_errors']=[line for line in lines if any(term in line.lower() for term in ('draw failed:', 'update failed:', 'runtime error:', 'stack traceback:', 'hot-path pcall failed'))]
    evidence['passed']=process.returncode==0 and any(line.startswith(marker) for line in lines) and not evidence['runtime_errors']
    evidence['log_sha256']=hashlib.sha256(log.read_bytes()).hexdigest()
    shot_mode={'hatch':'hatch','easy-chat':'easy-chat','minigames':'minigame','uitour':'ui','reference':'reference'}.get(args.mode)
    shot_prefix=args.game+'-'+language+'-'+shot_mode+'-' if shot_mode else None
    game_prefixes=(args.game+'-'+language+'-',('' if args.game=='emerald' else args.game+'-')+language+'-')
    evidence['captures_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.png')
        if before.get(p.name)!=p.stat().st_mtime_ns and p.name.startswith(game_prefixes)
        and (not shot_prefix or p.name.startswith(shot_prefix))}
    log.with_suffix('.evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    for line in lines:
        if line.startswith(('LANGUAGE_','PTBR_','RELEASE_UI_','PERFORMANCE_')) or 'failed:' in line:print(line)
    if not evidence['passed']:
        raise SystemExit('QA failed; see '+str(log))
    print('QA_LOG',log)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mod-root',type=Path,help='Alternate runtime for controlled before/after QA')
    parser.add_argument('--game',default='emerald',choices=['emerald','ruby','sapphire','firered','leafgreen'])
    parser.add_argument('--identity',default=IDENTITY,help='Dedicated isolated QA profile; use distinct identities for independent functional runs')
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--love',default=os.environ.get('LOVE','love'))
    parser.add_argument('--base-cache',type=Path)
    parser.add_argument('--rom',type=Path)
    parser.add_argument('--private-profile',type=Path,help='Private FRLG recipe directory; never changes the shipped catalog')
    parser.add_argument('--language',default='pt-BR',choices=['en','de','fr','it','es','pt-BR'])
    parser.add_argument('--mode',default='live',choices=['snapshot','hatch','easy-chat','reference','load','live','smoke','dialogues','battle-dialogues','performance','menu','picker','endings','vocabulary','panels','braille','gender','uitour','side-menus','frontier','minigames'])
    parser.add_argument('--choices',type=int,default=2)
    parser.add_argument('--label')
    parser.add_argument('--timeout',type=int,default=240)
    run(parser.parse_args())
