"""Inventory static GB engine Strings calls, including literal concatenation.

The engine is a pinned local development input, not part of the mod package.
LuaJIT evaluates only quoted literal expressions collected by the scanner.
"""
import json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LITERAL=r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')'''
CALL=re.compile(r'\bStrings(?:\.source)?\(\s*('+LITERAL+r'(?:\s*\.\.\s*'+LITERAL+r')*)')
SCOPES={'battle','core','inventory','link','mods','online','pokemon','script','ui','world'}
def inventory():
 engine=ROOT/'build/upstream-engine';rows=[]
 for p in sorted((engine/'src').rglob('*.lua')):
  rel=p.relative_to(engine)
  if rel.parts[1] not in SCOPES or any(x in rel.parts for x in ('game3','g3u','gba')):continue
  source=p.read_text()
  for m in CALL.finditer(source):
   if source[m.end():].lstrip().startswith('..'):continue
   expression=m[1];first=re.match(LITERAL,expression)[0]
   rows.append('{'+expression+','+first+','+json.dumps(str(rel))+','+str(source.count('\n',0,m.start())+1)+'}')
 path=ROOT/'build/european-source-literals.lua';path.parent.mkdir(exist_ok=True)
 path.write_text('return {'+','.join(rows)+'}')
 result=json.loads(subprocess.check_output([os.environ.get('LUAJIT','luajit'),str(engine/'tools/lua_to_json.lua'),str(path)]))
 out={};joined={}
 for key,first,path,line in result:
  out.setdefault(key,[]).append({'file':path,'line':line})
  if key!=first:joined.setdefault(first,set()).add(key)
 return out,joined
if __name__=='__main__':
 out,_=inventory();ui=json.loads((ROOT/'translations/european/gb-ui.json').read_text())
 missing={k:v for k,v in out.items() if k not in ui}
 (ROOT/'build/european-source-coverage.json').write_text(json.dumps({'sources':out,'missing':missing},ensure_ascii=False,indent=2)+'\n')
 print('GB_ENGINE_UI_SOURCE_AUDIT',len(out),'keys;',len(missing),'missing')
