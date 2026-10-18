"""Produce the distributable QA summary only from completed private runs."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
def results(suite,count):
 rows=load(f'build/european-{suite}-results.json')
 assert len(rows)==count and all(x['passed'] for x in rows),(suite,rows)
 assert len({(x['game'],x.get('language',x.get('mode')))for x in rows})==count
 if suite!='lifecycle':
  assert len({x['fingerprint'] for x in rows})==1
  digest=hashlib.sha256()
  for path in sorted((ROOT/'mod').rglob('*')):
   if path.is_file() and path.suffix.lower() not in ('.md','.html','.txt') and not path.name.endswith('QA.json'):
    digest.update(str(path.relative_to(ROOT/'mod')).encode());digest.update(path.read_bytes())
  driver={'live':'european_gb_live.lua','menu':'european_gb_menus.lua','catalog':'european_catalog_live.lua','gameplay':'european_gameplay_live.lua','link':'european_link_live.lua'}[suite]
  for path in [ROOT/'tests'/driver,ROOT/'tests/european_frlg_live.lua',ROOT/'translations/european/gb-ui.json']:digest.update(path.read_bytes())
  assert rows[0]['fingerprint']==digest.hexdigest(),('Stale QA result',suite)
 for row in rows:
  body=(ROOT/'build'/row['log']).read_text()
  assert 'FAILED' not in body and 'TEST_FAIL' not in body,row
 return rows
ui=load('translations/european/gb-ui.json')
source=load('build/european-source-coverage.json');assert not source['missing']
gfx=(ROOT/'build/european-final-gfx.log').read_text()
images=int(re.search(r'EU_GFX_ROUNDTRIP_OK\s+(\d+)',gfx)[1]);assert images==339
matrix=(ROOT/'build/european-release-matrix.log').read_text()
assert 'EUROPEAN_RELEASE_MATRIX_OK' in matrix,'Matrix has not completed'
checks=['unit','startup_unit','intro_unit','preferences_unit','catalog','european_identities_unit']
# A payload digest independent of test-driver fingerprints; docs are omitted
# because this very report is copied into the mod after all executable checks.
h=hashlib.sha256()
for p in sorted((ROOT/'mod').rglob('*')):
 if p.is_file() and p.suffix.lower() not in ('.md','.html','.txt') and not p.name.endswith('QA.json'):
  h.update(str(p.relative_to(ROOT/'mod')).encode());h.update(p.read_bytes())
report={
 'version':load('mod/manifest.json')['version'],'tested':'2026-10-17',
 'platform':'macOS / LÖVE','baseline':'5843925',
 'engineCommit':load('compatibility/upstream.json')['commit'],
 'runtimePayloadSha256':h.hexdigest(),'unitChecks':checks,
 'liveProfiles':results('live',13),'gbMenuProfiles':results('menu',9),
 'gbCatalogProfiles':results('catalog',9),'gbGameplayProfiles':results('gameplay',9),
 'gbLocalLinkProfiles':results('link',9),'processRestartChecks':results('lifecycle',10),
 'translationReview':{'method':'Complete AI editorial pass; no independent native-speaker certification',
  'keysPerLanguage':len(ui),'languages':['es','fr','it'],'staticEngineKeysAudited':len(source['sources']),
  'missingAuditedKeys':0,'sourceLayer':'translations/european/gb-ui-overrides.tsv'},
 'additionalChecks':{
  'uiCatalog':{'passed':True,'keysPerLanguage':len(ui),'profileCount':9,'checks':['all compiled strings match reviewed source','printf/brace/control identities','exact whitespace padding','fixed field geometry','actual raster glyphs and TextBox pagination','native Gen2 descriptions and 251 Pokedex entries','fixed and composed radio lines']},
  'graphicsRoundtrip':{'passed':True,'profiles':7,'images':images,'checks':['every RGBA pixel','tile flips','transparent color zero','image dimensions','native credits and diploma art']}},
 'graphicsRecipes':{g+'_'+l:79 if g!='crystal' else 85 for g,l in [('gold','es'),('gold','fr'),('gold','it'),('silver','es'),('silver','fr'),('crystal','es'),('crystal','it')]},
 'gbGameplayChecks':['real nurse healing and status cure','wild battle input through win callback','normal save writer and reload','persisted native NPC/gift identities','saved player/nickname/custom box name protection','native diploma render and credits completion'],
 'gameplaySpeed':'4X for full matrix; selected setup checks also ran at 1X',
 'localLinkScope':'Two genuine ENet endpoints on localhost; handshake, accented names, strict mon rebuild, and all 64 native NPC trade records. No public relay or full two-device link battle tested.',
 'nativeIdentities':{'npcTradeRows':64,'gen2ShuckleProfiles':7,'crystalOddEggProfiles':2,'gen2SpearowScriptProfiles':7,'gen1TrainerOTProfiles':2},
 'limitations':['No independent native-speaker sign-off','No complete manual playthrough or exhaustive battle/special-event coverage','Windows/Linux not run','No public relay or full two-device link battle','PT-BR development not merged','3 inherited FRLG English pluralization helper keys (sPluralTxt/sText_IES/sText_S) and 2 existing Emerald English credits keys remain'],
 'privateInputs':'No ROMs, saves, extracted image files or compilation caches are included in the ZIP.'}
for target in ['EUROPE-QA.json','mod/EUROPE-QA.json']:(ROOT/target).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('EUROPEAN_QA_REPORT_OK',report['version'],len(ui),images,h.hexdigest())
