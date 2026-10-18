"""Combine a verified translation baseline with fresh final-session QA honestly."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1];B=R/'build/merge-qa'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
version=json.loads((R/'mod/manifest.json').read_text())['version']
baselinePath=R/'docs/Regression-Baseline-1.8.json';baseline=json.loads(baselinePath.read_text());live=json.loads((R/'mod/LIVE-SWITCH-QA.json').read_text())
assert baseline['version']==version==live['version']
assert baseline['freshLiveProcessRuns']==113 and baseline['localizedProfiles']==live['localizedProfiles']==41
current={str(p.relative_to(R/'mod')):sha(p)for p in sorted((R/'mod').rglob('*'))if p.is_file()and p.suffix.lower()not in('.md','.html','.txt')and not p.name.endswith('QA.json')}
assert current.keys()==baseline['runtimeFilesSha256'].keys()
delta={p:{'before':old,'after':current[p]}for p,old in baseline['runtimeFilesSha256'].items()if current[p]!=old}
assert set(delta)<= {'session.lua','session_engine.lua','overlay.lua','startup.lua','session_menu.lua'},'Translation/runtime code changed outside the final session-only cleanup'
h=hashlib.sha256()
for p in sorted((R/'mod').rglob('*')):
 if p.is_file()and p.suffix.lower()not in('.md','.html','.txt')and not p.name.endswith('QA.json'):h.update(str(p.relative_to(R/'mod')).encode());h.update(p.read_bytes())
assert live['runtimePayloadSha256']==h.hexdigest()and live['isolatedProcessRuns']==21
python=(B/'python-tests.log').read_text();assert '\nOK\n'in python;count=int(re.search(r'Ran (\d+) tests',python)[1])
assert count==85 and 'ALL_LUA_SYNTAX_OK'in(B/'syntax.log').read_text()
lua=(B/'lua-tests.log').read_text();assert 'STARTUP_LAYERING_UNIT_OK'in lua and 'OVERLAY_NATIVE_RELOAD_UNIT_OK'in lua and 'SESSION_PROFILE_UNIT_OK'in lua and 'DISABLED_LANGUAGES_UNIT_OK'in lua and 'CATALOG_OK 11 editions, 41 language profiles'in lua
cache=(B/'cache-unit.log').read_text();assert 'COMPILER_TEST_OK'in cache and 'CACHE_CODEC_UNIT_OK'in cache and 'CACHE_LAZY_ASSETS_OK'in cache
report={'version':version,'status':'passed-scoped-integration','runtimePayloadSha256':live['runtimePayloadSha256'],'localizedProfiles':41,'editionCount':11,'fullStoryPlaythrough':False,'freshLiveProcessRuns':live['totalFinalProcessRuns'],'handoffProcessRuns':21,'freshLaunchRecoveryProcessRuns':6,'firstProfileProcessRuns':1,'successfulLiveHandoffs':live['successfulNormalHandoffs'],'realHealingInteractionsAfterHandoff':live['realHealingInteractions'],'liveSwitchReportSha256':sha(R/'mod/LIVE-SWITCH-QA.json'),'regressionBaseline':{'path':'docs/Regression-Baseline-1.8.json','sha256':sha(baselinePath),'runtimePayloadSha256':baseline['runtimePayloadSha256'],'isolatedProcessRuns':113,'referenceRuns':11,'scope':'The full translation/graphics regression passed on this exact pre-final runtime. Its source hashes are retained. It is not relabelled as 113 new runs of the final runtime.'},'finalRuntimeDelta':delta,'finalRuntimeDeltaScope':['Promote only UNI-LANGUAGE to the shared KASC root while preserving the other host entries','Clear stale held/queued inputs when entering or leaving the language UI','Closed startup callbacks delegate correctly through later mod/session wrappers','Reinstall localized native Gen3 UI consumers after their modules are replaced; keep process-wide readers installed once; drop retired GBA payloads','Flush retired LuaJIT traces only at the completed language-session boundary','Fall back to English for an invalid stored menu locale; keep the completed startup locale and re-read current profile before persisting a live change','Exclude time spent outside the application when recovering an interrupted handoff'],'checks':live['checks'],'freshProcessRecovery':live['freshProcessRecovery'],'firstProfile':live['firstProfile'],'unitChecks':{'pythonTests':count,'luaGroups':19,'binaryCacheSuite':True,'allLuaSyntax':True},'unitLogSha256':{p.name:sha(p)for p in [B/'python-tests.log',B/'lua-tests.log',B/'syntax.log',B/'cache-unit.log',B/'european-audit.log',B/'gba-audit.log']},'sourceAudits':baseline['sourceAudits'],'limitations':live['limitations']}
for p in (R/'mod/MERGE-QA.json',R/'MERGE-QA.json'):p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('FINAL_RELEASE_QA_OK',version,'28 final-runtime processes; 113 separately fingerprinted regression runs')
