"""New-process English and disabled-mod regression, with isolated QA saves."""
import os,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
QA=Path.home()/'Library/Application Support/LOVE/ula-europe-expansion-qa'
preferences=QA/'mods/german_rom_source/baseroms/.uni-language-profile'
options=QA/'options.lua'
backup={p:p.read_bytes() if p.exists() else None for p in (preferences,options)}
results=[]
try:
 for mode in ['english','disabled']:
  options.write_text('return {mods={german_rom_source='+('false' if mode=='disabled' else 'true')+'}}\n')
  for game in ['red','yellow','gold','silver','crystal']:
   preferences.write_text('ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt=en\npreferences/'+game+'.txt=en\n')
   env=dict(os.environ,POKEPORT_VERSION=game,POKEPORT_IDENTITY='ula-europe-expansion-qa',QA_MODE=mode,POKEPORT_DRIVER=str(ROOT/'tests/european_lifecycle_live.lua'))
   log=ROOT/f'build/{game}-europe-{mode}.log'
   with log.open('w') as f:p=subprocess.run([os.environ['LOVE'],str(ROOT/'build/upstream-engine')],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=90)
   body=log.read_text();ok=p.returncode==0 and 'EUROPEAN_LIFECYCLE_OK' in body and 'FAILED' not in body
   results.append({'game':game,'mode':mode,'passed':ok,'log':log.name})
   print(game,mode,'PASS' if ok else body[-2000:],flush=True)
finally:
 for path,data in backup.items():
  if data is None:path.unlink(missing_ok=True)
  else:path.write_bytes(data)
 (ROOT/'build/european-lifecycle-results.json').write_text(json.dumps(results,indent=2)+'\n')
assert len(results)==10 and all(row['passed'] for row in results)
