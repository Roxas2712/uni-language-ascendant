"""Build address-only Korean Gen2 profiles from exact, locally supplied ROMs.

Profiles remain development-only until the independent live QA gate enables them.
"""
import collections,hashlib,json,re,sys
from pathlib import Path
from asian_gen2 import TextReader,korean_charmap,symbols,offset
from build_european_gb import lua
from asian_engine_bindings import bind
from asian_menu_labels import labels
from asian_engine_ui import translations as engine_ui
from asian_engine_extra import translations as engine_extra
from asian_engine_fields import translations as engine_fields
from asian_text_arguments import argument_orders
from asian_engine_ui import harvest
R=Path(__file__).resolve().parents[1];B=R/'build/asian-gen2'
REFERENCE=R.parent/'Uni-Language-Ascendant-Europe/build'

# English-only regional branches have no corresponding Korean cartridge text.
# These are explicit authored translations, never represented as ROM spans.
AUTHORED={
'21:66db':'명예의 전당 마스터!',
'5e:4d7f':'그래픽 디자이너가\n상장을 인쇄해 줄 거야.\f가서 자랑해 봐!{DONE}',
'5e:4dd0':'나는 그래픽 디자이너!\n너의 모습을 그렸어!{DONE}',
'5e:4df4':'나는 그래픽 디자이너!\f포켓몬 도감을\n완성했구나!\f상장을 인쇄할까?{DONE}',
'5e:4e4c':'상장을 인쇄하고 싶으면\n말을 걸어 줘!{DONE}',
'60:5878':'서머 타임을 바꾸려면\n집으로 돌아오렴.\f그런데 포켓기어는\n사용할 줄 아니?{DONE}',
'60:58e0':'포켓기어를 켜고\n전화 표시를 고르면\n되는 거지?{DONE}',
'60:591c':'설명서를 읽어 볼게.\f포켓기어를 켜고\n전화 표시를 골라.{DONE}',
'60:5965':'전화번호는 저장돼 있어.\f전화하고 싶은 사람의\n이름을 고르면 돼.\f정말 편리하구나!{DONE}'}
NAMED_AUTHORED={
'_DSTIsThatOKText':'이 시간이 맞나요?{DONE}',
'_MomLostGearBookletText':'포켓기어 설명서를\n어디에 두었더라?{DONE}',
'_TimeAskOkayText':'이 시간이 맞나요?{DONE}',
'_TimesetAskAdjustDSTText':'서머 타임으로\n바꾸겠습니까?{DONE}',
'_TimesetAskDSTText':'서머 타임입니까?{DONE}',
'_TimesetAskNotDSTText':'서머 타임이 아닙니까?{DONE}',
'_TimesetDSTText':'서머 타임입니다.{DONE}',
'_TimesetNotDSTText':'서머 타임이 아닙니다.{DONE}'}
UI={'YES':'예','NO':'아니오','Yes':'예','No':'아니오','CANCEL':'취소','CANCEL?':'취소할까?', 'POKéMON':'포켓몬','POKEMON':'포켓몬','POKéDEX':'포켓몬 도감','POKEDEX':'포켓몬 도감','PACK':'가방','POKéGEAR':'포켓기어','POKEGEAR':'포켓기어','SAVE':'저장','OPTION':'설정','OPTIONS':'설정','EXIT':'닫기','FIGHT':'싸운다','PKMN':'포켓몬','RUN':'도망간다','ITEM':'도구','ITEMS':'도구','KEY ITEMS':'중요한 도구','BALLS':'몬스터볼','TM/HM':'기술머신','STATS':'능력치','SWITCH':'순서 바꾸기','MOVE':'이동','MOVES':'기술','CANCEL':'취소','USE':'사용','GIVE':'지니게 한다','TOSS':'버리기','QUIT':'그만두기','CONTINUE':'계속하기','NEW GAME':'처음부터','NEW GAME?':'처음부터 할까?','ATTACK':'공격','DEFENSE':'방어','SPCL.ATK':'특수공격','SPCL.DEF':'특수방어','SPEED':'스피드','STATUS':'상태','NAME':'이름','TRAINER':'트레이너','TRAINER CARD':'트레이너 카드','MONEY':'돈','TIME':'시간','PLAY TIME':'플레이 시간','BADGES':'배지','TYPE':'타입','LEVEL':'레벨','HP':'HP','PP':'PP','EXP. POINTS':'경험치','NEXT LEVEL':'다음 레벨','NORMAL':'노말','FIRE':'불꽃','WATER':'물','GRASS':'풀','ELECTRIC':'전기','ICE':'얼음','FIGHTING':'격투','POISON':'독','GROUND':'땅','FLYING':'비행','PSYCHIC':'에스퍼','BUG':'벌레','ROCK':'바위','GHOST':'고스트','DRAGON':'드래곤','DARK':'악','STEEL':'강철','BUY':'산다','SELL':'판다','WELCOME!':'어서 오세요!','PAGE':'설명','AREA':'분포','CRY':'울음','PRNT':'인쇄','HT':'키','WT':'몸무게',' PAGE AREA CRY PRNT':' 설명   분포   울음  인쇄','lower':'문자','UPPER':'문자','DEL':'삭제','END':'결정','YOUR NAME?':'이름은?','RIVAL\'S NAME?':'라이벌 이름은?','MOTHER\'S NAME?':'어머니 이름은?','BOX NAME?':'박스 이름은?','NICKNAME?':'별명은?','%s\'S':'%s의'}

def build(game):
    source=R/'build/pokegold-kr';rom=(source/f'poke{game}.gbc').read_bytes();sy=symbols(source/f'poke{game}.sym');us_symbols=symbols(REFERENCE/f'pokegold/poke{game}.sym')
    expected={'gold':'c0ff3999e1093e1af59ef3eea3f1bfd7c1f18a65','silver':'cb22d7e03a74dc3a563fde6be8626626b2b392e7'}[game]
    assert hashlib.sha1(rom).hexdigest()==expected
    m=json.loads((R/f'build/upstream-engine/tools/rom_manifest_{game}.json').read_text());cm=korean_charmap(source);reader=TextReader(rom,'ko',cm)
    us_rom=(REFERENCE/f'pokegold/poke{game}.gbc').read_bytes();assert hashlib.sha1(us_rom).hexdigest()==m['romSha1']
    graph=json.loads((R/f'tools/asian_gen2_refs/{game}.json').read_text());assert graph['sourceSha1']==expected and graph['baseSha1']==m['romSha1'];base=dict.fromkeys(graph['dialogueKeys']);reverse=collections.defaultdict(list)
    for name,(bank,address) in us_symbols.items():reverse[f'{bank:02x}:{address:04x}'].append(name)
    cats={};decoded={};fail={}
    for key,text in base.items():
        names=[n for n in reverse[key] if n in sy]
        loc=sy[names[0]] if names else graph['texts'].get(key)
        try:
            if key in AUTHORED:recipe,value={'value':AUTHORED[key]},AUTHORED[key]
            elif loc:
                at=offset(*loc);b,a=(int(n,16) for n in key.split(':'));command=us_rom[offset(b,a)]<=0x16
                if command:recipe,value=reader.text(at)
                else:recipe,value,*_=reader.span(at)
            else:raise ValueError('No proven target')
            cats.setdefault('dialogue.lua',{})[key]=recipe;decoded[key]=value
        except (ValueError,AssertionError,IndexError) as e:fail[key]=str(e)
    assert not fail,fail
    named={}
    for name in m['text']['labels']:
        if name in NAMED_AUTHORED:named[name]={'value':NAMED_AUTHORED[name]}
        else:named[name]=reader.text(offset(*sy[name]))[0]
    cats['rom_text.lua']=named
    cats['text_arguments.lua']=argument_orders(TextReader(us_rom,'en',m['charmap']),us_symbols,reader,{k:offset(*sy[k])for k in named if k in sy and k not in NAMED_AUTHORED},native_symbols=sy)
    def at(name):return offset(*sy[name])
    def names(name,keys,stride=None):
        pos=at(name);out={}
        for key in keys:
            recipe,_,end,_=reader.span(pos,stride or 512,fixed=bool(stride));out[key]=recipe;pos=pos+stride if stride else end
        return out
    for name,cat,keys,stride in [('PokemonNames','species_names',m['constants']['speciesOrder'],10),('MoveNames','move_names',m['constants']['moveOrder'],None),('ItemNames','item_names',m['constants']['itemOrder'],None),('TrainerClassNames','trainer_class_names',m['constants']['trainerClassOrder'][1:],None)]:cats[cat+'.lua']=names(name,keys,stride)
    def pointer(table,index):
        start=at(table);return offset(start//16384,int.from_bytes(rom[start+2*index:start+2*index+2],'little'))
    for table,cat,keys in [('MoveDescriptions','move_descriptions',m['constants']['moveOrder']),('ItemDescriptions','item_descriptions',m['constants']['itemOrder'][:m['constants']['itemNameCount']])]:cats[cat+'.lua']={key:reader.span(pointer(table,i))[0] for i,key in enumerate(keys)}
    cats['type_names.lua']={key:reader.span(pointer('TypeNames',number))[0] for key,number in m['constants']['types'].items()}
    cats['landmark_names.lua']={}
    table=at('Landmarks')
    for i,key in enumerate(m['constants']['landmarkOrder']):
        pos=offset(table//16384,int.from_bytes(rom[table+i*4+2:table+i*4+4],'little'));cats['landmark_names.lua'][key]=reader.span(pos)[0]
    dex={};metrics={}
    for key in m['constants']['speciesOrder']:
        label=m['pokemonAssets'][key]['dexLabel'];pos=at(label);kind,_,end,_=reader.span(pos)
        # Korean retail has a single three-line entry, not two English pages.
        t1,_,_,_=reader.span(end+3,tokens={0x59:'<NEXT>'});t2={'empty':True}
        dex[key]={'table':[['kind',kind],['text',t1],['text2',t2]]}
        metrics[key]={'value':{'heightM':rom[end]/10,'weightKg':int.from_bytes(rom[end+1:end+3],'little')/10}}
        assert 0<metrics[key]['value']['heightM']<15 and 0<metrics[key]['value']['weightKg']<1000,key
    cats['dex_entries.lua']=dex;cats['dex_metrics.lua']=metrics
    # Exact English text -> source-derived localized text for authored UI callers.
    strings={}
    strings.update({k:{'value':v} for k,v in UI.items()})
    pos=at('BattleMenuHeader.Text')
    for key in ('FIGHT','PACK','<PK><MN>','RUN'):
        recipe,_,pos,_=reader.span(pos);strings[key]=recipe
    strings['TYPE/']=reader.span(at('MoveInfoBox.Type'))[0]
    strings['Disabled!']=reader.span(at('MoveInfoBox.Disabled'))[0]
    strings.update({k:v for k,v in bind(R/'build/upstream-engine',TextReader(us_rom,'en',m['charmap']),us_symbols,reader,{k:offset(*sy[k])for k in named if k in sy},named).items()if k not in strings})
    strings.update({k:{'value':v}for k,v in {
      'Wild %s appeared!':'앗! 야생의\n%s(이)가 나타났다!',
      'Go! %s!':'가랏! %s!',
      '%s\nused %s!':'%s의\n%s!',
      '%s used %s!':'%s의\n%s!',
      'Enemy %s fainted!':'상대 %s(은)는\n쓰러졌다!',
      '%s fainted!':'%s(은)는\n쓰러졌다!',
      '%s gained %d EXP. Points!':'%s(은)는\n%d 경험치를 얻었다!',
      '%s gained a boosted %d EXP. Points!':'%s(은)는 특별히\n%d 경험치를 얻었다!',
      '%s grew to level %d!':'%s(은)는\n레벨 %d(으)로 올랐다!',
      '%s wants to battle!':'%s(이)가\n승부를 걸어왔다!',
      '%s sent out %s!':'%s(은)는\n%s(을)를 내보냈다!',
    }.items()})
    cats['strings.lua']=strings
    cats['status_labels.lua']={k:{'value':v} for k,v in {'PSN':'독','PAR':'마비','SLP':'잠듦','BRN':'화상','FRZ':'얼음','FNT':'기절'}.items()}
    # Trainer groups are matched by canonical class/member IDs, never names.
    trainer_names={}
    for i,cls in enumerate(m['constants']['trainerClassOrder'][1:]):
        pos=pointer('TrainerGroups',i)
        source_table=offset(*us_symbols['TrainerGroups']);src=offset(source_table//16384,int.from_bytes(us_rom[source_table+i*2:source_table+i*2+2],'little'))
        for j,member in enumerate(m['constants']['trainerClassMembers'].get(cls,[])):
            assert rom[pos]!=255,(cls,j,'Missing trainer')
            name,_,pos,_=reader.span(pos,32);trainer_names[f'{cls}:{j+1}']=name
            src=us_rom.index(0x50,src,src+32)+1;target_party=pos;source_party=src
            typ=rom[pos];assert typ<4;assert typ==us_rom[src];stride=2+(4 if typ&1 else 0)+(1 if typ&2 else 0);pos+=1;src+=1
            for _ in range(6):
                if rom[pos]==255:break
                pos+=stride;src+=stride
            assert rom[pos]==us_rom[src]==255
            parties=(us_rom[source_party:src+1].hex(),rom[target_party:pos+1].hex())
            # Native regional Pokéfan has a level-58 Magikarp in the last slot;
            # US has a level-29 Seaking. Only his name is imported.
            assert parties[0]==parties[1] or (cls,j+1,parties)==('POKEFANM',12,('021d22ad1dc7ad1d77adff','021d22ad1dc7ad3a81adff')),(cls,j+1,'Trainer party identity differs',parties)
            pos+=1;src+=1
    cats['trainer_names.lua']=trainer_names
    def table(rows):return {'table':[[k,v] for k,v in rows.items()]}
    def spec(old,new):return table({'from':{'value':old},'to':new})
    us_reader=TextReader(us_rom,'en',m['charmap'])
    trades=[];source_trade=offset(*us_symbols['NPCTrades']);target_trade=at('NPCTrades')
    for i in range(6):
        src=source_trade+i*32;dst=target_trade+i*32
        assert us_rom[src:src+3]==rom[dst:dst+3] and us_rom[src+14:src+19]==rom[dst+14:dst+19] and us_rom[src+30:src+32]==rom[dst+30:dst+32]
        fields={}
        for field,relative in [('nickname',3),('otName',19)]:
            original=us_reader.span(src+relative,11)[1]
            fields[field]=spec(original,reader.span(dst+relative,11)[0])
        trades.append(table(fields))
    identities={'trades':{'array':trades}}
    identities['shuckle']=table({field:spec(us_reader.span(offset(*us_symbols[label]))[1],reader.span(at(label))[0]) for field,label in [('nickname','SpecialShuckleNickname'),('otName','SpecialShuckleOT')]})
    cats['mon_names.lua']=identities
    script_strings={}
    for key,loc in graph['strings'].items():
        bank,address=(int(x,16) for x in key.split(':'))
        original=us_reader.span(offset(bank,address))[1]
        script_strings[original]=reader.span(offset(*loc))[0]
    cats['script_strings.lua']=script_strings
    assets={};fontmap={};pages={}
    # Native 8x16 Hangul. Each encoded character occupies two 8x8 ROM tiles.
    for prefix in range(1,12):
        path=f'assets/fonts/hangul-{prefix}.png';start=0x1e0000+prefix*4096
        assets[path]={'width':128,'height':256,'bits':1,'transparent':True,'tiles':[{'off':start,'size':4096}]}
        pages[str(prefix)]={'path':path,'base':0x1000+prefix*512}
    for code,char in cm.items():
        if ':' in code and len(char)==1:
            prefix,second=map(int,code.split(':'));fontmap[char]=0x1000+prefix*512+second*2
    # Naming jamo live in Hangul page B, not in the Latin main font.
    for code,char in cm.items():
        if code.startswith('11:') and len(char)==3 and char[0]=='<' and 0x3130<=ord(char[1])<=0x318f:
            fontmap[char[1]]=0x1000+11*512+int(code.split(':')[1])*2
    cats['font_pages.lua']={'lookupDialogue':{'value':True},'pages':{'value':pages}}
    cats['strings.lua'].update(labels('ko',harvest(R/'build/upstream-engine')))
    cats['strings.lua'].update({k:v for k,v in engine_ui('ko',harvest(R/'build/upstream-engine')).items()if k not in cats['strings.lua']})
    cats['strings.lua'].update({k:v for k,v in engine_extra('ko',harvest(R/'build/upstream-engine')).items()if k not in cats['strings.lua']})
    cats['strings.lua'].update({k:v for k,v in engine_fields('ko',harvest(R/'build/upstream-engine')).items()if k not in cats['strings.lua']})
    # Finite prize labels use exactly the native item/species name recipes.
    for source,ident in {'TM32':'TM_DOUBLE_TEAM','TM29':'TM_PSYCHIC_M','TM15':'TM_HYPER_BEAM','TM25':'TM_THUNDER','TM14':'TM_BLIZZARD','TM38':'TM_FIRE_BLAST'}.items():cats['strings.lua'][source]=cats['item_names.lua'][ident]
    for source in ['MR.MIME','EEVEE','PORYGON','ABRA','EKANS','SANDSHREW','DRATINI']:cats['strings.lua'][source]=cats['species_names.lua'][source.replace('.','__')]
    profile={'sha1':expected,'md5':hashlib.md5(rom).hexdigest(),'size':len(rom),'game':game,'language':'ko','encoding':'korean-gen2','charmap':cm,'fontmap':fontmap,'catalogs':sorted(cats)}
    dest=R/f'mod/gb/profiles/{game}_ko';dest.mkdir(parents=True,exist_ok=True)
    for name,rows in cats.items():(dest/name).write_text('return '+lua({'table':[[k,v] for k,v in sorted(rows.items())]})+'\n')
    for name,obj in [('profile.lua',profile),('assets.lua',assets)]:(dest/name).write_text('return '+lua(obj)+'\n')
    (B/f'{game}-ko-decoded.json').write_text(json.dumps(decoded,ensure_ascii=False,indent=2))
    print(game, 'dialogue',len(decoded),'named',len(named),'glyphs',len(fontmap),'catalogs',len(cats))

if __name__=='__main__':
    for game in sys.argv[1:] or ('gold','silver'):build(game)
