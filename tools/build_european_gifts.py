"""Build exact-ROM recipes for persistent NPC trade/gift identities.

Non-text trade bytes, complete table shape and independent CPU references prove
locations. Target names remain private cartridge bytes; only recipes are shipped.
"""
import hashlib,json,os,re,sys
from pathlib import Path
from build_european_gb import ROOT,lua,offset,read_symbols
from build_gb_profiles import export
from relocate_gb_refs import recover
PAIRS=[('red','es'),('yellow','es'),('gold','es'),('gold','fr'),('gold','it'),('silver','es'),('silver','fr'),('crystal','es'),('crystal','it')]
QA=Path.home()/'Library/Application Support/LOVE/ula-europe-expansion-qa'
def recipe(rom,off,limit=32):
 end=rom.index(0x50,off,off+limit)
 return {'parts':[{'off':off,'size':end-off}]} if end>off else {'empty':True}
def decode(rom,off,cmap,limit=32):
 end=rom.index(0x50,off,off+limit)
 return ''.join(cmap[str(c)] for c in rom[off:end])
def table(value):return {'table':[[k,v] for k,v in value.items()]}
def spec(old,new):return table({'from':{'value':old},'to':new})
def function_name_pointer(us,rom,symbols,label):
 odd=label=='_GiveOddEgg.Odd'
 # GiveShuckle's whole code block ends at the adjacent name records. Decode
 # instruction boundaries before masking address operands; literal species,
 # level, item, trainer ID and branch bytes remain independent anchors.
 start=offset(*symbols['_GiveOddEgg' if odd else 'GiveShuckle']);end=offset(*symbols['_GiveOddEgg.Odd' if odd else 'SpecialShuckleOT'])
 raw=us[start:end];assert 80<len(raw)<256
 absolute={0x01,0x08,0x11,0x21,0x31,0xc2,0xc3,0xc4,0xca,0xcc,0xcd,0xd2,0xd4,0xda,0xdc,0xea,0xfa}
 immediate={0x06,0x0e,0x10,0x16,0x18,0x1e,0x20,0x26,0x28,0x2e,0x30,0x36,0x38,0x3e,0xc6,0xcb,0xce,0xd6,0xde,0xe0,0xe6,0xe8,0xee,0xf0,0xf6,0xf8,0xfe}
 ignored=set();refs=[];i=0
 while i<len(raw):
  op=raw[i];size=3 if op in absolute else 2 if op in immediate else 1
  if size==3:
   ignored.update((i+1,i+2))
   if op==(0x21 if odd else 0x11) and int.from_bytes(raw[i+1:i+3],'little')==symbols[label][1]:refs.append(i+1)
  i+=size
 assert i==len(raw) and len(refs)==1
 pattern=b''.join(b'.' if i in ignored else re.escape(bytes([v])) for i,v in enumerate(raw))
 hits=[z.start() for z in re.finditer(b'(?=('+pattern+b'))',rom,re.S)]
 assert len(hits)==1,('complete GiveShuckle code',label,hits)
 at=hits[0];ptr=int.from_bytes(rom[at+refs[0]:at+refs[0]+2],'little');dst=offset(at//16384,ptr)
 return dst,{'code':at,'bytes':len(raw),'literalBytes':len(raw)-len(ignored),'pointerOperand':at+refs[0]}
def run(game,lang):
 folder=ROOT/f'mod/gb/profiles/{game}_{lang}';profile=export(folder/'profile.lua');cm=profile['charmap']
 m=json.loads((ROOT/'build/upstream-engine/tools'/('rom_manifest'+('' if game=='red' else '_'+game)+'.json')).read_text())
 inputs=json.loads((ROOT/'build/european-inputs.json').read_text());inv=json.loads((ROOT/'build/gb-rom-inventory.json').read_text())
 rom=Path(next(x['file'] for x in inputs if x.get('game')==game and x.get('language')==lang)).read_bytes()
 us=Path(next(x['file'] for x in inv if x['sha1']==m['romSha1'])).read_bytes()
 assert hashlib.sha1(rom).hexdigest()==profile['sha1']
 assert hashlib.sha1(us).hexdigest()==m['romSha1']
 gen=1 if game in ('red','yellow') else 2
 if gen==1:
  base=export(QA/f'{game}/data/generated/field.lua')['trades'];stride=14;count=len(base)
  first=base[0]['nickname'];reverse={v:int(k) for k,v in m['charmap'].items()}
  hit=us.index(bytes(reverse[c] for c in first)+b'\x50');start=hit-3
  assert all(decode(us,start+i*stride+3,m['charmap'])==r['nickname'] for i,r in enumerate(base))
 else:
  base=export(QA/f'{game}/data/generated/events.lua')['trades'];stride=32;count=len(base);start=offset(*m['symbols']['NPCTrades'])
 mask={i for i in range(count*stride) if i%stride<3 or (gen==2 and (14<=i%stride<17 or i%stride==30))}
 pattern=b''.join(re.escape(bytes([us[start+i]])) if i in mask else b'.' for i in range(count*stride))
 hits=[x.start() for x in re.finditer(b'(?=('+pattern+b'))',rom,re.S)]
 assert len(hits)==1,(game,lang,'trade table',hits)
 target=hits[0];names=[];proof={'tradeTable':target,'tradeCount':count,'numericAnchors':len(mask)}
 for i,row in enumerate(base):
  fields={};off=target+i*stride
  fields['nickname']=spec(row['nickname'],recipe(rom,off+3,11))
  if gen==2:fields['otName']=spec(row['otName'],recipe(rom,off+19,11))
  names.append(table(fields))
 result={'trades':{'array':names}};strings={}
 if gen==1:
  redspec=next(x for x in inputs if x.get('game')=='red' and x.get('language')=='es')
  red=Path(redspec['file']).read_bytes()
  assert hashlib.sha1(red).hexdigest()==redspec['sha1']
  trainer=offset(*read_symbols(ROOT/'build/pokered-es/pokered.sym')['TrainerCharText'])
  # The complete adjacent PKMN/TM/TRAINER/POKE/Enemy token dictionary is a
  # unique byte-identical block in both Spanish cartridges.
  block=red[trainer-6:trainer+19]
  hits=[z.start()+6 for z in re.finditer(re.escape(block),rom)]
  assert len(hits)==1
  at=hits[0];operand=at.to_bytes(2,'little')
  refs=[z.start() for z in re.finditer(re.escape(b'\xd5\x11'+operand+b'\x18'),rom[:16384])]
  assert len(refs)==1
  result['tradeOT']=spec('TRAINER',recipe(rom,at,11))
  proof['tradeOT']={'off':at,'dictionaryBytes':len(block),'loadDE':refs[0]}

 if gen==2:
  audit=json.loads((ROOT/f'build/{game}-{lang}-relocation.json').read_text())
  source_syms=read_symbols(ROOT/('build/pokecrystal/pokecrystal.sym' if game=='crystal' else f'build/pokegold/poke{game}.sym'))
  def locate(label):
   b,a=source_syms[label];src=offset(b,a)
   try:dst,refs=recover(us,rom,b,a);proof[label]={'off':dst,'references':refs}
   except ValueError:
    dst=audit['mapped'].get(str(src))
    if dst is not None:proof[label]={'off':dst,'evidence':'paired script graph'}
    elif label in ('SpecialShuckleOT','SpecialShuckleNickname','_GiveOddEgg.Odd'):
     try:
      dst,evidence=function_name_pointer(us,rom,source_syms,label)
      proof[label]={'off':dst,'completeFunction':evidence}
      return dst
     except AssertionError:
      if label!='SpecialShuckleNickname':raise
     source_ot=offset(*source_syms['SpecialShuckleOT'])
     assert us.index(0x50,source_ot)+1==src
     dst=rom.index(0x50,proof['SpecialShuckleOT']['off'])+1
     pointer=(dst%16384+16384).to_bytes(2,'little')
     refs=[z.start()+b*16384 for z in re.finditer(re.escape(b'\x11'+pointer),rom[b*16384:(b+1)*16384])]
     assert len(refs)==1,(label,refs)
     proof[label]={'off':dst,'loadDE':refs[0],'evidence':'adjacent terminated name plus unique CPU reference'}
    elif label=='OddEggs':
     raw=us[src:src+14*59]
     pattern=b''.join(re.escape(bytes([v])) if i%59<48 else b'.' for i,v in enumerate(raw))
     hits=[z.start() for z in re.finditer(b'(?=('+pattern+b'))',rom,re.S)]
     assert len(hits)==1,(label,hits)
     dst=hits[0];proof[label]={'off':dst,'evidence':'all 14 complete numeric party records match'}
    else:raise AssertionError((game,lang,label))
   return dst
  ot=locate('SpecialShuckleOT');nick=locate('SpecialShuckleNickname')
  result['shuckle']=table({'nickname':spec('SHUCKIE',recipe(rom,nick,11)),'otName':spec('MANIA',recipe(rom,ot,11))})
  proof['shuckleOT']=decode(rom,ot,cm,11);proof['shuckleNickname']=decode(rom,nick,cm,11)
  string_audit=audit['strings']
  if game=='crystal' and lang=='it':
   string_audit={}
   for old in json.loads((ROOT/'build/crystal-es-relocation.json').read_text())['strings']:
    b,a=(int(x,16) for x in old.split(':'));dst=audit['mapped'].get(str(offset(b,a)))
    assert dst is not None,(game,lang,old)
    string_audit[old]=[dst//16384,dst%16384+16384]
  for old,pointer in string_audit.items():
   b,a=(int(x,16) for x in old.split(':'));original=decode(us,offset(b,a),m['charmap']);dst=offset(*pointer)
   value=recipe(rom,dst);translated=decode(rom,dst,cm)
   if original in strings:
    assert decode(rom,strings[original]['parts'][0]['off'],cm)==translated,original
   strings[original]=value
  proof['scriptStrings']=len(strings)
  if game=='crystal':
   odd=locate('_GiveOddEgg.Odd')
   # The first complete OddEgg party structure ends in its localized nickname.
   egg_table=locate('OddEggs');egg_name=egg_table+48
   assert decode(us,offset(*source_syms['OddEggs'])+48,m['charmap'],11)=='EGG'
   result['oddEgg']=table({'nickname':spec('EGG',recipe(rom,egg_name,11)),'otName':spec('ODD',recipe(rom,odd,11))})
   proof['oddEggOT']=decode(rom,odd,cm,11);proof['oddEggNickname']=decode(rom,egg_name,cm,11)
 (folder/'mon_names.lua').write_text('return '+lua(table(result))+'\n')
 if strings:(folder/'script_strings.lua').write_text('return '+lua(table(strings))+'\n')
 for name in ['mon_names.lua']+(['script_strings.lua'] if strings else []):
  if name not in profile['catalogs']:profile['catalogs'].append(name)
 (folder/'profile.lua').write_text('return '+lua(profile)+'\n')
 (ROOT/f'build/{game}-{lang}-gift-identities.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
 print('EU_NATIVE_IDENTITIES',game,lang,count,'trades',proof.get('shuckleOT'),proof.get('shuckleNickname'),proof.get('oddEggOT'),flush=True)
if __name__=='__main__':
 for g,l in ([tuple(sys.argv[1:])] if len(sys.argv)>1 else PAIRS):run(g,l)
