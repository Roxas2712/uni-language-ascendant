"""Native Korean menu sheets and placement metadata; no pixels are shipped."""
import hashlib,json,re
from pathlib import Path
from asian_gen2 import symbols,offset,TextReader,korean_charmap,japanese_charmap
from gb_lz import decompress
from asian_pokegear_art import build as pokegear
from build_gb_profiles import export,lua
R=Path(__file__).resolve().parents[1]
def build(game):
 lang='ja'if game=='crystal'else'ko';folder=R/f'mod/gb/profiles/{game}_{lang}';profile=export(folder/'profile.lua')
 rom=(R.parent/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes()if lang=='ja'else(R/f'build/pokegold-kr/poke{game}.gbc').read_bytes()
 assert hashlib.sha1(rom).hexdigest()==profile['sha1']
 if lang=='ko':sy=symbols(R/f'build/pokegold-kr/poke{game}.sym')
 else:
  # Independent native Pack_InitGFX, picture-pointer table, and card loads.
  assert rom[0x1095b:0x10966]==bytes.fromhex('21704b1100900100063e04')
  assert rom[0x108c6:0x108ce]==bytes.fromhex('3051b0527050f051')
  assert rom[0x251d2:0x251dc]==bytes.fromhex('113855219092015609cd')
  assert rom[0x25210:0x2521a]==bytes.fromhex('119855219092015609cd')
  addresses={'PackMenuGFX':0x10b70,'PackGFX':0x11070,'CardStatusGFX':0x25538,'LeaderGFX':0x25598,'_CGB_PackPals.PackPals':0x93f6,'PokedexLZ':0x41242}
  sy={k:(a//16384,a%16384+16384)for k,a in addresses.items()}
  base=R.parent/'Uni-Language-Ascendant-Europe/build/pokecrystal';ussy=symbols(base/'pokecrystal.sym');us=(base/'pokecrystal.gbc').read_bytes();pal=offset(*ussy['_CGB_PackPals.ChrisPackPals'])
  assert rom[0x93f6:0x93f6+48]==us[pal:pal+48]
 assets=export(folder/'assets.lua');layout_recipe=export(folder/'layouts.lua')
 layouts=layout_recipe.get('value')or{k:v['value']for k,v in layout_recipe['table']if k not in ('diploma','pokegear')}
 if lang=='ja':assert rom[0x404f9:0x40505]==bytes.fromhex('214252111093013110cd5d0e')
 dex=offset(*sy['PokedexLZ']);raw,z=decompress(rom,dex);assert len(raw)==784
 assets['assets/pokedex/dex.png']={'width':392,'height':8,'bits':2,'tiles':[{'off':dex,'size':z,'lz':True,'start':0,'length':784}]}
 layouts.setdefault('menu',{})['pokedex']={'nativeAsianDex':True,'tiles':'assets/generated/pokedex/dex.png','tilesWide':49,'firstTile':0x31}
 menu=offset(*sy['PackMenuGFX']);pack=offset(*sy['PackGFX']);assert pack-menu==1280
 assets['assets/pack/menu.png']={'width':128,'height':40,'bits':2,'tiles':[{'off':menu,'size':1280}]}
 assets['assets/pack/pack.png']={'width':32,'height':96,'bits':2,'tiles':[{'off':pack,'size':768}]}
 status=offset(*sy['CardStatusGFX']);leaders=offset(*sy['LeaderGFX']);assert leaders-status==96
 assets['assets/trainer_card/status.png']={'width':48,'height':8,'bits':2,'tiles':[{'off':status,'size':96}]}
 # The native sheet has 86 cells. An 86-wide atlas needs no invented padding.
 assets['assets/trainer_card/leaders.png']={'width':688,'height':8,'bits':2,'tiles':[{'off':leaders,'size':1376}]}
 layouts.setdefault('menu',{})['trainerCard']={'status':'assets/generated/trainer_card/status.png','statusWide':6,'leaders':'assets/generated/trainer_card/leaders.png','leadersWide':86}
 pal=offset(*sy['_CGB_PackPals.PackPals']);colors=[]
 for i in range(6):
  row=[]
  for j in range(4):
   value=int.from_bytes(rom[pal+i*8+j*2:pal+i*8+j*2+2],'little');row.append([round(((value>>shift)&31)*255/31)for shift in(0,5,10)]+[255])
  colors.append(row)
 # Palette arrays use zero-based shades and 0..255 components in GbcPalette.
 layouts.setdefault('menu',{})['pack']={'nativeAsianPack':True,'menu':'assets/generated/pack/menu.png','pack':'assets/generated/pack/pack.png','packTilesWide':4,'packTilesHigh':3,'pocketPicture':{'ITEM':12,'BALL':36,'KEY_ITEM':0,'TM_HM':24},'nativePocketName':{'ITEM':4,'BALL':28,'KEY_ITEM':12,'TM_HM':20},'paletteZones':[[0,0,10,2,2],[10,0,10,2,3],[8,3,1,9,4],[0,7,6,2,5],[1,3,4,3,6]],'palettes':colors}
 # Native certificate art, tilemap and four text lines are independent
 # cartridge reads. Rendering retains the base game's certificate palette.
 if lang=='ko':
  rd=TextReader(rom,lang,korean_charmap(R/'build/pokegold-kr'))
  gfx=offset(*sy['DiplomaGFX']);tilemap=offset(*sy['DiplomaPage1Tilemap'])
  names={key:offset(*sy['PlaceDiplomaOnScreen.'+symbol])for key,symbol in [('player','Player'),('honorific','Honorific'),('certificate','Certification'),('studio','GameFreak')]}
 else:
  assert rom[0xe0013:0xe0028]==bytes.fromhex('21ed40110090cd3a0b21fd4411a0c4016801cdf22f')
  rd=TextReader(rom,lang,japanese_charmap(R.parent/'Uni-Language-Ascendant-Europe/build/pokecrystal/constants/charmap.asm'))
  gfx=0xe00ed;tilemap=0xe04fd;names={'player':0xe0067,'honorific':0xe006d,'certificate':0xe0070,'studio':0xe00a5}
 raw,size=decompress(rom,gfx);assert len(raw)==1664 and max(rom[tilemap:tilemap+360])*16<len(raw)
 assets['assets/diploma/sheet.png']={'width':832,'height':8,'bits':2,'tiles':[{'off':gfx,'size':size,'lz':True,'start':0,'length':len(raw)}]}
 diploma={'nativeAsian':{'value':True},'image':{'value':'assets/generated/diploma/sheet.png'},'sheetTiles':{'value':104},'width':{'value':20},'height':{'value':18},'page1':{'bytes':{'off':tilemap,'size':360}}}
 for key,at in names.items():diploma[key]=rd.span(at)[0]
 # The retail ending deliberately says THE END in all three cartridges.
 # Exact equality proves that retaining the stock English artwork is native.
 base=R.parent/'Uni-Language-Ascendant-Europe/build'/('pokecrystal'if lang=='ja'else'pokegold')
 usrom=(base/f'poke{game}.gbc').read_bytes();ussy=symbols(base/f'poke{game}.sym')
 old=offset(*ussy['TheEndGFX']);needle=usrom[old:old+256]
 if lang=='ko':native=offset(*sy['TheEndGFX']);assert rom[native:native+256]==needle
 else:
  hits=[m.start()for m in re.finditer(re.escape(needle),rom)];assert len(hits)==1;native=hits[0]
 assets['assets/credits/theend.png']={'width':64,'height':16,'bits':2,'tiles':[{'off':native,'size':256}]}
 gear=pokegear(R,rom,lang,sy,assets)
 layout={'table':[[key,{'value':value}]for key,value in layouts.items()]+[['diploma',{'table':[[k,v]for k,v in diploma.items()]}],['pokegear',gear]]}
 (folder/'assets.lua').write_text('return '+lua(assets)+'\n');(folder/'layouts.lua').write_text('return '+lua(layout)+'\n')
 print('ASIAN_PACK_ART_OK',game,hex(menu),hex(pack))
if __name__=='__main__':
 import sys
 for game in sys.argv[1:]or ('gold','silver','crystal'):build(game)
