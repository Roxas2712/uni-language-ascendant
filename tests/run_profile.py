from pathlib import Path
import os,subprocess,shutil
r=Path(__file__).resolve().parents[1];engine=r/'build/upstream-engine'
shutil.copytree(r/'mod',engine/'mods/german_rom_source',dirs_exist_ok=True)
qa=Path.home()/'Library/Application Support/LOVE/german-rom-mod-qa'
options=qa/'options.lua';original=options.read_bytes()
profile=qa/'mods/german_rom_source/baseroms/.uni-language-profile';prior=profile.read_bytes() if profile.exists() else None
try:
 profile.unlink(missing_ok=True)
 options.write_text('return {modOptions={german_rom_source={language="de",showPicker=false}}}\n')
 log=r/'build/profile-live.log'
 with log.open('w') as f:
  result=subprocess.run([os.environ.get('LOVE', 'love'),str(engine)],env=dict(os.environ,POKEPORT_IDENTITY='german-rom-mod-qa',POKEPORT_VERSION='firered',POKEPORT_DRIVER=str(r/'tests/profile_live.lua'),QA_SCREENSHOT=str(r/'build/profile')),stdout=f,stderr=subprocess.STDOUT,timeout=90)
 assert result.returncode==0 and 'PROFILE_LIVE_OK' in log.read_text(),log
 print('PROFILE_LIVE_OK')
finally:
 options.write_bytes(original)
 if prior is None:profile.unlink(missing_ok=True)
 else:profile.write_bytes(prior)
