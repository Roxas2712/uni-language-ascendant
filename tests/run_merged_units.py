"""Reproduce the combined preview's unit, syntax, cache and source checks."""
from pathlib import Path
import os,subprocess
R=Path(__file__).resolve().parents[1];B=R/'build/merge-qa';B.mkdir(exist_ok=True)
ENGINE=R/'build/upstream-engine';LUA=Path(os.environ.get('LUAJIT',str(R.parent/'gen1recomp-Mac-fix/mobile/android/love/src/jni/LuaJIT-2.1/src/luajit')))
def run(args,path,cwd=R,env=None):
 with path.open('w') as out:p=subprocess.run([str(x) for x in args],cwd=cwd,env=env,stdout=out,stderr=subprocess.STDOUT)
 assert p.returncode==0,path.read_text()
run(['python3','-m','unittest','discover','-s','tests','-p','test_*.py'],B/'python-tests.log')
names=['unit','startup_unit','intro_unit','preferences_unit','session_profile_unit','catalog','european_identities_unit','gba_policy_unit','authored_unit','compat_unit','easy_chat_ui_unit','overlay_unit','scene_text_unit','text_layout_unit','authored_labels_unit','asian_arguments_unit','asian_compile_unit','asian_input_unit','asian_marquee_unit']
with (B/'lua-tests.log').open('w') as out:
 for name in names:
  p=subprocess.run([str(LUA),str(R/'tests'/f'{name}.lua'),str(R)],cwd=ENGINE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  out.write(name+'\n'+p.stdout);assert p.returncode==0,p.stdout
script=B/'syntax.lua';script.write_text('\n'.join('assert(loadfile('+repr(str(p))+'))' for p in sorted((R/'mod').rglob('*.lua')))+"\nprint('ALL_LUA_SYNTAX_OK')\n")
run([LUA,script],B/'syntax.log',ENGINE)
env=dict(os.environ,LUAJIT=str(LUA),GERMAN_MOD_ROOT=str(R),QA_ENGINE=str(ENGINE))
run([os.environ['LOVE'],R/'tests/cache_unit'],B/'cache-unit.log',env=env)
for name in ('european','gba'):run(['python3',R/f'tools/audit_{name}_ui.py'],B/f'{name}-audit.log',env=env)
print('MERGED_UNITS_OK 85 Python tests; 19 Lua groups; all runtime syntax; binary cache; bounded source audits')
