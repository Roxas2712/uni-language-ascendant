"""Native outdoor signage, preserving US map geometry and collisions.

Only atlases with byte-identical used metatile and collision definitions pass.
No artwork is distributed: output contains local-ROM span recipes only.
"""
import hashlib,json,sys
from pathlib import Path
from asian_gen2 import offset,symbols
from build_gb_profiles import export,lua
from gb_lz import decompress
R=Path(__file__).resolve().parents[1];REF=R.parent/'Uni-Language-Ascendant-Europe/build'
def build(game):
 lang='ja' if game=='crystal'else 'ko';folder=R/f'mod/gb/profiles/{game}_{lang}'
 p=export(folder/'profile.lua');assets=export(folder/'assets.lua')
 rom=(R.parent/'Pocket Monsters - Crystal Version (Japan).gbc' if lang=='ja'else R/f'build/pokegold-kr/poke{game}.gbc').read_bytes()
 m=json.loads((R/f'build/upstream-engine/tools/rom_manifest_{game}.json').read_text());us=(REF/('pokecrystal'if lang=='ja'else'pokegold')/f'poke{game}.gbc').read_bytes()
 assert hashlib.sha1(rom).hexdigest()==p['sha1'] and hashlib.sha1(us).hexdigest()==m['romSha1']
 table=offset(*m['symbols']['Tilesets']);maps=export(Path.home()/f'Library/Application Support/LOVE/ula-asian-gen2-qa/{game}/data/generated/maps.lua')
 used={}
 for row in maps.values():used.setdefault(row['tileset'],set()).update(row['blocks']+[row['borderBlock']])
 def far(data):return offset(data[0],int.from_bytes(data[1:3],'little'))
 if lang=='ko':target=offset(*symbols(R/f'build/pokegold-kr/poke{game}.sym')['Tilesets'])
 else:
  first=us[table+15:table+30];meta=us[far(first[3:6]):far(first[3:6])+2048];coll=us[far(first[6:9]):far(first[6:9])+512]
  def find_all(needle):
   rows=[];pos=rom.find(needle)
   while pos>=0:rows.append(pos);pos=rom.find(needle,pos+1)
   return rows
  hits=[]
  for a in find_all(meta):
   for b in find_all(coll):
    key=bytes([a//16384])+(a%16384+16384).to_bytes(2,'little')+bytes([b//16384])+(b%16384+16384).to_bytes(2,'little')
    hits.extend(c-18 for c in find_all(key))
  valid=[]
  for candidate in set(hits):
   try:
    for i,name in enumerate(m['constants']['tilesetOrder'][:3],1):
     a=us[table+i*15:table+(i+1)*15];b=rom[candidate+i*15:candidate+(i+1)*15]
     for rel,width in ((3,16),(6,4)):
      src,dst=far(a[rel:rel+3]),far(b[rel:rel+3])
      assert all(us[src+block*width:src+(block+1)*width]==rom[dst+block*width:dst+(block+1)*width]for block in used[name])
    valid.append(candidate)
   except (AssertionError,IndexError):pass
  assert len(valid)==1,('Native tileset table',valid);target=valid[0]
 zero=rom.find(bytes(16));proof={}
 for index,name in enumerate(m['constants']['tilesetOrder'][:3],1):
  src=us[table+index*15:table+(index+1)*15];dst=rom[target+index*15:target+(index+1)*15]
  for rel,width in ((3,16),(6,4)):
   a,b=far(src[rel:rel+3]),far(dst[rel:rel+3])
   for block in used[name]:assert us[a+block*width:a+(block+1)*width]==rom[b+block*width:b+(block+1)*width],(name,block,'metatile'if rel==3 else'collision')
  off=far(dst[:3]);raw,size=decompress(rom,off);original,_=decompress(us,far(src[:3]));tiles=[];count=256 if lang=='ja'else 96
  for i in range(count):
   source=i if lang=='ko'or i<96 else i-32
   if (lang=='ja'and(96<=i<128 or i>=224))or source*16+16>len(raw):tiles.append({'off':zero,'size':16})
   else:tiles.append({'off':off,'size':size,'lz':True,'start':source*16,'length':16})
  path='assets/tilesets/'+name.lower().removeprefix('tileset_')+'.png';assets[path]={'width':128,'height':count//16*8,'bits':2,'tiles':tiles}
  proof[name]={'sourceOffset':off,'compressedBytes':size,'usedBlocks':len(used[name]),'changedTiles':[i for i in range(min(len(raw),len(original))//16)if raw[i*16:i*16+16]!=original[i*16:i*16+16]],'geometryAndCollisions':'identical'}
 (folder/'assets.lua').write_text('return '+lua(assets)+'\n')
 (R/f'build/asian-gen2/{game}-{lang}-world.json').write_text(json.dumps(proof,indent=2)+'\n');print('ASIAN_WORLD_OK',game,proof)
if __name__=='__main__':build(sys.argv[1])
