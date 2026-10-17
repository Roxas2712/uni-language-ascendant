"""Seed relocation with unique, byte-identical complete data objects.

This establishes identity only. An unchanged string may still require an
authored translation; it is never counted as language coverage here.
"""
import argparse
import hashlib
import json
from pathlib import Path


def unique_copy(source, target, offset, size):
    if size < 24 or offset + size > len(source):
        return None
    block = source[offset:offset + size]
    if len(set(block)) < 8:
        return None
    if source.find(block) != offset or source.find(block, offset + 1) >= 0:
        return None
    match = target.find(block)
    if match < 0 or target.find(block, match + 1) >= 0:
        return None
    return match


def run(a):
    source, target = a.base.read_bytes(), a.target.read_bytes()
    audit = json.loads(a.relocation.read_text())
    assert hashlib.sha1(source).hexdigest() == audit['base_sha1']
    assert hashlib.sha1(target).hexdigest() == audit['target_sha1']
    rows = json.loads(a.symbols.read_text())
    proof = []
    seen = set()
    for row in rows:
        offset, size = row['off'], row['size']
        if row['type'] == 'FUNC' or (offset, size) in seen:
            continue
        seen.add((offset, size))
        key = str(offset)
        if key in audit['mapped'] or key in audit['conflicts']:
            continue
        match = unique_copy(source, target, offset, size)
        if match is not None:
            audit['mapped'][key] = match
            proof.append([offset, match, size, row['name']])
    audit['identical_objects'] = proof
    a.output.write_text(json.dumps(audit))
    print('IDENTICAL_OBJECTS', len(proof), 'total', len(audit['mapped']))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for key in ['base', 'target', 'relocation', 'symbols', 'output']:
        p.add_argument('--' + key, type=Path, required=True)
    run(p.parse_args())
