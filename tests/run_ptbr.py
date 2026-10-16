"""Run PT-BR QA in an isolated LÖVE save identity (never the player's profile)."""
import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
IDENTITY='german-rom-mod-ptbr-qa'


def run(args):
    qa=Path.home()/'Library/Application Support/LOVE'/IDENTITY
    qa.mkdir(parents=True,exist_ok=True)
    if not (qa/'emerald').exists():
        if args.base_cache is None:
            raise SystemExit('Provide --base-cache pointing to an already imported US Emerald cache directory.')
        shutil.copytree(args.base_cache,qa/'emerald')
    shutil.copytree(ROOT/'mod',qa/'mods/german_rom_source',dirs_exist_ok=True)
    imports=qa/'mods/german_rom_source/baseroms'
    imports.mkdir(exist_ok=True)
    if args.rom:
        shutil.copyfile(args.rom,imports/'emerald_ptbr.gba')
    if not (imports/'emerald_ptbr.gba').exists():
        raise SystemExit('Provide --rom with the exact locally patched Emerald PT-BR ROM.')
    language='en' if args.mode=='menu' else args.language
    (imports/'.uni-language-profile').write_text('ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt=pt-BR\npreferences/emerald.txt='+language+'\n')
    picker='true' if args.mode in ('menu','picker') else 'false'
    (qa/'options.lua').write_text('return {mods={german_rom_source=true},modOptions={german_rom_source={language="auto",showPicker='+picker+'}}}\n')
    out=ROOT/'build/ptbr-qa';out.mkdir(parents=True,exist_ok=True)
    driver={'performance':'performance.lua','menu':'ptbr_menu_live.lua','picker':'emerald_release_ui.lua'}.get(args.mode,'languages_live.lua')
    env=dict(os.environ,POKEPORT_IDENTITY=IDENTITY,POKEPORT_VERSION='emerald',
             POKEPORT_DRIVER=str(ROOT/'tests'/driver),QA_LANGUAGE=language,QA_MODE=args.mode,
             QA_FRAMES='360',SHOT_DIR=str(out),GERMAN_MOD_ROOT=str(ROOT),QA_CHOICES=str(args.choices))
    log=out/f'{language}-{args.label or args.mode}.log'
    with log.open('w') as stream:
        process=subprocess.run([args.love,str(args.engine)],env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=240)
    marker={'load':'LANGUAGE_LOAD ','live':'LANGUAGE_LIVE_OK','menu':'PTBR_MENU_OK','picker':'RELEASE_UI_OK','performance':'PERFORMANCE_JSON '}[args.mode]
    lines=log.read_text().splitlines()
    for line in lines:
        if line.startswith(('LANGUAGE_','PTBR_','RELEASE_UI_','PERFORMANCE_')) or 'failed:' in line:print(line)
    if process.returncode!=0 or not any(line.startswith(marker) for line in lines):
        raise SystemExit('QA failed; see '+str(log))
    print('QA_LOG',log)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--love',default=os.environ.get('LOVE','love'))
    parser.add_argument('--base-cache',type=Path)
    parser.add_argument('--rom',type=Path)
    parser.add_argument('--language',default='pt-BR',choices=['en','de','fr','it','es','pt-BR'])
    parser.add_argument('--mode',default='live',choices=['load','live','performance','menu','picker'])
    parser.add_argument('--choices',type=int,default=2)
    parser.add_argument('--label')
    run(parser.parse_args())
