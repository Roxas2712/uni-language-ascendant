"""Validate the expanded FRLG PT-BR display tables against cartridge IDs.

Headers identify fixed typed pointers; Pokédex records are recognized only by
the complete 387-record sequence of metric facts. Names are length-bounded,
terminated and zero-padded. Nothing here modifies gameplay records.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
BASE=0x08000000
HEADER={0x128:'gMonFrontPicTable',0x12c:'gMonBackPicTable',0x130:'gMonPaletteTable',
 0x134:'gMonShinyPaletteTable',0x138:'gMonIconTable',0x13c:'gMonIconPaletteIndices',
 0x140:'gMonIconPaletteTable',0x144:'gSpeciesNames',0x148:'gMoveNames',0x14c:'gDecorations',
 0x1bc:'gSpeciesInfo',0x1c0:'gAbilityNames',0x1c4:'gAbilityDescriptionPointers',0x1c8:'gItems',
 0x1cc:'gBattleMoves',0x1d0:'gBallSpriteSheets',0x1d4:'gBallSpritePalettes'}
def run(a):
 src=a.base.read_bytes();dst=a.target.read_bytes();audit=json.loads(a.relocation.read_text())
 assert hashlib.sha1(src).hexdigest()==audit['base_sha1']
 assert hashlib.sha1(dst).hexdigest()==audit['target_sha1']
 rows=json.loads(a.symbols.read_text());sy={r['name']:r for r in rows};maps={};proof=[];fields={}
 def bind(name,new,why):
  old=sy[name]['off'];assert 0<=new<len(dst)
  maps[old]=new;proof.append([name,old,new,why]);return new
 for pos,name in HEADER.items():
  assert struct.unpack_from('<I',src,pos)[0]-BASE==sy[name]['off'],name
  bind(name,struct.unpack_from('<I',dst,pos)[0]-BASE,['GFRomHeader',pos])
 def fixed_names(name,count,candidates):
  off=maps[sy[name]['off']];valid=[]
  for stride in candidates:
   for i in range(count):
    row=dst[off+i*stride:off+(i+1)*stride]
    if 255 not in row or any(c not in (0,255) for c in row[row.index(255)+1:]):break
   else:valid.append(stride)
  assert len(valid)==1,(name,valid)
  proof.append(['fixed-terminated-names',name,count,valid[0]]);return valid[0]
 fields['SPECIES_NAME_LENGTH']=fixed_names('gSpeciesNames',412,range(11,25))
 fields['MOVE_NAME_LENGTH']=fixed_names('gMoveNames',355,range(13,25))-1
 fields['ABILITY_NAME_LENGTH']=fixed_names('gAbilityNames',78,range(13,25))-1
 # Item IDs, price, held effect and parameter preserve every original slot.
 # Four extra name bytes move the aligned description pointer from 20 to 24.
 old=sy['gItems']['off'];new=maps[old];valid=[]
 for stride in range(44,65,4):
  shift=stride-44
  if all(src[old+i*44+14:old+i*44+20]==dst[new+i*stride+14+shift:new+i*stride+20+shift] for i in range(375)):valid.append((stride,shift))
 assert len(valid)==1,valid
 stride,shift=valid[0];fields.update(ITEM_STRIDE=stride,ITEM_NAME_LENGTH=14+shift,ITEM_DESCRIPTION_OFFSET=20+shift)
 for i in range(375):
  row=dst[new+i*stride:new+i*stride+14+shift];assert 255 in row and not any(c not in (0,255) for c in row[row.index(255)+1:]),('item name',i)
  op=struct.unpack_from('<I',src,old+i*44+20)[0]-BASE;np=struct.unpack_from('<I',dst,new+i*stride+20+shift)[0]-BASE
  assert 0<=np<len(dst)
  if op in maps:assert maps[op]==np
  maps[op]=np
 proof.append(['item-table',old,new,stride,shift,375])
 old=sy['gPokedexEntries']['off'];needle=src[old+36+12:old+36+16];hits=[]
 for match in re.finditer(re.escape(needle),dst):
  for stride in range(36,53,4):
   height=12+stride-36;new=match.start()-stride-height
   if new<0 or new%4:continue
   if all(src[old+i*36+12:old+i*36+16]==dst[new+i*stride+height:new+i*stride+height+4] for i in range(387)):hits.append((new,stride,height))
 assert len(hits)==1,('Pokedex',hits)
 new,stride,height=hits[0];bind('gPokedexEntries',new,['metric-sequence',387,stride,height])
 # Bound the complete category field including its EOS and alignment padding;
 # an 18-letter translated category places EOS at byte 18, before height=20.
 fields.update(POKEDEX_ENTRY_SIZE=stride,POKEDEX_NAME_LENGTH=height,POKEDEX_HEIGHT_OFFSET=height,POKEDEX_TEXT_OFFSET=height+4)
 for i in range(387):
  row=dst[new+i*stride:new+i*stride+height];assert 255 in row and not any(c not in (0,255) for c in row[row.index(255)+1:]),('dex kind',i)
  # The remaining scales/offsets must also be unchanged for every species.
  assert src[old+i*36+24:old+(i+1)*36]==dst[new+i*stride+height+12:new+(i+1)*stride],('dex metadata',i)
  for rel in [0,4]:
   op=struct.unpack_from('<I',src,old+i*36+16+rel)[0]-BASE;np=struct.unpack_from('<I',dst,new+i*stride+height+4+rel)[0]-BASE
   assert 0<=np<len(dst)
   # Aliased empty descriptions can have identical distinct PT targets.
   if op in maps and maps[op]!=np:
    def string(p):return dst[p:dst.index(255,p)+1]
    assert string(maps[op])==string(np),('dex alias',i,rel)
   else:maps[op]=np
 # Native PT adds one trailing class. The code reference anchors slot zero;
 # inferring the beginning backwards using the US count shifts every class.
 old=sy['gTrainerClassNames']['off'];following=sy['gTrainers']['off']
 assert following-old==(107*13+3)&~3
 new_end=audit['mapped'][str(following)];new=audit['mapped'][str(old)];valid=[]
 for stride in range(13,25):
  for padding in range(4):
   span=new_end-new-padding
   if span%stride or not 107<=span//stride<=110:continue
   count=span//stride
   if any(dst[new+count*stride:new_end]):continue
   for i in range(count):
    row=dst[new+i*stride:new+(i+1)*stride]
    if 255 not in row or any(c not in (0,255) for c in row[row.index(255)+1:]):break
   else:valid.append((stride,count))
 assert len(valid)==1,('trainer classes',valid)
 stride,count=valid[0];bind('gTrainerClassNames',new,['code-anchored-class-array',107,count,stride,new_end]);fields['TRAINER_CLASS_NAME_STRIDE']=stride
 from frlg_summary_relocation import extract as summary_pages
 pages,summary_proof=summary_pages(src,dst,sy,audit['mapped'])
 for old,new in pages.items():
  assert old not in maps or maps[old]==new
  maps[old]=new
 proof.append(summary_proof)
 from frlg_tileset_relocation import extract as tileset_header
 tiles,tiles_proof=tileset_header(src,dst,sy)
 for old,new in tiles.items():
  assert old not in maps or maps[old]==new
  maps[old]=new
 proof.append(tiles_proof)
 a.output.write_text(json.dumps(dict(base_sha1=audit['base_sha1'],target_sha1=audit['target_sha1'],mapped=maps,fields=fields,proof=proof),indent=2))
 print('STRUCTURES',len(maps),fields)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for key in ['base','target','symbols','relocation','output']:p.add_argument('--'+key,type=Path,required=True)
 run(p.parse_args())
