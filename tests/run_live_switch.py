"""In-process switch QA, isolated from all player profiles."""
from pathlib import Path
import os,json,subprocess,shutil,argparse,hashlib,time
R=Path(__file__).resolve().parents[1];SAVE=Path.home()/'Library/Application Support/LOVE';QA=SAVE/os.environ.get('QA_LIVE_IDENTITY','ula-live-switch-qa');OUT=R/'build/live-switch';OUT.mkdir(exist_ok=True,parents=True);QA.mkdir(exist_ok=True)
def prepare(game,mods=()):
 recovery=QA/'mod_cache/german_rom_source/live-switch-recovery.bin'
 if recovery.exists():recovery.unlink()
 dest=QA/'mods/german_rom_source'
 if dest.exists():shutil.rmtree(dest)
 shutil.copytree(R/'mod',dest);imports=dest/'baseroms';imports.mkdir()
 roots=[SAVE/n/'mods/german_rom_source/baseroms' for n in ['ula-merged-menu-qa','ula-asian-gen2-qa','ula-gba-completion-qa','german-rom-mod-ptbr-gen1-qa','german-rom-mod-ptbr-qa']]
 m=json.loads((R/'mod/manifest.json').read_text())
 for spec in m['optional_imports']:
  source=next((root/spec['file'] for root in roots if (root/spec['file']).exists()),None)
  if source:shutil.copyfile(source,imports/spec['file'])
 for name in ['VOXEL_ASCENDANT','kanto_ascendant','ORIGAMI_ASCENDANT']:
  path=QA/'mods'/name
  if path.exists():shutil.rmtree(path)
 sources={'vasc':('VOXEL_ASCENDANT',R.parent/'Voxel-Ascendant-3'),'kasc':('kanto_ascendant',R.parent/'Kanto-Ascendant-6'),'origami':('ORIGAMI_ASCENDANT',R.parent/'Origami-Hoenn-Innenraeume/game/mods/ORIGAMI_ASCENDANT')}
 for name in mods:
  key,source=sources[name];subprocess.run(['cp','-cR',str(source),str(QA/'mods'/key)],check=True)
 if not (QA/game).exists():
  source=next(SAVE/name/game for name in ['german-rom-mod-ptbr-gen1-qa','german-rom-mod-ptbr-qa','ula-gba-completion-qa'] if (SAVE/name/game).exists())
  subprocess.run(['cp','-cR',str(source),str(QA/game)],check=True)
 ui='invalid-language'if os.getenv('QA_BAD_UI')=='1'else'en'
 (imports/'.uni-language-profile').write_text(f'ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt={ui}\npreferences/{game}.txt=en\n')
 enabled=['german_rom_source=true']+[sources[n][0]+'=true' for n in mods]
 (QA/'options.lua').write_text('return {mods={'+','.join(enabled)+'},modOptions={german_rom_source={language="auto",showPicker=false}}}')
def run(game,mods=()):
 suffix='-'.join(mods) or 'bare'
 suffix+='-all'if os.getenv('QA_ALL')=='1'else''
 suffix+='-recovery'if os.getenv('QA_RECOVERY')=='1'else''
 suffix+='-repeat'+os.getenv('QA_REPEAT')if os.getenv('QA_REPEAT')else''
 log=OUT/f'{game}-{suffix}.log'
 opts={'nurse':os.getenv('QA_NURSE')=='1','allProfiles':os.getenv('QA_ALL')=='1','repeatPairs':int(os.getenv('QA_REPEAT','0')),'recovery':os.getenv('QA_RECOVERY')=='1','badUI':os.getenv('QA_BAD_UI')=='1','scriptedSpeed':int(os.getenv('POKEPORT_SPEED','4'))}
 evidence=OUT/f'{game}-{suffix}.evidence.json'
 if os.getenv('QA_REUSE_CURRENT')=='1'and evidence.exists():
  old=json.loads(evidence.read_text());h=hashlib.sha256()
  for path in sorted((R/'mod').rglob('*')):
   if path.is_file()and path.suffix.lower()not in('.md','.html','.txt')and not path.name.endswith('QA.json'):h.update(str(path.relative_to(R/'mod')).encode());h.update(path.read_bytes())
  valid=old.get('passed')and old.get('runtimePayloadSha256')==h.hexdigest()and old.get('testOptions')==opts and old.get('mods')==list(mods)and old.get('driverSha256')==hashlib.sha256((R/'tests/live_switch.lua').read_bytes()).hexdigest()
  valid=valid and log.exists()and old.get('logSha256')==hashlib.sha256(log.read_bytes()).hexdigest()
  for name,sha in old.get('helpersSha256',{}).items():
   if name=='gba_language_handoff.lua'and game in ('red','blue','yellow','gold','silver','crystal'):continue
   valid=valid and hashlib.sha256((R/'tests'/name).read_bytes()).hexdigest()==sha
  if valid:print('LIVE_QA_REUSE_VERIFIED',game,suffix,flush=True);return
 prepare(game,mods)
 start=time.monotonic()
 test_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in (R/'tests').glob('live_switch*.lua')}
 if game not in ('red','blue','yellow','gold','silver','crystal'):test_hashes['gba_language_handoff.lua']=hashlib.sha256((R/'tests/gba_language_handoff.lua').read_bytes()).hexdigest()
 test_hashes['ptbr_nurse_live.lua']=hashlib.sha256((R/'tests/ptbr_nurse_live.lua').read_bytes()).hexdigest()
 staged={str(p.relative_to(QA/'mods/german_rom_source')):p.read_bytes() for p in (QA/'mods/german_rom_source').rglob('*') if p.is_file() and 'baseroms'not in p.parts and p.suffix.lower()not in('.md','.html','.txt') and not p.name.endswith('QA.json')}
 print('LIVE_QA_START',game,suffix,flush=True)
 with log.open('w') as f:
  p=subprocess.run([os.environ['LOVE'],str(R/'build/upstream-engine')],env=dict(os.environ,POKEPORT_SPEED=str(opts['scriptedSpeed']),POKEPORT_IDENTITY=QA.name,POKEPORT_VERSION=game,POKEPORT_DRIVER=str(R/'tests/live_switch.lua'),GERMAN_MOD_ROOT=str(R),SHOT_DIR=str(OUT)),stdout=f,stderr=subprocess.STDOUT,timeout=1200)
 body=log.read_text();print(body[-6500:],flush=True);assert p.returncode==0 and 'LIVE_SWITCH_OK' in body,game
 for name,sha in test_hashes.items():assert hashlib.sha256((R/'tests'/name).read_bytes()).hexdigest()==sha,'Test changed during QA: '+name
 digest=hashlib.sha256()
 for path in sorted((R/'mod').rglob('*')):
  if path.is_file() and path.suffix.lower()not in('.md','.html','.txt')and not path.name.endswith('QA.json'):
   rel=str(path.relative_to(R/'mod'));assert staged[rel]==path.read_bytes(),'Runtime changed during QA: '+rel
   digest.update(rel.encode());digest.update(path.read_bytes())
 proof={'game':game,'mods':list(mods),'testOptions':{'nurse':os.getenv('QA_NURSE')=='1','allProfiles':os.getenv('QA_ALL')=='1','repeatPairs':int(os.getenv('QA_REPEAT','0')),'recovery':os.getenv('QA_RECOVERY')=='1','badUI':os.getenv('QA_BAD_UI')=='1','scriptedSpeed':int(os.getenv('POKEPORT_SPEED','4'))},'passed':True,'exitCode':p.returncode,'seconds':round(time.monotonic()-start,3),'runtimePayloadSha256':digest.hexdigest(),'log':log.name,'logSha256':hashlib.sha256(log.read_bytes()).hexdigest(),'driverSha256':hashlib.sha256((R/'tests/live_switch.lua').read_bytes()).hexdigest(),'helpersSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'tests/live_switch_state.lua',R/'tests/live_switch_nurse.lua',R/'tests/live_switch_controls.lua',R/'tests/ptbr_nurse_live.lua',R/'tests/live_switch_recovery.lua',R/'tests/gba_language_handoff.lua'] if p.name!='gba_language_handoff.lua'or game not in ('red','blue','yellow','gold','silver','crystal')}}
 (OUT/f'{game}-{suffix}.evidence.json').write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('games',nargs='*',default=['red']);ap.add_argument('--mods',default='');a=ap.parse_args()
 for game in a.games:run(game,tuple(x for x in a.mods.split(',') if x))
