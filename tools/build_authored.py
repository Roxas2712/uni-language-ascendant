"""Build authored IR supplements, pinned to exact imported source IR hashes.

Only our translations and source fingerprints are shipped. Original text stays
in the private build input. Control operands must survive unchanged.
"""
import argparse, hashlib, json, subprocess
from pathlib import Path
from build_profiles import lua

LAYOUT = {'text', 'nl', 'para', 'scroll', 'eos'}

def controls(ir):
    return [seg for seg in ir if seg['t'] not in LAYOUT]

def fingerprints(source, engine, luajit):
    code = "local J=require('src.link.Json');local W=require('src.import.LuaWriter');local out={};for k,v in pairs(J.decode(io.read('*a'))) do out[k]=W.encode(v) end;io.write(J.encode(out))"
    encoded = json.loads(subprocess.check_output([str(luajit), '-e', code], cwd=engine, input=json.dumps(source), text=True))
    return {key: hashlib.sha256(value.encode()).hexdigest() for key, value in encoded.items()}

def build(source, targets, engine, luajit):
    # Script bytecode may use an address key while UI code uses its symbol.
    # Expand only exact IR aliases; every alias still carries its own base hash.
    canonical = lambda ir: json.dumps(ir, sort_keys=True, ensure_ascii=False)
    by_ir = {}
    for key, target in targets.items():
        assert key in source, f'Missing base key: {key}'
        identity = canonical(source[key])
        assert identity not in by_ir or by_ir[identity] == target, f'Conflicting aliases: {key}'
        by_ir[identity] = target
    targets = {key:by_ir[canonical(ir)] for key,ir in source.items() if canonical(ir) in by_ir}
    for key, target in targets.items():
        assert key in source, f'Missing base key: {key}'
        assert target and target[-1] == {'t':'eos'}, f'Missing EOS: {key}'
        assert controls(source[key]) == controls(target), f'Control operands changed: {key}'
    hashes = fingerprints({k:source[k] for k in targets}, engine, luajit)
    return {k: {'sourceSha256':hashes[k], 'target':v} for k,v in targets.items()}

if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('base','targets','engine','luajit','output'): ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args()
    rows=build(json.loads(a.base.read_text()),json.loads(a.targets.read_text()),a.engine,a.luajit)
    a.output.write_text('-- Authored PT-BR supplements; validated against original base IR.\nreturn '+lua(rows)+'\n')
    print('AUTHORED_BUILD_OK',len(rows),a.output)
