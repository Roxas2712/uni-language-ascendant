"""Build private PT-BR Gen-2 catalogs from verified cartridge tables.

Text recipes and graphics point into the user's language ROM. Gameplay records
remain those of the US base game. This tool does not enable menu availability.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
from lua_literal import lua
from gen1_ptbr_dialogue import offset
from gen2_ptbr_text import alphabet
from gen2_ptbr_graphics import world_assets
from gen2_engine_strings import harvest,bind_rom_strings
ROOT=Path(__file__).resolve().parents[1]
SHA={'gold':'652c0208a5c54313e2d3efb336346e59a17cbab6','silver':'9d9536f14a1874d27ea9167fdf00b80439204a6d','crystal':'e41c519d7ca680facf546fa34b7b00f3149f428f'}

def build(a):
 m=json.loads(a.manifest.read_text());rom=a.rom.read_bytes();base=a.base.read_bytes();c=m['constants'];syms=m['symbols'];cm=alphabet(m,True,a.game=='crystal')
 cm[0x1f]='\n'
 assert hashlib.sha1(rom).hexdigest()==SHA[a.game]
 assert hashlib.sha1(base).hexdigest()==m['romSha1']
 report=json.loads((a.text/'report.json').read_text());assert not report['failures']
 cats={};audit={};missing_descriptions=[]
 base_cm=alphabet(m)
 def loc(k):return offset(*syms[k])
 def word(pos,data=rom):return int.from_bytes(data[pos:pos+2],'little')
 def plain(pos,limit=256,fixed=False):
  end=rom.find(0x50,pos,pos+limit)
  if end<0:
   assert fixed,('Unterminated string',hex(pos));end=pos+limit
  assert all(b in cm and not cm[b].startswith('<') for b in rom[pos:end]),(hex(pos),rom[pos:end].hex())
  begin=pos
  while begin<end and cm[rom[begin]]==' ':begin+=1
  finish=end
  while finish>begin and cm[rom[finish-1]]==' ':finish-=1
  return ({'parts':[{'off':begin,'size':finish-begin}]} if finish>begin else {'empty':True}),end+1,''.join(cm[b] for b in rom[begin:finish])
 def add(name,k,r,text):
  cats.setdefault(name, {})[k]=r;audit.setdefault(name,{})[k]=text
 def names(label,keys,cat,stride=None):
  pos=loc(label)
  for k in keys:
   r,end,text=plain(pos,stride or 64,fixed=bool(stride));pos=pos+stride if stride else end
   if k!='UNUSED':add(cat,k,r,text)
 names('PokemonNames',c['speciesOrder'],'species_names',10)
 names('ItemNames',c['itemOrder'][:c['itemNameCount']],'item_names')
 names('TrainerClassNames',c['trainerClassOrder'][1:],'trainer_class_names')
 moves=json.loads((ROOT/'translations/pt-BR/move-names.json').read_text())['moves']
 for i,k in enumerate(c['moveOrder'],1):add('move_names',k,{'value':moves[str(i)]},moves[str(i)])
 for label,keys,cat in [('ItemDescriptions',c['itemOrder'],'item_descriptions'),('MoveDescriptions',c['moveOrder'],'move_descriptions')]:
  table=loc(label);bank=syms[label][0]
  authored=json.loads((ROOT/'translations/pt-BR'/('gen2-'+cat.replace('_','-')+'.json')).read_text())
  by_hash={row['source_sha256']:row['text'] for row in authored.values()}
  for i,k in enumerate(keys):
   if k=='UNUSED':continue
   pos=offset(bank,word(table+i*2,base));end=base.index(0x50,pos)
   source=''.join(base_cm[b] for b in base[pos:end]);digest=hashlib.sha256(source.encode()).hexdigest()
   if digest in by_hash:
    text=by_hash[digest];r={'value':text}
   else:
    r,_,text=plain(offset(bank,word(table+i*2)),256)
    if source!='?':missing_descriptions.append(dict(category=cat,key=k,source=source))
   add(cat,k,r,text)
 types=json.loads((ROOT/'translations/pt-BR/type-names.json').read_text())
 for k in c['types']:add('type_names',k,{'value':types[k]},types[k])
 for i,k in enumerate(c['landmarkOrder']):
  if k=='LANDMARK_SPECIAL':
   add('landmark_names',k,{'value':'LOCAL ESPECIAL'},'LOCAL ESPECIAL');continue
  r,_,text=plain(offset(syms['Landmarks'][0],word(loc('Landmarks')+i*4+2)),64);add('landmark_names',k,r,text)
 for category,rows in json.loads((ROOT/'translations/pt-BR/gen2-catalog-corrections.json').read_text()).items():
  for key,value in rows.items():
   assert key in cats[category],(category,key)
   add(category,key,{'value':value},value)
 # The legacy PT patch overwrites some category terminators/measurement
 # words and leaves most prose English. Do not read that broken layout.
 # Each authored entry is bound to the intact base cartridge's exact prose.
 dex_base=json.loads((ROOT/'build/ptbr-qa'/f'{a.game}-dex-base.json').read_text())['entries']
 dex_file=ROOT/'translations/pt-BR/gen2-dex'/f'{a.game}.json'
 authored=json.loads(dex_file.read_text()) if dex_file.exists() else {}
 cats['dex_entries']={};missing_dex=[];ignored_dex_measurements=[]
 for k,entry in dex_base.items():
  source={field:entry[field] for field in ('kind','text','text2')}
  digest=hashlib.sha256(json.dumps(source,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  if k not in authored:
   if a.game!='crystal':missing_dex.append(k);continue
   # Crystal keeps the species-indexed pointer table and bank selection.
   # Check every original pointer against its named entry before following PT.
   label=m['pokemonAssets'][k]['dexLabel'];bank,address=syms[label]
   index=c['speciesOrder'].index(k);table=loc('PokedexDataPointerTable')
   assert word(table+index*2,base)==address,(k,'Dex pointer identity changed')
   pos=offset(bank,word(table+index*2))
   kind,end,kind_text=plain(pos,24)
   base_kind_end=base.index(0x50,offset(bank,address))+1
   if rom[end:end+4]!=base[base_kind_end:base_kind_end+4]:ignored_dex_measurements.append(k)
   p1,end,t1=plain(end+4,256);p2,end,t2=plain(end,256)
   def dex_lines(r):
    parts=[]
    for run in r.get('parts',[]):
     start=run['off'];stop=start+run['size']
     for at in range(start,stop):
      if rom[at] in (0x4e,0x4f):
       if at>start:parts.append({'off':start,'size':at-start})
       parts.append({'token':'<NEXT>'});start=at+1
     if stop>start:parts.append({'off':start,'size':stop-start})
    return {'parts':parts}
   add('dex_entries',k,{'table':[['kind',kind],['text',dex_lines(p1)],['text2',dex_lines(p2)]]},
       dict(kind=kind_text,text=t1,text2=t2))
   continue
  row=authored[k];assert row['source_sha256']==digest,(k,'Dex prose changed')
  value={field:row[field] for field in ('kind','text','text2')}
  add('dex_entries',k,{'value':value},value)
 ui=json.loads((ROOT/'translations/pt-BR/gen1-ui.json').read_text())
 extra=ROOT/'translations/pt-BR/gen2-ui.json'
 if extra.exists():ui.update(json.loads(extra.read_text()))
 engine=a.manifest.parent.parent
 keys=harvest(engine)
 cats['strings'],missing_ui=bind_rom_strings(keys,json.loads((a.text/'private-review.json').read_text()),json.loads((a.text/'private-recipes.json').read_text()),ui)
 neutral=set(json.loads((ROOT/'translations/pt-BR/gen2-ui-neutral.json').read_text())['keys'])
 missing_ui=[key for key in missing_ui if key not in neutral]
 cats['status_labels']={k:{'value':v} for k,v in {'PSN':'ENV','BRN':'QUE','FRZ':'CON','PAR':'PAR','SLP':'SON','FNT':'DES'}.items()}
 fontmap={v:k for k,v in cm.items() if k>=0x80 and len(v)==1};fontmap[' ']=0x7f
 fontmap.update({'É':0xc9,'À':0xc6,'→':0xed})
 font=loc('Font');font_tiles=[]
 for code in range(0x80,0x100):
  pos=font+(code-0x80)*8
  if code==0xc9:
   font_tiles.append({'off':font+(0xba-0x80)*8,'size':2})
   for row in [1,2,4,5,6,7]:font_tiles.append({'off':font+(0x84-0x80)*8+row,'size':1})
  elif code==0xc6:
   font_tiles.extend([{'off':font+(0xbd-0x80)*8,'size':2},{'off':font+2,'size':6}])
  else:font_tiles.append({'off':pos,'size':8})
 assets={'assets/fonts/font.png':{'width':128,'height':64,'bits':1,'ink':True,'tiles':font_tiles},
         'assets/fonts/font_battle_extra.png':{'width':128,'height':16,'bits':2,'ink':True,'tiles':[{'off':loc('FontBattleExtra'),'size':512}]}}
 # PS: replaces the native HP: plaque; the bar cells start at tile 2.
 ps_rows=['0000000000000000','1100111000000000','1010100010000000',
          '1100111000000000','1000001010000000','1000111000000000',
          '0000000000000000','0000000000000000']
 assets['assets/fonts/font_battle_extra.png']['authoredPixels']=[dict(x=0,y=0,rows=ps_rows)]
 badge=['0'*16]
 for y in range(5):
  row=list('0'*16)
  for x,b in enumerate(['110','101','110','100','100'][y]):row[2+x]=b
  for x,b in enumerate(['111','100','111','001','111'][y]):row[6+x]=b
  if y in (1,3):row[11]='1'
  badge.append(''.join(row))
 assets['assets/battle/hud/hp_bar.png']=dict(width=96,height=8,bits=2,
  tiles=[dict(off=loc('FontBattleExtra'),size=192)],
  authoredPixels=[dict(x=0,y=1,rows=badge,colors=[[0,0,0,1],[2/3,2/3,2/3,1]])])
 world,graphics_proof=world_assets(m,base,rom,a.game=='crystal');assets.update(world)
 native_path=ROOT/'build/ptbr-qa'/f'{a.game}-native-art-recipes.json'
 assert native_path.exists(),'Build and inspect native menu/title graphics first'
 native=json.loads(native_path.read_text());assets.update(native['assets'])
 graphics_proof['native_images']=native['images'];graphics_proof['title_pointer_proof']=native['title_pointer_proof']
 from gen2_ptbr_graphics import dex_labels,certificate_labels,end_labels
 assets['assets/pokedex/dex.png']['authoredPixels']=dex_labels()
 graphics_proof['authored_dex_labels']=['OPÇÕES','BUSCAR']
 assets['assets/diploma/diploma.png']['authoredPixels']=certificate_labels()
 if a.game=='crystal':assets['assets/credits/theend.png']['authoredPixels']=end_labels()
 graphics_proof['certificate_caption']='PARABÉNS';graphics_proof['credits_end']='O FIM'

 a.output.mkdir(parents=True,exist_ok=True)
 for name,rows in cats.items():(a.output/(name+'.lua')).write_text('return '+lua({'table':[[k,v] for k,v in sorted(rows.items())]})+'\n')
 (a.output/'dialogue.lua').write_bytes((a.text/'dialogue.lua').read_bytes())
 profile=dict(game=a.game,language='pt-BR',sha1=SHA[a.game],md5=hashlib.md5(rom).hexdigest(),size=len(rom),charmap={str(k):v for k,v in cm.items()},fontmap=fontmap,catalogs=sorted([k+'.lua' for k in cats]+['dialogue.lua']))
 for name,data in [('profile',profile),('assets',assets)]: (a.output/(name+'.lua')).write_text('return '+lua(data)+'\n')
 (a.output/'private-catalogs.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
 (a.output/'build-report.json').write_text(json.dumps({'missing_engine_strings':missing_ui,'graphics':graphics_proof,'missing_dex':missing_dex,'missing_authored_descriptions':missing_descriptions,'ignored_source_dex_measurements':ignored_dex_measurements,'runtime_enabled':False,'complete':False},indent=2)+'\n')
 print('GEN2_PROFILE',a.game,{k:len(v) for k,v in cats.items()})

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game',choices=SHA,required=True)
 for name in ['manifest','rom','base','text','output']:p.add_argument('--'+name,type=Path,required=True)
 build(p.parse_args())
