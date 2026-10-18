"""Encode inspected native menu/title artwork as cartridge tile recipes.

Inputs are private PNGs produced by the stock extractor with verified title
pointer overrides. Output contains tile addresses/palettes, never image bytes.
"""
import argparse,ctypes,json,struct
from pathlib import Path
from PIL import Image
from gb_lz import decompress
from gen1_ptbr_dialogue import offset

def title_symbols(m,base,rom):
 out={};proof=[]
 for label,de,copy in [('TitleScreenGFX1',0x9000,False),('TitleScreenGFX2',0x8800,False),('TitleScreenGFX4',0x8000,False),('TitleScreenGFX3',0x8f80,True),('TitleScreenTilemap',0x9800,False)]:
  if label not in m['symbols']:continue
  bank,address=m['symbols'][label]
  pattern=b'\x21'+struct.pack('<H',address)+b'\x11'+struct.pack('<H',de)+(b'\x01\x80\x00' if copy else b'')+bytes([0x3e,bank])
  at=base.find(pattern);assert at>=0 and base.find(pattern,at+1)<0,(label,'Ambiguous graphics load')
  raw=rom[at:at+len(pattern)]
  assert raw[0]==0x21 and raw[3:-1]==pattern[3:-1],(label,'Graphics load instructions changed')
  out[label]=[raw[-1],int.from_bytes(raw[1:3],'little')]
  assert 0x4000<=out[label][1]<0x8000
  proof.append(dict(label=label,load_offset=at,source=[bank,address],target=out[label]))
 return out,proof

def build(a):
 m=json.loads(a.manifest.read_text());rom=a.rom.read_bytes();base=a.base.read_bytes()
 import hashlib
 from build_gen2_ptbr import SHA
 assert hashlib.sha1(rom).hexdigest()==SHA[a.game]
 assert hashlib.sha1(base).hexdigest()==m['romSha1']
 syms=dict(m['symbols']);extra,witness=title_symbols(m,base,rom);syms.update(extra)
 lib=ctypes.CDLL(str(a.library));lib.tile.argtypes=[ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.POINTER(ctypes.c_int)]
 streams=[]
 for label in ['TitleScreenGFX1','TitleScreenGFX2','TitleLogoGFX','TitleSuicuneGFX','TitleCrystalGFX','TownMapGFX','PokegearGFX','PokedexLZ','DiplomaGFX']:
  if label not in syms:continue
  off=offset(*syms[label]);raw,size=decompress(rom,off);streams.append((off,size,raw))
 names=['pack/menu.png','pokegear/gear.png','pokedex/dex.png','trainer_card/status.png','trainer_card/leaders.png','credits/theend.png','diploma/diploma.png']
 if a.game=='crystal':names+=['title/crystal_screen.png','title/crystal_screen_gray.png','title/crystal_logo.png','title/crystal_wordmark.png']
 else:names+=['title/title_screen.png','title/title_screen_gray.png','title/pokemon_logo.png']
 assets={};report=[]
 for name in names:
  im=Image.open(a.images/name).convert('RGBA');w,h=im.size;assert w%8==h%8==0
  tiles=[]
  for y in range(0,h,8):
   for x in range(0,w,8):
    pixels=[im.getpixel((x+xx,y+yy)) for yy in range(8) for xx in range(8)];colors=list(dict.fromkeys(pixels));assert len(colors)<=4,(name,x,y)
    target=bytes(colors.index(p) for p in pixels);pal=(ctypes.c_int*4)();found=None
    for off,size,raw in streams:
     at=lib.tile(raw,len(raw),target,pal)
     if at>=0:found=dict(off=off,size=size,lz=True,start=at,length=16);break
    if found is None:
     at=lib.tile(rom,len(rom),target,pal);assert at>=0,('Tile not in cartridge',name,x,y)
     found=dict(off=at,size=16)
    found['palette']=[list(colors[k if k>=0 else 0]) for k in pal];tiles.append(found)
  assets['assets/'+name]=dict(width=w,height=h,bits=2,palettes=True,tiles=tiles)
  report.append(dict(path=name,width=w,height=h,pixel_sha256=hashlib.sha256(im.tobytes()).hexdigest()))
 a.output.write_text(json.dumps(dict(assets=assets,title_pointer_proof=witness,images=report),indent=2)+'\n')
 print('NATIVE_ART_RECIPES',a.game,len(assets))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game',choices=['gold','silver','crystal'],required=True)
 for k in ['manifest','base','rom','images','library','output']:p.add_argument('--'+k,type=Path,required=True)
 build(p.parse_args())
