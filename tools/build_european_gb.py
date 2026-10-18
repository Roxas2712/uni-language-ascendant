"""Build address-only GB language catalogs from audited retail ROM inputs."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from relocate_gen2 import offset

ROOT=Path(__file__).resolve().parents[1]


def lua(v):
    if v is None:return 'nil'
    if isinstance(v,bool):return str(v).lower()
    if isinstance(v,(int,float)):return str(v)
    if isinstance(v,str):
        return re.sub(r'\\u00([0-9a-fA-F]{2})',lambda m:'\\%03d'%int(m[1],16),json.dumps(v,ensure_ascii=False))
    if isinstance(v,list):return '{'+','.join(map(lua,v))+'}'
    return '{'+','.join('['+lua(k)+']='+lua(x) for k,x in v.items())+'}'


def read_symbols(path):
    out={}
    for line in path.read_text().splitlines():
        m=re.match(r'^([0-9a-fA-F]+):([0-9a-fA-F]+) (\S+)',line)
        if m:out[m[3]]=(int(m[1],16),int(m[2],16))
    return out


def cmap_gen2(m,lang):
    cm={int(k):v for k,v in m['charmap'].items()}
    for seq,code in re.findall(r'^\s*charmap "([^"\n]+)",\s*\$([0-9a-fA-F]+)',(ROOT/'build/pokecrystal-es/charmap.asm').read_text(),re.M):
        if all(ord(c)<0x3000 for c in seq):cm[int(code,16)]=seq
    if lang=='fr':
        for code,seq in enumerate('àèéùßçÄÖÜäöüëïâôûêî',0xba):cm[code]=seq
        for code,seq in enumerate(["c'","d'","j'","l'","m'","n'","p'","s'","'s","t'","u'","y'"],0xd4):cm[code]=seq
    cm.update({0x3f:'{ENEMY}',0x14:'{PLAYER}',0x1f:' ',0x22:'\n',0x25:'',0x49:'{MOM}',0x4a:'POKéMON',0x4b:'\v',0x4c:'\v',0x4e:'\n',0x4f:'\n',
               0x51:'\f',0x52:'{PLAYER}',0x53:'{RIVAL}',0x54:'POKé',0x55:'\v',0x56:'……',
               0x59:'{TARGET}',0x5a:'{USER}',0x5b:'PC',0x5c:'CT' if lang=='fr' else 'MT',0x5d:{'es':'ENTREN.','fr':'DRESSEUR','it':'ALLEN.'}[lang],0x5e:'ROCKET',
               0x6d:':',0x70:'PO',0x71:'Ké',0xbc:'é',0xe1:'POKé',0xe2:'MON',0xf0:'¥',0xf2:'.'})
    return cm


def text_recipe(rom,start,generation,dynamic=()):
    pos=offset(*start);parts=[];seen=set();pending=0
    for _ in range(4096):
        assert pos not in seen,'Text command cycle';seen.add(pos)
        command=rom[pos];pos+=1
        if command==0:
            begin=pos
            while rom[pos] not in (0x50,0x57,0x58,0x5f):pos+=1
            if pos>begin:parts.append({'off':begin,'size':pos-begin})
            end=rom[pos];pos+=1
            if end!=0x50:
                if end!=0x5f:parts.append({'token':'{PROMPT}' if end==0x58 else '{DONE}'})
                break
        elif command in (0x50,0x57,0x58):
            if parts:parts.append({'token':'{PROMPT}' if command==0x58 else '{DONE}'})
            break
        elif command==(0x17 if generation==1 else 0x16):
            pos=offset(rom[pos+2],int.from_bytes(rom[pos:pos+2],'little'))
        elif generation==1 and command in (1,2,9):
            expected=dynamic[pending];assert expected[0]==command,'Dynamic command mismatch'
            parts.append({'token':expected[1]});pending+=1;pos+=2 if command==1 else 3
        elif generation==2 and command in (1,9,0x14):
            parts.append({'token':'{NUM}' if command==9 else '{STRBUF}'})
            pos+={1:2,9:3,0x14:1}[command]
        elif generation==2 and command==0xc:pos+=1
        elif generation==2 and command in (5,6,7,0xa,0xb,0xd,0xe,0xf,0x10,0x11,0x12,0x13,0x15):pass
        else:raise ValueError(('Unsupported text command',hex(command),start))
    else:raise ValueError('Unterminated text stream')
    if generation==1:assert pending==len(dynamic),'Missing dynamic field'
    return {'parts':parts}


class Builder:
    def __init__(self,game,lang):
        self.game,self.lang=game,lang
        self.spec=next(x for x in json.loads((ROOT/'build/european-inputs.json').read_text()) if x.get('game')==game and x.get('language')==lang)
        self.rom=Path(self.spec['file']).read_bytes()
        assert hashlib.sha1(self.rom).hexdigest()==self.spec['sha1']
        self.m=json.loads((ROOT/'build/upstream-engine/tools'/('rom_manifest'+('' if game=='red' else '_'+game)+'.json')).read_text())
        self.cats={};self.assets={};self.missing={}

    def span(self,pos,limit=256,fixed=False):
        end=self.rom.find(b'\x50',pos,pos+limit)
        if end<0:
            assert fixed,('Unterminated name',hex(pos),limit)
            end=pos+limit
        return {'parts':[{'off':pos,'size':end-pos}]} if end>pos else {'empty':True}

    def names(self,pos,keys,stride=None):
        result={}
        for key in keys:
            result[key]=self.span(pos,stride or 100,fixed=bool(stride))
            pos=pos+stride if stride else self.rom.index(0x50,pos)+1
        return result,pos

    def gen2(self):
        m=self.m;rom=self.rom;cm=cmap_gen2(m,self.lang);self.cm=cm
        audit=json.loads((ROOT/f'build/{self.game}-{self.lang}-relocation.json').read_text())
        assert audit['sha1']==self.spec['sha1']
        assert not audit['conflicts'],'Conflicting text correspondence'
        dialogue={};named={}
        for key,place in audit['texts'].items():
            try:dialogue[key]=text_recipe(rom,place,2)
            except (ValueError,IndexError,AssertionError) as e:self.missing[key]=str(e)
        for key in m['text']['labels']:
            original=offset(*m['symbols'][key]);target=audit['mapped'].get(str(original))
            if target is None:self.missing[key]='No proven relocation';continue
            try:named[key]=text_recipe(rom,(target//16384,target%16384+0x4000),2)
            except (ValueError,IndexError,AssertionError) as e:self.missing[key]=str(e)
        self.cats['dialogue.lua']=dialogue;self.cats['rom_text.lua']=named
        # The dedicated Names section starts at $4000 in each retail EU build.
        # All 256 item slots, all 66 trainer classes and all 256 fixed cells
        # are walked; no translated-name-length delta is guessed.
        if self.game=='crystal':
            def address(label):return audit['mapped'][str(offset(*m['symbols'][label]))]
            for cat,label,keys,stride in [
                ('item_names','ItemNames',m['constants']['itemOrder'],None),
                ('trainer_class_names','TrainerClassNames',m['constants']['trainerClassOrder'][1:],None),
                ('species_names','PokemonNames',m['constants']['speciesOrder'],10),
                ('move_names','MoveNames',m['constants']['moveOrder'],None)]:
                self.cats[cat+'.lua'],_=self.names(address(label),keys,stride)
        else:
            bank,addr=m['symbols']['ItemNames'];assert addr==0x4000
            start=offset(bank,addr)
            all_items,pos=self.names(start,m['constants']['itemOrder'])
            assert len(m['constants']['itemOrder'])==250
            for _ in range(6):pos=rom.index(0x50,pos)+1
            self.cats['item_names.lua']=all_items
            self.cats['trainer_class_names.lua'],pos=self.names(pos,m['constants']['trainerClassOrder'][1:])
            self.cats['species_names.lua'],_=self.names(pos,m['constants']['speciesOrder'],10)
            pos+=256*10
            self.cats['move_names.lua'],pos=self.names(pos,m['constants']['moveOrder'])
        for cat,label,keys in [('move_descriptions','MoveDescriptions',m['constants']['moveOrder']),
                               ('item_descriptions','ItemDescriptions',m['constants']['itemOrder'][:m['constants']['itemNameCount']])]:
            bank,addr=m['symbols'][label]
            table=audit['mapped'][str(offset(bank,addr))] if self.game=='crystal' else offset(bank,addr)
            bank=table//16384
            values={}
            for i,key in enumerate(keys):
                ptr=int.from_bytes(rom[table+i*2:table+i*2+2],'little')
                assert table%16384+0x4000+len(keys)*2<=ptr<0x8000
                values[key]=self.span(offset(bank,ptr))
            self.cats[cat+'.lua']=values
        self.gen2_extra(audit)
        # The cartridge's font is a fixed-slot atlas; verify the complete
        # uppercase Latin alphabet against the exact US import first.
        inv=json.loads((ROOT/'build/gb-rom-inventory.json').read_text())
        us=Path(next(x['file'] for x in inv if x['sha1']==m['romSha1'])).read_bytes()
        font=offset(*m['symbols']['Font']);font=audit['mapped'].get(str(font),font);assert rom[font:font+26*8]==us[offset(*m['symbols']['Font']):offset(*m['symbols']['Font'])+26*8]
        self.assets['assets/fonts/font.png']={'width':128,'height':64,'bits':1,'transparent':True,'tiles':[{'off':font,'size':1024}]}
        extra=offset(*m['symbols']['FontBattleExtra']);extra=audit['mapped'].get(str(extra),extra)
        self.assets['assets/fonts/font_battle_extra.png']={'width':128,'height':16,'bits':2,'ink':True,'tiles':[{'off':extra,'size':512}]}

    def gen2_extra(self,audit):
        from relocate_gb_refs import recover
        m=self.m;rom=self.rom
        inv=json.loads((ROOT/'build/gb-rom-inventory.json').read_text())
        source=Path(next(x['file'] for x in inv if x['sha1']==m['romSha1'])).read_bytes()
        def address(label):
            bank,addr=m['symbols'][label];old=offset(bank,addr)
            if label=='TypeNames':
                hits=[]
                for at in range(bank*16384,(bank+1)*16384-56):
                    ptrs=[int.from_bytes(rom[at+j*2:at+j*2+2],'little') for j in range(28)]
                    if ptrs[0]!=at%16384+16384+56:continue
                    if all(ptrs[j]==ptrs[0] for j in range(10,19)) and all(ptrs[0]<=v<0x8000 for v in ptrs):hits.append(at)
                assert len(hits)==1,('Type name table topology',len(hits))
                return hits[0]
            if str(old) in audit['mapped']:return audit['mapped'][str(old)]
            try:return recover(source,rom,bank,addr)[0]
            except ValueError:
                assert self.lang!='es'
                es=Path(next(x['file'] for x in json.loads((ROOT/'build/european-inputs.json').read_text()) if x.get('game')==self.game and x.get('language')=='es')).read_bytes()
                if self.game=='crystal':middle=json.loads((ROOT/'build/crystal-es-relocation.json').read_text())['mapped'][str(old)]
                else:middle=recover(source,es,bank,addr)[0]
                return recover(es,rom,middle//16384,middle%16384+16384)[0]
        types=address('TypeNames');bank=types//16384
        self.cats['type_names.lua']={key:self.span(offset(bank,int.from_bytes(rom[types+number*2:types+number*2+2],'little'))) for key,number in m['constants']['types'].items()}
        table=address('TrainerGroups');bank=m['symbols']['Trainers'][0];names={}
        original=offset(*m['symbols']['TrainerGroups'])
        for i,cls in enumerate(m['constants']['trainerClassOrder'][1:]):
            pos=offset(bank,int.from_bytes(rom[table+i*2:table+i*2+2],'little'))
            src=offset(bank,int.from_bytes(source[original+i*2:original+i*2+2],'little'))
            for j,member in enumerate(m['constants']['trainerClassMembers'].get(cls,[])):
                if rom[pos]==255:break
                names[f'{cls}:{j+1}']=self.span(pos,24)
                pos=rom.index(0x50,pos)+1;src=source.index(0x50,src)+1
                assert rom[pos]==source[src],(cls,j,'trainer type')
                typ=rom[pos];assert typ<4;stride=2+(4 if typ&1 else 0)+(1 if typ&2 else 0)
                start=pos;ss=src;pos+=1;src+=1
                for _ in range(6):
                    if rom[pos]==255:break
                    pos+=stride;src+=stride
                assert rom[pos]==source[src]==255
                assert rom[start:pos+1]==source[ss:src+1],(cls,j,'trainer party')
                pos+=1;src+=1
        self.cats['trainer_names.lua']=names
        # Match the entire coordinate table independently of translated pointers.
        bank,addr=m['symbols']['Landmarks'];raw=source[offset(bank,addr):offset(bank,addr)+4*len(m['constants']['landmarkOrder'])]
        pattern=b''.join(re.escape(bytes([v])) if i%4<2 else b'.' for i,v in enumerate(raw))
        hits=list(re.finditer(b'(?=('+pattern+b'))',rom,re.S))
        assert len(hits)==1,('Landmarks',len(hits));table=hits[0].start();bank=table//16384
        landmarks={}
        for i,key in enumerate(m['constants']['landmarkOrder']):
            pos=offset(bank,int.from_bytes(rom[table+i*4+2:table+i*4+4],'little'));end=rom.index(0x50,pos);parts=[];begin=pos
            for j in range(pos,end):
                if rom[j] in (0x1e,0x1f,0x25):
                    if j>begin:parts.append({'off':begin,'size':j-begin})
                    parts.append({'token':'\n'});begin=j+1
            if end>begin:parts.append({'off':begin,'size':end-begin})
            landmarks[key]={'parts':parts} if parts else {'empty':True}
        self.cats['landmark_names.lua']=landmarks
        table=address('PokedexDataPointerTable');dex={};metrics={}
        for i,key in enumerate(m['constants']['speciesOrder']):
            bank=m['symbols'][m['pokemonAssets'][key]['dexLabel']][0]
            pos=offset(bank,int.from_bytes(rom[table+i*2:table+i*2+2],'little'));end=rom.index(0x50,pos,pos+32)
            text=end+4;text2=rom.index(0x50,text)+1
            def dex_span(start):
                stop=rom.index(0x50,start,start+300);parts=[];begin=start
                for j in range(start,stop):
                    if rom[j]==0x4e:
                        if j>begin:parts.append({'off':begin,'size':j-begin})
                        parts.append({'token':'<NEXT>'});begin=j+1
                if stop>begin:parts.append({'off':begin,'size':stop-begin})
                return {'parts':parts}
            dex[key]={'table':[['kind',self.span(pos,32)],['text',dex_span(text)],['text2',dex_span(text2)]]}
            metrics[key]={'value':{'heightM':rom[end+1]/10,'weightKg':int.from_bytes(rom[end+2:end+4],'little')/10}}
            assert 0<metrics[key]['value']['heightM']<15 and 0<metrics[key]['value']['weightKg']<1000,(key,'metric layout')
        self.cats['dex_entries.lua']=dex;self.cats['dex_metrics.lua']=metrics

    def gen1(self):
        game=self.game;m=self.m;rom=self.rom
        spec=json.loads((ROOT/f'build/{game}-es-source-metadata.json').read_text())
        cm={int(k):v for k,v in spec['charmap'].items()}
        cm.update({0x5c:'MT',0x5d:'ENTREN.'})
        for k,v in cm.items():
            for seq,value in [('\\n','\n'),('\\x0c','\f'),('\\x0b','\v')]:v=v.replace(seq,value)
            if re.fullmatch(r'<[^<>]+>',v):v='{'+v[1:-1]+'}'
            cm[k]=v
        cm.update({0x4b:'{_CONT}',0x4c:'{SCROLL}',0x6d:'{COLON}',0xf0:'¥'})
        self.cm=cm;places=dict(spec['dialogue'])
        if game=='red':places.update({k:list(v) for k,v in read_symbols(ROOT/'build/pokered-es/pokered.sym').items() if k in m['text']['labels']})
        if game=='yellow':places.update(json.loads((ROOT/'tools/data/yellow-es-extra-addresses.json').read_text()))
        rows={}
        for key in m['text']['labels']:
            if key not in places:self.missing[key]='No address metadata';continue
            try:
                dynamic=m['text']['dynamic'].get(key,[])
                if game=='yellow' and key=='_SafariZoneGateSafariZoneWorker1ThatllBe500PleaseText':dynamic=[]
                rows[key]=text_recipe(rom,places[key],1,dynamic)
            except (ValueError,IndexError,AssertionError) as e:self.missing[key]=str(e)
        self.cats['dialogue.lua']=rows
        for key,table in spec['names'].items():
            out,_=self.names(offset(table['bank'],table['address']),table['order'],table.get('width'))
            self.cats[{'species':'species_names','moves':'move_names','items':'item_names','trainers':'trainer_names'}[key]+'.lua']=out
        self.cats['type_names.lua']={row['id']:self.span(offset(row['bank'],row['address'])) for row in spec['types']}
        dex=spec['dex'];table=offset(dex['bank'],dex['address']);kinds={};metrics={}
        for i,key in enumerate(dex['order']):
            if key not in m['dexOrder']:continue
            ptr=int.from_bytes(rom[table+i*2:table+i*2+2],'little');pos=offset(dex['bank'],ptr);end=rom.index(0x50,pos)
            kinds[key]=self.span(pos,32)
            metrics[key]={'value':{'heightM':rom[end+1]/10,'weightKg':int.from_bytes(rom[end+2:end+4],'little')/10}}
        self.cats['dex_kinds.lua']=kinds;self.cats['dex_metrics.lua']=metrics
        gfx=spec['gfx']
        for key,path,w,h,bits in [('font','fonts/font.png',128,64,1),('hpbar','battle/font_battle_extra.png',120,16,2),('version','title/'+game+'_version.png',80,8,1)]:
            if key in gfx:
                g=gfx[key];self.assets['assets/'+path]={'width':w,'height':h,'bits':bits,'transparent':True,'tiles':[{'off':offset(g['bank'],g['address']),'size':w*h*bits//8}]}

    def save(self):
        generation=self.m.get('generation',1)
        ui=json.loads((ROOT/'translations/european/gb-ui.json').read_text())
        ix={'es':0,'fr':1,'it':2}[self.lang]
        self.cats.setdefault('strings.lua',{}).update({k:{'value':v[ix]} for k,v in ui.items()})
        self.cats.setdefault('status_labels.lua',{})
        profile={k:self.spec[k] for k in ['sha1','md5','size']}
        profile.update(game=self.game,language=self.lang,charmap={str(k):v for k,v in self.cm.items()},
                       fontmap={v:k for k,v in self.cm.items() if len(v)==1 and k>=0x80},catalogs=sorted(self.cats))
        profile['fontmap'][' ']=0x7f
        dest=ROOT/f'mod/gb/profiles/{self.game}_{self.lang}';dest.mkdir(exist_ok=True,parents=True)
        for name,rows in self.cats.items():(dest/name).write_text('return '+lua({'table':[[k,v] for k,v in sorted(rows.items())]})+'\n')
        for name,obj in [('profile.lua',profile),('assets.lua',self.assets)]:(dest/name).write_text('return '+lua(obj)+'\n')
        report={'game':self.game,'language':self.lang,'sha1':self.spec['sha1'],'catalogs':{k:len(v) for k,v in self.cats.items()},'missing':self.missing}
        (ROOT/f'build/{self.game}-{self.lang}-gb-profile-report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(self.game,self.lang,'catalogs',report['catalogs'],'missing',len(self.missing))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('game');p.add_argument('language');a=p.parse_args()
    b=Builder(a.game,a.language)
    (b.gen1 if a.game in ('red','yellow') else b.gen2)();b.save()
