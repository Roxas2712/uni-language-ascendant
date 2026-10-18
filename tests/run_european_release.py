"""Reproducible bounded release matrix; no ordinary player saves are used."""
import argparse,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--from-suite',choices=['catalog','menu','live','link','gameplay','lifecycle'],default='catalog')
start=ap.parse_args().from_suite
active=False
GB='red_es yellow_es gold_es gold_fr gold_it silver_es silver_fr crystal_es crystal_it'.split()
env=dict(os.environ)
for key in ['QA_GB_DRIVER','QA_SUITE','QA_MARKER','QA_MODE']:
 env.pop(key,None)
def run(script,args=(),extra=None):
 subprocess.run([sys.executable,str(ROOT/'tests'/script),*args],cwd=ROOT,env=dict(env,**(extra or {})),check=True)
for suite,driver,marker,args in [
 ('catalog','european_catalog_live.lua','EUROPEAN_CATALOG_LIVE_OK',GB),
 ('menu','european_gb_menus.lua','EUROPEAN_MENU_LIVE_OK',GB),
 ('live',None,None,[]),
 ('link','european_link_live.lua','EUROPEAN_LINK_LIVE_OK',GB),
 ('gameplay','european_gameplay_live.lua','EUROPEAN_GAMEPLAY_LIVE_OK',GB),
]:
 if suite==start:active=True
 if not active:continue
 print('EU_RELEASE_SUITE',suite,flush=True)
 extra={'QA_SUITE':suite,'QA_TIMEOUT':'180'}
 if driver:extra.update(QA_GB_DRIVER=driver,QA_MARKER=marker)
 if suite=='gameplay':extra['QA_SPEED']='4'
 run('run_european_languages.py',args,extra)
print('EU_RELEASE_SUITE lifecycle',flush=True)
run('run_european_lifecycle.py')
run('european_ui_catalog.py')
for name in ['unit','startup_unit','intro_unit','preferences_unit','catalog','european_identities_unit']:
 subprocess.run([env['LUAJIT'],str(ROOT/'tests'/f'{name}.lua'),str(ROOT)],cwd=ROOT/'build/upstream-engine',env=env,check=True)
print('EUROPEAN_RELEASE_MATRIX_OK',flush=True)
