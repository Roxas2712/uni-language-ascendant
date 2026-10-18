"""Verify all PT-BR payloads against the committed 1.5.2 runtime, privately."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tarfile
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from compare_cache_snapshots import compare
LOVE=Path(os.environ['LOVE']);ENGINE=R/'build/upstream-engine'
LUA=R.parent/'gen1recomp-Mac-fix/mobile/android/love/src/jni/LuaJIT-2.1/src/luajit'
IDENTITY='ula-merged-ptbr-qa';SAVE=Path.home()/'Library/Application Support/LOVE';QA=SAVE/IDENTITY
OUT=R/'build/merge-qa';OUT.mkdir(exist_ok=True);QA.mkdir(exist_ok=True)
BASE=OUT/'ptbr-1.5.2-source';BASE.mkdir(exist_ok=True)
archive=OUT/'baseline.tar';archive.write_bytes(subprocess.check_output(['git','archive','e79e37d','mod'],cwd=R))
with tarfile.open(archive) as t:t.extractall(BASE,filter='data')
archive.unlink()
def digest(root):
 h=hashlib.sha256()
 for p in sorted(root.rglob('*')):
  if p.is_file() and p.suffix.lower() not in ('.md','.html','.txt') and not p.name.endswith('QA.json'):
   h.update(str(p.relative_to(root)).encode());h.update(p.read_bytes())
 return h.hexdigest()
fp=digest(R/'mod');results=[]
manifest=json.loads((R/'mod/manifest.json').read_text());dest=QA/'mods/german_rom_source'
def stage(root):
 if dest.exists():shutil.rmtree(dest)
 shutil.copytree(root,dest)
 imports=dest/'baseroms';imports.mkdir()
 for game in GAMES:
  source=('ruby' if game=='sapphire' else game)+'_ptbr'
  spec=next(x for x in manifest['optional_imports'] if x['id']==source)
  parent='german-rom-mod-ptbr-gen1-qa' if game in GAMES[:6] else 'german-rom-mod-ptbr-qa'
  data=(SAVE/parent/'mods/german_rom_source/baseroms'/spec['file']).read_bytes()
  assert len(data)==spec['size'] and hashlib.md5(data).hexdigest()==spec['md5'],game
  (imports/spec['file']).write_bytes(data)
def run(game,mode,driver='merged_snapshot_live.lua',marker='CACHE_SNAPSHOT_OK'):
 (dest/'baseroms/.uni-language-profile').write_text(f'ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt=pt-BR\npreferences/{game}.txt=pt-BR\n')
 (QA/'options.lua').write_text('return {mods={german_rom_source=true},modOptions={german_rom_source={language="auto",showPicker=false}}}')
 log=OUT/f'{game}-ptbr-{mode}.log'
 env=dict(os.environ,POKEPORT_IDENTITY=IDENTITY,POKEPORT_VERSION=game,POKEPORT_DRIVER=str(R/'tests'/driver),GERMAN_MOD_ROOT=str(R),SHOT_DIR=str(OUT),QA_LANGUAGE='pt-BR',QA_CACHE_STATE='warm' if mode=='warm' else 'cold',QA_MODE='smoke',QA_EXPECT_COVERED='0' if mode=='baseline' else '1')
 # Make reference/cold checks reproducible even when this disposable QA
 # identity contains a cache from an earlier run. Retain old indexes for the
 # later baseline payload comparison; never touch ordinary player caches.
 indexes={}
 if mode in ('baseline','cold'):
  for index in (QA/'mod_cache/german_rom_source/compiled').glob('*/index.lua'):
   indexes[index]=index.read_bytes();index.unlink()
 try:
  with log.open('w') as f:p=subprocess.run([str(LOVE),str(ENGINE)],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=200)
 finally:
  for index,data in indexes.items():
   if not index.exists():index.write_bytes(data)
 text=log.read_text();ok=p.returncode==0 and marker in text and not any(x in text.lower() for x in ('draw failed:', 'update failed:', 'entry failed:', 'stack traceback:','hot-path pcall failed'))
 row={'game':game,'language':'pt-BR','mode':mode,'passed':ok,'log':log.name,'logSha256':hashlib.sha256(log.read_bytes()).hexdigest(),'runtimePayloadSha256':digest(BASE/'mod') if mode=='baseline' else fp,'driver':driver,'driverSha256':hashlib.sha256((R/'tests'/driver).read_bytes()).hexdigest()};results.append(row)
 (OUT/'ptbr-results.json').write_text(json.dumps(results,indent=2)+'\n');print(game,mode,'PASS' if ok else 'FAIL',flush=True)
 if not ok:print(text[-3500:],flush=True);raise SystemExit(1)
 if marker=='CACHE_SNAPSHOT_OK':shutil.copyfile(OUT/f'{game}-pt-BR-snapshot.json',OUT/f'{game}-{mode}-snapshot.json')
GAMES=['red','blue','yellow','gold','silver','crystal','firered','leafgreen','ruby','sapphire','emerald']
for game in GAMES:
 parent=SAVE/('german-rom-mod-ptbr-gen1-qa' if game in GAMES[:6] else 'german-rom-mod-ptbr-qa')/game
 if not (QA/game).exists():subprocess.run(['cp','-cR',str(parent),str(QA/game)],check=True)
if '--reuse-baseline' in sys.argv:
 old=json.loads((OUT/'ptbr-results.json').read_text())
 results=[x for x in old if x['mode']=='baseline']
 assert len(results)==11 and all(x['passed'] and x['runtimePayloadSha256']==digest(BASE/'mod') for x in results)
else:
 stage(BASE/'mod')
 for game in GAMES:run(game,'baseline')
stage(R/'mod')
comparisons=[]
for game in GAMES:
 run(game,'cold');run(game,'warm')
 row=compare(OUT/f'{game}-baseline-snapshot.json',OUT/f'{game}-cold-snapshot.json',QA/'mod_cache/german_rom_source',LUA,ENGINE,compare_coverage=False)
 a=json.loads((OUT/f'{game}-cold-snapshot.json').read_text());b=json.loads((OUT/f'{game}-warm-snapshot.json').read_text())
 assert a['assets']==b['assets'] and a['registries']==b['registries'],'Warm payload changed'
 comparisons.append(row);(OUT/'ptbr-comparisons.json').write_text(json.dumps(comparisons,indent=2)+'\n')
for game,driver,marker in [('red','gen1_ptbr_live.lua','GEN1_PTBR_LIVE_OK'),('gold','gen2_ptbr_live.lua','GEN2_PTBR_LIVE_OK'),('emerald','languages_live.lua','LANGUAGE_LIVE_OK')]:
 run(game,'live',driver,marker)
assert fp==digest(R/'mod'),'Runtime changed during tests'
print('MERGED_PTBR_OK 11 baseline/cold/warm payload comparisons; 3 representative live runs',flush=True)
