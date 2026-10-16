"""Real LÖVE runs against the stock engine, with a dedicated QA save identity."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/'build/upstream-engine'
LOVE=os.environ.get('LOVE', 'love')
IDENTITY='german-rom-mod-eu-qa'
QA=Path.home()/'Library/Application Support/LOVE'/IDENTITY

def prepare():
    QA.mkdir(exist_ok=True)
    if not (QA/'emerald').exists():
        subprocess.run(['cp','-cR',str(QA.parent/'german-rom-mod-qa/emerald'),str(QA/'emerald')],check=True)
    shutil.copytree(ROOT/'mod',QA/'mods/german_rom_source',dirs_exist_ok=True)
    imports=QA/'mods/german_rom_source/baseroms';imports.mkdir(exist_ok=True)
    for row in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms']:
        dest=imports/f'emerald_{row["language"]}.gba'
        if not dest.exists():shutil.copyfile(row['staged_file'],dest)
    de=imports/'emerald_de.gba'
    if not de.exists():shutil.copyfile(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba',de)
    return imports

def run(lang,mode,label=None):
    imports=prepare()
    (imports/'.uni-language-profile').write_text('ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt='+lang+'\npreferences/emerald.txt='+lang+'\n')
    (QA/'options.lua').write_text('return {mods={german_rom_source=true},modOptions={german_rom_source={language="auto",showPicker='+('true' if mode=='ui' else 'false')+'}}}\n')
    shots=ROOT/'build/emerald-languages';shots.mkdir(exist_ok=True)
    log=shots/f'{lang}-{label or mode}.log'
    env=dict(os.environ,POKEPORT_IDENTITY=IDENTITY,POKEPORT_VERSION='emerald',POKEPORT_DRIVER=str(ROOT/'tests'/('performance.lua' if mode=='performance' else 'emerald_release_ui.lua' if mode=='ui' else 'emerald_text_fix.lua' if mode=='fix' else 'languages_live.lua')),QA_LANGUAGE=lang,QA_MODE=mode,QA_FRAMES='360',SHOT_DIR=str(shots),GERMAN_MOD_ROOT=str(ROOT))
    with log.open('w') as f:
        result=subprocess.run([LOVE,str(ENGINE)],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240)
    lines=log.read_text().splitlines()
    for line in lines:
        if line.startswith(('LANGUAGE_','PERFORMANCE_','RELEASE_UI_','TEXT_FIX_','FIX_TEXT_')) or 'entry failed' in line:print(line,flush=True)
    assert result.returncode==0 and any(x.startswith('LANGUAGE_LOAD ' if mode=='load' else 'PERFORMANCE_JSON ' if mode=='performance' else 'RELEASE_UI_OK' if mode=='ui' else 'TEXT_FIX_OK' if mode=='fix' else 'LANGUAGE_LIVE_OK') for x in lines),log
    return log

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('language',choices=['fr','it','es','de','en']);ap.add_argument('--mode',default='load',choices=['load','live','performance','ui','fix']);ap.add_argument('--label');a=ap.parse_args();run(a.language,a.mode,a.label)
