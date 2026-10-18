"""Compile validated offline UI, status and naming catalogs for every EU GB profile."""
import json,os,sys
from pathlib import Path
from build_european_gb import ROOT,lua
from build_gb_profiles import export
pairs=[('red','es'),('yellow','es'),('gold','es'),('gold','fr'),('gold','it'),('silver','es'),('silver','fr'),('crystal','es'),('crystal','it')]
ui=json.loads((ROOT/'translations/european/gb-ui.json').read_text())
for game,lang in pairs:
 ix=('es','fr','it').index(lang);path=ROOT/f'mod/gb/profiles/{game}_{lang}'
 rows={k:{'value':v[ix]} for k,v in ui.items()}
 (path/'strings.lua').write_text('return '+lua({'table':[[k,v] for k,v in sorted(rows.items())]})+'\n')
 status={k:{'value':ui[k][ix]} for k in ('PSN','BRN','FRZ','PAR','SLP')}
 (path/'status_labels.lua').write_text('return '+lua({'table':[[k,v] for k,v in status.items()]})+'\n')
 print('UI_PROFILE',game,lang,len(rows),'keys')
