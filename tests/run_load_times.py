from pathlib import Path
import os,subprocess,shutil,json
r=Path(__file__).resolve().parents[1]
love=os.environ.get('LOVE', 'love')
shutil.copytree(r/'mod',r/'build/upstream-engine/mods/german_rom_source',dirs_exist_ok=True)
results=[]
for identity,games in [('german-rom-mod-gb-qa',['red','blue','yellow','gold','silver','crystal']),('german-rom-mod-qa',['firered','leafgreen','ruby','sapphire','emerald'])]:
 qa=Path.home()/'Library/Application Support/LOVE'/identity
 cache=qa/'mod_cache/german_rom_source/compiled'
 # Temporarily move only the generated QA cache. Never touch user game saves.
 backup=cache.with_name('compiled-before-cold-test')
 assert not backup.exists(),backup
 if cache.exists():cache.rename(backup)
 options=qa/'options.lua';original=options.read_bytes()
 try:
  options.write_text('return {modOptions={german_rom_source={language="de",showPicker=false}}}\n')
  for g in games:
   for mode in ['cold','warm']:
    log=r/f'build/{g}-load-{mode}.log'
    with log.open('w') as f:
     p=subprocess.run([love,str(r/'build/upstream-engine')],env=dict(os.environ,POKEPORT_IDENTITY=identity,POKEPORT_VERSION=g,POKEPORT_DRIVER=str(r/'tests/load_time.lua')),stdout=f,stderr=subprocess.STDOUT,timeout=180)
    rows=[x[len('LOAD_TIME_JSON '):] for x in log.read_text().splitlines() if x.startswith('LOAD_TIME_JSON ')]
    assert p.returncode==0 and len(rows)==1,log
    row=json.loads(rows[0]);assert row['cacheHit']==(mode=='warm'),(g,mode,row)
    row['mode']=mode;results.append(row);print(g,mode,round(row['seconds'],3),flush=True)
    (r/'build/load-times.json').write_text(json.dumps(results,indent=2)+'\n')
 finally:
  options.write_bytes(original)
  # Preserve the freshly verified cache, and restore the older keys too.
  if backup.exists():
   shutil.copytree(backup,cache,dirs_exist_ok=True);shutil.rmtree(backup)
print('LOAD_TIMES_OK',len(results))
