"""Bounded static coverage of actual Gen2 Strings calls, not a playthrough."""
import json,hashlib
from pathlib import Path
from gen2_engine_strings import harvest
from build_gb_profiles import export
R=Path(__file__).resolve().parents[1]
TECHNICAL={
 'formatting':['%s%s','%s.','%s %s','{STRBUF}.','???','№.','♂','♀','⁂','/','……'],
 'native unit or glyph macro':['PP','HP','<LV>','<ID>№','<ID>№.','lb','m','kg'],
 'hardware and scale notation':['1X','2X','3X','4X','%dX','DMG'],
 'numeric coin prices':[' 50 :  ¥1000','500 : ¥10000'],
}
def audit():
 keys=harvest(R/'build/upstream-engine');allow={k:reason for reason,values in TECHNICAL.items()for k in values};rows=[]
 for game,lang in [('gold','ko'),('silver','ko'),('crystal','ja')]:
  path=R/f'mod/gb/profiles/{game}_{lang}/strings.lua';recipes=dict(export(path)['table'])
  missing={k:v for k,v in keys.items()if k not in recipes and k not in allow}
  assert not missing,(game,missing)
  rows.append({'game':game,'language':lang,'actualSourceKeys':len(keys),'localizedKeys':sum(k in recipes for k in keys),'unchangedNotation':{k:allow[k]for k in keys if k not in recipes},'missing':missing,'recipeSha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 (R/'build/asian-gen2/ui-coverage.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 print('ASIAN_UI_COVERAGE_OK',[(r['game'],r['actualSourceKeys'],r['localizedKeys'],len(r['unchangedNotation']))for r in rows])
if __name__=='__main__':audit()
