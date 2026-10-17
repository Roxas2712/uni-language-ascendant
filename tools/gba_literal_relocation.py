"""Recover ROM references from unique, unchanged instruction/literal windows.

Each witness contains an actual Thumb PC-relative LDR and its literal, inside
one source function. Both normalized windows must occur exactly once. This
extends code evidence for functions changed elsewhere by the translation.
"""
import argparse,collections,json,struct,hashlib
from pathlib import Path
from gba_relocation import normalize,BASE

def run(a):
 src=a.base.read_bytes();dst=a.target.read_bytes();audit=json.loads(a.relocation.read_text());rows=json.loads(a.symbols.read_text())
 assert hashlib.sha1(src).hexdigest()==audit['base_sha1']
 assert hashlib.sha1(dst).hexdigest()==audit['target_sha1']
 known={r['off'] for r in rows};ns=normalize(src,True);nt=normalize(dst,True);candidates=collections.defaultdict(set);proof=[]
 for key,value in audit['mapped'].items():candidates[int(key)].add(value)
 for key,values in audit['conflicts'].items():candidates[int(key)].update(values)
 seen=set()
 for row in rows:
  off,size=row['off'],row['size']
  if row['type']!='FUNC' or (off,size) in seen:continue
  seen.add((off,size));end=off+size
  for pos in range(off,end-1,2):
   ins=struct.unpack_from('<H',src,pos)[0]
   if ins&0xf800!=0x4800:continue
   literal=((pos+4)&~3)+(ins&255)*4
   if not pos<literal<=end-4:continue
   old=struct.unpack_from('<I',src,literal)[0]-BASE
   if old not in known or old in candidates:continue
   # Try bounded prefixes as well as local windows. A struct-offset constant
   # immediately after this literal may have changed while the complete load
   # and its caller sequence remain identical. Every accepted window still
   # contains the instruction and referenced literal and is unique in both ROMs.
   for start in sorted({off,max(off,(pos-64)&~3),max(off,(pos-24)&~3),pos&~3}):
    stop=min(end,max(start+64,literal+4))
    if start%4 or stop-start<64 or stop-start>512:continue
    window=ns[start:stop]
    if len(set(window))<24:continue
    hit=nt.find(window)
    if hit<0 or hit%4 or nt.find(window,hit+1)>=0 or ns.find(window)!=start or ns.find(window,start+1)>=0:continue
    at=hit+literal-start;new=struct.unpack_from('<I',dst,at)[0]-BASE
    if not 0<=new<len(dst):continue
    candidates[old].add(new);proof.append([old,new,row['name'],pos,literal,start,stop,hit])
 audit['mapped']={str(k):next(iter(v)) for k,v in candidates.items() if len(v)==1}
 audit['conflicts']={str(k):sorted(v) for k,v in candidates.items() if len(v)>1}
 audit['literal_windows']=proof
 a.output.write_text(json.dumps(audit));print('LITERAL_WINDOWS',len(proof),'total',len(audit['mapped']))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['base','target','relocation','symbols','output']:p.add_argument('--'+name,type=Path,required=True)
 run(p.parse_args())
