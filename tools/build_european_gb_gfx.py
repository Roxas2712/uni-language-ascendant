"""Derive EU graphics addresses and export target-owned layouts privately."""
import copy,ctypes,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
from build_european_gb import ROOT,offset,read_symbols,lua
from relocate_gb_refs import recover
# Image helpers are developer-only; use the bundled Python with Pillow.
from build_gb_assets import scan,unlz,raw_image,lib
from PIL import Image
LOVE=os.environ.get('LOVE') or shutil.which('love')
PAIRS=[('gold','es'),('gold','fr'),('gold','it'),('silver','es'),('silver','fr'),('crystal','es'),('crystal','it')]

def plan(game,lang):
 assert LOVE,'Set LOVE to the LÖVE executable'
 m=json.loads((ROOT/f'build/upstream-engine/tools/rom_manifest_{game}.json').read_text())
 spec=next(x for x in json.loads((ROOT/'build/european-inputs.json').read_text()) if x.get('game')==game and x.get('language')==lang)
 rom=Path(spec['file']).read_bytes();assert hashlib.sha1(rom).hexdigest()==spec['sha1']
 us=Path(next(x['file'] for x in json.loads((ROOT/'build/gb-rom-inventory.json').read_text()) if x['sha1']==m['romSha1'])).read_bytes()
 needs=json.loads((ROOT/f'build/{game}-gfx-needed.json').read_text())['needed']
 audit=json.loads((ROOT/f'build/{game}-{lang}-relocation.json').read_text())
 mapped={int(k):v for k,v in audit['mapped'].items()};done={};proof={};todo=dict(needs)
 for _ in range(4):
  for name,info in list(todo.items()):
   b,a=m['symbols'][name];src=offset(b,a);size=info['size'];dest=None;kind=None
   if src in mapped:dest=mapped[src];kind='symbols/event graph'
   if dest is None and size>=8 and not info.get('lz'):
    # An exact complete read range also proves identical rendered pixels.
    found=rom.find(us[src:src+size])
    if found>=0:dest=found;kind='exact entire read range'
   if dest is None and info.get('lz'):
    raw,consumed=unlz(us,src)
    for n in (len(raw),128,64,32):
     hits=scan(rom,raw[:n]) if len(raw)>=n else []
     if len(hits)==1:
      data,_z=unlz(rom,hits[0])
      if 0<len(data)<=16384 and len(data)%16==0:dest=hits[0];kind=f'unique complete LZ prefix {n}';break
   if dest is None:
    try:
     candidate,refs=recover(us,rom,b,a)
     if info.get('lz'):unlz(rom,candidate)
     dest=candidate;kind={'cpu_references':refs}
    except (ValueError,IndexError):pass
   if dest is None:
    for other,value in done.items():
     prev=offset(*m['symbols'][other]);ni=needs[other]
     if ni.get('lz'):
      _d,z=unlz(us,prev)
      if prev+z==src:
       _d,tz=unlz(rom,value);dest=value+tz;kind='adjacent complete LZ stream';break
     elif ni['size'] and prev+ni['size']==src:
      dest=value+ni['size'];kind='adjacent exact-size graphics';break
   if dest is None and name=='LoadQuestionMarkPic.QuestionMarkLZ':
    other=next(x for x in json.loads((ROOT/'build/european-inputs.json').read_text()) if x.get('game')=='crystal' and x.get('language')==lang)
    reference=Path(other['file']).read_bytes()
    reference_off=json.loads((ROOT/f'build/crystal-{lang}-gfx-addresses.json').read_text())['addresses'].get(name)
    if reference_off is not None:
     pixels,_z=unlz(reference,reference_off);hits=scan(rom,pixels)
     if len(hits)==1:dest=hits[0];kind='complete exact localized Crystal reference graphic'
   if dest is None and name=='PackMenuGFX' and 'PackGFX' in done:
    gap=offset(*m['symbols']['PackGFX'])-src
    candidate=done['PackGFX']-gap
    if rom[candidate:candidate+64]==us[src:src+64]:dest=candidate;kind='fixed pack atlas size, exact leading border and following complete pack'
   if dest is None and name=='CopyrightGFX':
    anchors=[done[n]-offset(*m['symbols'][n]) for n in ('TitleScreenGFX3','TitleScreenGFX4') if n in done]
    if len(anchors)==2 and len(set(anchors))==1:dest=src+anchors[0];kind='bank section start, two independent adjacent graphics anchors'
   if dest is None and info.get('lz'):
    _raw,z=unlz(us,src)
    for n,loc in done.items():
     if offset(*m['symbols'][n])!=src+z:continue
     hits=[]
     for candidate in range(max(0,loc-2048),loc):
      try:
       data,consumed=unlz(rom,candidate)
       if candidate+consumed==loc and len(data)==size:hits.append(candidate)
      except (ValueError,IndexError):pass
     if len(hits)==1:dest=hits[0];kind='unique complete preceding LZ stream and exact output size';break
   if dest is not None:
    if info.get('lz'):
     try:
      raw,z=unlz(rom,dest)
      if not (0<len(raw)<=16384 and len(raw)%16==0):continue
     except (ValueError,IndexError):continue
    assert 0<=dest<len(rom)
    done[name]=dest;proof[name]=kind;del todo[name]
  if not todo:break
 out=ROOT/f'build/{game}-gfx-{lang}';out.mkdir(exist_ok=True)
 target=copy.deepcopy(m)
 for name,off in done.items():target['symbols'][name]=[off//16384,off%16384+16384]
 p={'manifest':target,'rom':spec['file'],'game':game,'out':str(out),'report':str(ROOT/f'build/{game}-{lang}-gfx-export.json')}
 dest=ROOT/f'build/{game}-{lang}-gfx-plan.json';dest.write_text(json.dumps(p))
 (ROOT/f'build/{game}-{lang}-gfx-addresses.json').write_text(json.dumps({'sha1':spec['sha1'],'addresses':done,'evidence':proof,'unresolved':todo},indent=2))
 print(game,lang,'resolved',len(done),'missing',list(todo),flush=True)
 if todo:return False
 env=dict(os.environ,ULA_ROOT=str(ROOT),ULA_GFX_PLAN=str(dest))
 result=subprocess.run([LOVE,str(ROOT/'build/eu-gfx-harness')],env=env,capture_output=True,text=True,timeout=60)
 print(result.stdout[-1500:],result.stderr[-300:],flush=True)
 assert result.returncode==0
 return True


def compile_assets(game,lang):
 from build_gb_profiles import export
 p=ROOT/f'mod/gb/profiles/{game}_{lang}'
 recipes=export(p/'assets.lua')
 report=json.loads((ROOT/f'build/{game}-{lang}-gfx-addresses.json').read_text())
 spec=next(x for x in json.loads((ROOT/'build/european-inputs.json').read_text()) if x.get('game')==game and x.get('language')==lang)
 rom=Path(spec['file']).read_bytes();streams=[]
 needs=json.loads((ROOT/f'build/{game}-gfx-needed.json').read_text())['needed']
 for name,off in report['addresses'].items():
  if needs[name].get('lz'):
   data,z=unlz(rom,off);streams.append((off,z,data))
 errors={};cache={}
 for path in sorted((ROOT/f'build/{game}-gfx-{lang}').glob('*')):
  name='assets/'+path.name.replace('__','/');source_image=Image.open(path)
  # Pillow reports low-bit grayscale tRNS in its original 0..3 range,
  # while convert(RGBA) sees expanded 0..255 pixels. Preserve cartridge OBJ
  # transparency explicitly before conversion.
  depth=path.read_bytes()[24]
  if source_image.mode=='L' and depth<8 and isinstance(source_image.info.get('transparency'),int):source_image.info['transparency']*=255//((1<<depth)-1)
  im=source_image.convert('RGBA');tiles=[];missing=[]
  colors_all=set(im.getdata())
  alpha_by_rgb={}
  for color in colors_all:alpha_by_rgb.setdefault(color[:3],set()).add(color[3])
  simple_alpha=all(len(v)==1 for v in alpha_by_rgb.values()) and all(c[3]==255 or c[:3]==(255,255,255) for c in colors_all)
  if simple_alpha and all(c[:3] in ((0,0,0),(255,255,255)) for c in colors_all):
   raw=bytearray()
   for ty in range(0,im.height,8):
    for tx in range(0,im.width,8):
     for y in range(8):raw.append(sum((im.getpixel((tx+x,ty+y))[0]<128 and im.getpixel((tx+x,ty+y))[3]>0)<<(7-x) for x in range(8)))
   raw=bytes(raw);chunks=[]
   for off in range(0,len(raw),8):
    at=rom.find(raw[off:off+8])
    if at<0:break
    chunks.append({'off':at,'size':8})
   if len(chunks)*8==len(raw):
    recipes[name]={'width':im.width,'height':im.height,'bits':1,'transparent':any(c[3]==0 for c in colors_all),'tiles':chunks}
    print('GFX_COMPILE',game,lang,name,'1bpp',flush=True);continue
  if simple_alpha and all(c[0]==c[1]==c[2] for c in colors_all):
   raw=raw_image(im,2);found=rom.find(raw)
   if found>=0:
    recipes[name]={'width':im.width,'height':im.height,'bits':2,'transparent':any(c[3]==0 for c in colors_all),'tiles':[{'off':found,'size':len(raw)}]}
    print('GFX_COMPILE',game,lang,name,'raw',flush=True);continue
  for ty in range(0,im.height,8):
   for tx in range(0,im.width,8):
    pixels=[im.getpixel((tx+x,ty+y)) for y in range(8) for x in range(8)]
    colors=list(dict.fromkeys(pixels));assert len(colors)<=4,(name,len(colors))
    target=bytes(colors.index(v) for v in pixels);located=None
    if target in cache:
     original,palette=cache[target];located=dict(original);located['palette']=[list(colors[k if k>=0 else 0]) for k in palette];tiles.append(located);continue
    for fx,fy in [(False,False),(True,False),(False,True),(True,True)]:
     mirrored=bytes(target[(7-y if fy else y)*8+(7-x if fx else x)] for y in range(8) for x in range(8))
     pal=(ctypes.c_int*4)()
     for off,z,data in streams:
      at=lib.tile(data,len(data),mirrored,pal)
      if at>=0:located={'off':off,'size':z,'lz':True,'start':at,'length':16};break
     if located is None:
      at=lib.tile(rom,len(rom),mirrored,pal)
      if at>=0:located={'off':at,'size':16}
     if located is not None:
      if fx:located['flipX']=True
      if fy:located['flipY']=True
      cache[target]=(dict(located),list(pal))
      located['palette']=[list(colors[k if k>=0 else 0]) for k in pal];break
    if located:tiles.append(located)
    else:missing.append([tx,ty])
  print('GFX_COMPILE',game,lang,name,'tiles',len(tiles),'missing',len(missing),flush=True)
  if missing:errors[name]=missing
  else:recipes[name]={'width':im.width,'height':im.height,'bits':2,'palettes':True,'tiles':tiles}
 assert not errors,(game,lang,errors)
 (p/'assets.lua').write_text('return '+lua(recipes)+'\n')
 layouts=json.loads((ROOT/f'build/{game}-{lang}-gfx-export.json').read_text())['layouts']
 (p/'layouts.lua').write_text('return '+lua({'value':layouts})+'\n')
 profile=export(p/'profile.lua')
 if 'layouts.lua' not in profile['catalogs']:profile['catalogs'].append('layouts.lua')
 (p/'profile.lua').write_text('return '+lua(profile)+'\n')
 print('EU_GFX_CATALOG',game,lang,len(recipes),'complete verified tile recipes',flush=True)

if __name__=='__main__':
 for g,l in ([tuple(sys.argv[1:])] if len(sys.argv)>1 else PAIRS):
  if plan(g,l):compile_assets(g,l)
