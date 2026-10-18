"""Run independent generation groups in separate disposable QA identities."""
import os,subprocess,sys,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def group(index,games,combos):
 def run(games,mods='',**flags):
  env=dict(os.environ,QA_ALL='0',QA_NURSE='0',QA_RECOVERY='0',QA_BAD_UI='0',QA_REUSE_CURRENT='1',QA_LIVE_IDENTITY='ula-live-switch-suite-'+str(index));env.pop('QA_REPEAT',None);env.update({k:str(v)for k,v in flags.items()})
  subprocess.run([sys.executable,str(R/'tests/run_live_switch.py'),*games,'--mods',mods],env=env,cwd=R,check=True)
 run(games,QA_ALL=1,QA_NURSE=1)
 for game,mods,nurse in combos:run([game],mods,QA_NURSE=nurse)
 representative=games[0]if index<2 else'emerald'
 run([representative],QA_RECOVERY=1,QA_BAD_UI=1)
 run([representative],QA_REPEAT=3)
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
  jobs=[pool.submit(group,0,['red','blue','yellow'],[('red','vasc,kasc',1),('red','vasc',0)]),pool.submit(group,1,['gold','silver','crystal'],[('gold','vasc,kasc',1)]),pool.submit(group,2,['firered','leafgreen','ruby','sapphire','emerald'],[('emerald','origami',1)])]
  for job in concurrent.futures.as_completed(jobs):job.result()
 print('LIVE_SWITCH_SUITE_OK',flush=True)
