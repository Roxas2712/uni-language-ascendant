from pathlib import Path
import os,sys,shutil,json,subprocess
r=Path(__file__).resolve().parents[1];engine=r/'build/upstream-engine';dest=engine/'mods/german_rom_source'
shutil.copytree(r/'mod',dest,dirs_exist_ok=True)
sys.path.insert(0,str(r/'tools'));from build_gb_profiles import DE
inv=json.loads((r/'build/gb-rom-inventory.json').read_text())
for g in DE:
 imp=next(x for x in json.loads((dest/'manifest.json').read_text())['optional_imports'] if x['id']==g+'_de')
 (dest/'baseroms').mkdir(exist_ok=True)
 shutil.copyfile(next(x['file'] for x in inv if x['sha1']==DE[g]),dest/'baseroms'/imp['file'])
failed=[]
for g in sys.argv[1:] or list(DE):
 log=r/f'build/{g}-gb-smoke.log'
 with log.open('w') as f:
  try:p=subprocess.run([os.environ.get('LOVE', 'love'),str(engine)],env=dict(os.environ,POKEPORT_VERSION=g,POKEPORT_IDENTITY='german-rom-mod-gb-qa',POKEPORT_DRIVER=str(r/'tests'/os.environ.get('QA_DRIVER','gb_smoke.lua')),GERMAN_MOD_ROOT=str(r)),stdout=f,stderr=subprocess.STDOUT,timeout=75)
  except subprocess.TimeoutExpired:failed.append(g);print(g,'TIMEOUT',flush=True);continue
 print(g,p.returncode,log.read_text()[-2600:],flush=True)

 if p.returncode or 'FAILED' in log.read_text():failed.append(g)
if failed:raise SystemExit('Failed: '+', '.join(failed))
