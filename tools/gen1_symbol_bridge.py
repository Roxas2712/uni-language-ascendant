"""Bridge renamed text/RAM symbols through a checksum-identical original ROM.

The old English build MUST equal the compiler's supported original SHA-1.
This proves symbol identity across source revisions; it does not prove a fan
translation kept the original semantics at each symbol. Review that separately.
"""
import argparse,collections,hashlib,json,re
from pathlib import Path
from gen1_ptbr_dialogue import symbols,offset


def bridge(a):
 rom=a.rom.read_bytes();m=json.loads(a.manifest.read_text())
 assert hashlib.sha1(rom).hexdigest()==m['romSha1'], 'Reference build is not the exact original ROM'
 old=symbols(a.symbols);target=symbols(a.target_symbols)
 byaddr=collections.defaultdict(list)
 for name,address in old.items():
  if name in target:byaddr[address].append(name)
 aliases={}
 for label in m['text']['labels']:
  candidates=byaddr[tuple(m['symbols'][label])]
  assert candidates,'No shared symbol: '+label
  assert len({target[n] for n in candidates})==1, 'Ambiguous translated address: '+label
  aliases[label]=label if label in candidates else sorted(candidates)[0]
 ram=collections.defaultdict(set)
 for label,rows in m['text']['dynamic'].items():
  pos=offset(*old[aliases[label]]);index=0;visited=set()
  for _ in range(1000):
   assert pos not in visited,'Command cycle';visited.add(pos)
   command=rom[pos];pos+=1
   if command==0:
    while rom[pos] not in (0x50,0x57,0x58,0x5f):pos+=1
    end=rom[pos];pos+=1
    if end!=0x50:break
   elif command==0x50:break
   elif command in (1,2,9):
    assert rows[index][0]==command,(label,'Operand type mismatch')
    name=re.search(r':([^,}]+)',rows[index][1])[1]
    ram[name].add(int.from_bytes(rom[pos:pos+2],'little'))
    pos+=2 if command==1 else 3;index+=1
   elif command==0x17:pos=offset(rom[pos+2],int.from_bytes(rom[pos:pos+2],'little'))
   else:raise ValueError((label,'Unsupported command',command))
  assert index==len(rows),(label,'Missing operands')
 ram_aliases={}
 for name,addresses in ram.items():
  assert len(addresses)==1,(name,'RAM identity changed between callers')
  address=next(iter(addresses))
  candidates=[n for n,(_,addr) in old.items() if addr==address and n in target and n.startswith(('w','h'))]
  assert candidates and len({target[n] for n in candidates})==1,(name,'Ambiguous RAM identity')
  ram_aliases[name]=name if name in candidates else sorted(candidates)[0]
 a.output.mkdir(exist_ok=True,parents=True)
 for name,rows in [('labels',aliases),('ram',ram_aliases)]:
  (a.output/(name+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
 proof={'base_sha1':m['romSha1'],'labels':len(aliases),'ram_symbols':len(ram_aliases),
        'symbols_sha256':hashlib.sha256(a.symbols.read_bytes()).hexdigest(),
        'target_symbols_sha256':hashlib.sha256(a.target_symbols.read_bytes()).hexdigest()}
 (a.output/'proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','symbols','target-symbols','manifest','output'):p.add_argument('--'+name,type=Path,required=True)
 bridge(p.parse_args())
