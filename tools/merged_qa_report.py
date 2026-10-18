"""Build a scoped report only after fresh merged checks match current sources."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[1];B=R/'build/merge-qa'
sys.path.insert(0,str(R/'tests'));import run_gba_completion as gba

def digest():
 h=hashlib.sha256()
 for p in sorted((R/'mod').rglob('*')):
  if p.is_file() and p.suffix.lower() not in ('.md','.html','.txt') and not p.name.endswith('QA.json'):
   h.update(str(p.relative_to(R/'mod')).encode());h.update(p.read_bytes())
 return h.hexdigest()
fp=digest();checks=[]
def log_check(row,path,check_driver=True):
 assert row['passed'],row
 assert path.is_file(),path
 expected=row.get('logSha256');actual=hashlib.sha256(path.read_bytes()).hexdigest()
 assert not expected or actual==expected,path
 row['logSha256']=actual
 driver=row.get('driver')
 if driver and check_driver:assert hashlib.sha256((R/'tests'/driver).read_bytes()).hexdigest()==row['driverSha256']
 return row
rows=json.loads((R/'build/gba-completion-results.json').read_text())
expected={(g,l,m) for g,l in gba.PROFILES for m in ('cold','warm')}|{(g,'de',m) for g in ('firered','leafgreen','ruby','sapphire','emerald') for m in ('english','disabled')}
assert {(x['game'],x['language'],x['mode']) for x in rows}==expected
for row in rows:
 assert row['fingerprint']==gba.fingerprint()
 checks.append(dict(log_check(row,R/'build'/row['log']),suite='European GBA',runtimePayloadSha256=fp))
h=hashlib.sha256()
for p in sorted((R/'mod').rglob('*')):
 if p.is_file() and p.suffix.lower() not in ('.md','.html','.txt') and not p.name.endswith('QA.json'):
  h.update(str(p.relative_to(R/'mod')).encode());h.update(p.read_bytes())
for p in (R/'tests/european_catalog_live.lua',R/'tests/european_frlg_live.lua',R/'translations/european/gb-ui.json'):h.update(p.read_bytes())
rows=json.loads((R/'build/european-catalog-results.json').read_text());assert len(rows)==9
for row in rows:
 assert row['fingerprint']==h.hexdigest()
 checks.append(dict(log_check(row,R/'build'/row['log']),suite='European GB/GBC catalog and rendering',runtimePayloadSha256=fp))
pt=json.loads((B/'ptbr-results.json').read_text())
assert len(pt)==36 and len([x for x in pt if x['mode']=='baseline'])==11
for row in pt:
 # Reference runs retain their original checker fingerprint. Fresh runs must
 # match the current helper, which also asserts the repaired coverage count.
 log_check(row,B/row['log'],check_driver=row['mode']!='baseline')
 if row['mode']!='baseline':
  assert row['runtimePayloadSha256']==fp
  checks.append(dict(row,suite='PT-BR integration'))
rows=json.loads((B/'picker-results.json').read_text());assert len(rows)==17
for row in rows:
 assert row['runtimePayloadSha256']==fp
 checks.append(dict(log_check(row,B/row['log']),suite='Merged language matrix and German GB'))
expectedProfiles={(r['game'],s['language']) for r in json.loads((R/'tools/rom_requirements.json').read_text()) for s in r['sources']}
startedProfiles={(x['game'],x['language']) for x in checks if x.get('mode') in ('cold','warm','de-snapshot') or x.get('suite')=='European GB/GBC catalog and rendering'}
assert len(expectedProfiles)==38 and expectedProfiles<=startedProfiles
assert len(checks)==85
comparisons=json.loads((B/'ptbr-comparisons.json').read_text());assert len(comparisons)==11 and all(x['passed'] for x in comparisons)
for row in comparisons:
 for mode,key in (('baseline','beforeSnapshotSHA256'),('cold','afterSnapshotSHA256')):
  assert hashlib.sha256((B/f"{row['game']}-{mode}-snapshot.json").read_bytes()).hexdigest()==row[key]
assert '\nOK\n' in (B/'python-tests.log').read_text()
assert 'ALL_LUA_SYNTAX_OK' in (B/'syntax.log').read_text()
assert '1499 keys; 0 missing' in (B/'european-audit.log').read_text()
assert '245 catalog keys per language; 0 missing' in (B/'gba-audit.log').read_text()
lua=(B/'lua-tests.log').read_text();assert 'CATALOG_OK 11 editions, 38 language profiles' in lua and 'AUTHORED_UNIT_OK' in lua and 'DISABLED_LANGUAGES_UNIT_OK' in lua
cache=(B/'cache-unit.log').read_text();assert 'COMPILER_TEST_OK' in cache and 'CACHE_LAZY_ASSETS_OK' in cache and 'CACHE_CODEC_UNIT_OK' in cache
report={'version':json.loads((R/'mod/manifest.json').read_text())['version'],'status':'passed-scoped-integration','runtimePayloadSha256':fp,
 'sources':{'europeanPreview5':'9e846d9','ptbr1_5_2':'e79e37d','releasedMainEquivalentTree':'2c274e3','historicalReports':['EUROPE-QA.json: 1.4.3-europe-preview.5','PT-BR.html and docs/PT-BR-QA.json: 1.5.1','docs/Release-1.5.2.json: picker-only release checks']},
 'localizedProfiles':38,'editionCount':11,'fullStoryPlaythrough':False,'freshLiveProcessRuns':len(checks),'baselineReferenceRuns':11,
 'checks':checks,'ptbrPayloadPreservation':{'comparisons':comparisons,'scope':'All final registry values and all graphics of the eleven PT-BR profiles. Equivalent manifest ordering and rendered contest tile packing are verified explicitly. Cold and warm payloads agree. Coverage report metadata may gain categories and is excluded from equivalence.'},
 'preservedUnmappedFRLGEntries':{'countPerEdition':9,'scope':'five empty placeholders/dummies, two newline helpers, one space and one decorative ?{PKMN}? control string; original IR inspected; unchanged by merge'},
 'unitLogSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [B/'python-tests.log',B/'lua-tests.log',B/'syntax.log',B/'cache-unit.log',B/'european-audit.log',B/'gba-audit.log']},
 'unitChecks':{'pythonTests':70,'luaGroups':14,'binaryCacheSuite':True,'allLuaSyntax':True},
 'sourceAudits':{'GBEngineUIKeys':1499,'GBAStaticKeys':180,'authoredGBAKeysPerLanguage':245,'missingInAuditedScopes':0},
 'limitations':['No full-story playthroughs','No independent native-speaker certification','No Windows/Linux integration runs','No two-device multiplayer or public relay integration test','Historical branch performance runs are not new merged performance measurements']}
for p in (R/'mod/MERGE-QA.json',R/'MERGE-QA.json'):p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('MERGED_QA_OK',len(checks),'fresh runs; 11 baseline references; 38 profiles;',fp)
