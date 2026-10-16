"""Turn the user's previous localization catalogs into ROM address recipes.

Reference translations are development inputs only. Every retained text span
must be found byte-for-byte (after the cart character map) in the supplied ROM.
No guessed addresses or source text fallbacks are emitted.
"""
from pathlib import Path
import json,subprocess,re,hashlib,bisect,os
ROOT=Path(__file__).resolve().parents[1]
REF=Path(os.environ.get('ULA_GB_REFERENCE', ROOT/'build/translation-german-universal-0'))
ENGINE=ROOT/'build/upstream-engine'
LUA=os.environ.get('LUAJIT', 'luajit')
GAMES=['red','blue','yellow','gold','silver','crystal']
DE={'red':'87d523fe1a0c548db7c5477b451ddec1eb083c06','blue':'20e72dc6f41493eee1fdd0cef54214e6c3389688','yellow':'42f3714eec6eca25200d42461ff08d57c98f6d1d','gold':'9254195d461ea942eaaa08cc4b83de3cf82aea0d','silver':'8ecc58d621faaedf2a934bd2583d527220df7bb9','crystal':'accb584293ba056152f1fd908439b019017ff2fe'}
def export(p):
 return json.loads(subprocess.check_output([LUA,str(ENGINE/'tools/lua_to_json.lua'),str(p)]))
def lua(v):
 if v is None:return 'nil'
 if isinstance(v,bool):return str(v).lower()
 if isinstance(v,(int,float)):return str(v)
 if isinstance(v,str):return json.dumps(v,ensure_ascii=False).replace('\\u000b','\\011').replace('\\u000c','\\012')
 if isinstance(v,list):return '{'+','.join(lua(x) for x in v)+'}'
 return '{'+','.join('['+lua(k)+']='+lua(x) for k,x in v.items())+'}'

def build(game):
 inv=json.loads((ROOT/'build/gb-rom-inventory.json').read_text());row=next(r for r in inv if r['sha1']==DE[game]);rom=Path(row['file']).read_bytes()
 files={}
 if game=='crystal':files.update({p.name:p for p in (REF/'editions/silver/lang').glob('*.lua')})
 files.update({p.name:p for p in (REF/f'editions/{game}/lang').glob('*.lua')})
 cats={name:export(p) for name,p in files.items()}
 if game=='crystal':
  for name,p in files.items():
   base=REF/'editions/silver/lang'/name
   if base.exists() and name not in ['dialogue.lua','dex_entries.lua','dex_kinds.lua','trainer_names.lua','battle_tower_trainer_names.lua']:
    a=export(base)
    if isinstance(a,dict) and isinstance(cats[name],dict):cats[name]={**a,**cats[name]}
 from gb_reference_corrections import correct
 correct(game,cats)
 (ROOT/f'build/gb-reference/{game}.json').write_text(json.dumps(cats,ensure_ascii=False))
 manifest=json.loads((ENGINE/'tools'/('rom_manifest'+('' if game=='red' else '_'+game)+'.json')).read_text())
 cm={int(k):v for k,v in manifest['charmap'].items()}
 cm.update({int(v):k for k,v in cats['charmap.lua'].items()})
 cm.update({0x1e:'\n',0x1f:'\n',0x25:'\n'} if game=='crystal' else {})
 cm.update({0x4e:'\n',0x4f:'\n',0x51:'\f',0x55:'\v',0x54:'POKé',0x4a:'PKMN',0x56:'……',0xf0:'¥',0xdc:"'s"})
 # Only characters/formatting with defined meaning. Other bytes form barriers.
 chars={i:(cm[i] if i in cm and cm[i] and not cm[i].startswith('<') and not cm[i].startswith('{') else chr(0xe000+i)) for i in range(256)}
 display=''.join(chars[b] for b in rom)
 starts=[0];n=0
 for b in rom:n+=len(chars[b]);starts.append(n)
 spans={};missing=[];stats={};catalogs={}
 def aligned(part):
  at=display.find(part)
  while at>=0:
   a=bisect.bisect_left(starts,at);b=bisect.bisect_left(starts,at+len(part))
   if starts[a]==at and starts[b]==at+len(part):return at
   at=display.find(part,at+1)
  return -1
 def text_recipe(s):
  if s=='':return {'empty':True}
  match=re.fullmatch(r'(TM|VM)([0-9]{2})',s)
  if match:
   prefix=text_recipe(match[1])
   if prefix:return {'parts':prefix['parts']+[{'number':int(match[2]),'width':2}]}
  if s in spans:return spans[s]
  parts=[]
  for part in re.split(r'(\{[^{}]+\}|<[^<>]+>)',s):
   if not part:continue
   if re.fullmatch(r'\{[^{}]+\}|<[^<>]+>',part):parts.append({'token':part});continue
   at=aligned(part)
   if at>=0:
    a=bisect.bisect_left(starts,at);b=bisect.bisect_left(starts,at+len(part))
    if starts[a]==at and starts[b]==at+len(part):parts.append({'off':a,'size':b-a});continue
   # Separate original line breaks from literal text; no per-letter synthesis.
   for line in re.split(r'([\n\f\v])',part):
    if not line:continue
    if line in ('\n','\f','\v'):parts.append({'token':line});continue
    at=aligned(line)
    if at<0:return None
    a=bisect.bisect_left(starts,at);b=bisect.bisect_left(starts,at+len(line))
    if starts[a]!=at or starts[b]!=at+len(line):return None
    parts.append({'off':a,'size':b-a})
  value={'parts':parts};spans[s]=value;return value
 def rec(v,path):
  if isinstance(v,str):
   if path.startswith('mon_names.lua/') and path.endswith('/from'):return {'value':v}
   result=text_recipe(v)
   if result is None:missing.append(path);return None
   return result
  if isinstance(v,list):
   items=[rec(x,path+'/'+str(i)) for i,x in enumerate(v)]
   if any(x is None for x in items):return None
   return {'array':items}
  if isinstance(v,dict):
   rows=[]
   for k,x in v.items():
    value=rec(x,path+'/'+str(k))
    if value is not None:rows.append([k,value])
   return {'table':rows}
  return {'value':v}
 for name,cat in cats.items():
  # Syntax regexes and aliases are program metadata; handled separately.
  if 'patterns' in name:continue
  if name=='charmap.lua':continue
  before=len(missing);catalogs[name]=rec(cat,name);stats[name]={'missing_leaves':len(missing)-before}
 cats['charmap.lua']["'s"]=0xdc
 profile={'game':game,'sha1':row['sha1'],'md5':row['md5'],'size':row['size'],'charmap':{str(k):v for k,v in chars.items()},'fontmap':cats['charmap.lua'],'catalogs':catalogs}
 # Split catalogs to avoid LuaJIT's per-chunk constant ceiling.
 out=ROOT/f'mod/gb/profiles/{game}';out.mkdir(parents=True,exist_ok=True)
 profile['catalogs']=list(catalogs)
 for name,value in catalogs.items():
  (out/name).write_text('return '+lua(value)+'\n')
 (out/'profile.lua').write_text('return '+lua(profile)+'\n')
 (ROOT/f'build/{game}-gb-profile-report.json').write_text(json.dumps({'stats':stats,'missing':missing},ensure_ascii=False,indent=2))
 print(game,'spans',len(spans),'missing',len(missing),'dialogue missing',stats.get('dialogue.lua'),flush=True)
if __name__=='__main__':
 for game in GAMES:build(game)
