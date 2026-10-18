"""Build the Japanese Crystal development profile; QA gates release separately."""
import collections,hashlib,json,re,unicodedata
from pathlib import Path
from asian_gen2 import TextReader,japanese_charmap,symbols,offset
from build_european_gb import lua
from asian_engine_bindings import bind
from asian_menu_labels import labels
from asian_engine_ui import translations as engine_ui
from asian_engine_extra import translations as engine_extra
from asian_engine_fields import translations as engine_fields
from asian_text_arguments import argument_orders
from asian_engine_ui import harvest
from asian_gen2_refs.crystal_ja_compat import TEXT as COMPAT
R=Path(__file__).resolve().parents[1];B=R/'build/asian-gen2';REF=R.parent/'Uni-Language-Ascendant-Europe/build'

def build():
 rom=(R.parent/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes();sha='95127b901bbce2407daf43cce9f45d4c27ef635d';assert hashlib.sha1(rom).hexdigest()==sha
 us=(REF/'pokecrystal/pokecrystal.gbc').read_bytes();sy=symbols(REF/'pokecrystal/pokecrystal.sym');m=json.loads((R/'build/upstream-engine/tools/rom_manifest_crystal.json').read_text());assert hashlib.sha1(us).hexdigest()==m['romSha1']
 cm=japanese_charmap(REF/'pokecrystal/constants/charmap.asm');reader=TextReader(rom,'ja',cm)
 graph=json.loads((R/'tools/asian_gen2_refs/crystal.json').read_text());assert graph['sourceSha1']==sha and graph['baseSha1']==m['romSha1'];mapped={int(k):v for k,v in graph['mapped'].items()}
 def read_native(source,command=True):
  fragment=graph.get('fragments',{}).get(str(source))
  if fragment:
   assert rom[fragment['stop']]==8,'Reviewed text_asm boundary changed'
   return reader.text(fragment['start'],stop_at=fragment['stop'])
  target=mapped.get(source)
  if target is None:raise ValueError('No verified target address')
  return reader.text(target)if command else reader.span(target)
 base=dict.fromkeys(graph['dialogueKeys']);cats={};missing={};dialogue={}
 for key,text in base.items():
  if not re.fullmatch(r'[0-9a-f]{2}:[0-9a-f]{4}',key):continue
  pos=offset(*(int(x,16) for x in key.split(':')));target=mapped.get(pos)
  try:dialogue[key]=read_native(pos,us[pos]<=0x16)[0]
  except (ValueError,AssertionError,IndexError) as e:missing[key]=str(e)
 cats['dialogue.lua']=dialogue
 named={}
 for label in m['text']['labels']:
  target=mapped.get(offset(*sy[label]))
  try:named[label]=read_native(offset(*sy[label]))[0]
  except (ValueError,AssertionError,IndexError) as e:missing[label]=str(e)
 native_counts={'dialogue':len(dialogue),'named':len(named)}
 source_reader=TextReader(us,'en',m['charmap']);compat_proof={}
 for key,translated in COMPAT.items():
  source=offset(*sy[key])if key in sy else offset(*(int(x,16)for x in key.split(':')))
  original=source_reader.text(source)[1]if us[source]<=0x16 else source_reader.span(source)[1]
  original=re.sub(r'<(USER|TARGET|ENEMY|PLAYER|RIVAL|MOM)>',r'{\1}',original)
  tokens=lambda text:collections.Counter(re.findall(r'\{(?:STRBUF|NUM|USER|TARGET|ENEMY|PLAYER|RIVAL|MOM)\}',text))
  assert tokens(original)==tokens(translated),('Compatibility fields differ',key)
  assert key in missing,('Compatibility text unexpectedly masks native mapping',key)
  (named if key in m['text']['labels'] else dialogue)[key]={'value':translated}
  missing.pop(key)
  compat_proof[key]={'source':source,'sourceDecodedSha256':hashlib.sha256(original.encode()).hexdigest(),'translationSha256':hashlib.sha256(translated.encode()).hexdigest(),'origin':'authored US-engine compatibility translation'}
 assert not missing,('Unresolved Japanese text slots',missing)
 cats['rom_text.lua']=named
 cats['text_arguments.lua']=argument_orders(TextReader(us,'en',m['charmap']),sy,reader,{k:mapped[offset(*sy[k])]for k in named if offset(*sy[k])in mapped},rammap={int(k):v for k,v in graph['argumentRamCrosswalk']['addresses'].items()},fragments=graph.get('fragments'))
 # NamesPointers is independently identified by all four ordered ROM banks
 # and pointers, the null row, and the two WRAM OT buffers.
 table=0x3377
 assert rom[table:table+24]==bytes.fromhex('141a74103b5600000001fa7000c5dd00d9d30b195304485d')
 def far(i):return offset(rom[table+i*3],int.from_bytes(rom[table+i*3+1:table+i*3+3],'little'))
 def names(pos,keys,stride=None):
  result={}
  for key in keys:
   recipe,value,end,_=reader.span(pos,stride or 128,fixed=bool(stride));assert value,(key,hex(pos));result[key]=recipe;pos=pos+stride if stride else end
  return result
 for cat,i,keys,stride in [('species_names',0,m['constants']['speciesOrder'],5),('move_names',1,m['constants']['moveOrder'],None),('item_names',3,m['constants']['itemOrder'],None),('trainer_class_names',6,m['constants']['trainerClassOrder'][1:],None)]:cats[cat+'.lua']=names(far(i),keys,stride)
 def ptr(at,i):return offset(at//16384,int.from_bytes(rom[at+i*2:at+i*2+2],'little'))
 # Complete 256-entry description table topology, including its five shared
 # unused entries, independently anchors the native move description table.
 move_table=0x2dd48;assert ptr(move_table,0)==move_table+514
 assert len({ptr(move_table,i) for i in range(256)})==252
 cats['move_descriptions.lua']={key:reader.span(ptr(move_table,i))[0] for i,key in enumerate(m['constants']['moveOrder'])}
 item_table=0x2c02d
 cats['item_descriptions.lua']={key:reader.span(ptr(item_table,i))[0] for i,key in enumerate(m['constants']['itemOrder'][:m['constants']['itemNameCount']])}
 cats['type_names.lua']={key:reader.span(ptr(0x50a6b,number))[0] for key,number in m['constants']['types'].items()}
 # Japanese GetDexEntryPointer uses two native tables, split at dex 100.
 # Three independent CPU paths load $4337/$58b3 and bank $11.
 assert rom[0xeef1:0xeef1+18]==bytes.fromhex('213743fe643805d66321b3583d5f16001919')
 dex={};metrics={}
 for i,key in enumerate(m['constants']['speciesOrder']):
  pos=ptr(0x44337 if i<99 else 0x458b3,i if i<99 else i-99)
  kind,_,end,_=reader.span(pos,32);text,_,_,term=reader.span(end+3,256,tokens={0x4e:'<NEXT>'});assert term==0x5f,(key,term)
  dex[key]={'table':[['kind',kind],['text',text],['text2',{'empty':True}]]}
  height=rom[end]/10;weight=int.from_bytes(rom[end+1:end+3],'little')/10
  assert 0<height<15 and 0<weight<1000,(key,height,weight)
  metrics[key]={'value':{'heightM':height,'weightKg':weight}}
 cats['dex_entries.lua']=dex;cats['dex_metrics.lua']=metrics
 # Independent complete coordinate signature identifies the landmark table.
 start=offset(*sy['Landmarks']);raw=us[start:start+4*len(m['constants']['landmarkOrder'])]
 pattern=b''.join(re.escape(bytes([v])) if i%4<2 else b'.' for i,v in enumerate(raw));hits=[z.start() for z in re.finditer(b'(?=('+pattern+b'))',rom,re.S)]
 assert len(hits)==1,('Landmarks',hits);landmarks={}
 for i,key in enumerate(m['constants']['landmarkOrder']):landmarks[key]=reader.span(ptr(hits[0]+2,i*2))[0]
 cats['landmark_names.lua']=landmarks
 # Authored labels cover engine UI, separate from cartridge-derived prose.
 ui={'YES':'はい','NO':'いいえ','CANCEL':'やめる','POKéMON':'ポケモン','POKéDEX':'ポケモンずかん','POKéGEAR':'ポケギア','SAVE':'レポート','OPTION':'せってい','EXIT':'とじる','FIGHT':'たたかう','<PK><MN>':'ポケモン','PACK':'どうぐ','RUN':'にげる','TYPE/':'タイプ／','NEW GAME':'さいしょから はじめる','CONTINUE':'つづきから はじめる','HT':'たかさ','WT':'おもさ',' PAGE AREA CRY PRNT':' せつめい ぶんぷ なきごえ','SEEN':'みつけたかず','OWN':'つかまえたかず','STATS':'つよさをみる','SWITCH':'ならびかえ','MOVE':'いどう','MOVES':'わざ','USE':'つかう','GIVE':'もたせる','TOSS':'すてる','QUIT':'やめる','BUY':'かう','SELL':'うる','lower':'もじ','UPPER':'もじ','DEL':'けす','END':'おわり','YOUR NAME?':'なまえは？','RIVAL\'S NAME?':'ライバルの なまえは？','MOTHER\'S NAME?':'おかあさんの なまえは？','BOX NAME?':'ボックスの なまえは？','NICKNAME?':'ニックネームは？','%s\'S':'%sの'}
 cats['strings.lua']={key:{'value':value} for key,value in ui.items()};cats['mon_names.lua']={};cats['trainer_names.lua']={};cats['script_strings.lua']={};cats['status_labels.lua']={key:{'value':value} for key,value in {'PSN':'どく','PAR':'まひ','SLP':'ねむり','BRN':'やけど','FRZ':'こおり','FNT':'ひんし'}.items()}
 bound=bind(R/'build/upstream-engine',TextReader(us,'en',m['charmap']),sy,reader,{k:mapped.get(offset(*sy[k]),0)for k in named if offset(*sy[k])in mapped or k in COMPAT},named,fragments=graph.get('fragments'))
 cats['strings.lua'].update({k:v for k,v in bound.items()if k not in ui})
 cats['strings.lua'].update({k:{'value':v}for k,v in {
  'Wild %s appeared!':'あ！ やせいの\n%sが とびだしてきた！',
  'Go! %s!':'ゆけっ！ %s！',
  '%s\nused %s!':'%sの\n%s！',
  '%s used %s!':'%sの\n%s！',
  'Enemy %s fainted!':'あいての %sは\nたおれた！',
  '%s fainted!':'%sは\nたおれた！',
  '%s gained %d EXP. Points!':'%sは\n%d けいけんちを もらった！',
  '%s gained a boosted %d EXP. Points!':'%sは おおめに\n%d けいけんちを もらった！',
  '%s grew to level %d!':'%sは\nレベル%dに あがった！',
  '%s wants to battle!':'%sが\nしょうぶを しかけてきた！',
  '%s sent out %s!':'%sは\n%sを くりだした！',
 }.items()})
 # Native trainer table: every class/member is paired with its US identity.
 # One regional party differs; only the displayed name is localized.
 us_reader=TextReader(us,'en',m['charmap']);trainer_names={};party_differences=[]
 def trainer_record(rd,data,pos):
  recipe,name,end,_=rd.span(pos,40);pos=end;typ=data[pos];assert typ<4
  stride=2+(4 if typ&1 else 0)+(1 if typ&2 else 0);pos+=1
  for _ in range(6):
   if data[pos]==255:break
   pos+=stride
  assert data[pos]==255
  return recipe,pos+1,data[end:pos+1]
 for i,cls in enumerate(m['constants']['trainerClassOrder'][1:]):
  dst=ptr(0x399ba,i);source_table=offset(*sy['TrainerGroups']);src=offset(source_table//16384,int.from_bytes(us[source_table+i*2:source_table+i*2+2],'little'))
  for j,member in enumerate(m['constants']['trainerClassMembers'].get(cls,[])):
   recipe,dst,party=trainer_record(reader,rom,dst);_,src,original=trainer_record(us_reader,us,src)
   if party!=original:party_differences.append((cls,j+1,original.hex(),party.hex()))
   trainer_names[f'{cls}:{j+1}']=recipe
 assert party_differences==[('POKEFANM',12,'021d22ad1dc7ad1d77adff','021d22ad1dc7ad3a81adff')],party_differences
 cats['trainer_names.lua']=trainer_names
 def table(rows):return {'table':[[k,v]for k,v in rows.items()]}
 def rename(src,dst,size):return table({'from':{'value':us_reader.span(src,11)[1]},'to':reader.span(dst,size,fixed=True)[0]})
 trades=[];source_trade=offset(*sy['NPCTrades'])
 for i in range(7):
  src=source_trade+i*32;dst=0xfce57+i*16
  assert us[src:src+3]==rom[dst:dst+3] or (i==6 and us[src:src+3]==bytes.fromhex('003352') and rom[dst:dst+3]==bytes.fromhex('003334'))
  assert us[src+14:src+19]==rom[dst+7:dst+12] and us[src+30]==rom[dst+15]
  trades.append(table({'nickname':rename(src+3,dst+3,4),'otName':rename(src+19,dst+12,3)}))
 cats['mon_names.lua']={'trades':{'array':trades}}
 native_strings={}
 for key,target in graph['strings'].items():
  bnk,addr=(int(x,16)for x in key.split(':'))
  original=us_reader.span(offset(bnk,addr))[1]
  native_strings[original]=reader.span(offset(*target))[0]
 cats['script_strings.lua']=native_strings
 assets={'assets/fonts/japanese-main.png':{'width':128,'height':64,'bits':1,'transparent':True,'tiles':[{'off':0xf8200,'size':1024}]},'assets/fonts/japanese-extra.png':{'width':128,'height':16,'bits':2,'ink':True,'tiles':[{'off':0xf8000,'size':512}]}}
 fontmap={};composite={}
 for key,char in cm.items():
  code=int(key)
  if len(char)==1 and (ord(char)>127 or char==' '):
   if code>=0x80:fontmap[char]=0x4000+code-0x80
   elif code>=0x60:fontmap[char]=0x4100+code-0x60
 fontmap[' ']=0x7f; fontmap['ヘ']=fontmap['へ'];fontmap['リ']=fontmap['り']
 for key,char in cm.items():
  if len(char)!=1 or int(key)>=0x60:continue
  normalized=unicodedata.normalize('NFD',char)
  if len(normalized)==2 and normalized[1] in ('\u3099','\u309a'):
   base_char=normalized[0];base_char={'ヘ':'へ','リ':'り'}.get(base_char,base_char)
   code=0x5000+int(key);fontmap[char]=code;composite[code]={'base':fontmap[base_char],'mark':fontmap['ﾞ' if normalized[1]=='\u3099' else 'ﾟ']}
 fontmap['ベ']=fontmap['べ'];fontmap['ペ']=fontmap['ぺ']
 cats['font_pages.lua']={'lookupDialogue':{'value':True},'singlePages':{'value':{'main':{'path':'assets/fonts/japanese-main.png','base':0x4000},'extra':{'path':'assets/fonts/japanese-extra.png','base':0x4100}}},'composite':{'value':composite}}
 cats['strings.lua'].update(labels('ja',harvest(R/'build/upstream-engine')))
 cats['strings.lua'].update({k:v for k,v in engine_ui('ja',harvest(R/'build/upstream-engine')).items()if k not in cats['strings.lua']})
 cats['strings.lua'].update({k:v for k,v in engine_extra('ja',harvest(R/'build/upstream-engine')).items()if k not in cats['strings.lua']})
 cats['strings.lua'].update({k:v for k,v in engine_fields('ja',harvest(R/'build/upstream-engine')).items()if k not in cats['strings.lua']})
 # Finite prize labels use exactly the native item/species name recipes.
 for source,ident in {'TM32':'TM_DOUBLE_TEAM','TM29':'TM_PSYCHIC_M','TM15':'TM_HYPER_BEAM','TM25':'TM_THUNDER','TM14':'TM_BLIZZARD','TM38':'TM_FIRE_BLAST'}.items():cats['strings.lua'][source]=cats['item_names.lua'][ident]
 for source in ['MR.MIME','EEVEE','PORYGON','ABRA','EKANS','SANDSHREW','DRATINI']:cats['strings.lua'][source]=cats['species_names.lua'][source.replace('.','__')]
 profile={'game':'crystal','language':'ja','encoding':'japanese-gen2','sha1':sha,'md5':hashlib.md5(rom).hexdigest(),'size':len(rom),'charmap':cm,'fontmap':fontmap,'catalogs':sorted(cats),'development':True}
 dest=R/'mod/gb/profiles/crystal_ja';dest.mkdir(exist_ok=True)
 for name,rows in cats.items():(dest/name).write_text('return '+lua({'table':[[k,v] for k,v in sorted(rows.items())]})+'\n')
 for name,data in [('profile.lua',profile),('assets.lua',assets)]:(dest/name).write_text('return '+lua(data)+'\n')
 (B/'crystal-ja-profile-report.json').write_text(json.dumps({'sha1':sha,'dialogue':len(dialogue),'named':len(named),'missing':missing,'native':native_counts,'authoredCompatibility':compat_proof,'catalogs':{k:len(v) for k,v in cats.items()}},indent=2))
 print('JA_DEVELOPMENT_PROFILE',len(dialogue),len(named),'unresolved',len(missing))
if __name__=='__main__':build()
