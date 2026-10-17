"""Rebuild authored display vocabulary; numeric IDs remain game identities."""
import json
from pathlib import Path
from lua_literal import lua
ROOT=Path(__file__).resolve().parents[1]

def build():
 source=ROOT/'translations/pt-BR'
 moves=json.loads((source/'move-names.json').read_text())['moves']
 abilities=json.loads((source/'ability-names.json').read_text())
 types=json.loads((source/'type-names.json').read_text())
 assert set(moves)=={str(i) for i in range(1,355)}
 assert set(abilities)=={str(i) for i in range(78)}
 for filename,rows in [('ptbr_moves',moves),('ptbr_abilities',abilities),('ptbr_ability_descriptions',json.loads((source/'ability-descriptions.json').read_text()))]:
  assert all(v and not any(c in v for c in '\n\r\t') for v in rows.values())
  (ROOT/'mod'/f'{filename}.lua').write_text('-- Generated authored PT-BR display vocabulary.\nreturn '+lua({int(k):v for k,v in rows.items()})+'\n')
 descriptions=json.loads((source/'move-description-corrections.json').read_text())
 assert all(1<=int(k)<=354 and v.count('\n')<=2 and '\r' not in v for k,v in descriptions.items())
 (ROOT/'mod/ptbr_move_descriptions.lua').write_text('-- Authored corrections for shared Gen-3 move descriptions.\nreturn '+lua({int(k):v for k,v in descriptions.items()})+'\n')
 trainers=json.loads((source/'pokenav-trainers.json').read_text())
 assert len(trainers)==69 and all(len(r['lines'])==4 for r in trainers)
 (ROOT/'mod/ptbr_pokenav_trainers.lua').write_text('-- Authored from the original four-line Trainer Eyes records.\nreturn '+lua(trainers)+'\n')
 scene=json.loads((source/'scene-supplement.json').read_text())
 assert all(len(k)==64 and 'target' in v for k,v in scene.items())
 (ROOT/'mod/ptbr_scene_authored.lua').write_text('-- Own translations, keyed by complete native source SHA-256.\nreturn '+lua(scene)+'\n')
 easy=json.loads((source/'easy-chat.json').read_text())
 assert all(len(k)==64 and r['target'] for k,r in easy.items())
 (ROOT/'mod/ptbr_easy_chat_words.lua').write_text('-- Authored vocabulary; identity hashes include the original group context.\nreturn '+lua(easy)+'\n')
 for filename,sourcefile in [('ptbr_items','item-names'),('ptbr_item_descriptions','item-description-corrections')]:
  rows=json.loads((source/(sourcefile+'.json')).read_text())
  assert all(1<=int(k)<=376 and isinstance(v,str) and v.strip() for k,v in rows.items())
  (ROOT/'mod'/(filename+'.lua')).write_text('-- Authored Gen3 item display text; numeric IDs stay native.\nreturn '+lua({int(k):v for k,v in rows.items()})+'\n')
 order=['NORMAL','FIGHTING','FLYING','POISON','GROUND','ROCK','BUG','GHOST','STEEL','MYSTERY','FIRE','WATER','GRASS','ELECTRIC','PSYCHIC','ICE','DRAGON','DARK']
 (ROOT/'mod/ptbr_types.lua').write_text('-- Generated authored PT-BR type names, Gen-3 numeric IDs.\nreturn '+lua({i:types[k] for i,k in enumerate(order)})+'\n')
if __name__=='__main__':build()
