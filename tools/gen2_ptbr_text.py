"""Decode Gen-2 cartridge text into address recipes and audit substitutions.

This development tool does not activate profiles. Identical addresses and
matching operands are necessary checks, not semantic translation evidence.
"""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
from gen1_ptbr_dialogue import offset
from lua_literal import lua

NO_GLYPH={5,7,10,11,13,14,15,16,17,18,19,21}
SLOTS={0x52:'{PLAYER}',0x53:'{RIVAL}',0x59:'{TARGET}',0x5a:'{USER}',0x3f:'{ENEMY}'}
PT_ACCENTS={0xba:'á',0xbb:'â',0xbc:'ã',0xbd:'à',0xbe:'ê',0xbf:'í',
            0xc0:'ó',0xc1:'ô',0xc2:'õ',0xc3:'ú',0xc4:'ç',0xc5:'º',
            0xcb:'Á',0xcc:'Ô',0xcd:'Í',0xce:'Ã',0xcf:'Â',0xd0:'Ê',0xd1:'Ó',0xd4:'Ç',0xd5:'Ã',0xd6:'Õ',0xeb:'Ú'}

def alphabet(manifest, portuguese=False, crystal=False):
    cm={int(k):v for k,v in manifest['charmap'].items() if not any(0x3000<=ord(c)<=0x30ff or 0xff00<=ord(c)<=0xffef for c in v)}
    cm.update({0x1f:' ',0x22:'\n',0x25:' ',0x4e:'\n',0x4f:'\n',0x51:'\f',0x55:'\v',0x54:'POKé',0x56:'……',0x7f:' ',0xe1:'POKé',0xe2:'MON'})
    cm.update({0x24:'POKé',0x4a:'POKéMON',0x49:'{MOM}',0x4b:'\v',0x4c:'\v',0x5b:'PC',0x5c:'TM',0x5d:'TRAINER',0x5e:'ROCKET',0x70:'PO',0x71:'Ké',0x6d:':'})
    cm.update(SLOTS)
    if portuguese:
        cm.update(PT_ACCENTS)
        cm.update({0x24:'QU',0x56:'DADE',0x4a:'DO',0x5b:'ÃO',0x5c:'TA',0x5d:'POKéMON',0x5e:'SEGUND',0xc6:'AR',0xc7:'ER',0xc8:'SOU',0xca:'AL',0xd2:'UR',0xd3:'M',0xd7:'É',0xd8:'Pá',0xd9:'C',0xda:'NA',0xdb:'PR',0xdc:'GO',0xdd:'IR',0xde:'PE'})
    if portuguese and crystal:
        cm.update({0x5e:'NÍVEL',0xc8:'SOU',0xd7:'É',0xdc:'GO',0x49:'ado',0x35:'PROFESSOR',0x36:'batalh',0x37:'está',0x38:'ndo',0x39:'ão',0x23:'Você'})
    return cm

def decode(rom, bank, address, cm, crystal=False):
    pos=offset(bank,address);start=pos;parts=[];signature=[];inside=False;seen=set();out=[]
    def token(s):parts.append({'token':s});out.append(s)
    def glyph(p,b):
        ch=cm.get(b)
        if ch is None or ch.startswith('<'):raise ValueError(f'Undefined glyph {b:02x} at {p:x}')
        if parts and 'off' in parts[-1] and parts[-1]['off']+parts[-1]['size']==p:parts[-1]['size']+=1
        else:parts.append({'off':p,'size':1})
        out.append(ch)
        if ch in SLOTS.values():signature.append(('slot',ch))
    for _ in range(8192):
        if pos in seen:raise ValueError('Text cycle')
        seen.add(pos);p=pos;b=rom[pos];pos+=1
        if b==0x50:
            if not inside:break
            inside=False
        elif b in (0x57,0x58):
            if parts:token('{DONE}' if b==0x57 else '{PROMPT}')
            break
        elif b==0:inside=True
        elif b==0x16 and not inside:
            addr=int.from_bytes(rom[pos:pos+2],'little');bank=rom[pos+2];pos=offset(bank,addr)
        elif b==1:
            operand=rom[pos:pos+2];pos+=2;signature.append(('ram',operand.hex()));token('{STRBUF}')
        elif b==9 and not inside:
            operand=rom[pos:pos+3];pos+=3;signature.append(('num',operand.hex()));token('{NUM}')
        elif b==0x14 and not inside:
            signature.append(('buffer',rom[pos]));pos+=1;token('{STRBUF}')
        elif b==0x14 and inside and crystal:
            signature.append(('slot','{PLAYER}'));token('{PLAYER}')
        elif b==0x0c and not inside:pos+=1
        elif b==6 or (not inside and b in NO_GLYPH):pass
        else:glyph(p,b)
    else:raise ValueError('Unterminated text')
    return {'parts':parts},signature,''.join(out)


def main(a):
    m=json.loads(a.manifest.read_text());base=a.base_rom.read_bytes();pt=a.rom.read_bytes()
    assert hashlib.sha1(base).hexdigest()==m['romSha1'],'Wrong US revision'
    expected={'gold':'652c0208a5c54313e2d3efb336346e59a17cbab6','silver':'9d9536f14a1874d27ea9167fdf00b80439204a6d','crystal':'e41c519d7ca680facf546fa34b7b00f3149f428f'}
    assert hashlib.sha1(pt).hexdigest()==expected[a.game],'Wrong PT-BR revision'
    labels={k:tuple(m['symbols'][k]) for k in m['text']['labels']}
    texts=json.loads(subprocess.check_output([a.luajit,str(a.engine/'tools/lua_to_json.lua'),str(a.cache/'data/generated/text.lua')]))
    labels.update({k:tuple(int(v,16) for v in k.split(':')) for k in texts if re.fullmatch(r'[0-9a-f]{2}:[0-9a-f]{4}',k)})
    root=Path(__file__).resolve().parents[1]
    corrections=json.loads((root/'translations/pt-BR/gen2-corrections.json').read_text())
    fingerprints=json.loads((root/'translations/pt-BR/gen2-correction-sources.json').read_text())
    authored={fingerprints[k]:v for k,v in corrections.items()}
    extra=root/'translations/pt-BR'/f'{a.game}-corrections.json'
    if extra.exists():
        extra_fingerprints=json.loads(extra.with_name(f'{a.game}-correction-sources.json').read_text())
        authored.update({extra_fingerprints[k]:v for k,v in json.loads(extra.read_text()).items()})
    authored_keys=[]
    crystal=a.game=='crystal'
    cm=alphabet(m,True,crystal);references=json.loads(a.references.read_text()) if a.references else {};rows={};failed={};review=[];same=[]
    for key,at in labels.items():
        try:
            _,sig,original=decode(base,*at,alphabet(m),crystal)
            fingerprint=hashlib.sha256(json.dumps([original,sig],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
            if fingerprint in authored:
                value=authored[fingerprint]
                expected=re.findall(r'\{(?:PLAYER|RIVAL|TARGET|USER|ENEMY|STRBUF|NUM)\}',original)
                assert re.findall(r'\{(?:PLAYER|RIVAL|TARGET|USER|ENEMY|STRBUF|NUM)\}',value)==expected,key
                rec={'value':value};pt_sig=sig;authored_keys.append(key)
            else:
                mapped=references.get(f'{at[0]:02x}:{at[1]:04x}',at);rec,pt_sig,value=decode(pt,*mapped,cm,crystal)
            if sig!=pt_sig:raise ValueError(f'Substitution changed: {sig!r} -> {pt_sig!r}')
            rows[key]=rec
            if value==original and any(c.isalpha() for c in value):same.append(key)
            review.append({'key':key,'original':original,'translated':value,'same':value==original})
        except (ValueError,IndexError) as e:failed[key]=str(e)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'dialogue.lua').write_text('return '+lua({'table':[[k,v] for k,v in sorted(rows.items())]})+'\n')
    (a.output/'charmap.json').write_text(json.dumps(cm,ensure_ascii=False,indent=2))
    report={'game':a.game,'total':len(labels),'decoded':len(rows),'authored_keys':authored_keys,'failures':failed,'unchanged':same,'semantic_alignment_verified':False,'runtime_enabled':False}
    (a.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    assert 'build' in a.output.parts,'Private source audit must stay under build/'
    (a.output/'private-recipes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    (a.output/'private-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2))
    print(json.dumps({k:len(v) if isinstance(v,(dict,list)) else v for k,v in report.items()}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('manifest','base-rom','rom','output','cache','engine'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--references',type=Path)
    p.add_argument('--game',choices=['gold','silver','crystal'],required=True);p.add_argument('--luajit',required=True);main(p.parse_args())
