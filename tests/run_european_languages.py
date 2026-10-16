"""Exercise every added exact-ROM profile in the isolated QA identity."""
import json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/'build/upstream-engine'
QA=Path.home()/'Library/Application Support/LOVE/ula-europe-expansion-qa'
DEST=QA/'mods/german_rom_source'
shutil.copytree(ROOT/'mod',DEST,dirs_exist_ok=True)
manifest=json.loads((DEST/'manifest.json').read_text())
inputs=json.loads((ROOT/'build/european-inputs.json').read_text())
profiles=[('red','es'),('yellow','es'),('gold','es'),('gold','fr'),('gold','it'),('silver','es'),('silver','fr'),('crystal','es'),('crystal','it'),('firered','es'),('firered','it'),('leafgreen','es'),('leafgreen','fr')]
if sys.argv[1:]:profiles=[tuple(x.split('_')) for x in sys.argv[1:]]
(DEST/'baseroms').mkdir(exist_ok=True)
for game,lang in profiles:
 row=next(x for x in inputs if x.get('game')==game and x.get('language')==lang)
 spec=next(x for x in manifest['optional_imports'] if x['id']==game+'_'+lang)
 shutil.copyfile(row['file'],DEST/'baseroms'/spec['file'])
prior=ROOT/('build/european-menu-results.json' if os.environ.get('QA_GB_DRIVER') else 'build/european-live-results.json')
results=json.loads(prior.read_text()) if sys.argv[1:] and prior.exists() else []
for game,lang in profiles:
 (DEST/'baseroms/.uni-language-profile').write_text('ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt='+lang+'\npreferences/'+game+'.txt='+lang+'\n')
 gb=game in ('red','yellow','gold','silver','crystal')
 env=dict(os.environ,POKEPORT_VERSION=game,POKEPORT_IDENTITY='ula-europe-expansion-qa',LANGUAGE_SHOT=lang,QA_LANGUAGE=lang,QA_MODE='load',SHOT_DIR=str(ROOT/'build'),POKEPORT_DRIVER=str(ROOT/'tests'/(os.environ.get('QA_GB_DRIVER','european_gb_live.lua') if gb else 'european_frlg_live.lua')),GERMAN_MOD_ROOT=str(ROOT))
 suffix='menu' if os.environ.get('QA_GB_DRIVER') else 'live'
 log=ROOT/f'build/{game}-{lang}-europe-{suffix}.log'
 try:
  with log.open('w') as f:p=subprocess.run([os.environ['LOVE'],str(ENGINE)],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=100)
  body=log.read_text();ok=p.returncode==0 and (('EUROPEAN_MENU_LIVE_OK' if os.environ.get('QA_GB_DRIVER') else 'EUROPEAN_GB_LIVE_OK') if gb else 'EUROPEAN_FRLG_LIVE_OK') in body and 'FAILED' not in body
 except subprocess.TimeoutExpired:ok=False
 results=[x for x in results if (x['game'],x['language'])!=(game,lang)]
 results.append({'game':game,'language':lang,'passed':ok,'log':log.name})
 print(game,lang,'PASS' if ok else 'FAIL',flush=True)
 if not ok:print(log.read_text()[-1800:],flush=True)
prior.write_text(json.dumps(results,indent=2)+'\n')
assert all(x['passed'] for x in results)
