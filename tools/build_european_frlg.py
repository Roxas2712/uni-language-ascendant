"""Relocate FRLG address profiles using checksum-identical European builds.

Requires private ROMs and ELF files from the same pokefirered-europe source.
Never emits ROM bytes. Missing/ambiguous asset relocations abort the build.
"""
import argparse
import bisect
import collections
import hashlib
import json
import subprocess
from pathlib import Path

from build_profiles import elf_symbols, lua

def all_symbols(path):
    rows = elf_symbols(path, READELF)
    obj = ''
    for line in subprocess.check_output([READELF, '-sW', str(path)], text=True).splitlines():
        parts = line.split()
        if len(parts) < 8 or not parts[0][:-1].isdigit(): continue
        _, addr, size, kind, bind, vis, ndx, name = parts[:8]
        if kind == 'FILE': obj = name
        if kind != 'FUNC': continue
        addr = int(addr, 16)
        if not 0x08000000 <= addr < 0x09000000: continue
        key = (obj + ':' if bind == 'LOCAL' else '') + name
        rows[key] = (addr - 0x08000000, int(size))
    return rows


ROOT = Path(__file__).resolve().parents[1]
READELF = '/opt/homebrew/bin/arm-none-eabi-readelf'


def build(game, lang, source, target, elfs):
    original = json.loads((ROOT / f'build/{game}-metadata.json').read_text())
    assert hashlib.sha1(source).hexdigest() == original['sha1']
    spec = next(x for x in json.loads((ROOT / 'build/european-inputs.json').read_text())
                if x.get('game') == game and x.get('language') == lang)
    assert hashlib.sha1(target).hexdigest() == spec['sha1']
    assert (elfs / f'poke{game}_{lang}.gba').read_bytes() == target, 'Nonmatching build'
    de = all_symbols(elfs / f'poke{game}_de.elf')
    eu = all_symbols(elfs / f'poke{game}_{lang}.elf')
    for name in de:
        if name not in eu and ':' in name and name.split(':',1)[1] in eu:
            eu[name] = eu[name.split(':',1)[1]]
    exact = collections.defaultdict(set)
    ranges = collections.defaultdict(list)
    for name, (off, size) in de.items():
        if name in eu:
            end, newsize = eu[name]
            exact[off].add(end)
            if size == newsize and size:
                ranges[off].append((size, end, name))
    starts = sorted(ranges)
    ends = []
    for start in starts:
        ends.append(max(ends[-1] if ends else 0, max(start + row[0] for row in ranges[start])))
    evidence = collections.Counter()
    def relocate(off, label):
        hits = exact.get(off, set())
        if len(hits) == 1:
            evidence['symbol_start'] += 1
            return next(iter(hits))
        # Byte deltas are valid inside unchanged-size structures, never text.
        ix = bisect.bisect_right(starts, off) - 1
        candidates = set()
        while ix >= 0 and ends[ix] > off:
            start = starts[ix]
            candidates.update(new + off - start for size, new, name in ranges[start]
                              if off < start + size and (not label.startswith('text.') or '[' in label and label[5:].split('[')[0] == name))
            ix -= 1
        if len(candidates) == 1:
            evidence['structure_member'] += 1
            return candidates.pop()
        raise ValueError(f'Unresolved address {label}: {off:#x} ({sorted(hits)})')

    def tree(v, label):
        if isinstance(v, dict):
            return {k: tree(x, label + '.' + str(k)) for k, x in v.items()}
        if isinstance(v, list):
            return [tree(x, label + '.' + str(i)) for i, x in enumerate(v)]
        if isinstance(v, int) and not isinstance(v, bool) and v > 65535:
            return relocate(v, label)
        return v

    profile = {k: v for k, v in original.items() if k != 'texts'}
    for k in ('sha1', 'md5', 'size'):
        profile[k] = spec[k]
    profile['fields'] = tree(profile['fields'], 'fields')
    texts, missing = {}, []
    for name, row in original['texts'].items():
        try:
            texts[name] = [relocate(row[0], 'text.' + name), *row[1:]]
        except ValueError:
            missing.append(name)
    # Prefer semantic symbol identity over an ambiguous shared source address.
    for name in original['texts']:
        if name in eu:
            texts[name] = [eu[name][0], *original['texts'][name][1:]]
            if name in missing:
                missing.remove(name)

    cfg = json.loads((ROOT / f'build/{game}-table-metadata.json').read_text())
    for table in cfg['tables']:
        address = relocate(table['addr'], 'table.' + table['name'])
        for i in range(table['count'] * table.get('inner', 1)):
            if table.get('ids') is not None:
                ids = cfg['battleIds']; ix = i + table['ids']
                key = ids[str(ix)] if isinstance(ids, dict) else ids[ix - 1]
            elif table.get('inner'):
                key = f"{table['name']}[{i // table['inner']}][{i % table['inner']}]"
            else:
                key = f"{table['name']}[{i}]"
            off = address + i * table['stride']
            if not table.get('inline'):
                off = int.from_bytes(target[off:off + 4], 'little') - 0x08000000
            if not 0 <= off < len(target): continue
            texts[key] = [off, bool(table.get('battle') and not table.get('inline'))]
            if key in missing: missing.remove(key)

    assets = json.loads((ROOT / f'build/{game}_assets-metadata.json').read_text())
    assets['fields'] = tree(assets['fields'], 'assets.fields')
    for method, values in assets.get('calls', {}).items():
        assets['calls'][method] = {k: tree(v, 'calls.' + method + '.' + k) for k, v in values.items()}
    if not isinstance(assets['symbols'], dict): assets['symbols'] = {}
    for method in ('off',):
        for name, values in assets['symbols'].get(method, {}).items():
            values[0] = relocate(values[0], 'symbol.' + name)
    for method in ('size',):
        for name, values in assets['symbols'].get(method, {}).items():
            if name in eu:
                values[0] = eu[name][1]
    for method in ('namesAt', 'funcAt'):
        if method not in assets['symbols']: continue
        result = {}
        for address, values in assets['symbols'].get(method, {}).items():
            n = int(address)
            base = 0x08000000 if n >= 0x08000000 else 0
            result[str(relocate(n - base, method + '.' + address) + base)] = values
        assets['symbols'][method] = result
    world = json.loads((ROOT / f'build/{game}_world-metadata.json').read_text())
    world['pairs'] = tree(world['pairs'], 'world')
    rows = ''.join(f'{key}\t{v[0]}\t{int(v[1])}\t{v[2] if len(v)>2 and v[2] else ""}\t{v[3] if len(v)>3 and v[3] else ""}\n'
                   for key, v in sorted(texts.items()))
    body = '-- Generated address metadata; no ROM payload.\nlocal p=' + lua(profile)
    body += '\np.texts={}\nlocal rows=[==[\n' + rows + ']==]\n'
    body += 'for key,off,battle,kind,len in rows:gmatch("([^\\t\\n]+)\\t(%d+)\\t([01])\\t([^\\t]*)\\t([^\\n]*)\\n") do\n p.texts[key]={tonumber(off),battle=="1",kind~="" and kind or nil,tonumber(len)}\nend\nreturn p\n'
    prefix = ROOT / f'mod/profiles/{game}_{lang}'
    prefix.with_suffix('.lua').write_text(body)
    Path(str(prefix) + '_assets.lua').write_text('-- Address metadata; no ROM payload.\nreturn ' + lua(assets) + '\n')
    Path(str(prefix) + '_world.lua').write_text('-- Address metadata; no ROM payload.\nreturn ' + lua(world) + '\n')
    report = {'game': game, 'language': lang, 'sha1': spec['sha1'], 'mappings': len(texts),
              'missing': missing, 'evidence': dict(evidence)}
    (ROOT / f'build/{game}-{lang}-profile-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('game', choices=['firered', 'leafgreen'])
    p.add_argument('language', choices=['fr', 'it', 'es'])
    p.add_argument('--elfs', type=Path, required=True)
    p.add_argument('--source-rom', type=Path, required=True)
    p.add_argument('--target-rom', type=Path, required=True)
    a = p.parse_args()
    build(a.game, a.language, a.source_rom.read_bytes(), a.target_rom.read_bytes(), a.elfs)
