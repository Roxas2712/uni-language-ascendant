"""Private gameplay QA for Gen1 and Gen2 profiles; does not enable public profiles."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IDENTITY='german-rom-mod-ptbr-gen1-qa'

def run(a):
 if a.language=='de' and (not a.public_profile or a.mode=='live'):raise SystemExit('German comparisons require public profiles and snapshot/performance mode')
 qa=Path.home()/'Library/Application Support/LOVE'/IDENTITY;qa.mkdir(exist_ok=True)
 if not (qa/a.game).exists():shutil.copytree(Path.home()/'Library/Application Support/LOVE/german-rom-mod-gb-qa'/a.game,qa/a.game)
 dest=qa/'mods/german_rom_source';shutil.copytree(a.mod_root or ROOT/'mod',dest,dirs_exist_ok=True)
 gen=2 if a.game in ('gold','silver','crystal') else 1
 profile=ROOT/'build/ptbr-qa'/f'{a.game}-profile'
 if not a.public_profile:shutil.copytree(profile,dest/'gb/profiles'/f'{a.game}_ptbr',dirs_exist_ok=True)
 rom=(ROOT/'build/ptbr-inputs'/f'{a.game}-ptbr-candidate.gbc') if gen==2 else ROOT/('build/pokeamarelo-ptbr' if a.game=='yellow' else 'build/pokeazul-ptbr')/f'poke{a.game}.gbc'
 raw=rom.read_bytes()
 if not a.public_profile:
  manifest=json.loads((dest/'manifest.json').read_text())
  manifest['optional_imports']=[r for r in manifest['optional_imports'] if r['id']!=a.game+'_ptbr']
  manifest['optional_imports'].append({'id':a.game+'_ptbr','name':a.game+' PT-BR QA','file':a.game+'_ptbr.gbc','md5':hashlib.md5(raw).hexdigest(),'size':len(raw)})
  (dest/'manifest.json').write_text(json.dumps(manifest))
  catalog='\n'.join(line for line in (dest/'catalog.lua').read_text().splitlines() if "id='"+a.game+"_ptbr'" not in line).replace('return {',"return {\n {id='%s_ptbr',game='%s',language='pt-BR',name='Português (Brasil)',generation=1,profile='gb/profiles/%s_ptbr/profile.lua',root='gb/profiles/%s_ptbr/',runtime='gb/runtime/ptbr.lua',adapter='gb/adapters/gen1.lua'},"%(a.game,a.game,a.game,a.game),1)
  if gen==2:catalog=catalog.replace("generation=1,profile='gb/profiles/"+a.game,"generation=2,profile='gb/profiles/"+a.game).replace("runtime='gb/runtime/ptbr.lua',adapter='gb/adapters/gen1.lua'","runtime='gb/runtime/ptbr_gen2.lua',adapter='gb/adapters/gen2.lua'")
  (dest/'catalog.lua').write_text(catalog)
 imports=dest/'baseroms';imports.mkdir(exist_ok=True);(imports/(a.game+'_ptbr.gbc')).write_bytes(raw)
 (imports/'.uni-language-profile').write_text('ULA1\npreferences/notice.txt=accepted\npreferences/ascendant-intro-v1.txt=seen\npreferences/ui-language.txt=pt-BR\npreferences/'+a.game+'.txt='+a.language+'\n')
 (qa/'options.lua').write_text('return {mods={german_rom_source=true},modOptions={german_rom_source={language="auto",showPicker=false}}}')
 out=ROOT/'build/ptbr-qa';driver=ROOT/('tests/cache_snapshot.lua' if a.mode=='snapshot' else 'tests/performance.lua' if a.mode=='performance' else 'tests/gen2_ptbr_live.lua' if gen==2 else 'tests/gen1_ptbr_live.lua')
 env=dict(os.environ,POKEPORT_IDENTITY=IDENTITY,POKEPORT_VERSION=a.game,POKEPORT_DRIVER=str(driver),QA_LANGUAGE=a.language,QA_FRAMES='360',SHOT_DIR=str(out),GERMAN_MOD_ROOT=str(ROOT))
 log=out/f'{a.game}-{a.language}-{a.label or a.mode}.log'
 before={p.name:p.stat().st_mtime_ns for p in out.glob('*.png')}
 evidence={'game':a.game,'language':a.language,'mode':a.mode,'driver':driver.name,'identity':IDENTITY,'fixture':('Fresh save, injured Chikorita, Cherrygrove Pokecenter NPC interaction' if gen==2 else 'Fresh save, injured Bulbasaur, Viridian Pokecenter NPC interaction'),
           'runtime_sha256':{str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*.lua') if 'baseroms' not in p.parts},'driver_sha256':hashlib.sha256(driver.read_bytes()).hexdigest()}
 with log.open('w') as f:result=subprocess.run([a.love,str(a.engine)],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180)
 text=log.read_text();evidence['runtime_errors']=[line for line in text.splitlines() if any(term in line.lower() for term in ('draw failed:', 'update failed:', 'runtime error:', 'stack traceback:', 'hot-path pcall failed'))]
 evidence['passed']=result.returncode==0 and ('CACHE_SNAPSHOT_OK' if a.mode=='snapshot' else 'PERFORMANCE_JSON ' if a.mode=='performance' else 'GEN2_PTBR_LIVE_OK' if gen==2 else 'GEN1_PTBR_LIVE_OK') in text and not evidence['runtime_errors'];evidence['log_sha256']=hashlib.sha256(log.read_bytes()).hexdigest()
 evidence['captures_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob(a.game+'-'+a.language+'-*.png') if before.get(p.name)!=p.stat().st_mtime_ns}
 log.with_suffix('.evidence.json').write_text(json.dumps(evidence,indent=2))
 print(text[-7000:])
 if not evidence['passed']:raise SystemExit('Failed: '+str(log))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game',choices=['red','blue','yellow','gold','silver','crystal'],required=True);p.add_argument('--language',choices=['en','pt-BR','de'],default='pt-BR');p.add_argument('--engine',type=Path,required=True);p.add_argument('--love',required=True);p.add_argument('--mod-root',type=Path);p.add_argument('--public-profile',action='store_true');p.add_argument('--mode',choices=['live','performance','snapshot'],default='live');p.add_argument('--label');run(p.parse_args())
