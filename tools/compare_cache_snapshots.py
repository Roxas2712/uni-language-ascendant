"""Compare full localized payloads before/after a cache implementation change.

Uses private local QA snapshots/caches. No ROM or translated dialogue is exported.
Only manifest file-list order and equivalent contest tile packing may differ.
"""
import argparse, collections, hashlib, json, os, struct, subprocess, zlib
from pathlib import Path


def compare(before, after, cache_root, luajit, engine):
    def lua(path, manifest=False):
        code="local S=require('src.core.SaveSerializer');local f=assert(io.open(os.getenv('QA_VALUE')));print(require('src.link.Json').encode(assert(S.decode(f:read('*a'),{maxNodes=500000,maxBytes=16777216}))))"
        if manifest:
            # Generated manifests also use positional arrays, outside the save
            # parser grammar. Evaluate only this known manifest allowlist with
            # no globals and a bounded instruction budget, in a child process.
            code="local f=assert(io.open(os.getenv('QA_VALUE')));local fn=assert(loadstring(f:read('*a')));setfenv(fn,{});debug.sethook(function()error('Manifest instruction limit')end,'',1000000);local value=fn();debug.sethook();print(require('src.link.Json').encode(value))"
        return json.loads(subprocess.check_output([str(luajit),'-e',code],env=dict(os.environ,QA_VALUE=str(path),LUA_PATH=str(engine/'?.lua')+';;')).decode('utf-8','surrogateescape'))
    def cache(snapshot):
        root=cache_root/'compiled'/snapshot['cacheKey']
        index=lua(root/'index.lua');assets={};report=None
        for row in index['rows']:
            if row['kind'].startswith('asset'):
                raw=(root/row['path']).read_bytes()
                assert len(raw)==row['size'] and hashlib.sha256(raw).hexdigest()==row['hash']
                if row['kind']=='asset-zlib':
                    raw=zlib.decompress(raw)
                    assert len(raw)==row['rawSize'] and hashlib.sha256(raw).hexdigest()==row['rawHash']
                assert hashlib.sha256(raw).hexdigest()==snapshot['assets'][row['name']]
                assets[row['name']]=raw
            elif row['kind']=='report' and row['path'].endswith('.lua'): report=lua(root/row['path'])
        return assets,report
    a,b=json.loads(Path(before).read_text()),json.loads(Path(after).read_text())
    assert a['game']==b['game'] and a['language']==b['language']
    assert a['registries']==b['registries'],'Effective text/registry values changed'
    assert a['assetBytes']==b['assetBytes'] and a['assets'].keys()==b['assets'].keys(),'Asset inventory changed'
    old,old_report=cache(a);new,_=cache(b)
    changed=[p for p in old if old[p]!=new[p]]
    folder='data/generated/gba/rse/contest_gfx/'
    manifests={'data/generated/gba/rse/pokedex/manifest.lua','data/generated/gba/rse/trainer_card/manifest.lua'}
    map_names=['title','title_normal','title_super','title_hyper','title_master','title_link','title_cool','title_beauty','title_cute','title_smart','title_tough']
    allowed=manifests|{folder+'results.gfx'}|{folder+n+'.map' for n in map_names}
    assert set(changed)<=allowed,'Unexpected changed assets: '+str(set(changed)-allowed)
    import tempfile
    def decode_bytes(raw):
        with tempfile.NamedTemporaryFile() as f:
            f.write(raw);f.flush();return lua(f.name, manifest=True)
    for path in manifests&set(changed):
        x,y=decode_bytes(old[path]),decode_bytes(new[path])
        x['files'].sort();y['files'].sort();assert x==y,'Manifest content changed: '+path
    pixel_maps=0
    if any(p.startswith(folder) for p in changed):
        x,y=old[folder+'results.gfx'],new[folder+'results.gfx']
        tiles=lambda data:collections.Counter(data[i:i+32] for i in range(0,len(data),32))
        assert tiles(x)==tiles(y),'Contest tile pixels changed'
        def render(data,gfx):
            pixels=bytearray()
            for (entry,) in struct.iter_unpack('<H',data):
                tile=gfx[(entry&1023)*32:(entry&1023)*32+32];assert len(tile)==32
                for yy in range(8):
                    for xx in range(8):
                        tx=7-xx if entry&1024 else xx;ty=7-yy if entry&2048 else yy
                        pixels.append(((tile[ty*4+tx//2]>>(4*(tx%2)))&15)+16*(entry>>12))
            return pixels
        for name in map_names:
            path=folder+name+'.map'
            assert render(old[path],x)==render(new[path],y),'Displayed pixels changed: '+path
            pixel_maps+=1
    if old_report and b.get('coverageData'):
        # Source report file arrays originate from pairs(); all values still
        # must be present. Only arrays of strings are treated as unordered.
        def normalize(v):
            if isinstance(v,dict):return {k:normalize(x) for k,x in v.items() if k!='cacheHit'}
            if isinstance(v,list):return sorted(v) if all(isinstance(x,str) for x in v) else [normalize(x) for x in v]
            return v
        assert normalize(old_report)==normalize(b['coverageData']),'Coverage report content changed'
    elif a['coverage']!=b['coverage']:
        raise AssertionError('Cannot verify changed coverage report')
    return {'game':a['game'],'language':a['language'],'assetCount':a['assetCount'],'assetBytes':a['assetBytes'],
            'effectiveRegistryValues':sum(len(v) for v in a['registries'].values()) if a['registries'] else 0,'rawIdenticalAssets':len(old)-len(changed),
            'equivalentRepackedAssets':changed,'pixelComparedMaps':pixel_maps,'passed':True,
            'beforeSnapshotSHA256':hashlib.sha256(Path(before).read_bytes()).hexdigest(),
            'afterSnapshotSHA256':hashlib.sha256(Path(after).read_bytes()).hexdigest()}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['before','after','cache-root','luajit','engine']:p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();print(json.dumps(compare(a.before,a.after,a.cache_root,a.luajit,a.engine),indent=2))
