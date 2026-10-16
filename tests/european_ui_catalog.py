"""Offline UI invariants: field geometry, formats and every generated profile."""
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_european_ui import TOKENS
from build_gb_profiles import export
ui=json.loads((ROOT/'translations/european/gb-ui.json').read_text())
assert len(ui)>=856
# Limits come from the engine's actual fixed tile columns, not string lengths
# in the original English.  They protect adjacent numeric/player-name fields.
limits={'NAME/':5,'MONEY':5,'PLAY TIME':9,'BADGES':6,'BOX NAME?':14,
        "RIVAL'S NAME?":14,"MOTHER'S NAME?":14,'EXP POINTS':10,'LEVEL UP':10,
        'ATTACK':9,'DEFENSE':9,'SPEED':9,'SPCL.ATK':9,'SPCL.DEF':9,'SWITCH':6}
for key,values in ui.items():
 for value in values:
  assert value.strip() and 'ZXQ' not in value,key
  assert sorted(TOKENS.findall(key))==sorted(TOKENS.findall(value)),key
  if key in limits:assert len(value)<=limits[key],(key,value)
for game,lang in [('red','es'),('yellow','es'),('gold','es'),('gold','fr'),('gold','it'),('silver','es'),('silver','fr'),('crystal','es'),('crystal','it')]:
 rows=dict(export(ROOT/f'mod/gb/profiles/{game}_{lang}/strings.lua')['table'])
 assert set(rows)==set(ui)
 ix=('es','fr','it').index(lang)
 for key,values in ui.items():assert rows[key]['value']==values[ix],(game,lang,key)
print('EU_UI_CATALOG_OK',len(ui),'keys x 3 languages, 9 profiles, fixed fields and format/control identities')
