from pathlib import Path
import os,subprocess,shutil,json,sys,time
r=Path(__file__).resolve().parents[1]
love=os.environ.get('LOVE', 'love')
shutil.copytree(r/'mod',r/'build/upstream-engine/mods/german_rom_source',dirs_exist_ok=True)
games=sys.argv[1:] or ['red','blue','yellow','gold','silver','crystal','firered','leafgreen','ruby','sapphire','emerald']
folder=r/'build/performance';folder.mkdir(exist_ok=True)
results=[]
for g in games:
 identity='german-rom-mod-gb-qa' if g in ['red','blue','yellow','gold','silver','crystal'] else 'german-rom-mod-qa'
 options=Path.home()/'Library/Application Support/LOVE'/identity/'options.lua';original=options.read_bytes()
 try:
  # Paired, reversed second pass reduces ordering/thermal bias. Cold-start
  # compilation is separately labelled by the cacheHit emitted by the mod.
  for i,mode in enumerate(['baseline','de','en','de','baseline']):
   enabled='false' if mode=='baseline' else 'true'
   options.write_text('return {mods={german_rom_source='+enabled+'},modOptions={german_rom_source={language="'+('en' if mode=='baseline' else mode)+'",showPicker=false}}}\n')
   log=folder/f'{g}-{i}-{mode}.log'
   start=time.monotonic()
   with log.open('w') as f:
    p=subprocess.run([love,str(r/'build/upstream-engine')],env=dict(os.environ,POKEPORT_IDENTITY=identity,POKEPORT_VERSION=g,POKEPORT_DRIVER=str(r/'tests/performance.lua'),QA_LANGUAGE=mode),stdout=f,stderr=subprocess.STDOUT,timeout=180)
   rows=[x[len('PERFORMANCE_JSON '):] for x in log.read_text().splitlines() if x.startswith('PERFORMANCE_JSON ')]
   assert p.returncode==0 and len(rows)==1,log
   row=json.loads(rows[0]);row['processSeconds']=time.monotonic()-start;row['run']=i;results.append(row)
   (folder/'results.json').write_text(json.dumps(results,indent=2)+'\n')
   print(g,mode,'hit',row['cacheHit'],'mod',round(row['modLoadSeconds'],3),'update',round(row['update']['meanMs'],3),'draw',round(row['draw']['meanMs'],3),flush=True)
 finally:options.write_bytes(original)
print('PERFORMANCE_OK',len(results),flush=True)
