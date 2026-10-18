"""Exercise the merged import matrix and remaining six German GB profiles."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
R=Path(__file__).resolve().parents[1];OUT=R/'build/merge-qa';SAVE=Path.home()/'Library/Application Support/LOVE';QA=SAVE/'ula-merged-menu-qa'
QA.mkdir(exist_ok=True);dest=QA/'mods/german_rom_source'
if dest.exists():shutil.rmtree(dest)
shutil.copytree(R/'mod',dest);imports=dest/'baseroms';imports.mkdir()
requirements=json.loads((R/'tools/rom_requirements.json').read_text());manifest=json.loads((R/'mod/manifest.json').read_text())
roots=[SAVE/'ula-asian-gen2-qa/mods/german_rom_source/baseroms',SAVE/'ula-europe-expansion-qa/mods/german_rom_source/baseroms',SAVE/'ula-gba-completion-qa/mods/german_rom_source/baseroms',R.parent/'German-ROM-Mod/build/upstream-engine/mods/german_rom_source/baseroms',SAVE/'german-rom-mod-ptbr-gen1-qa/mods/german_rom_source/baseroms',SAVE/'german-rom-mod-ptbr-qa/mods/german_rom_source/baseroms']
for spec in manifest['optional_imports']:
 source=next((p/spec['file'] for p in roots if (p/spec['file']).exists()),None);assert source,spec['id']
 data=source.read_bytes();assert len(data)==spec['size'] and hashlib.md5(data).hexdigest()==spec['md5'],spec['id'];(imports/spec['file']).write_bytes(data)
h=hashlib.sha256()
for p in sorted((R/'mod').rglob('*')):
 if p.is_file() and p.suffix.lower() not in ('.md','.html','.txt') and not p.name.endswith('QA.json'):h.update(str(p.relative_to(R/'mod')).encode());h.update(p.read_bytes())
fp=h.hexdigest();results=[]
for row in requirements:
 game=row['game'];gb=row['generation']<3
 if not (QA/game).exists():
  source=SAVE/('german-rom-mod-ptbr-gen1-qa' if gb else 'german-rom-mod-ptbr-qa')/game
  subprocess.run(['cp','-cR',str(source),str(QA/game)],check=True)
 modes=['de-snapshot','picker'] if gb else ['picker']
 for mode in modes:
  lang='de' if mode=='de-snapshot' else 'en';picker=mode=='picker'
  (imports/'.uni-language-profile').write_text(f'ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt=de\npreferences/{game}.txt={lang}\n')
  (QA/'options.lua').write_text('return {mods={german_rom_source=true},modOptions={german_rom_source={language="auto",showPicker='+str(picker).lower()+'}}}')
  driver='available_languages_live.lua' if picker else 'cache_snapshot.lua';marker='AVAILABLE_LANGUAGES_OK' if picker else 'CACHE_SNAPSHOT_OK'
  available=','.join(['en']+[x['language'] for x in row['sources']]);log=OUT/f'{game}-{mode}.log'
  env=dict(os.environ,POKEPORT_IDENTITY=QA.name,POKEPORT_VERSION=game,POKEPORT_DRIVER=str(R/'tests'/driver),GERMAN_MOD_ROOT=str(R),SHOT_DIR=str(OUT),QA_LANGUAGE=lang,QA_AVAILABLE_LANGUAGES=available,QA_EXPECTED_LANGUAGE=lang)
  with log.open('w') as f:p=subprocess.run([os.environ['LOVE'],str(R/'build/upstream-engine')],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=100)
  body=log.read_text();ok=p.returncode==0 and marker in body and not any(x in body.lower() for x in ('draw failed:', 'update failed:', 'entry failed:', 'stack traceback:'))
  results.append({'game':game,'language':lang,'mode':mode,'available':available,'passed':ok,'log':log.name,'logSha256':hashlib.sha256(log.read_bytes()).hexdigest(),'runtimePayloadSha256':fp,'driver':driver,'driverSha256':hashlib.sha256((R/'tests'/driver).read_bytes()).hexdigest()})
  (OUT/'picker-results.json').write_text(json.dumps(results,indent=2)+'\n');print(game,mode,'PASS' if ok else 'FAIL',flush=True)
  if not ok:print(body[-2200:]);raise SystemExit(1)
