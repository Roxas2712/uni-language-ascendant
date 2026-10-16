"""Match event bytecode with pointer operands decoded from the opcode schema.
Unlike byte-pattern pointer masking, literal 0x08 bytes inside addresses cannot
consume the preceding opcode. Matching scripts retain every nonpointer operand.
"""
import json,sys,struct,re,collections
from pathlib import Path
from map_emerald_languages import ROOT,BASE
from build_profiles import lua_symbols
from chain_emerald_languages import eos

def run(lang,write=False):
 path=ROOT/f'build/emerald-{lang}-relocation.json';audit=json.loads(path.read_text());old={int(k):v for k,v in audit['mapped'].items()}
 spec=next(x for x in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms'] if x['language']==lang)
 src=(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba').read_bytes();dst=Path(spec['staged_file']).read_bytes()
 cfg=json.loads((ROOT/'build/emerald-script-opcodes.json').read_text());ops=cfg['ops'];types=cfg['trainers'];tp=cfg['trainerPointers']
 sy=lua_symbols(ROOT/'build/profile-engine/src/import/gba/syms/emeraldde.lua');names=collections.defaultdict(list);scripts={}
 for k,(off,size) in sy.items():
  names[off].append(k)
  if 'EventScript_' in k and 0x180000<off<0x300000:scripts[off]=size
 def decode(a,size):
  end=a+size;pc=a;ptrs=[]
  while pc<end:
   op=ops.get(str(src[pc]));pc+=1
   if not op:return
   if op['name']=='trainerbattle':
    kind=types.get(str(src[pc]));fields=tp.get(kind)
    if fields is None:return
    pc+=5
    args=[{'kind':'word'} for _ in fields]
   else:args=op['args']
   for arg in args:
    n={'byte':1,'half':2,'word':4}[arg['kind']]
    if pc+n>end:return
    if n==4:
     v=struct.unpack_from('<I',src,pc)[0]-BASE
     if 0<=v<len(src):ptrs.append((pc-a,v))
    pc+=n
  if pc!=end:return
  pieces=[];at=0
  for pos,_ in ptrs:pieces.extend([re.escape(src[a+at:a+pos]),b'[\x00-\xff]{3}\x08']);at=pos+4
  pieces.append(re.escape(src[a+at:end]));pattern=re.compile(b''.join(pieces))
  return pattern,ptrs
 candidates=collections.defaultdict(set);proof=[];done=set();queue=[]
 def add(a,b,why):
  if not 0<=b<len(dst):return
  if b not in candidates[a]:
   candidates[a].add(b)
   if a in scripts:queue.append((a,b))
  proof.append((a,b,why))
 for a,size in sorted(scripts.items()):
  # Combine adjacent scripts, but never cross text/data symbols.
  for _ in range(8):
   if a+size not in scripts:break
   size+=scripts[a+size]
  decoded=decode(a,size)
  if not decoded:continue
  pattern,ptrs=decoded
  if size-4*len(ptrs)<10 or len(set(src[a:a+size]))<8:continue
  source_matches=pattern.finditer(src,0x180000,0x300000);source_first=next(source_matches,None)
  if source_first is None or source_first.start()!=a or next(source_matches,None) is not None:continue
  matches=pattern.finditer(dst,0x180000,0x300000);first=next(matches,None)
  if first is None or next(matches,None) is not None:continue
  b=first.start();add(a,b,('unique',a,size))
  for pos,v in ptrs:add(v,struct.unpack_from('<I',dst,b+pos)[0]-BASE,('operand',a,b,pos))
 while queue:
  a,b=queue.pop()
  if (a,b) in done:continue
  done.add((a,b));size=scripts[a];decoded=decode(a,size)
  if not decoded:continue
  pattern,ptrs=decoded
  if not pattern.fullmatch(dst[b:b+size]):continue
  for pos,v in ptrs:add(v,struct.unpack_from('<I',dst,b+pos)[0]-BASE,('follow',a,b,pos))
 p=json.loads((ROOT/'build/emerald-de-metadata.json').read_text());base=json.loads((ROOT/'build/emerald-base-texts.json').read_text());textaddrs={v[0] for k,v in p['texts'].items() if k in base}
 resolved={};conflicts={}
 for a,bs in candidates.items():
  if len(bs)==1:resolved[a]=next(iter(bs))
  elif a in textaddrs and len({dst[b:eos(dst,b)] for b in bs})==1:resolved[a]=min(bs)
  else:conflicts[a]=sorted(bs)
 changes={a:b for a,b in resolved.items() if a in textaddrs and a in old and dst[old[a]:eos(dst,old[a])]!=dst[b:eos(dst,b)]}
 print(lang,'typed-script references',len(resolved),'text addresses',len(textaddrs&resolved.keys()),'changed text',len(changes),'conflicts',len(conflicts))
 for a,b in changes.items():print('CORRECT',hex(a),hex(old[a]),'->',hex(b),names[a][:1])
 for a,bs in conflicts.items():
  if a in textaddrs:print('TEXT_CONFLICT',hex(a),list(map(hex,bs)),names[a][:1])
 report={'resolved':resolved,'changed_text':changes,'conflicts':conflicts,'proof':proof}
 (ROOT/f'build/emerald-{lang}-typed-scripts.json').write_text(json.dumps(report,indent=2))
 if write:
  assert not conflicts, 'Ambiguous script references must be resolved before publishing'
  old.update(resolved);audit['mapped']={str(a):b for a,b in old.items()};audit['counts']['typed-script-texts']=len(textaddrs&resolved.keys());path.write_text(json.dumps(audit))
if __name__=='__main__':run(sys.argv[1],'--write' in sys.argv)
