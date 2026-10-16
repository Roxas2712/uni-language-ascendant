from pathlib import Path
import os,subprocess,shutil
r=Path(__file__).resolve().parents[1];engine=r/'build/upstream-engine'
shutil.copytree(r/'mod',engine/'mods/german_rom_source',dirs_exist_ok=True)
love=os.environ.get('LOVE', 'love')
for identity,cases in [
 ('german-rom-mod-qa',[('firered','abort',True),('firered','natural',True),('leafgreen','repeat',True),('emerald','repeat',False)]),
 ('german-rom-mod-gb-qa',[('red','natural',False),('blue','repeat',False),('gold','skip',True),('silver','repeat',True)])]:
 qa=Path.home()/'Library/Application Support/LOVE'/identity
 options=qa/'options.lua';original=options.read_bytes()
 marker=qa/'mods/german_rom_source/baseroms/.uni-language-profile'
 prior=marker.read_bytes() if marker.exists() else None
 try:
  marker.parent.mkdir(parents=True,exist_ok=True)
  marker.write_text('ULA1\npreferences/notice.txt=accepted\npreferences/ui-language.txt=de\n')
  for game,mode,picker in cases:
   if game=='gold':marker.write_text('ULA1\npreferences/notice.txt=accepted\npreferences/ui-language.txt=de\n')
   options.write_text('return {modOptions={german_rom_source={language="en",showPicker='+str(picker).lower()+'}}}\n')
   log=r/f'build/intro-{game}-{mode}.log'
   with log.open('w') as f:
    p=subprocess.run([love,str(engine)],env=dict(os.environ,POKEPORT_IDENTITY=identity,POKEPORT_VERSION=game,POKEPORT_DRIVER=str(r/'tests/intro_live.lua'),QA_INTRO_MODE=mode,QA_PICKER=str(picker).lower(),QA_SCREENSHOT=str(r/f'build/intro-{game}')),stdout=f,stderr=subprocess.STDOUT,timeout=90)
   assert p.returncode==0 and 'INTRO_LIVE_OK' in log.read_text(),log
   if mode=='abort':assert 'intro-v1.txt=seen' not in marker.read_text(),'Aborted intro consumed marker'
   else:assert 'intro-v1.txt=seen' in marker.read_text(),'First-run marker missing'
   print(game,mode,'INTRO_LIVE_OK',flush=True)
 finally:
  options.write_bytes(original)
  if prior is None:marker.unlink(missing_ok=True)
  else:marker.write_bytes(prior)
print('INTRO_SUITE_OK',flush=True)
