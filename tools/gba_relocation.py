"""Offline relocation evidence from complete unique code/data blocks.

Only known symbol targets from aligned ROM literal slots are followed. This
report is evidence for subsequent typed structure/text checks, not a profile.
"""
import argparse,collections,hashlib,json,re,struct,subprocess
from pathlib import Path
BASE=0x08000000

def elf_symbols(path):
    rows=[];obj=''
    data=subprocess.check_output(['/opt/homebrew/bin/arm-none-eabi-readelf','-sW',str(path)],text=True)
    for line in data.splitlines():
        p=line.split()
        if len(p)<8 or not p[0][:-1].isdigit():continue
        _,addr,size,typ,bind,_,_,name=p[:8]
        if typ=='FILE':obj=name;continue
        value=int(addr,16)
        if typ in ('FILE','SECTION') or not BASE<=value<BASE+0x1000000 or name.startswith(('$','.')):continue
        if typ=='FUNC':value&=~1
        rows.append(dict(name=name,object=obj if bind=='LOCAL' else '',off=value-BASE,size=int(size),type=typ))
    # ASM labels have size 0. Bound by the next real symbol; never treat an
    # arbitrary suffix as a complete C object/function.
    addresses=sorted({r['off'] for r in rows});next_at=dict(zip(addresses,addresses[1:]))
    for row in rows:
        if row['size']==0 and row['type']=='NOTYPE':row['size']=next_at.get(row['off'],row['off'])-row['off']
    return rows

def normalize(data,code=False):
    data=bytearray(data)
    # Only aligned literal words for code. Data is used solely after an
    # independently matched pointer anchor; full non-pointer bytes must agree.
    for at in range(0,len(data)-3,4 if code else 1):
        value=int.from_bytes(data[at:at+4],'little')
        rom_pointer=BASE<=value<BASE+0x1000000
        # Expanded translated buffers also move static EWRAM/IWRAM symbols.
        # In code, these are aligned literal words just like ROM pointers.
        ram_pointer=code and (0x02000000<=value<0x02040000 or 0x03000000<=value<0x03008000)
        if rom_pointer or ram_pointer:data[at:at+3]=bytes(3)
    if code:
        for at in range(0,len(data)-3,2):
            first,second=struct.unpack_from('<HH',data,at)
            if first&0xf800==0xf000 and second&0xf800==0xf800:struct.pack_into('<HH',data,at,0xf000,0xf800)
    return bytes(data)

def run(a):
    src=a.base.read_bytes();dst=a.target.read_bytes()
    assert hashlib.sha1(src).hexdigest()==a.base_sha1
    assert hashlib.sha1(dst).hexdigest()==a.target_sha1
    rows=elf_symbols(a.elf);known={r['off'] for r in rows};by_at=collections.defaultdict(list)
    for row in rows:by_at[row['off']].append(row)
    candidates=collections.defaultdict(set);proof=[]
    def add(old,new,why):
        if old in known and 0<=new<len(dst):
            candidates[old].add(new);proof.append([old,new,why])
    ns=normalize(src,True);nt=normalize(dst,True);seen=set();blocks=[]
    for row in rows:
        off,size=row['off'],row['size']
        if row['type']!='FUNC' or (off,size) in seen or size<24 or size>16384 or off%4:continue
        seen.add((off,size));sample=ns[off:off+size]
        if len(set(sample))<8:continue
        hit=nt.find(sample)
        if hit<0 or hit%4 or nt.find(sample,hit+1)>=0:continue
        if ns.find(sample)!=off or ns.find(sample,off+1)>=0:continue
        add(off,hit,['complete-function',row['name'],size]);blocks.append([off,hit,size,row['name']])
        for rel in range(0,size-3,4):
            old=int.from_bytes(src[off+rel:off+rel+4],'little')-BASE
            new=int.from_bytes(dst[hit+rel:hit+rel+4],'little')-BASE
            if old in known:add(old,new,['literal-in-matched-function',row['name'],off,hit,rel])
    # A BL inside an already verified complete function identifies its callee
    # even when that callee is too short or has changed its local constants.
    funcs={r['off']:r['size'] for r in rows if r['type']=='FUNC'}
    verified={(a,b) for a,b,_,_ in blocks};pending=list(verified);followed=set()
    def calls(data,off,size):
        for pos in range(off,off+size-3,2):
            hi,lo=struct.unpack_from('<HH',data,pos)
            if hi&0xf800==0xf000 and lo&0xf800==0xf800:
                rel=((hi&0x7ff)<<12)|((lo&0x7ff)<<1)
                if rel&(1<<22):rel-=1<<23
                yield pos-off,pos+4+rel
    while pending:
        off,hit=pending.pop()
        if (off,hit) in followed:continue
        followed.add((off,hit));size=funcs[off]
        if ns[off:off+size]!=nt[hit:hit+size]:continue
        target_calls=dict(calls(dst,hit,size))
        for rel,old in calls(src,off,size):
            new=target_calls.get(rel)
            if old not in funcs or new is None or new%2:continue
            add(old,new,['call-in-matched-function',off,hit,rel])
            if len(candidates[old])==1:pending.append((old,new))
        for pos in range((off+3)&~3,off+size-3,4):
            rel=pos-off
            old=int.from_bytes(src[pos:pos+4],'little')-BASE
            new=int.from_bytes(dst[hit+rel:hit+rel+4],'little')-BASE
            if old in known:add(old,new,['literal-in-followed-function',off,hit,rel])
    print('UNIQUE_CODE',len(blocks),'followed',len(followed),'targets',len(candidates),flush=True)
    # Follow complete structured objects only from established anchors.
    ns=normalize(src);nt=normalize(dst);done=set()
    for _ in range(20):
        added=0
        for off in list(candidates):
            if len(candidates[off])!=1:continue
            hit=next(iter(candidates[off]))
            if (off,hit) in done:continue
            done.add((off,hit))
            sizes={r['size'] for r in by_at[off] if r['type']!='FUNC' and r['size']>=4}
            for size in sizes:
                if ns[off:off+size]!=nt[hit:hit+size]:continue
                for rel in range(size-3):
                    old=int.from_bytes(src[off+rel:off+rel+4],'little')-BASE
                    if old not in known:continue
                    new=int.from_bytes(dst[hit+rel:hit+rel+4],'little')-BASE
                    before=len(candidates[old]);add(old,new,['anchored-object',off,hit,size,rel]);added+=len(candidates[old])-before
        if not added:break
    result=dict(base_sha1=a.base_sha1,target_sha1=a.target_sha1,blocks=blocks,
        mapped={str(k):next(iter(v)) for k,v in candidates.items() if len(v)==1},
        conflicts={str(k):sorted(v) for k,v in candidates.items() if len(v)>1},proof=proof)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'symbols.json').write_text(json.dumps(rows))
    (a.output/'relocation.json').write_text(json.dumps(result))
    print('RELOCATION',len(result['mapped']),'conflicts',len(result['conflicts']),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['base','target','elf','output']:p.add_argument('--'+k,type=Path,required=True)
    for k in ['base-sha1','target-sha1']:p.add_argument('--'+k,required=True)
    run(p.parse_args())
