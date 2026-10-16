"""Compose Spanish Yellow's own title tilemaps from its private cartridge."""
import json
from pathlib import Path
from build_european_gb import ROOT,offset,lua
from build_gb_profiles import export
from build_european_gb_world import find_all

def run():
 m=json.loads((ROOT/'build/upstream-engine/tools/rom_manifest_yellow.json').read_text())
 spec=next(x for x in json.loads((ROOT/'build/european-inputs.json').read_text()) if x.get('game')=='yellow' and x.get('language')=='es')
 rom=Path(spec['file']).read_bytes();us=Path(next(x['file'] for x in json.loads((ROOT/'build/gb-rom-inventory.json').read_text()) if x['sha1']==m['romSha1'])).read_bytes()
 anchors=[]
 for label,size in [('TitlePikachuBGGraphics',1024),('TitlePikachuOBGraphics',192),('PokemonLogoCornerGraphics',48)]:
  old=offset(*m['symbols'][label]);hits=find_all(rom,us[old:old+size])
  if len(hits)==1:anchors.append(hits[0]-old)
 assert len(anchors)>=2 and len(set(anchors))==1,anchors
 delta=anchors[0];symbols={k:offset(*v)+delta for k,v in m['symbols'].items() if k.startswith(('TitleScreen','TitlePikachu','PokemonLogo'))}
 zero=rom.find(bytes(16));assert zero>=0
 def tile(t):
  if t<128:
   assert t<115;return symbols['PokemonLogoGraphics']+t*16
  if t<240:return symbols['TitlePikachuBGGraphics']+(t-128)*16
  if t<253:return symbols['TitlePikachuOBGraphics']+(t-240)*16
  return symbols['PokemonLogoCornerGraphics']+(t-253)*16
 folder=ROOT/'mod/gb/profiles/yellow_es';assets=export(folder/'assets.lua')
 start=symbols['TitleScreenPokemonLogoTilemap'];tiles=[{'off':tile(t),'size':16} for t in rom[start:start+112]]
 assets['assets/title/pokemon_logo.png']={'width':128,'height':56,'bits':2,'tiles':tiles}
 start=symbols['TitleScreenPikaBubbleTilemap'];ids=list(rom[start:start+28])+[None,None,None,0x64,0x65,None,None]
 palettes=[[255-i*85]*3+[255] for i in range(4)]
 tiles=[{'off':tile(t) if t is not None else zero,'size':16,'palette':palettes if t is not None else [[255,255,255,0]]*4} for t in ids]
 assets['assets/title/pika_bubble.png']={'width':56,'height':40,'bits':2,'palettes':True,'matte':True,'tiles':tiles}
 (folder/'assets.lua').write_text('return '+lua(assets)+'\n')
 (ROOT/'build/yellow-es-title-graphics-report.json').write_text(json.dumps({'anchors':anchors,'symbols':symbols,'sha1':spec['sha1']},indent=2))
 print('YELLOW_ES_TITLE_OK two cartridge tilemaps, three independent section anchors')
if __name__=='__main__':run()
