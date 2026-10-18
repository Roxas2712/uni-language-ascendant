"""Cold/warm GBA localization and English/disabled restarts in a private identity."""
import argparse,hashlib,json,os,shutil,subprocess,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IDENTITY='ula-gba-completion-qa'
QA=Path.home()/'Library/Application Support/LOVE'/IDENTITY
DEST=QA/'mods/german_rom_source'
PROFILES=[('firered','de'),('firered','es'),('firered','it'),('leafgreen','de'),('leafgreen','es'),('leafgreen','fr'),('ruby','de'),('sapphire','de'),('emerald','de'),('emerald','es'),('emerald','fr'),('emerald','it')]
def fingerprint():
 h=hashlib.sha256()
 for p in sorted((ROOT/'mod').rglob('*')):
  if p.is_file() and p.suffix.lower()not in('.md','.html','.txt')and not p.name.endswith('QA.json'):
   h.update(str(p.relative_to(ROOT/'mod')).encode());h.update(p.read_bytes())
 h.update((ROOT/'tests/gba_completion_live.lua').read_bytes());return h.hexdigest()
def prepare():
 QA.mkdir(exist_ok=True)
 for game in ('firered','leafgreen','ruby','sapphire','emerald'):
  if not (QA/game).exists():subprocess.run(['cp','-cR',str(QA.parent/'german-rom-mod-qa'/game),str(QA/game)],check=True)
 shutil.copytree(ROOT/'mod',DEST,dirs_exist_ok=True)
 inputs=json.loads((ROOT/'build/european-inputs.json').read_text())
 imports=DEST/'baseroms';imports.mkdir(exist_ok=True)
 for game,lang in PROFILES:
  path=imports/f'{game}_{lang}.gba'
  spec=next(x for x in json.loads((ROOT/'mod/manifest.json').read_text())['optional_imports']if x['id']==f'{game}_{lang}')
  if path.exists()and hashlib.md5(path.read_bytes()).hexdigest()==spec['md5']:continue
  if lang=='de':
   # Existing private, checksum-verified development input; never packaged.
   src=ROOT.parent/'German-ROM-Mod/build/upstream-engine/mods/german_rom_source/baseroms'/path.name
   data=src.read_bytes()
  else:
   src=next(x['file']for x in inputs if x.get('game')==game and x.get('language')==lang)
   if '::' in src:
    archive,member=src.split('::');data=zipfile.ZipFile(archive).read(member)
   else:data=Path(src).read_bytes()
  assert hashlib.md5(data).hexdigest()==spec['md5']and len(data)==spec['size'],path.name
  path.write_bytes(data)
def run(profiles,modes):
 prepare();output=ROOT/'build/gba-completion-results.json';fp=fingerprint()
 results=json.loads(output.read_text())if output.exists()else[]
 results=[x for x in results if x.get('fingerprint')==fp]
 for game,lang in profiles:
  for mode in modes:
   if mode=='cold':
    cache=QA/'mod_cache/german_rom_source'
    if cache.exists():shutil.rmtree(cache)
   selected='en'if mode=='english'else lang
   (DEST/'baseroms/.uni-language-profile').write_text(f'ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt={selected}\npreferences/{game}.txt={selected}\n')
   (QA/'options.lua').write_text('return {mods={german_rom_source='+('false'if mode=='disabled'else'true')+'},modOptions={german_rom_source={language="auto",showPicker=false}}}\n')
   log=ROOT/f'build/{game}-{lang}-gba-{mode}.log'
   env=dict(os.environ,POKEPORT_VERSION=game,POKEPORT_IDENTITY=IDENTITY,POKEPORT_DRIVER=str(ROOT/'tests/gba_completion_live.lua'),GERMAN_MOD_ROOT=str(ROOT),QA_LANGUAGE=selected,QA_MODE=mode,QA_ROM=str(DEST/f'baseroms/{game}_{lang}.gba'),SHOT_DIR=str(ROOT/'build'))
   started=time.monotonic()
   try:
    with log.open('w')as f:p=subprocess.run([os.environ['LOVE'],str(ROOT/'build/upstream-engine')],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=150)
    body=log.read_text();ok=p.returncode==0 and'GBA_COMPLETION_OK'in body and'GBA_COMPLETION_FAILED'not in body and'entry failed'not in body
   except subprocess.TimeoutExpired:ok=False;body=log.read_text()
   row={'game':game,'language':lang,'mode':mode,'passed':ok,'fingerprint':fp,'log':log.name,'seconds':round(time.monotonic()-started,2)}
   for line in body.splitlines():
    if line.startswith('GBA_COMPLETION_REPORT '):row['coverage']=json.loads(line.split(' ',1)[1])
   results=[x for x in results if(x['game'],x['language'],x['mode'])!=(game,lang,mode)]+[row]
   output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
   print(game,lang,mode,'PASS'if ok else'FAIL',round(time.monotonic()-started,1),flush=True)
   if not ok:print(body[-2800:],flush=True);raise SystemExit(1)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('profiles',nargs='*');ap.add_argument('--modes',default='cold,warm');a=ap.parse_args()
 run([tuple(x.split('_'))for x in a.profiles]if a.profiles else PROFILES,a.modes.split(','))
