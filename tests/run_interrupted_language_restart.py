"""Fresh-process interruption/recovery gate, using its own disposable identity."""
import os,sys,hashlib,json,subprocess
from pathlib import Path
os.environ['QA_LIVE_IDENTITY']='ula-language-interrupted-restart-qa'
import run_live_switch as qa
R=qa.R;OUT=R/'build/live-switch';results=[]
def fingerprint():
 h=hashlib.sha256()
 for p in sorted((R/'mod').rglob('*')):
  if p.is_file()and p.suffix.lower()not in('.md','.html','.txt')and not p.name.endswith('QA.json'):h.update(str(p.relative_to(R/'mod')).encode());h.update(p.read_bytes())
 return h.hexdigest()
fp=fingerprint();driver=R/'tests/interrupted_language_restart.lua';driver_sha=hashlib.sha256(driver.read_bytes()).hexdigest()
for game in ('red','gold','emerald'):
 qa.prepare(game)
 for mode in ('write','resume'):
  log=OUT/f'{game}-interrupted-{mode}.log'
  with log.open('w')as f:p=subprocess.run([os.environ['LOVE'],str(R/'build/upstream-engine')],env=dict(os.environ,POKEPORT_SPEED=os.getenv('POKEPORT_SPEED','4'),POKEPORT_IDENTITY=qa.QA.name,POKEPORT_VERSION=game,POKEPORT_DRIVER=str(driver),GERMAN_MOD_ROOT=str(R),QA_RESTART_MODE=mode,POKEPORT_BOOT_CINEMA='1'),stdout=f,stderr=subprocess.STDOUT,timeout=360)
  body=log.read_text();marker='INTERRUPTED_BACKUP_WRITTEN'if mode=='write'else'INTERRUPTED_FRESH_PROCESS_RECOVERY_OK'
  assert p.returncode==0 and marker in body,body[-3000:]
  assert fingerprint()==fp and hashlib.sha256(driver.read_bytes()).hexdigest()==driver_sha,'Sources changed during recovery QA'
  results.append({'game':game,'mode':mode,'passed':True,'runtimePayloadSha256':fp,'driverSha256':driver_sha,'log':log.name,'logSha256':hashlib.sha256(log.read_bytes()).hexdigest()})
  print('INTERRUPTED_RESTART_OK',game,mode,flush=True)
(OUT/'restart-results.json').write_text(json.dumps(results,indent=2)+'\n')
print('INTERRUPTED_RESTART_SUITE_OK',flush=True)
