from pathlib import Path
import os,subprocess,shutil
r=Path(__file__).resolve().parents[1]
love=os.environ.get('LOVE', 'love')
shutil.copytree(r/'mod',r/'build/upstream-engine/mods/german_rom_source',dirs_exist_ok=True)
for g,identity in [('red','german-rom-mod-gb-qa'),('gold','german-rom-mod-gb-qa'),('firered','german-rom-mod-qa')]:
 options=Path.home()/'Library/Application Support/LOVE'/identity/'options.lua';original=options.read_bytes()
 try:
  options.write_text('return {modOptions={german_rom_source={language="en",showPicker=true}}}\n')
  log=r/f'build/{g}-startup.log'
  with log.open('w') as f:
   p=subprocess.run([love,str(r/'build/upstream-engine')],env=dict(os.environ,POKEPORT_IDENTITY=identity,POKEPORT_VERSION=g,POKEPORT_DRIVER=str(r/'tests/startup_live.lua'),QA_LANGUAGE='en',QA_SCREENSHOT=str(r/f'build/{g}-startup.png')),stdout=f,stderr=subprocess.STDOUT,timeout=90)
  assert p.returncode==0 and 'STARTUP_LIVE_OK' in log.read_text(),log
  print(g,'STARTUP_LIVE_OK',flush=True)
 finally:options.write_bytes(original)
