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


def recover_code_pointer(source,target,source_start,size,address,opcode=0x21,bank_operand=None):
    """Match a bounded instruction block, masking absolute operands only.

    Unlike recover(), this follows instruction boundaries and searches all ROM
    banks. bank_operand locates an explicit bank byte relative to the pointer
    operand (for inter-bank graphics loads). Callers validate independent data
    anchors and output sizes before retaining a mapping.
    """
    raw=source[source_start:source_start+size]
    three={0x01,0x08,0x11,0x21,0x31,0xc2,0xc3,0xc4,0xca,0xcc,0xcd,0xd2,0xd4,0xda,0xdc,0xea,0xfa}
    two={0x06,0x0e,0x10,0x16,0x18,0x1e,0x20,0x26,0x28,0x2e,0x30,0x36,0x38,0x3e,0xc6,0xcb,0xce,0xd6,0xde,0xe0,0xe6,0xe8,0xee,0xf0,0xf6,0xf8,0xfe}
    ignored=set();refs=[];i=0
    while i<len(raw):
        op=raw[i];width=3 if op in three else 2 if op in two else 1
        if width==3:
            ignored.update((i+1,i+2))
            if op==opcode and int.from_bytes(raw[i+1:i+3],'little')==address:refs.append(i+1)
        i+=width
    if i!=size or len(refs)!=1:raise ValueError('Unbounded or ambiguous source code reference')
    pattern=b''.join(b'.' if i in ignored else re.escape(bytes([v])) for i,v in enumerate(raw))
    def hits(rom):return [m.start() for m in re.finditer(b'(?=('+pattern+b'))',rom,re.S)]
    if hits(source)!=[source_start]:raise ValueError('Non-unique source code block')
    found=hits(target)
    if len(found)!=1:raise ValueError(('Non-unique target code block',found))
    pos=found[0]+refs[0];ptr=int.from_bytes(target[pos:pos+2],'little')
    bank=target[pos+bank_operand] if bank_operand is not None else found[0]//16384
    if not (0x4000<=ptr<0x8000):raise ValueError('Target is not banked ROM')
    return bank*16384+ptr%16384,{'code':found[0],'bytes':size,'literalBytes':size-len(ignored),'pointerOperand':pos}
