from pathlib import Path
import json,ctypes,itertools,sys
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent))
from build_gb_profiles import ROOT,REF,DE,GAMES,lua
lib=ctypes.CDLL(str(ROOT/'build/lzscan.dylib'))
lib.tile.argtypes=[ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.POINTER(ctypes.c_int)]
lib.scan.argtypes=[ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.POINTER(ctypes.c_int)]
def scan(rom,raw):
 out=(ctypes.c_int*32)();n=lib.scan(rom,len(rom),raw,min(len(raw),32768),out);return list(out[:n])
def unlz(rom,start):
 p=start;out=bytearray()
 while p<len(rom) and len(out)<32768:
  h=rom[p];p+=1
  if h==255:return bytes(out),p-start
  c=h>>5;n=(h&31)+1
  if c==7:c=(h>>2)&7;n=((h&3)<<8)+rom[p]+1;p+=1
  if c==0:out+=rom[p:p+n];p+=n
  elif c==1:out+=bytes([rom[p]])*n;p+=1
  elif c==2:out+=bytes([rom[p],rom[p+1]])*(n//2)+bytes([rom[p]])*(n%2);p+=2
  elif c==3:out+=b'\0'*n
  else:
   a=rom[p];p+=1
   if a&128:src=len(out)-(a&127)-1
   else:src=a*256+rom[p];p+=1
   for k in range(n):
    i=src+(-k if c==6 else k)
    if i<0 or i>=len(out):raise ValueError('backref')
    v=out[i]
    if c==5:v=int(f'{v:08b}'[::-1],2)
    out.append(v)
 raise ValueError('unterminated')
def raw_image(im,bits):
 w,h=im.size;out=bytearray()
 for ty in range(0,h,8):
  for tx in range(0,w,8):
   for y in range(8):
    vals=[im.getpixel((tx+x,ty+y)) for x in range(8)]
    if bits==1:out.append(sum((p[3]>0)<<(7-x) for x,p in enumerate(vals)))
    else:
     shades=[3-round(p[0]/85) for p in vals]
     out.extend([sum(((v>>b)&1)<<(7-x) for x,v in enumerate(shades)) for b in range(2)])
 return bytes(out)
def build(game):
 inv=json.loads((ROOT/'build/gb-rom-inventory.json').read_text());rom=Path(next(r['file'] for r in inv if r['sha1']==DE[game])).read_bytes()
 recipes={};streams=[];images={}
 mf=json.loads((ROOT/'build/upstream-engine/tools'/('rom_manifest'+('' if game=='red' else '_'+game)+'.json')).read_text())
 us=Path(next(r['file'] for r in inv if r['sha1']==mf['romSha1'])).read_bytes()
 if game in ['gold','silver','crystal']:
  # Locate compressed artwork by exact decompressed prefixes from the US
  # counterpart; verify the resulting images against the German reference.
  for label in ['TownMapGFX','PokegearGFX','TitleScreenGFX1','TitleScreenGFX2','TitleScreenGFX3','TitleScreenGFX4','TitleLogoGFX','TitleSuicuneGFX','TitleCrystalGFX']:
   loc=mf['symbols'].get(label)
   if not loc:continue
   off=loc[0]*16384+loc[1]%16384
   try:data,_=unlz(us,off)
   except (ValueError,IndexError):continue
   if len(data)<64:continue
   for candidate in scan(rom,data[:64]):
    try:
     d,z=unlz(rom,candidate)
     if len(d)>=64:streams.append((candidate,z,True,d))
    except (ValueError,IndexError):pass
 else:
  cache=Path.home()/'Library/Application Support/LOVE/german-rom-mod-gb-qa'/game/'assets/generated/tilesets/overworld.png'
  im=Image.open(cache).convert('RGBA');raw=raw_image(im,2)
  # The sign tile is later in the sheet; independent unchanged anchors agree.
  offsets=[]
  for a in [0,128,512,1024]:
   q=rom.find(raw[a:a+128])
   if q>=0 and rom.find(raw[a:a+128],q+1)<0:offsets.append(q-a)
  assert offsets and len(set(offsets))==1,(game,offsets)
  off=offsets[0];target=rom[off:off+len(raw)]
  assert sum(a!=b for a,b in zip(raw,target))<128
  recipes['assets/tilesets/overworld.png']={'width':im.width,'height':im.height,'bits':2,'tiles':[{'off':off,'size':len(raw)}]}

 files={}
 if game=='crystal':files.update({str(p.relative_to(REF/'editions/silver/assets')):p for p in (REF/'editions/silver/assets').rglob('*.png') if not str(p.relative_to(REF/'editions/silver/assets')).startswith(('tilesets/','title/'))})
 files.update({str(p.relative_to(REF/f'editions/{game}/assets')):p for p in (REF/f'editions/{game}/assets').rglob('*.png')})
 for name,p in files.items():
  im=Image.open(p).convert('RGBA');colors=set(im.getdata());bits=1 if all(c[:3] in [(0,0,0),(255,255,255)] for c in colors) and any(c[3]==0 for c in colors) else 2
  if bits==2 and any(c[0]!=c[1] or c[1]!=c[2] for c in colors):continue
  raw=raw_image(im,bits)
  if name=='fonts/font_battle_extra.png':
   for parity in [0,1]:
    q=rom[parity::2].find(raw)
    if q>=0:
     recipes['assets/'+name]={'width':im.width,'height':im.height,'bits':2,'ink':True,'tiles':[{'off':q*2+parity-1,'size':len(raw)*2}]}
     break
   if 'assets/'+name in recipes:continue
  images[name]=(im,bits,raw)
  # Extracted padding is not part of a cartridge's source stream.
  target=raw.rstrip(b'\0')
  if game=='crystal' and name.startswith('tilesets/'):
   target=raw[:96*16]+raw[128*16:224*16]
  found=rom.find(target)
  if found>=0:streams.append((found,len(target),False,raw[:len(target)]));continue
  if game in ['gold','silver','crystal']:
   for off in scan(rom,target):
    try:
     data,size=unlz(rom,off)
     if data.startswith(target):streams.append((off,size,True,data));break
    except (ValueError,IndexError):pass
 # Tile recipes can compose graphics whose source has padding or column order.
 for name,(im,bits,raw) in images.items():
  bpt=bits*8;tiles=[];missing=0
  for i in range(0,len(raw),bpt):
   tile=raw[i:i+bpt];at=rom.find(tile)
   if at>=0:tiles.append({'off':at,'size':bpt});continue
   located=None
   for off,size,lz,data in streams:
    j=data.find(tile)
    if j>=0:located={'off':off,'size':size,'lz':lz,'start':j,'length':bpt};break
   if located:tiles.append(located)
   else:missing+=1
  if missing:print(game,name,'MISSING',missing,flush=True);continue
  recipes['assets/'+name]={'width':im.width,'height':im.height,'bits':bits,'transparent':bits==1,'tiles':tiles}
  print(game,name,'OK',flush=True)
 # Compose every title from whole ROM tiles. Per-tile palettes are renderer
 # metadata (including OBP transparency), never embedded pixel payloads.
 for name,path in files.items():
  if not name.startswith('title/'):continue
  im=Image.open(path).convert('RGBA');tiles=[];missing=0
  for ty in range(0,im.height,8):
   for tx in range(0,im.width,8):
    pixels=[im.getpixel((tx+x,ty+y)) for y in range(8) for x in range(8)]
    colors=list(dict.fromkeys(pixels));target=bytes(colors.index(p) for p in pixels)
    if len(colors)>4:missing+=1;continue
    pal=(ctypes.c_int*4)();located=None
    for off,size,lz,data in streams:
     at=lib.tile(data,len(data),target,pal)
     if at>=0:
      located={'off':off,'size':size,'lz':lz,'start':at,'length':16};break
    if located is None:
     at=lib.tile(rom,len(rom),target,pal)
     if at>=0:located={'off':at,'size':16}
    if located is None:missing+=1;continue
    located['palette']=[list(colors[k if k>=0 else 0]) for k in pal]
    tiles.append(located)
  if missing:print(game,name,'TITLE MISSING',missing,flush=True)
  else:
   recipes['assets/'+name]={'width':im.width,'height':im.height,'bits':2,'palettes':True,'tiles':tiles}
   print(game,name,'TITLE OK',flush=True)
 if game=='yellow':
  # Retail German tilemap; the earlier universal mod manually respaced the
  # wordmark. Here preserve the actual cartridge layout.
  sources=[(0xf46fb,115*16),(0xf4e2b,3*16),(0xf4e5b,64*16),(0xf525b,12*16)]
  def tile_offset(t):
   return 0xf46fb+t*16 if t<128 else (0xf4e5b+(t-128)*16 if t<240 else (0xf525b+(t-240)*16 if t<253 else 0xf4e2b+(t-253)*16))
  tiles=[{'off':tile_offset(t),'size':16} for t in rom[0xf45f9:0xf45f9+112]]
  recipes['assets/title/pokemon_logo.png']={'width':128,'height':56,'bits':2,'tiles':tiles}
  palette=[[255-i*85]*3+[255] for i in range(4)]
  ids=list(rom[0xf4673:0xf4673+28])+[None,None,None,0x64,0x65,None,None]
  bubble=[]
  for t in ids:
   bubble.append({'off':tile_offset(t) if t is not None else rom.find(bytes(16)), 'size':16,
                  'palette':palette if t is not None else [[255,255,255,0]]*4})
  recipes['assets/title/pika_bubble.png']={'width':56,'height':40,'bits':2,'palettes':True,'matte':True,'tiles':bubble}
 out=ROOT/f'mod/gb/profiles/{game}/assets.lua';out.write_text('return '+lua(recipes)+'\n')
 (ROOT/f'build/{game}-gb-streams.json').write_text(json.dumps([{'off':a,'size':b,'lz':c,'length':len(d)} for a,b,c,d in streams]))
if __name__=='__main__':
 for g in GAMES:build(g)
