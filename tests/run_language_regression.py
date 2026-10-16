from pathlib import Path
import os,subprocess,shutil,json
r=Path(__file__).resolve().parents[1];engine=r/'build/upstream-engine'
shutil.copytree(r/'mod',engine/'mods/german_rom_source',dirs_exist_ok=True)
love=os.environ.get('LOVE', 'love')
for game,identity in [('red','german-rom-mod-gb-qa'),('gold','german-rom-mod-gb-qa'),('emerald','german-rom-mod-qa')]:
 qa=Path.home()/'Library/Application Support/LOVE'/identity
 options=qa/'options.lua';original=options.read_bytes()
 profile=qa/'mods/german_rom_source/baseroms/.uni-language-profile';prior=profile.read_bytes() if profile.exists() else None
 try:
  profile.parent.mkdir(parents=True,exist_ok=True)
  profile.write_text('ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt=de\n')
  options.write_text('return {modOptions={german_rom_source={language="de",showPicker=false}}}\n')
  log=r/f'build/profile-de-{game}.log'
  with log.open('w') as f:
   result=subprocess.run([love,str(engine)],env=dict(os.environ,POKEPORT_IDENTITY=identity,POKEPORT_VERSION=game,POKEPORT_DRIVER=str(r/'tests/load_time.lua')),stdout=f,stderr=subprocess.STDOUT,timeout=90)
  data=[json.loads(x.removeprefix('LOAD_TIME_JSON ')) for x in log.read_text().splitlines() if x.startswith('LOAD_TIME_JSON ')]
  assert result.returncode==0 and len(data)==1 and data[0]['cacheHit'],log
  print(game,'GERMAN_PROFILE_REGRESSION_OK',flush=True)
 finally:
  options.write_bytes(original)
  if prior is None:profile.unlink(missing_ok=True)
  else:profile.write_bytes(prior)
