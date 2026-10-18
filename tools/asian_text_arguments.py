"""Preserve RAM-field identities when a native sentence changes word order."""
from asian_gen2 import offset

def fields(reader,at,stop_at=None):
    result=[];seen=set()
    for _ in range(2048):
        if stop_at is not None:
            assert at<=stop_at,'Argument scan crossed reviewed boundary'
            if at==stop_at:break
        assert at not in seen;seen.add(at);cmd=reader.rom[at];at+=1
        if cmd==0:
            _,_,at,end=reader.span(at)
            if end!=0x50:break
        elif cmd==0x50:break
        elif cmd==0x16:at=offset(reader.rom[at+2],int.from_bytes(reader.rom[at:at+2],'little'))
        elif cmd in (1,2,9,0x14):
            width={1:2,2:3,9:3,0x14:1}[cmd]
            result.append(('NUM'if cmd in(2,9)else'STRBUF',cmd,int.from_bytes(reader.rom[at:at+(1 if cmd==0x14 else 2)],'little')));at+=width
        elif cmd==0xc:at+=1
        elif cmd in (5,6,7,0xa,0xb,0xd,0xe,0xf,0x10,0x11,0x12,0x13,0x15):pass
        else:raise ValueError(('Unsupported command',cmd,at-1))
    return result

def argument_orders(source_reader,source_symbols,native_reader,targets,native_symbols=None,rammap=None,fragments=None):
    """Only emit proven permutations, keyed by original named-text label.

    Korean uses the matching disassembly's RAM symbol identities. Japanese
    uses a separately reviewed RAM crosswalk in the address checkpoint.
    """
    reverse={}
    if native_symbols:
        for name,(bank,addr) in native_symbols.items():
            if addr>=0xc000 and name in source_symbols:
                reverse.setdefault(addr,set()).add(source_symbols[name][1])
    out={}
    for name,target in targets.items():
        if name not in source_symbols:continue
        try:
            source=offset(*source_symbols[name]);fragment=(fragments or {}).get(str(source))
            a=fields(source_reader,source);b=fields(native_reader,target,fragment['stop']if fragment else None)
        except (ValueError,AssertionError,IndexError):continue
        if len(a)<2 or len(a)!=len(b):continue
        translated=[]
        for kind,cmd,addr in b:
            if cmd==0x14:translated.append((kind,cmd,addr));continue
            dest=(rammap or {}).get(addr)
            # Banked WRAM aliases can share an address with unrelated mail
            # buffers. Resolve only among the actual source sentence fields.
            candidates=reverse.get(addr,set()) & {x[2]for x in a if x[:2]==(kind,cmd)}
            if dest is None and len(candidates)==1:dest=next(iter(candidates))
            translated.append((kind,cmd,dest))
        if any(item not in a for item in translated):continue
        order=[a.index(item)+1 for item in translated]
        if order!=list(range(1,len(a)+1)):out[name]={'value':order}
    return out
