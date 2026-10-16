"""Validate four player-count strings through their indexed pointer table."""
import json,sys,struct
from pathlib import Path
from map_emerald_languages import ROOT,BASE
from build_profiles import lua_symbols
from chain_emerald_languages import eos
lang=sys.argv[1];path=ROOT/f'build/emerald-{lang}-relocation.json';r=json.loads(path.read_text());maps={int(k):v for k,v in r['mapped'].items()}
spec=next(x for x in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms'] if x['language']==lang);dst=Path(spec['staged_file']).read_bytes()
sy=lua_symbols(ROOT/'build/profile-engine/src/import/gba/syms/emeraldde.lua')
a,size=sy['gTextTable_Players'];end=sy['gText_WonderCards'][0];assert a+size==end and size==16
b=maps[end]-16;prev=maps[sy['gText_PeopleCommunicating'][0]];lower=eos(dst,prev)
for i in range(4):
 target=struct.unpack_from('<I',dst,b+i*4)[0]-BASE
 assert lower<=target<b and dst[target:target+2]==bytes([247,i])
 finish=eos(dst,target);assert finish and finish<=b
 if i:assert target==last
 maps[sy[f'gText_F70{i}Players'][0]]=target;last=finish
assert b-last<4 and not any(dst[last:b]);maps[a]=b
r['mapped']={str(a):b for a,b in maps.items()};r['counts']['players-table']=4;path.write_text(json.dumps(r));print(lang,'PLAYERS_TABLE_OK')
