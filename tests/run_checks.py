"""Verify against the isolated upstream engine and local, user-supplied ROMs."""
import argparse, os, subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser()
ap.add_argument('--love',required=True)
ap.add_argument('--luajit',required=True)
ap.add_argument('--roms',required=True)
ap.add_argument('--caches',default=str(Path.home()/'Library/Application Support/LOVE'))
a=ap.parse_args()
engine=root/'build/upstream-engine'
def run(args,**kwargs):
    subprocess.run(args,check=True,**kwargs)
for test in ['unit.lua','startup_unit.lua','intro_unit.lua','preferences_unit.lua','catalog.lua']:
    run([a.luajit,str(root/'tests'/test),str(root)],cwd=engine)
run([a.luajit,str(root/'tests/coverage.lua'),str(root),a.caches,a.roms],cwd=engine)
run(['python3',str(root/'tests/run_smoke.py'),'--love',a.love,'--base-cache',a.caches+'/german-rom-mod-qa'])
for game in ['firered','leafgreen','ruby','sapphire','emerald']:
    env=dict(os.environ,POKEPORT_IDENTITY='german-rom-mod-qa',POKEPORT_VERSION=game,
        POKEPORT_DRIVER=str(root/'tests/assets.lua'),GERMAN_MOD_ROOT=str(root))
    log=root/f'build/{game}-assets.log'
    with log.open('w') as f:
        run([a.love,str(engine)],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=90)
    text=log.read_text()
    assert 'ASSET_LIFECYCLE_OK' in text and 'ASSET_TEST_FAILED' not in text,log
    for line in text.splitlines():
        if line.startswith(('ASSET_COMPARISON','ASSET_LIFECYCLE_OK')): print(line,flush=True)
harness=root/'build/compiler-harness'
harness.mkdir(exist_ok=True)
(harness/'conf.lua').write_text('function love.conf(t) t.window=false; t.modules.graphics=false; t.modules.audio=false end\n')
# Paths are supplied by environment; the harness is test-only.
(harness/'main.lua').write_text("package.path=os.getenv('GERMAN_MOD_ROOT')..'/build/upstream-engine/?.lua;'..package.path\nfunction love.load() dofile(os.getenv('GERMAN_MOD_ROOT')..'/tests/compiler.lua')({}) end\n")
log=root/'build/compiler-test.log'
with log.open('w') as f:
    run([a.love,str(harness)],env=dict(os.environ,GERMAN_MOD_ROOT=str(root)),stdout=f,stderr=subprocess.STDOUT,timeout=30)
assert 'COMPILER_TEST_OK' in log.read_text(),log
print('ALL_CHECKS_PASSED',flush=True)
