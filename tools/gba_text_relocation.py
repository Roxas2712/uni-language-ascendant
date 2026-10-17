"""Extend relocation evidence with bounded text pools and pointer tables.

Text runs require both independently mapped boundaries and the same number of
terminated entries. Pointer tables require full non-pointer identity and two
already resolved ROM references. New addresses remain private audit evidence.
"""
import argparse,collections,json,re,struct
from pathlib import Path
from chain_emerald_languages import eos
BASE=0x08000000

def run(a):
 src=a.base.read_bytes();dst=a.target.read_bytes();rows=json.loads(a.symbols.read_text())
 audit=json.loads(a.relocation.read_text());scripts=json.loads(a.scripts.read_text())
 import hashlib
 assert hashlib.sha1(src).hexdigest()==audit['base_sha1']==scripts['base_sha1']
 assert hashlib.sha1(dst).hexdigest()==audit['target_sha1']==scripts['target_sha1']
 mapped={int(k):v for k,v in audit['mapped'].items()};mapped.update({int(k):v for k,v in scripts['mapped'].items()})
 conflicts={int(k):v for k,v in audit['conflicts'].items()};conflicts.update({int(k):v for k,v in scripts['conflicts'].items()})
 for k in conflicts:mapped.pop(k,None)
 if a.structures:
  structures=json.loads(a.structures.read_text())
  assert structures['base_sha1']==audit['base_sha1'] and structures['target_sha1']==audit['target_sha1']
  for k,v in structures['mapped'].items():
   k=int(k)
   if k in mapped:assert mapped[k]==v,('structure disagrees',hex(k))
   mapped[k]=v
 by_at=collections.defaultdict(list)
 for r in rows:by_at[r['off']].append(r)
 functions={r['off'] for r in rows if r['type']=='FUNC'}
 texts={}
 for r in rows:
  if r['type']=='FUNC' or not re.search('text|string|description',r['name'],re.I):continue
  off,size=r['off'],r['size'];end=eos(src,off)
  if end is not None and 0<=off+size-end<=3 and not any(src[end:off+size]):texts[off]=end
 chains=[];chain=[]
 for off in sorted(texts):
  if chain and not (0<=off-texts[chain[-1]]<=3 and not any(src[texts[chain[-1]]:off])):chains.append(chain);chain=[]
  chain.append(off)
 if chain:chains.append(chain)
 proof=[];counts=collections.Counter();objects={r['off']:r['size'] for r in rows if (r['type']=='OBJECT' or (r['type']=='NOTYPE' and r['name'].endswith('_Layout') and r['size']==28)) and 8<=r['size']<=65536 and r['off']%4==0}
 # No known conflict is resolved by positional inference.
 pointer_hits={}
 def occurrences(value):
  if value not in pointer_hits:
   needle=struct.pack('<I',value);hits=[];at=0
   while True:
    hit=dst.find(needle,at)
    if hit<0:break
    if hit%4==0:hits.append(hit)
    at=hit+1
   pointer_hits[value]=hits
  return pointer_hits[value]
 for iteration in range(8):
  added=0
  for chain in chains:
   anchors=[i for i,k in enumerate(chain) if k in mapped]
   for lo,hi in zip(anchors,anchors[1:]):
    if hi-lo<2 or any(k in conflicts for k in chain[lo:hi+1]):continue
    matches=[]
    for align in [False,True]:
     ptr=mapped[chain[lo]];pairs=[]
     for i in range(lo,hi):
      old=chain[i];pairs.append((old,ptr));end=eos(dst,ptr)
      if end is None:break
      ptr=(end+3)&~3 if align or chain[i+1]!=texts[old] else end
     else:
      if ptr==mapped[chain[hi]]:matches.append(pairs)
    if not matches or any(x!=matches[0] for x in matches):continue
    for old,new in matches[0][1:]:
     if old not in mapped:mapped[old]=new;added+=1;counts['bounded-text']+=1
    proof.append(['bounded-text',chain[lo],chain[hi],mapped[chain[lo]],mapped[chain[hi]],matches[0]])
  for off,size in objects.items():
   if off in conflicts:continue
   ptrs=[];anchors=0;pieces=[];last=0;anchor_slots=[]
   for rel in range(0,size-3,4):
    old=struct.unpack_from('<I',src,off+rel)[0]-BASE
    thumb=1 if old&1 and old-1 in functions else 0
    old-=thumb
    if old not in by_at:continue
    ptrs.append((rel,old,thumb));pieces.append(re.escape(src[off+last:off+rel]));last=rel+4
    if old in mapped:
     value=BASE+mapped[old]+thumb
     pieces.append(re.escape(struct.pack('<I',value)));anchors+=1;anchor_slots.append((rel,value))
    else:pieces.append(b'[\x00-\xff]{3}\x08')
   if anchors<2 and off not in mapped:continue
   if off in mapped and all(old in mapped or old in conflicts for _,old,_ in ptrs):continue
   pieces.append(re.escape(src[off+last:off+size]));pat=re.compile(b''.join(pieces))
   if off in mapped:
    new=mapped[off]
    if pat.fullmatch(dst[new:new+size]) is None:continue
   else:
    # Search exact known pointer slots, then validate the complete object.
    # This avoids regex scans beginning with large runs of zero padding.
    rel,value=min(anchor_slots,key=lambda slot:len(occurrences(slot[1])))
    hits=[]
    for slot in occurrences(value):
     start=slot-rel
     if start>=0 and start+size<=len(dst) and pat.fullmatch(dst,start,start+size):hits.append(start)
     if len(hits)>1:break
    if len(hits)!=1:continue
    new=hits[0];mapped[off]=new;added+=1;counts['pointer-table']+=1
   witnesses=[]
   for rel,old,thumb in ptrs:
    ptr=struct.unpack_from('<I',dst,new+rel)[0]-BASE
    assert not thumb or ptr&1, ('Expected Thumb table reference',hex(off),rel)
    ptr-=thumb
    if old not in mapped and old not in conflicts and 0<=ptr<len(dst):
     mapped[old]=ptr;added+=1;counts['table-reference']+=1;witnesses.append([rel,old,ptr])
   proof.append(['pointer-table',off,new,size,anchors,witnesses])
  print('ROUND',iteration,'added',added,'total',len(mapped),dict(counts),flush=True)
  if not added:break
 a.output.write_text(json.dumps(dict(base_sha1=audit['base_sha1'],target_sha1=audit['target_sha1'],mapped=mapped,conflicts=conflicts,proof=proof,counts=counts)))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for key in ['base','target','symbols','relocation','scripts','output']:p.add_argument('--'+key,type=Path,required=True)
 p.add_argument('--structures',type=Path)
 run(p.parse_args())
