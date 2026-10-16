from pathlib import Path
import os,subprocess,shutil
r=Path(__file__).resolve().parents[1]
subprocess.run(['python3',str(r/'tests/run_startup.py')],check=True)
qa=Path.home()/'Library/Application Support/LOVE/german-rom-mod-qa'
p=qa/'options.lua';original=p.read_bytes()
try:
 p.write_text('return {modOptions={german_rom_source={language="en",showPicker=true}}}\n')
 log=r/'build/startup-interaction.log'
 with log.open('w') as f:
  result=subprocess.run([os.environ.get('LOVE', 'love'),str(r/'build/upstream-engine')],env=dict(os.environ,POKEPORT_IDENTITY='german-rom-mod-qa',POKEPORT_VERSION='firered',POKEPORT_DRIVER=str(r/'tests/startup_interaction.lua'),QA_SCREENSHOT=str(r/'build/startup-small.png')),stdout=f,stderr=subprocess.STDOUT,timeout=90)
 assert result.returncode==0 and 'STARTUP_INTERACTION_OK' in log.read_text(),log
 print('STARTUP_INTERACTION_OK',flush=True)
finally:p.write_bytes(original)
subprocess.run(['python3',str(r/'tests/run_gb_smoke.py')],check=True)
