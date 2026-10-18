"""Validate current-process evidence before publishing live-switch claims."""
from pathlib import Path
import hashlib,json,re,subprocess
R=Path(__file__).resolve().parents[1];B=R/'build/live-switch';version=json.loads((R/'mod/manifest.json').read_text())['version']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
h=hashlib.sha256()
for p in sorted((R/'mod').rglob('*')):
 if p.is_file()and p.suffix.lower()not in('.md','.html','.txt')and not p.name.endswith('QA.json'):h.update(str(p.relative_to(R/'mod')).encode());h.update(p.read_bytes())
fp=h.hexdigest();requirements=json.loads((R/'tools/rom_requirements.json').read_text());games=[r['game']for r in requirements]
expected=[(g,'bare-all')for g in games]+[(g,'vasc-kasc')for g in ('red','gold')]+[('red','vasc'),('emerald','origami')]+[(g,'bare-recovery')for g in ('red','gold','emerald')]+[(g,'bare-repeat3')for g in ('red','gold','emerald')]
checks=[];switches=[];healing=0;profiles=set()
for game,suffix in expected:
 p=B/f'{game}-{suffix}.evidence.json';row=json.loads(p.read_text());assert row['passed']and row['exitCode']==0 and row['runtimePayloadSha256']==fp,p
 assert row['driverSha256']==sha(R/'tests/live_switch.lua'),p
 unused_helpers={}
 for helper,digest in row['helpersSha256'].items():
  # This helper is only executed in the Gen3 branch of the unchanged driver.
  if helper=='gba_language_handoff.lua'and game in ('red','blue','yellow','gold','silver','crystal'):unused_helpers[helper]=digest;continue
  assert sha(R/'tests'/helper)==digest,helper
 if unused_helpers:
  row['nonExecutedHelpersAtCaptureSha256']=unused_helpers
  row['helpersSha256']={k:v for k,v in row['helpersSha256'].items()if k not in unused_helpers}
 log=B/row['log'];assert sha(log)==row['logSha256'];body=log.read_text();assert 'LIVE_SWITCH_OK\t'+game in body
 for marker in ('LIVE_MENU_ROUTE_OK','LIVE_IMPORT_OK','LIVE_CONTROLS_OK'):assert marker in body,(p,marker)
 assert not any(x in body for x in ('LIVE_SWITCH_FAILED','Font: no glyph','entry failed:','update failed:','draw failed:')),p
 seen=[]
 for line in body.splitlines():
  if line.startswith('LIVE_SWITCH_APPLIED\t'):
   values=line.split('\t');lang=values[2];seen.append(lang)
   assert 'LIVE_SWITCH_STATE_OK\t'+lang in body
   switches.append({'game':game,'language':lang,'combination':suffix,'secondsIncluding60SettlingFrames':float(values[values.index('seconds')+1]),'luaKiB':float(values[values.index('luaKiB')+1]),'textureBytes':int(values[values.index('textureBytes')+1])})
 if game in ('firered','leafgreen','ruby','sapphire','emerald'):
  for lang in seen:assert 'LIVE_GBA_UI_OK\t'+game+'\t'+lang in body,(p,lang,'Native UI consumers not checked')
 if suffix=='bare-all':
  wanted={s['language']for r in requirements if r['game']==game for s in r['sources']}|{'en'}
  assert set(seen)==wanted and len(seen)==len(wanted),(p,seen,wanted)
  profiles.update((game,lang)for lang in seen if lang!='en')
 if row['testOptions']['nurse']:
  for lang in seen:
   assert ('LIVE_NURSE_OK\t'+game+'\t'+lang in body)or('LANGUAGE_HEALING_OK\t'+lang in body),(p,lang)
  healing+=len(seen)
 if suffix=='bare-recovery':
  assert 'LIVE_ROLLBACK_OK\t'+game in body and 'LIVE_RECOVERY_OK\t'+game in body
 if suffix=='bare-repeat3':
  assert seen[-6:]==['de','en']*3
  samples=[x for x in switches if x['game']==game and x['combination']==suffix]
  # Compare equivalent warmed language states, excluding the initial pair.
  for lang in ('de','en'):
   steady=[x for x in samples[-4:]if x['language']==lang]
   assert len(steady)==2
   assert steady[-1]['luaKiB']-steady[0]['luaKiB']<2048,(game,lang,'Lua heap grows after warm-up',steady)
   assert steady[-1]['textureBytes']-steady[0]['textureBytes']<1048576,(game,lang,'GPU memory grows after warm-up',steady)
 row['languages']=seen;row['loadedModVersions']=dict(re.findall(r'loaded mod ([^\s]+) ([^\s]+)',body))
 for requested in row['mods']:
  wanted={'vasc':'VOXEL_ASCENDANT','kasc':'kanto_ascendant','origami':'ORIGAMI_ASCENDANT'}[requested]
  assert wanted in row['loadedModVersions'],(p,'Requested compatibility mod did not load',wanted)
 if 'origami'in row['mods']:assert 'LIVE_MENU_ROUTE_OK\tOrigami Ascendant'in body
 elif 'kasc'in row['mods']and game=='red':assert 'LIVE_MENU_ROUTE_OK\tKanto Ascendant'in body
 elif 'kasc'in row['mods']:assert re.search(r'LIVE_MENU_ROUTE_OK\tfallback hub\t[2-9]',body)
 elif 'vasc'in row['mods']:assert re.search(r'LIVE_MENU_ROUTE_OK\tfallback hub\t[2-9]',body)
 row['menuRoute']=re.search(r'LIVE_MENU_ROUTE_OK\t([^\n]+)',body)[1]
 checks.append(row)
assert len(profiles)==41 and len(checks)==21
restart=json.loads((B/'restart-results.json').read_text())
assert {(r['game'],r['mode'])for r in restart}=={(g,m)for g in ('red','gold','emerald')for m in ('write','resume')}
for r in restart:
 assert r['passed']and r['runtimePayloadSha256']==fp and r['driverSha256']==sha(R/'tests/interrupted_language_restart.lua')
 assert r['logSha256']==sha(B/r['log'])
 marker='INTERRUPTED_BACKUP_WRITTEN'if r['mode']=='write'else'INTERRUPTED_FRESH_PROCESS_RECOVERY_OK'
 assert marker in (B/r['log']).read_text()
first=json.loads((B/'initial-profile.evidence.json').read_text())
assert first['passed']and first['exitCode']==0 and first['runtimePayloadSha256']==fp
assert first['logSha256']==sha(B/first['log'])and'INITIAL_LANGUAGE_PROFILE_OK'in(B/first['log']).read_text()
for helper,digest in first['helpersSha256'].items():assert sha(R/'tests'/helper)==digest
engine=R/'build/upstream-engine'
engine_commit=subprocess.check_output(['git','-C',str(engine),'rev-parse','HEAD'],text=True).strip()
assert not subprocess.check_output(['git','-C',str(engine),'status','--porcelain','-uno'],text=True).strip(),'Engine changed during the release QA scope'
report={'engine':{'repository':'https://github.com/bryanthaboi/gen1recomp','commit':engine_commit,'trackedCheckoutClean':True},'version':version,'status':'passed-scoped-live-switch','runtimePayloadSha256':fp,'isolatedProcessRuns':len(checks),'restartProcessRuns':len(restart),'totalFinalProcessRuns':len(checks)+len(restart)+1,'firstProfileProcessRuns':1,'firstProfile':first,'freshProcessRecovery':restart,'localizedProfiles':len(profiles),'editionCount':len(games),'successfulNormalHandoffs':len(switches),'realHealingInteractions':healing,'menuLanguages':10,'checks':checks,'measurements':switches,'timingScope':'Request to restoration plus 60 fixed simulation steps; scripted QA runs four logic steps per presentation frame with native fixed-step driver observations. Wall time on a shared macOS machine is not an isolated loading benchmark. First compilation and cached handoffs differ.','compatibility':{'KantoAscendant':'6.7.16','VoxelAscendant':'3.0.33','testedCombinations':['Red + KASC + VASC','Gold + KASC + VASC','Red + VASC fallback hub','Emerald + installed Origami Ascendant Gen3']},'coverage':['All 41 localized profiles reached via same-process handoff and real nurse interaction, with English return in all eleven editions','Bare Gen3 handoffs also verify the four Ruby/Sapphire or five other native naming templates, 78 ability names, trainer-class labels and the native manifest consumer against the real compiled profile','Exact party/inventory/progression and custom modData comparisons in exercised states','Ten menu-language choices, Japanese/Korean/Chinese rendering captures, disabled choices, native ROM importer size/MD5/SHA-1 checks','Blocked transition during actual nurse dialogue and unsafe capture state','Fault injection: missing source after queue, successful rollback, persisted recovery restore, corrupt recovery rejection and explicit deletion in Gen1/2/3','Three repeated German/English pairs per generation with Lua/GPU memory samples'], 'limitations':['Prepared offline saves, not full-story playthroughs','No Windows/Linux/mobile native file-picker QA','No two-device or online handoffs; online rooms are blocked','Only listed Ascendant versions/combinations tested; Red uses the KASC collector, Gold uses the fallback hub with both mods loaded because no KASC menu collector is exposed in that Gen2 session','No independent native-speaker certification','Custom GBA nickname glyph rendering across different profile fonts is not certified','Memory observations include renderer caches and are not process-RSS leak certification']}
for path in (R/'mod/LIVE-SWITCH-QA.json',R/'docs/Live-Switch-QA.json'):path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('LIVE_SWITCH_QA_OK',len(checks),'processes;',len(switches),'normal handoffs;',healing,'real nurse interactions')
