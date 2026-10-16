from pathlib import Path
import os,shutil,subprocess,sys
root=Path(__file__).resolve().parents[1]
engine=root/'build/upstream-engine'
shutil.copytree(root/'mod',engine/'mods/german_rom_source',dirs_exist_ok=True)
identity='german-rom-mod-comparison'
saves=Path.home()/'Library/Application Support/LOVE'
qa=saves/identity;qa.mkdir(exist_ok=True)
shots=root/'build/comparison';shots.mkdir(exist_ok=True)
love=os.environ.get('LOVE', 'love')
for game in (sys.argv[1:] or ['firered','leafgreen','ruby','sapphire','emerald']):
 if not (qa/game).exists(): subprocess.run(['cp','-cR',str(saves/'german-rom-mod-qa'/game),str(qa/game)],check=True)
 for lang in ['en','de']:
  enabled='true' if lang=='de' else 'false'
  (qa/'options.lua').write_text('return { mods={german_rom_source='+enabled+'},modOptions={german_rom_source={language="'+lang+'",showPicker=false}} }')
  env=dict(os.environ,POKEPORT_IDENTITY=identity,POKEPORT_VERSION=game,POKEPORT_DRIVER=str(root/'tests/comparison.lua'),LANGUAGE_SHOT=lang,SHOT_DIR=str(shots),GERMAN_MOD_ROOT=str(root))
  with (shots/f'{game}-{lang}.log').open('w') as log:
   p=subprocess.run([love,str(engine)],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=150)
  lines=(shots/f'{game}-{lang}.log').read_text().splitlines()
  print(game,lang,p.returncode,flush=True)
  for line in lines:
   if 'CAPTURE_' in line or 'COMPARISON_' in line or 'entry failed' in line:print(line,flush=True)
  assert p.returncode==0 and any('COMPARISON_OK' in x for x in lines)
