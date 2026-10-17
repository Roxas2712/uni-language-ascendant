"""Preview-4 report: fresh GBA checks and explicitly inherited unchanged GB checks."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from run_gba_completion import PROFILES,fingerprint
from build_gba_ui import catalog
BASELINE='8d22d8f'
def old(path):return subprocess.check_output(['git','show',BASELINE+':'+path],cwd=ROOT)
def load(path):return json.loads((ROOT/path).read_text())
def verify_results():
 rows=load('build/gba-completion-results.json');fp=fingerprint()
 expected={(g,l,m)for g,l in PROFILES for m in('cold','warm')}
 expected|={(g,'de',m)for g in('firered','leafgreen','ruby','sapphire','emerald')for m in('english','disabled')}
 assert len(rows)==len(expected)==34
 assert {(x['game'],x['language'],x['mode'])for x in rows}==expected
 for row in rows:
  assert row['passed']and row['fingerprint']==fp,row
  body=(ROOT/'build'/row['log']).read_text()
  assert 'GBA_COMPLETION_OK'in body and'GBA_COMPLETION_FAILED'not in body and'entry failed'not in body,row
  if row['mode']in('cold','warm'):
   c=row['coverage'];assert not c['missing']and c['covered']==c['total']
   assert c['covered']==c['translated']+sum(len(c[k])for k in('authored','retainedProperNames','inapplicable'))
 for g,l in PROFILES:
  pair=[r for r in rows if(r['game'],r['language'])==(g,l)and r['mode']in('cold','warm')]
  assert len(pair)==2 and pair[0]['coverage']['cacheKey']==pair[1]['coverage']['cacheKey']
 return rows
# Preserve historical results as historical results. GB adapters and every GB
# profile are byte-identical to Preview 3. Changes in main start after the
# generation dispatch has returned for GB/GBC.
critical=['mod/gb','mod/startup.lua','mod/startup_view.lua','mod/catalog.lua','mod/adapters.lua','mod/preferences.lua','mod/options_schema.lua','mod/rom_requirements.lua','mod/locales.lua','mod/intro.lua','mod/compiler.lua']
subprocess.run(['git','diff','--exit-code',BASELINE,'--',*critical],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
assert old('mod/main.lua').split(b' local selected,profile,info')[0]==(ROOT/'mod/main.lua').read_bytes().split(b' local selected,profile,info')[0]
previous_manifest=json.loads(old('mod/manifest.json'));current_manifest=load('mod/manifest.json')
previous_manifest.pop('version');current_manifest.pop('version');assert previous_manifest==current_manifest
report=json.loads(old('EUROPE-QA.json'))
report['carriedForward']={'version':report['version'],'commit':BASELINE,'tested':report['tested'],
 'runtimePayloadSha256':report['runtimePayloadSha256'],'gbSourcesAndSharedStartupUnchanged':True,
 'checks':['liveProfiles','gbMenuProfiles','gbCatalogProfiles','gbGameplayProfiles','gbLocalLinkProfiles','processRestartChecks','translationReview','graphicsRoundtrip'],
 'note':'These Preview-3 results were not rerun for Preview 4. Fresh GBA results are listed separately.'}
for name in report['carriedForward']['checks']:
 if isinstance(report.get(name),list):
  for row in report[name]:row['originVersion']='1.4.3-europe-preview.3'
rows=verify_results();report['gbaCompletionProfiles']=[r for r in rows if r['mode']in('cold','warm')]
report['gbaRestartChecks']=[r for r in rows if r['mode']in('english','disabled')]
source=load('build/gba-ui-source-coverage.json');assert not any(source['missing'].values())
# Verify the generated distributable matches its editorial source exactly.
actual=json.loads(subprocess.check_output([os.environ.get('LUAJIT','luajit'),str(ROOT/'build/upstream-engine/tools/lua_to_json.lua'),str(ROOT/'mod/gba/ui.lua')]))
assert actual==catalog()
unit=(ROOT/'build/gba-completion-unit.log').read_text()
for marker in('UNIT_OK','STARTUP_UNIT_OK','INTRO_UNIT_OK','PREFERENCES_UNIT_OK','CATALOG_OK','EU_IDENTITIES_UNIT_OK','GBA_POLICY_UNIT_OK'):assert marker in unit
report['unitChecks'].append('gba_policy_unit')
report['version']=load('mod/manifest.json')['version'];report['tested']='2026-10-18'
h=hashlib.sha256()
for p in sorted((ROOT/'mod').rglob('*')):
 if p.is_file()and p.suffix.lower()not in('.md','.html','.txt')and not p.name.endswith('QA.json'):
  h.update(str(p.relative_to(ROOT/'mod')).encode());h.update(p.read_bytes())
report['runtimePayloadSha256']=h.hexdigest()
report['additionalChecks']['gbaCompletion']={
 'passed':True,'profiles':12,'coldAndWarmRuns':24,'englishAndDisabledRestarts':10,
 'languages':['de','es','fr','it'],'keysPerLanguage':len(actual['de']),
 'staticEngineKeysAudited':len(source['sources']),'missingAuditedKeys':0,
 'nativeRegistryMissingKeys':0,'editorialMethod':'AI editorial review plus reuse of reviewed shared UI; no independent native-speaker sign-off',
 'sourceLayer':['translations/gba/ui-extra.tsv','translations/gba/ui-common-de.tsv'],
 'checks':['actual raster glyphs and offscreen drawing','printf formatting with accented names','actual Message/TextIR pagination','fixed wonder-card and control-hint geometry','dynamic options and binding labels','settings SPEED versus Pokemon SPEED meaning','every native credit row versus regional ROM pointer data','native credit proper-name identity','script item buffers with variable operands and all three destinations','Pokemon Jump prize names','event-bus wrapper guard','unchanged species battle stats','normal save/load and custom nickname preservation','cold compilation and warm cache replay','English and disabled process restarts']}
report['gbaRegistryAccounting']={r['game']+'_'+r['language']:{k:r['coverage'][k]for k in('total','translated','covered','authored','retainedProperNames','inapplicable','missing','creditRows')}for r in rows if r['mode']=='warm'}
report['limitations']=[s for s in report['limitations']if not s.startswith('3 inherited FRLG')]
report['limitations'].append('Source audit is bounded: no claim that all dynamic, debug, launcher or unvisited engine paths are free of English.')
for path in('EUROPE-QA.json','mod/EUROPE-QA.json'):(ROOT/path).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('GBA_QA_REPORT_OK',report['version'],len(actual['de']),'keys;',len(rows),'fresh GBA runs;',h.hexdigest())
