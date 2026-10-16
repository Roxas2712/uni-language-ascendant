"""Run the installed QA mod with real LÖVE, in an isolated save identity."""
import argparse, os, shutil, subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser()
ap.add_argument('--love',required=True)
ap.add_argument('--base-cache',required=True)
a=ap.parse_args()
engine=root/'build/upstream-engine'
shutil.copytree(root/'mod',engine/'mods/german_rom_source',dirs_exist_ok=True)
failed=[]

def run(game,driver,label):
    env=os.environ.copy()
    env.update(POKEPORT_IDENTITY='german-rom-mod-qa',POKEPORT_VERSION=game,
        POKEPORT_DRIVER=str(root/'tests'/driver),GERMAN_BASE_CACHE=a.base_cache,
        GERMAN_SHOT=str(root/f'build/screenshots/{game}.png'))
    log=root/f'build/{label}.log'
    with log.open('w') as f:
        try: result=subprocess.run([a.love,str(engine)],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=75)
        except subprocess.TimeoutExpired:
            failed.append(label);print(label,'TIMEOUT',flush=True);return
    lines=log.read_text().splitlines()
    success=any('GERMAN_MOD_SMOKE_OK' in x or 'GERMAN_MOD_DISABLED_OK' in x for x in lines)
    if result.returncode or not success: failed.append(label)
    print(label,result.returncode,flush=True)
    for line in lines:
        if 'GERMAN_MOD_' in line or 'failed' in line.lower(): print(line,flush=True)

for game in ['firered','leafgreen','ruby','sapphire','emerald']: run(game,'smoke.lua',game+'-smoke')
options=Path.home()/'Library/Application Support/LOVE/german-rom-mod-qa/options.lua'
original=options.read_bytes() if options.exists() else None
try:
    options.write_text('return { mods={german_rom_source=false}, modsByVersion={leafgreen={german_rom_source=false}} }\n')
    run('leafgreen','disabled.lua','disabled-smoke')
finally:
    if original is None: options.unlink(missing_ok=True)
    else: options.write_bytes(original)
if failed: raise SystemExit('Failed: '+', '.join(failed))
