"""Audit literal GBA Strings calls; dynamic labels are listed separately.

This is a bounded source audit, not a claim to detect all English at runtime.
Only quoted literal expressions are evaluated by LuaJIT.
"""
import json,os,re,subprocess
from pathlib import Path
from build_gba_ui import ROOT,catalog
LITERAL=r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')'''
CALL=re.compile(r'(?:\bStrings(?:\.(?:source|lookup))?|require\(["\']src\.core\.Strings["\']\))\(\s*('+LITERAL+r'(?:\s*\.\.\s*'+LITERAL+r')*)')
def inventory():
 engine=ROOT/'build/upstream-engine';rows=[]
 for folder in ('src/core/game3','src/ui/game3'):
  for path in sorted((engine/folder).rglob('*.lua')):
   source=path.read_text()
   for m in CALL.finditer(source):
    if source[m.end():].lstrip().startswith('..'):continue
    rows.append('{'+m[1]+','+json.dumps(str(path.relative_to(engine)))+','+str(source.count('\n',0,m.start())+1)+'}')
 path=ROOT/'build/gba-ui-literals.lua';path.write_text('return {'+','.join(rows)+'}')
 literals=json.loads(subprocess.check_output([os.environ.get('LUAJIT','luajit'),str(engine/'tools/lua_to_json.lua'),str(path)]))
 result={}
 for key,path,line in literals:result.setdefault(key,[]).append({'file':path,'line':line})
 return result
if __name__=='__main__':
 sources=inventory();ui=catalog();missing={lang:sorted(set(sources)-set(rows)) for lang,rows in ui.items()}
 report={'sources':sources,'keysPerLanguage':len(ui['de']),'missing':missing}
 (ROOT/'build/gba-ui-source-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert not any(missing.values()),missing
 print('GBA_UI_SOURCE_AUDIT_OK',len(sources),'static keys;',len(ui['de']),'catalog keys per language; 0 missing')
