"""Localize world atlases without changing base map blocks or collisions."""
import json,re,sys
from pathlib import Path
from build_european_gb import ROOT,offset,lua
from build_gb_profiles import export
from build_gb_assets import unlz,raw_image
from PIL import Image

def find_all(data,needle):
 p=0;out=[]
 while True:
  p=data.find(needle,p)
  if p<0:return out
  out.append(p);p+=1

def run(game,lang):
 spec=next(x for x in json.loads((ROOT/'build/european-inputs.json').read_text()) if x.get('game')==game and x.get('language')==lang);rom=Path(spec['file']).read_bytes()
 m=json.loads((ROOT/'build/upstream-engine/tools'/('rom_manifest'+('' if game=='red' else '_'+game)+'.json')).read_text())
 us=Path(next(x['file'] for x in json.loads((ROOT/'build/gb-rom-inventory.json').read_text()) if x['sha1']==m['romSha1'])).read_bytes()
 folder=ROOT/f'mod/gb/profiles/{game}_{lang}';recipes=export(folder/'assets.lua');proof={}
 if game in ('red','yellow'):
  image=Image.open(Path.home()/f'Library/Application Support/LOVE/ula-europe-expansion-qa/{game}/assets/generated/tilesets/overworld.png').convert('RGBA');raw=raw_image(image,2);anchors=[]
  for start in [0,128,512,1024]:
   found=find_all(rom,raw[start:start+128])
   if len(found)==1:anchors.append(found[0]-start)
  assert len(anchors)>=2 and len(set(anchors))==1,anchors
  recipes['assets/tilesets/overworld.png']={'width':image.width,'height':image.height,'bits':2,'tiles':[{'off':anchors[0],'size':len(raw)}]};proof['overworld']=anchors
 else:
  table=offset(*m['symbols']['Tilesets']);row=us[table+15:table+30]
  def far(v):return offset(v[0],int.from_bytes(v[1:3],'little'))
  metas=find_all(rom,us[far(row[3:6]):far(row[3:6])+2048]);colls=find_all(rom,us[far(row[6:9]):far(row[6:9])+512]);hits=[]
  for meta in metas:
   for coll in colls:
    key=bytes([meta//16384])+((meta%16384)+16384).to_bytes(2,'little')+bytes([coll//16384])+((coll%16384)+16384).to_bytes(2,'little')
    hits.extend(at-18 for at in find_all(rom,key))
  maps=export(Path.home()/f'Library/Application Support/LOVE/ula-europe-expansion-qa/{game}/data/generated/maps.lua')
  used={}
  for row in maps.values():
   used.setdefault(row['tileset'],set()).update(row['blocks']+[row['borderBlock']])
  def same_blocks(a,b,indices,stride):return all(a[i*stride:(i+1)*stride]==b[i*stride:(i+1)*stride] for i in indices)
  valid=[]
  for candidate in hits:
   try:
    for index in range(1,len(m['constants']['tilesetOrder'])+1):
     src=us[table+index*15:table+(index+1)*15];dst=rom[candidate+index*15:candidate+(index+1)*15]
     if index<=3 and not same_blocks(us[far(src[3:6]):far(src[3:6])+2048],rom[far(dst[3:6]):far(dst[3:6])+2048],used.get(m['constants']['tilesetOrder'][index-1],{0}),16):break
     if not same_blocks(us[far(src[6:9]):far(src[6:9])+512],rom[far(dst[6:9]):far(dst[6:9])+512],used.get(m['constants']['tilesetOrder'][index-1],{0}),4):break
    else:valid.append(candidate)
   except (AssertionError,IndexError):pass
  hits=valid
  assert len(hits)==1,('tileset table',game,lang,hits)
  target=hits[0];zero=rom.find(bytes(16));assert zero>=0
  layouts={}
  for index,name in enumerate(m['constants']['tilesetOrder'],1):
   src=us[table+index*15:table+(index+1)*15];dst=rom[target+index*15:target+(index+1)*15]
   if game=='crystal':
    # Regional Unown wall lettering uses different graphical metatiles.
    # Keep all block IDs, map data and collision rules from the US game.
    rows=[]
    for block in sorted(used.get(name,{0})):
     old=far(src[3:6])+block*16;new=far(dst[3:6])+block*16
     if us[old:old+16]!=rom[new:new+16]:rows.append([block+1,{'bytes':{'off':new,'size':16}}])
    if rows:layouts[name]={'table':rows}
   else:assert same_blocks(us[far(src[3:6]):far(src[3:6])+2048],rom[far(dst[3:6]):far(dst[3:6])+2048],used.get(name,{0}),16),(name,'used metatiles changed')
   assert same_blocks(us[far(src[6:9]):far(src[6:9])+512],rom[far(dst[6:9]):far(dst[6:9])+512],used.get(name,{0}),4),(name,'used collision changed')
   off=far(dst[:3]);data,z=unlz(rom,off);tiles=[];count=256 if game=='crystal' else 96
   for i in range(count):
    source=i if game!='crystal' or i<96 else i-32
    if (game=='crystal' and (96<=i<128 or i>=224)) or source*16+16>len(data):tiles.append({'off':zero,'size':16})
    else:tiles.append({'off':off,'size':z,'lz':True,'start':source*16,'length':16})
   rel='assets/tilesets/'+name.lower().removeprefix('tileset_')+'.png'
   recipes[rel]={'width':128,'height':count//16*8,'bits':2,'tiles':tiles};proof[name]={'gfx':off,'usedBlocks':len(used.get(name,{})),'metatiles':'localized visual overrides' if name in layouts else 'identical for all base-map blocks','collisions':'identical for all base-map blocks'}
 if game=='crystal':
  (folder/'world_layout.lua').write_text('return '+lua({'table':[[k,v] for k,v in layouts.items()]})+'\n')
  profile=export(folder/'profile.lua')
  if 'world_layout.lua' not in profile['catalogs']:profile['catalogs'].append('world_layout.lua')
  (folder/'profile.lua').write_text('return '+lua(profile)+'\n')
 (folder/'assets.lua').write_text('return '+lua(recipes)+'\n')
 (ROOT/f'build/{game}-{lang}-world-graphics-report.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('EU_WORLD_OK',game,lang,len(proof),'atlases; base blocks/collisions unchanged',flush=True)
if __name__=='__main__':run(*sys.argv[1:])
