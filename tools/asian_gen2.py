"""Strict, ROM-backed Gen2 text recipes for multibyte Korean and Japanese.

All locations are private build evidence; no cartridge text is embedded here.
"""
import json
import re
from pathlib import Path


def symbols(path):
    return {m[3]: (int(m[1],16), int(m[2],16)) for line in Path(path).read_text().splitlines()
            if (m := re.match(r'([0-9a-fA-F]+):([0-9a-fA-F]+) (\S+)',line))}


def offset(bank,address):
    assert 0<=bank<128 and 0<=address<0x8000
    return address if address<0x4000 else bank*0x4000+address-0x4000


class TextReader:
    def __init__(self,rom,language,charmap):
        self.rom,self.language,self.charmap=rom,language,charmap
        self.terminators={0x50,0x5e,0x5f} if language=='ko' else {0x50,0x57,0x58,0x5f}

    def span(self,at,limit=8192,fixed=False,tokens=None):
        start=at;out=[];parts=[];begin=at
        def recipe(end):
            if end>begin:parts.append({'off':begin,'size':end-begin})
            return {'parts':parts} if parts else {'empty':True}
        while at<min(len(self.rom),start+limit):
            first=self.rom[at]
            if first in self.terminators:
                return recipe(at),''.join(out),at+1,first
            if tokens and first in tokens:
                if at>begin:parts.append({'off':begin,'size':at-begin})
                parts.append({'token':tokens[first]});out.append(tokens[first]);at+=1;begin=at;continue
            at+=1;code=str(first)
            if self.language=='ko' and 1<=first<=11:
                assert at<min(len(self.rom),start+limit),'Truncated Korean character'
                code=f'{first}:{self.rom[at]}';at+=1
            assert code in self.charmap,('Unknown character',code,hex(at-1))
            out.append(self.charmap[code])
        if fixed and at==start+limit:return recipe(at),''.join(out),at,None
        raise ValueError(('Unterminated string',hex(start)))

    def text(self,at,stop_at=None):
        parts=[];rendered=[];seen=set()
        for _ in range(2048):
            if stop_at is not None:
                assert at<=stop_at,('Fragment crossed command boundary',hex(at),hex(stop_at))
                if at==stop_at:break
            assert at not in seen,('Text cycle',hex(at));seen.add(at)
            cmd=self.rom[at];at+=1
            if cmd==0:
                recipe,text,at,end=self.span(at)
                parts.extend(recipe.get('parts',[]));rendered.append(text)
                if end!=0x50:
                    token='{PROMPT}' if end==(0x5f if self.language=='ko' else 0x58) else '{DONE}'
                    parts.append({'token':token});rendered.append(token);break
            elif cmd==0x50:break
            elif cmd==0x16:
                at=offset(self.rom[at+2],int.from_bytes(self.rom[at:at+2],'little'))
            elif cmd in (1,2,9,0x14):
                token='{NUM}' if cmd in (2,9) else '{STRBUF}'
                parts.append({'token':token});rendered.append(token);at+={1:2,2:3,9:3,0x14:1}[cmd]
            elif cmd==0xc:at+=1
            elif cmd in (5,6,7,0xa,0xb,0xd,0xe,0xf,0x10,0x11,0x12,0x13,0x15):pass
            else:raise ValueError(('Unsupported text command',hex(cmd),hex(at-1)))
        else:raise ValueError('Text command limit')
        return {'parts':parts} if parts else {'empty':True},''.join(rendered)


def korean_charmap(root):
    root=Path(root);out={}
    for p in sorted((root/'constants/charmap').glob('korean_table_*.asm')):
        body=p.read_text();table=int(re.search(r'def_kr_table (\d+)',body)[1])
        for char,byte in re.findall(r'kr_charmap "([^"\n]+)",\s*\$([\da-fA-F]+)',body):out[f'{table}:{int(byte,16)}']=char
    for p in (root/'constants/charmap/japanese.asm',root/'constants/charmap.asm'):
        for char,byte in re.findall(r'(?<!_)charmap "([^"\n]+)",\s*\$([\da-fA-F]+)',p.read_text()):
            if not char.startswith('<') and char not in ('@','#'):out[str(int(byte,16))]=char
    out.update({str(k):v for k,v in {0x1d:' ',0x1e:'\n',0x1f:'공격',0x33:'포켓',0x34:'',0x35:'번 도로',0x36:'나',0x37:'여기는',0x46:'포켓몬',0x47:'포켓몬',0x48:'……',0x49:'컴퓨터',0x4a:'기술머신',0x4b:'로켓단',0x4c:'',0x4d:'레드',0x4e:'그린',0x4f:'{ENEMY}',0x51:'{PLAYER}',0x52:'{RIVAL}',0x53:'{TARGET}',0x54:'{USER}',0x55:'트레이너',0x56:'\v',0x57:'\v',0x59:'\n',0x5a:'\n',0x5b:'{MOM}',0x5c:'\f',0x5d:'\v',0x7f:' '}.items()})
    return out


def japanese_charmap(path):
    # pret's explicit Japanese section overrides the shared Latin byte slots.
    body=Path(path).read_text();out={};nested=0
    for line in body.splitlines():
        # Mobile ASCII and Unown use separate RGBDS charmap scopes. Their
        # control bytes must never overwrite kana (09=ゴ, 0a=ザ, 0d=ゼ).
        directive=line.split(';',1)[0].strip()
        if directive=='pushc':nested+=1;continue
        if directive=='popc':nested-=1;assert nested>=0;continue
        if nested:continue
        if hit:=re.match(r'\s*charmap "([^"\n]+)",\s*\$([\da-fA-F]+)',line):
            char,byte=hit.groups()
            if not char.startswith('<') and char not in ('@','#'):out[str(int(byte,16))]=char
    assert nested==0,'Unclosed RGBDS charmap scope'
    out.update({str(k):v for k,v in {0x14:'{PLAYER}',0x15:'{DAY}',0x18:'ノ゛',0x1d:'に　',0x1e:'って',0x1f:'を　',0x22:'た！',0x23:'こうげき',0x24:'は　',0x25:'の　',0x35:'ばん　どうろ',0x36:'わたし',0x37:'ここは',0x38:'レッド',0x39:'グリーン',0x3f:'{ENEMY}',0x49:'{MOM}',0x4a:'が　',0x4b:'\v',0x4c:'\v',0x4e:'\n',0x4f:'\n',0x51:'\f',0x52:'{PLAYER}',0x53:'{RIVAL}',0x54:'ポケモン',0x55:'\v',0x56:'……',0x59:'{TARGET}',0x5a:'{USER}',0x5b:'パソコン',0x5c:'わざマシン',0x5d:'トレーナー',0x5e:'ロケットだん',0x72:'『'}.items()})
    return out
