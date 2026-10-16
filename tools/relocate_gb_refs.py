"""Recover a banked data address through unique surrounding CPU references."""
import collections
import re


def recover(source,target,bank,address):
    needle=address.to_bytes(2,'little')
    candidates=collections.defaultdict(list)
    for match in re.finditer(re.escape(needle),source):
        pos=match.start()
        if pos<17 or pos%16384<17 or pos%16384>16384-18:continue
        if source[pos-1] not in (0x01,0x11,0x21,0x31,0xfa,0xea):continue
        begin,end=pos-17,pos+18
        block=source[begin:end];ignored={17,18}
        # Absolute ROM/RAM operands vary across regional builds. The opcode
        # stream, relative jumps and arithmetic constants remain evidence.
        for i in range(len(block)-2):
            if block[i] in (0x01,0x11,0x21,0x31,0xfa,0xea,0xcd,0xc3,0xc2,0xca,0xd2,0xda,0xc4,0xcc,0xd4,0xdc):
                ignored.update((i+1,i+2))
        literal=[v for i,v in enumerate(block) if i not in ignored]
        if len(literal)<15 or len(set(literal))<8:continue
        pattern=b''.join(b'.' if i in ignored else re.escape(bytes([v])) for i,v in enumerate(block))
        sb=pos//16384;start=sb*16384;stop=start+16384
        if len(list(re.finditer(b'(?=('+pattern+b'))',source[start:stop],re.S)))!=1:continue
        hits=list(re.finditer(b'(?=('+pattern+b'))',target[start:stop],re.S))
        if len(hits)!=1:continue
        at=start+hits[0].start()+17
        ptr=int.from_bytes(target[at:at+2],'little')
        if 0x4000<=ptr<0x8000:candidates[ptr].append({'reference':pos,'target_reference':at,'literal_bytes':len(literal)})
    local={k:v for k,v in candidates.items() if any(row['reference']//16384==bank for row in v)}
    if len(local)==1:candidates=local
    if len(candidates)!=1:raise ValueError(('Unresolved CPU reference',bank,hex(address),{hex(k):len(v) for k,v in candidates.items()}))
    address,evidence=next(iter(candidates.items()))
    return bank*16384+address%16384,evidence
