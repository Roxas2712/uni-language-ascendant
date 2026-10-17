"""Instrument a private matching disassembly with zero-byte reference labels.

Rebuilding must preserve the complete original ROM SHA-1. The resulting
symbols identify actual pointer operands, avoiding pointer-like bytes in data.
"""
import argparse, json, re, hashlib
from pathlib import Path
from gen1_ptbr_dialogue import symbols, offset
OPS={'ld','text_far','writetext','jumptext','jumptextfaceplayer','farwritetext','farjumptext'}

def instrument(a):
    rows=[]
    for path in sorted(a.source.rglob('*.asm')):
        text=path.read_text();lines=[];changed=False
        for line in text.splitlines(True):
            body=line.split(';',1)[0].strip()
            match=re.fullmatch(r'(ld\s+hl,\s*|text_far\s+|writetext\s+|jumptext\s+|jumptextfaceplayer\s+|farwritetext\s+|farjumptext\s+)([A-Za-z_][\w.]*)',body)
            if match:
                target=match[2]
                if 'text' in target.lower():
                    marker=f'ULARef{len(rows):06d}'
                    rows.append({'marker':marker,'target':target,'instruction':body,'file':str(path.relative_to(a.source))})
                    lines.append('.'+marker+':\n');changed=True
            lines.append(line)
        if changed:path.write_text(''.join(lines))
    a.index.write_text(json.dumps(rows,indent=2)+'\n');print('INSTRUMENTED',len(rows))

def recover(a):
    rows=json.loads(a.index.read_text());syms=symbols(a.symbols);rom=a.base.read_bytes();pt=a.translated.read_bytes()
    assert hashlib.sha1(rom).hexdigest()==a.sha1,'Instrumented reference changed ROM bytes'
    markers={k.split('.')[-1]:v for k,v in syms.items() if '.ULARef' in k}
    proof={};rejected=[]
    for row in rows:
        if row['marker'] not in markers:continue # inactive conditional edition
        at=offset(*markers[row['marker']]);target=syms.get(row['target'])
        if not target:rejected.append({**row,'reason':'Unresolved target'});continue
        bank,addr=target;op=row['instruction'].split()[0]
        if op=='ld':length=3;word=1;bank_pos=None;expected_opcode=0x21
        elif op=='text_far':length=4;word=1;bank_pos=3;expected_opcode=0x16
        elif op in ('farwritetext','farjumptext'):length=4;word=2;bank_pos=1;expected_opcode=None
        else:length=3;word=1;bank_pos=None;expected_opcode=None
        original=rom[at:at+length];translated=pt[at:at+length]
        if int.from_bytes(original[word:word+2],'little')!=addr or (bank_pos is not None and original[bank_pos]!=bank):
            rejected.append({**row,'reason':'Operand did not resolve to symbol'});continue
        if expected_opcode is not None:assert original[0]==expected_opcode,row
        if original[0]!=translated[0]:rejected.append({**row,'reason':'Instruction opcode changed'});continue
        new_bank=translated[bank_pos] if bank_pos is not None else bank
        new_addr=int.from_bytes(translated[word:word+2],'little')
        try:offset(new_bank,new_addr)
        except ValueError:rejected.append({**row,'reason':'Target not in ROM'});continue
        key=f'{bank:02x}:{addr:04x}'
        proof.setdefault(key,[]).append({'source':row,'operand_offset':at+word,'target':[new_bank,new_addr],
                                        'original_bytes':original.hex(),'translated_bytes':translated.hex()})
    mapping={};conflicts={}
    for key,refs in proof.items():
        targets={tuple(r['target']) for r in refs}
        if len(targets)==1:mapping[key]=list(targets.pop())
        else:conflicts[key]=refs
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'reference-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
    (a.output/'reference-proof.json').write_text(json.dumps({'base_sha1':a.sha1,'pt_sha1':hashlib.sha1(pt).hexdigest(),'references':proof,'conflicts':conflicts,'rejected':rejected},indent=2)+'\n')
    print('REFERENCE_MAP',len(mapping),'conflicts',len(conflicts),'rejected',len(rejected))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    q=sub.add_parser('instrument');q.add_argument('--source',type=Path,required=True);q.add_argument('--index',type=Path,required=True)
    q=sub.add_parser('recover')
    for name in ('index','symbols','base','translated','output'):q.add_argument('--'+name,type=Path,required=True)
    q.add_argument('--sha1',required=True)
    a=p.parse_args();(instrument if a.mode=='instrument' else recover)(a)
