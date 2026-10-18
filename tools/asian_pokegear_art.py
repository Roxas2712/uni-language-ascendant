"""Native Pokégear sheets/maps. Recipes read the user's exact cartridge."""
import re
from asian_gen2 import offset,symbols
from gb_lz import decompress

def build(root,rom,lang,sy,assets):
 if lang=='ja':
  assert rom[0x90bca:0x90be0]==bytes.fromhex('21a04b1100903e3ecd2a0b21b2541100933e24cd3a0b')
  assert rom[0x9211a:0x92127]==bytes.fromhex('21a04b11009001303ecd5d0ec9')
  source=root.parent/'Uni-Language-Ascendant-Europe/build/pokecrystal'
  us=(source/'pokecrystal.gbc').read_bytes();usy=symbols(source/'pokecrystal.sym')
  addresses={'TownMapGFX':0xf8ba0,'PokegearGFX':0x914b2}
  for name,size in [('JohtoMap',361),('KantoMap',361),('TownMapPals.PalMap',48),('MalePokegearPals',48),('FemalePokegearPals',48)]:
   start=offset(*usy[name]);needle=us[start:start+size]
   hits=[m.start()for m in re.finditer(re.escape(needle),rom)];assert len(hits)==1,(name,hits)
   addresses[name]=hits[0]
  for name in ['ClockTilemapRLE','RadioTilemapRLE','PhoneTilemapRLE']:
   start=offset(*usy[name]);end=start
   while us[end]!=255:end+=2
   needle=us[start:end+1];hits=[m.start()for m in re.finditer(re.escape(needle),rom)]
   assert len(hits)==1,(name,hits);addresses[name]=hits[0]
 else:addresses={k:offset(*v)for k,v in sy.items()if v[0]<128 and v[1]<0x8000}
 tileparts=[]
 for name,length in [('TownMapGFX',768),('PokegearGFX',736)]:
  at=addresses[name];raw,size=decompress(rom,at);assert len(raw)==length
  tileparts.append({'off':at,'size':size,'lz':True,'start':0,'length':length})
 # The stock renderer reserves 48 cells for each half; native gear has 46.
 zero=rom.find(bytes(32));assert zero>=0;tileparts.append({'off':zero,'size':32})
 assets['assets/pokegear/gear.png']={'width':128,'height':48,'bits':2,'tiles':tileparts}
 def tilemap(name,rle):
  at=addresses[name];end=at;count=0
  while rom[end]!=255:
   count+=rom[end+1]if rle else 1;end+=2 if rle else 1
   assert count<=360 and end-at<1000
  return {'tilemap':{'off':at,'size':end-at+1,'cells':360,'rle':rle,'fill':79}}
 def palette(name):
  at=addresses[name];out=[]
  for i in range(6):
   row=[]
   for j in range(4):
    val=int.from_bytes(rom[at+8*i+2*j:at+8*i+2*j+2],'little')
    row.append([round(((val>>s)&31)*255/31)for s in(0,5,10)]+[255])
   out.append(row)
  return {'value':out}
 palmap=rom[addresses['TownMapPals.PalMap']:addresses['TownMapPals.PalMap']+48]
 result={'tiles':{'value':'assets/generated/pokegear/gear.png'},'tilesWide':{'value':16},'townMapTiles':{'value':48},'palMap':{'value':[n+1 for b in palmap for n in(b&7,(b>>4)&7)]},'palettes':palette('MalePokegearPals'if lang=='ja'else'PokegearPals')}
 if lang=='ja':result['palettesFemale']=palette('FemalePokegearPals')
 result['cards']={'table':[[k,tilemap(k.title()+'TilemapRLE',True)]for k in ['clock','phone','radio']]}
 result['maps']={'table':[[k,tilemap(k.title()+'Map',False)]for k in ['johto','kanto']]}
 return {'table':[[k,v]for k,v in result.items()]}
