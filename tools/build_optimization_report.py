"""Publish losslessness digests and controlled release-to-release measurements."""
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parents[1]

def build(inputs):
    version=json.loads((ROOT/'mod/manifest.json').read_text())['version']
    verified=json.loads((inputs/'losslessness.json').read_text())
    expected={(g,l) for g in ['red','blue','yellow','gold','silver','crystal','ruby','sapphire','emerald','firered','leafgreen'] for l in ['de','pt-BR']}|{('emerald',l) for l in ['fr','it','es']}
    assert len(verified)==len(expected) and {(r['game'],r['language']) for r in verified}==expected
    assert all(r['passed'] and r.get('warmVerified') for r in verified)
    runs=json.loads((inputs/'paired-performance.json').read_text())
    assert [r['version'] for r in runs]==['1.5.0',version,version,'1.5.0']
    current={p.relative_to(ROOT/'mod').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'mod').rglob('*.lua')}
    for r in runs:
        assert r['cacheHit'] and r['draw']['n']==360 and r['game']=='emerald' and r['language']=='pt-BR'
        if r['version']==version:
            assert all(r['runtimeSHA256'].get(p)==h for p,h in current.items()),'Stale measurement'
    summary={}
    for v in ['1.5.0',version]:
        selected=[r for r in runs if r['version']==v]
        summary[v]={k:median(r[k] for r in selected) for k in ['modLoadSeconds','bootToDriverSeconds','luaMemoryKiB','peakProcessRSSBytes']}
        summary[v]['observedFPS']=median(360/r['elapsedSeconds'] for r in selected)
    reductions={k:100*(1-summary[version][k]/summary['1.5.0'][k]) for k in ['modLoadSeconds','bootToDriverSeconds','luaMemoryKiB','peakProcessRSSBytes']}
    result={'version':version,'baseline':'1.5.0','baselineCommit':'f156088733edd0a42ae483fbf7ba4f37c70f1210','created':datetime.now(timezone.utc).isoformat(),
        'scope':'All 25 released localized profiles: 11 German, 11 PT-BR, Emerald FR/IT/ES.',
        'verification':'Cold/warm equivalence for all 25 caches, every compiled asset plus every effective Gen3 text/rom_text/pokemon/moves/items/trainers/strings registry value. Gen1/2 translated catalogs are included as assets. Manifest file-list order and equivalent tile packing are compared semantically; all 11 Emerald contest title maps must render identical indexed pixels.',
        'profileResults':verified,'pairedMeasurements':runs,'medians':summary,'reductionPercent':reductions,
        'method':'Fresh processes, warm caches, same pinned engine and Oldale Town scene; order 1.5.0 / 1.5.1 / 1.5.1 / 1.5.0. 180 warm-up frames and 360 measured frames. Only one QA performance process runs at a time.',
        'limits':'Two runs per version on Apple M3 with VSync and other applications running. Lua heap is sampled without forced collection; peak process RSS includes startup and is a different metric. Results are not a whole-story or worst-case benchmark. The first post-update start rebuilds the cache once. Deferred graphics expand on first use, so memory savings depend on visited screens.',
        'engineCommit':'1925fa9f97661f1e2d0922f7c6eb9546d262fd29'}
    dest=ROOT/'docs'/f'Optimization-{version}.json';dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('OPTIMIZATION_REPORT',dest,'profiles',len(verified),'reductions',reductions)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',type=Path,required=True);build(p.parse_args().inputs)
