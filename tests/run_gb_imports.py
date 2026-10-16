from pathlib import Path
import json,subprocess,os
root=Path(__file__).resolve().parents[1]
inv=json.loads((root/'build/gb-rom-inventory.json').read_text())
for g in ['red','blue','yellow','gold','silver','crystal']:
 mf=json.loads((root/'build/upstream-engine/tools'/('rom_manifest'+('' if g=='red' else '_'+g)+'.json')).read_text())
 row=next(r for r in inv if r['sha1']==mf['romSha1'])
 log=root/f'build/{g}-gb-import.log'
 with log.open('w') as f:
  p=subprocess.run([os.environ.get('LOVE', 'love'),str(root/'build/gb-import-harness')],env=dict(os.environ,GERMAN_MOD_ROOT=str(root),POKEPORT_VERSION=g,QA_ROM=row['file']),stdout=f,stderr=subprocess.STDOUT,timeout=180)
 print(g,p.returncode,log.read_text()[-350:],flush=True)
 if p.returncode:break
