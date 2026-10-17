"""Recover event-script references by full typed-bytecode identity.

All non-ROM-pointer operands must be identical. Unique complete scripts are
anchors; shorter scripts may only be followed from those anchors. Conflicts
remain explicit and must not become active translation recipes.
"""
import argparse,collections,hashlib,json,re,struct
from pathlib import Path
BASE=0x08000000
TRAINER_POINTERS={'SINGLE':2,'CONTINUE_SCRIPT_NO_MUSIC':3,'CONTINUE_SCRIPT':3,
 'SINGLE_NO_INTRO_TEXT':1,'DOUBLE':3,'REMATCH':2,'CONTINUE_SCRIPT_DOUBLE':4,
 'REMATCH_DOUBLE':3,'CONTINUE_SCRIPT_DOUBLE_NO_MUSIC':4,'EARLY_RIVAL':2}

def decode(src,start,size,cfg):
 end=start+size;pc=start;ptrs=[]
 if size<=0 or end>len(src):return
 while pc<end:
  op=cfg['ops'].get(str(src[pc]));pc+=1
  if op is None:return
  if op['name']=='trainerbattle':
   if pc+5>end:return
   fields=TRAINER_POINTERS.get(cfg['trainers'].get(str(src[pc])))
   if fields is None:return
   pc+=5;args=[{'kind':'word'}]*fields
  else:args=op['args']
  for arg in args:
   n={'byte':1,'half':2,'word':4}[arg['kind']]
   if pc+n>end:return
   if n==4:
    value=struct.unpack_from('<I',src,pc)[0]-BASE
    if 0<=value<len(src):ptrs.append((pc-start,value))
   pc+=n
 if pc!=end:return
 pieces=[];at=0
 for pos,_ in ptrs:
  pieces.extend([re.escape(src[start+at:start+pos]),b'[\x00-\xff]{3}\x08']);at=pos+4
 pieces.append(re.escape(src[start+at:end]))
 return re.compile(b''.join(pieces)),ptrs

def run(a):
 src=a.base.read_bytes();dst=a.target.read_bytes();audit=json.loads(a.relocation.read_text())
 assert hashlib.sha1(src).hexdigest()==audit['base_sha1']
 assert hashlib.sha1(dst).hexdigest()==audit['target_sha1']
 rows=json.loads(a.symbols.read_text());cfg=json.loads(a.opcodes.read_text())
 scripts={r['off']:r['size'] for r in rows if r['type']=='NOTYPE' and 'EventScript_' in r['name']}
 known={r['off'] for r in rows};candidates=collections.defaultdict(set);proof=[];queue=[];seen=set()
 def add(old,new,why):
  if old not in known or not 0<=new<len(dst):return
  if new not in candidates[old]:
   candidates[old].add(new)
   if old in scripts:queue.append((old,new))
  proof.append([old,new,why])
 # Code evidence is admitted only after an independently typed full-script
 # match here. It must not override the script witnesses below.
 for k,v in audit['mapped'].items():
  old=int(k)
  if old in scripts:
   d=decode(src,old,scripts[old],cfg)
   if d and d[0].fullmatch(dst[v:v+scripts[old]]):add(old,v,['code-anchored-script',old,v])
 decoded=0;unique=0
 for old,initial in sorted(scripts.items()):
  size=initial
  for _ in range(8):
   if old+size not in scripts:break
   size+=scripts[old+size]
  d=decode(src,old,size,cfg)
  if not d:continue
  decoded+=1;pat,ptrs=d
  if size-4*len(ptrs)<10 or len(set(src[old:old+size]))<8:continue
  sm=pat.finditer(src);first=next(sm,None)
  if first is None or first.start()!=old or next(sm,None) is not None:continue
  dm=pat.finditer(dst);first=next(dm,None)
  if first is None or next(dm,None) is not None:continue
  new=first.start();unique+=1;add(old,new,['unique-script',old,size])
  for pos,v in ptrs:add(v,struct.unpack_from('<I',dst,new+pos)[0]-BASE,['operand',old,new,pos])
 while queue:
  old,new=queue.pop()
  if (old,new) in seen:continue
  seen.add((old,new));d=decode(src,old,scripts[old],cfg)
  if d is None or not d[0].fullmatch(dst[new:new+scripts[old]]):continue
  for pos,v in d[1]:add(v,struct.unpack_from('<I',dst,new+pos)[0]-BASE,['follow',old,new,pos])
 out={'base_sha1':audit['base_sha1'],'target_sha1':audit['target_sha1'],
 'counts':dict(scripts=len(scripts),decoded=decoded,unique=unique),
 'mapped':{str(k):next(iter(v)) for k,v in candidates.items() if len(v)==1},
 'conflicts':{str(k):sorted(v) for k,v in candidates.items() if len(v)>1},'proof':proof}
 a.output.write_text(json.dumps(out));print(out['counts'],'mapped',len(out['mapped']),'conflicts',len(out['conflicts']),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for key in ['base','target','symbols','relocation','opcodes','output']:p.add_argument('--'+key,type=Path,required=True)
 run(p.parse_args())
