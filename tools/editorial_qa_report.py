"""Focused editorial follow-up with current short tests; no playthrough claims."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from run_gba_completion import PROFILES,fingerprint
from build_gba_ui import catalog
from build_european_ui import TOKENS
BASELINE='ed95763'
def old(path):return subprocess.check_output(['git','show',BASELINE+':'+path],cwd=ROOT)
def load(path):return json.loads((ROOT/path).read_text())
def runtime_hash():
 h=hashlib.sha256()
 for p in sorted((ROOT/'mod').rglob('*')):
  if p.is_file()and p.suffix.lower()not in('.md','.html','.txt')and not p.name.endswith('QA.json'):
   h.update(str(p.relative_to(ROOT/'mod')).encode());h.update(p.read_bytes())
 return h.hexdigest()
def lua_table(path):
 return json.loads(subprocess.check_output([os.environ.get('LUAJIT','luajit'),str(ROOT/'build/upstream-engine/tools/lua_to_json.lua'),str(path)]))
def verify_log(row,marker):
 assert row['passed'],row
 body=(ROOT/'build'/row['log']).read_text()
 assert marker in body and not any(x in body for x in('GBA_COMPLETION_FAILED','EUROPEAN_CATALOG_LIVE_FAILED','entry failed')),row
# Only the reviewed catalog cells and version may change executable payloads.
allowed={'mod/manifest.json','mod/gba/ui.lua'}
allowed|={f'mod/gb/profiles/{p}/strings.lua'for p in('red_es','yellow_es','gold_es','gold_fr','gold_it','silver_es','silver_fr','crystal_es','crystal_it')}
changed=subprocess.check_output(['git','diff','--name-only',BASELINE,'--','mod'],cwd=ROOT).decode().splitlines()
changed=[p for p in changed if Path(p).suffix.lower()not in('.md','.html','.txt')and not Path(p).name.endswith('QA.json')]
assert set(changed)<=allowed,changed
previous_manifest=json.loads(old('mod/manifest.json'));manifest=load('mod/manifest.json')
a=dict(previous_manifest);b=dict(manifest);a.pop('version');b.pop('version');assert a==b
before_gb=json.loads(old('translations/european/gb-ui.json'));gb=load('translations/european/gb-ui.json')
base_gba=ROOT/'build/editorial-baseline-gba-ui.lua';base_gba.write_bytes(old('mod/gba/ui.lua'))
before_gba=lua_table(base_gba);gba=lua_table(ROOT/'mod/gba/ui.lua');assert gba==catalog()
changes=[]
for key,values in gb.items():
 for i,lang in enumerate(('es','fr','it')):
  if values[i]!=before_gb[key][i]:changes.append(('gb',lang,key))
for lang,rows in gba.items():
 for key,value in rows.items():
  if value!=before_gba[lang][key]:changes.append(('gba',lang,key))
expected={('gb',l,'contribution is not a table')for l in('es','fr','it')}
expected|={('gb','fr','Failed to boot %s:\n%s'),('gba','es','%s seems to be busy right now.')}
assert set(changes)==expected,changes
# Screen every authored cell, not just the corrections. Source-like casts,
# company names and the Italian pronoun 'me' have explicit scoped exemptions.
shared={l:{k:v[i]for k,v in gb.items()}for i,l in enumerate(('es','fr','it'))}
reviewed=[];cells=0
english=set('the with would have your you are this that these those wants received obtained choose which their empty failed another from holding already'.split())
for family,langs in {'gb':shared,'gba':gba}.items():
 for lang,rows in langs.items():
  for key,value in rows.items():
   assert value.strip()and sorted(TOKENS.findall(key))==sorted(TOKENS.findall(value)),(family,lang,key)
   cleaned=re.sub(r'\{[^}]*\}|<[^>]*>|%[-+ #0-9.$]*[A-Za-z]','',value)
   words=re.findall(r'[A-Za-z]{2,}',cleaned)
   same_phrase=key==value and len(words)>=3
   copied_english=set(w.lower()for w in words)&english
   if same_phrase or copied_english:
    assert family=='gb'and key in('GENGAR VS NIDORINO','GAME FREAK inc.','me, DJ LILY!'),(family,lang,key,value)
    assert key!='me, DJ LILY!'or lang=='it'
    reason='Company identity'if key=='GAME FREAK inc.'else'Italian pronoun and DJ identity'if key=='me, DJ LILY!'else'Gen1 movie fallback cast label; French Gen1 profiles are not supported in this preview'
    reviewed.append({'family':family,'language':lang,'key':key,'reason':reason})
   cells+=1
assert cells==5540,cells
rows=load('build/gba-completion-results.json');fp=fingerprint()
wanted={(g,l,m)for g,l in PROFILES for m in('cold','warm')}|{(g,'de',m)for g in('firered','leafgreen','ruby','sapphire','emerald')for m in('english','disabled')}
assert len(rows)==34 and{(r['game'],r['language'],r['mode'])for r in rows}==wanted
for row in rows:
 verify_log(row,'GBA_COMPLETION_OK');assert row['fingerprint']==fp
 if row['mode']in('cold','warm'):
  c=row['coverage'];assert not c['missing']and c['covered']==c['total']
  assert c['covered']==c['translated']+sum(len(c[k])for k in('authored','retainedProperNames','inapplicable'))
for g,l in PROFILES:
 pair=[r for r in rows if(r['game'],r['language'])==(g,l)and r['mode']in('cold','warm')]
 assert len(pair)==2 and pair[0]['coverage']['cacheKey']==pair[1]['coverage']['cacheKey']
gb_rows=load('build/european-catalog-results.json');assert len(gb_rows)==9
h=hashlib.sha256()
for p in sorted((ROOT/'mod').rglob('*')):
 if p.is_file()and p.suffix.lower()not in('.md','.html','.txt')and not p.name.endswith('QA.json'):
  h.update(str(p.relative_to(ROOT/'mod')).encode());h.update(p.read_bytes())
for p in('tests/european_catalog_live.lua','tests/european_frlg_live.lua','translations/european/gb-ui.json'):h.update((ROOT/p).read_bytes())
for row in gb_rows:verify_log(row,'EUROPEAN_CATALOG_LIVE_OK');assert row['fingerprint']==h.hexdigest()
unit=(ROOT/'build/editorial-unit.log').read_text()
for marker in('UNIT_OK','STARTUP_UNIT_OK','INTRO_UNIT_OK','PREFERENCES_UNIT_OK','CATALOG_OK','EU_IDENTITIES_UNIT_OK','GBA_POLICY_UNIT_OK'):assert marker in unit
report=json.loads(old('EUROPE-QA.json'))
report['historicalInheritance']=report['carriedForward']
report['carriedForward']={'version':report['version'],'commit':BASELINE,'tested':report['tested'],
 'checks':['liveProfiles','gbMenuProfiles','gbGameplayProfiles','gbLocalLinkProfiles','processRestartChecks','graphicsRoundtrip'],
 'engineCodeAndNativeROMRecipesUnchanged':True,'authoredCatalogCellsChanged':len(changes),
 'note':'Broader earlier GB scene/gameplay/link checks are historical. Current catalog/font checks cover all nine EU GB profiles; current GBA results are listed separately. No complete playthroughs were run.'}
report['version']=manifest['version'];report['tested']='2026-10-18';report['runtimePayloadSha256']=runtime_hash()
report['gbCatalogProfiles']=gb_rows
report['gbaCompletionProfiles']=[r for r in rows if r['mode']in('cold','warm')]
report['gbaRestartChecks']=[r for r in rows if r['mode']in('english','disabled')]
report['gbaRegistryAccounting']={r['game']+'_'+r['language']:{k:r['coverage'][k]for k in('total','translated','covered','authored','retainedProperNames','inapplicable','missing','creditRows')}for r in rows if r['mode']=='warm'}
report['editorialFollowup']={'method':'Focused second AI editorial pass plus automatic screening; no independent native-speaker certification',
 'screenedCells':cells,'gbKeysPerLanguage':len(gb),'gbaKeysPerLanguage':len(gba['de']),
 'focus':['untranslated sentences','composed fragments and multiple format arguments','cross-generation event terminology','gender-neutral player-facing wording'],
 'changedCells':[{'family':f,'language':l,'key':k}for f,l,k in sorted(changes)],
 'reviewedExceptions':reviewed,'freshGBCatalogRuns':9,'freshGBARuns':34,'unitChecks':7,'fullPlaythroughs':0}
for target in('EUROPE-QA.json','mod/EUROPE-QA.json'):(ROOT/target).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('EDITORIAL_QA_OK',report['version'],cells,'screened cells;',len(changes),'corrections; 43 short live runs; 7 unit checks;',report['runtimePayloadSha256'])
