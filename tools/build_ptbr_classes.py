"""Compile compact class labels against complete base class-record identities."""
import argparse,json,re
from pathlib import Path
from build_authored import fingerprints
from lua_literal import lua
ROOT=Path(__file__).resolve().parents[1]

def build(a):
 names=json.loads((ROOT/'translations/pt-BR/trainer-classes.json').read_text())
 output={}
 for game in ('ruby','sapphire','emerald','firered','leafgreen'):
  source=json.loads((a.emerald_base if game=='emerald' else a.base_dir/(game+'-base-texts.json')).read_text())
  rows={k:v for k,v in source.items() if re.fullmatch(r'gTrainerClassNames\[\d+\]',k)}
  assert rows,game
  hashes=fingerprints(rows,a.engine,a.luajit);compiled={}
  for key,ir in rows.items():
   assert all(s['t'] in ('text','tag','eos') for s in ir),'Class label has dynamic operands'
   original=''.join(s.get('s',s.get('tag','')) for s in ir)
   target=names[original];index=int(key.split('[')[1][:-1])
   compiled[index]={'sourceSha256':hashes[key],'target':target}
  output[game]=compiled
 (ROOT/'mod/ptbr_classes.lua').write_text('-- Authored static class labels, pinned to base IR identities.\nreturn '+lua(output)+'\n')
 print('PTBR_CLASSES', {g:len(rows) for g,rows in output.items()})
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('base-dir','emerald-base','engine','luajit'):p.add_argument('--'+name,type=Path,required=True)
 build(p.parse_args())
