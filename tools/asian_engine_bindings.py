"""Bind exact engine literals to native ROM text, without distributing prose.

Only unambiguous static equivalents are automatic. Formatted engine messages
are separately authored; do not infer argument order from repeated RAM slots.
"""
import re
from gen2_engine_strings import harvest,normalize

def bind(engine,source_reader,source_symbols,native_reader,targets,recipes,fragments=None):
 candidates={};templates={}
 def normalized(text):
  text=normalize(text)
  text=re.sub(r'<(?:LINE|NEXT|CONT|PARA|SCROLL)>',' ',text)
  return ' '.join(text.split())
 for name,target in targets.items():
  if name not in recipes or name not in source_symbols:continue
  b,a=source_symbols[name];old=a if a<16384 else b*16384+a-16384
  try:
   original=source_reader.text(old)[1]
   if 'value'in recipes[name]:translated=recipes[name]['value']
   else:
    fragment=(fragments or {}).get(str(old));translated=native_reader.text(target,stop_at=fragment['stop']if fragment else None)[1]
   original=re.sub(r'<(USER|TARGET|ENEMY|PLAYER|RIVAL|MOM)>',r'{\1}',original)
   fields=re.findall(r'\{(USER|TARGET|ENEMY|PLAYER|RIVAL|MOM|STRBUF|NUM)\}',original)
   # Named roles can be reordered safely. Multiple anonymous RAM/number
   # fields cannot: keep those out until their argument roles are reviewed.
   if fields and len(fields)==len(set(fields)):
    parameters={field:f'%{i+1}$'+('d'if field=='NUM'else's')for i,field in enumerate(fields)}
    native_fields=set(re.findall(r'\{([A-Z]+)\}',translated))-{'DONE','PROMPT'}
    if native_fields<=parameters.keys():
     template=re.sub(r'\{([A-Z]+)\}',lambda m:('%d'if m[1]=='NUM'else'%s')if m[1]in parameters else m[0],original)
     templates.setdefault(normalized(template),[]).append((translated,parameters,recipes[name]))
     # TextBox also accepts named substitutions literally. Keep these roles
     # for callers that interpolate PLAYER later rather than via Strings.
     retained={key:'{'+key+'}'for key in parameters if key in ('PLAYER','RIVAL','MOM')}
     count=0;other={}
     for field in fields:
      if field not in retained:
       count+=1;other[field]=f'%{count}$'+('d'if field=='NUM'else's')
     parameters2={**retained,**other}
     template2=re.sub(r'\{([A-Z]+)\}',lambda m:('%d'if m[1]=='NUM'else'%s')if m[1]in other else m[0],original)
     templates.setdefault(normalized(template2),[]).append((translated,parameters2,recipes[name]))
   key=normalized(original)
   if not key or '{'in key or '%'in key or '{'in normalized(translated):continue
   candidates.setdefault(key,[]).append((normalized(translated),recipes[name]))
  except (AssertionError,ValueError,IndexError):continue
 out={}
 for source in harvest(engine):
  rows=candidates.get(normalized(source),[])
  if rows and len({x[0]for x in rows})==1 and '%'not in source:
   out[source]={'format':rows[0][1]}
  else:
   rows=templates.get(normalized(source),[])
   if rows and len({(normalized(t),tuple(sorted(p.items())))for t,p,_ in rows})==1:
    out[source]={'format':rows[0][2],'parameters':rows[0][1]}
 return out
