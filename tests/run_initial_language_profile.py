"""True fresh-profile integration, isolated from every ordinary save."""
import os,json,hashlib,subprocess
from pathlib import Path
os.environ['QA_LIVE_IDENTITY']='ula-language-first-profile-qa'
import run_live_switch as qa
R=qa.R;qa.prepare('red');profile=qa.QA/'mods/german_rom_source/baseroms/.uni-language-profile';profile.unlink()
log=R/'build/live-switch/initial-profile.log';driver=R/'tests/initial_language_profile.lua'
def fingerprint():
 h=hashlib.sha256()
 for p in sorted((R/'mod').rglob('*')):
  if p.is_file()and p.suffix.lower()not in('.md','.html','.txt')and not p.name.endswith('QA.json'):h.update(str(p.relative_to(R/'mod')).encode());h.update(p.read_bytes())
 return h.hexdigest()
fp=fingerprint();helpers={n:hashlib.sha256((R/'tests'/n).read_bytes()).hexdigest()for n in ('initial_language_profile.lua','live_switch_nurse.lua')}
with log.open('w')as f:p=subprocess.run([os.environ['LOVE'],str(R/'build/upstream-engine')],env=dict(os.environ,POKEPORT_SPEED=os.getenv('POKEPORT_SPEED','4'),POKEPORT_IDENTITY=qa.QA.name,POKEPORT_VERSION='red',POKEPORT_DRIVER=str(driver),GERMAN_MOD_ROOT=str(R)),stdout=f,stderr=subprocess.STDOUT,timeout=360)
body=log.read_text();print(body[-3000:]);assert p.returncode==0 and'INITIAL_LANGUAGE_PROFILE_OK'in body
assert fingerprint()==fp
for name,digest in helpers.items():assert hashlib.sha256((R/'tests'/name).read_bytes()).hexdigest()==digest
row={'passed':True,'exitCode':p.returncode,'runtimePayloadSha256':fp,'helpersSha256':helpers,'log':log.name,'logSha256':hashlib.sha256(log.read_bytes()).hexdigest()}
(R/'build/live-switch/initial-profile.evidence.json').write_text(json.dumps(row,indent=2)+'\n')
print('INITIAL_LANGUAGE_PROFILE_SUITE_OK')
