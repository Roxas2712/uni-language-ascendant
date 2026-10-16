"""Build address recipes for the exact Zambrakas 2013 Emerald translation.

Inputs are private, user-owned ROMs and stock-engine symbol metadata. No game
text or ROM data is emitted into the distributed profile.
"""
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path
from build_profiles import lua, lua_symbols

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x08000000
US_SHA = 'f3ae088181bf583e55daf962a92bb46f4f1d07b7'
PT_SHA = '18a2b0acdba046c71b8677bb58c9ee7d36f7a91f'


def build(args):
    us, pt = args.base.read_bytes(), args.translation.read_bytes()
    assert hashlib.sha1(us).hexdigest() == US_SHA
    assert hashlib.sha1(pt).hexdigest() == PT_SHA
    meta = json.loads(args.metadata.read_text())
    syms = lua_symbols(args.engine / 'src/import/gba/syms/emerald.lua')
    keys = json.loads(args.texts.read_text())
    braille_offsets = {off for name, (off, _) in syms.items() if 'Braille_' in name}
    references = collections.defaultdict(set)
    # The pinned binary patch preserves the US program layout. Retain pointer
    # witnesses only beside unchanged bytes, and reject conflicting targets.
    for match in re.finditer(b'(?=([\x00-\xff]{3}\x08))', us):
        at = match.start()
        before = int.from_bytes(us[at:at + 4], 'little') - BASE
        after = int.from_bytes(pt[at:at + 4], 'little') - BASE
        if 0 <= before < len(us) and 0 <= after < len(pt):
            if us[max(0, at - 4):at] == pt[max(0, at - 4):at] or us[at + 4:at + 8] == pt[at + 4:at + 8]:
                references[before].add(after)
    relocations = {off: next(iter(targets)) for off, targets in references.items() if len(targets) == 1}
    conflicts = {off: sorted(targets) for off, targets in references.items() if len(targets) > 1}
    def relocate(off):
        assert off not in conflicts, f'Conflicting pointers for {off:x}: {conflicts[off]}'
        return relocations.get(off, off)
    def pointer(at):
        value = int.from_bytes(pt[at:at + 4], 'little') - BASE
        assert 0 <= value < len(pt), f'Invalid pointer at {at:x}'
        return value
    texts = {}
    for key, row in meta['named'].items():
        if key in keys:
            texts[key] = [relocate(row[0]), row[1]]
    for key in keys:
        if key.startswith('g3:'):
            off = int(key[3:], 16) - BASE
            texts[key] = [relocate(off), False]
            if off in braille_offsets:
                texts[key].append('braille_emerald')
        elif key not in texts and key in syms:
            texts[key] = [relocate(syms[key][0]), False]
    for table in meta['tables']:
        start = relocate(table['addr'])
        for i in range(table['count'] * table.get('inner', 1)):
            if table.get('ids') is not None:
                ids, idx = meta['battleIds'], i + table['ids']
                key = ids[str(idx)] if isinstance(ids, dict) else ids[idx - 1]
            elif table.get('inner'):
                key = f"{table['name']}[{i // table['inner']}][{i % table['inner']}]"
            else:
                key = f"{table['name']}[{i}]"
            if key not in keys:
                continue
            at = start + i * table['stride']
            texts[key] = [relocate(at) if table.get('inline') else pointer(at), bool(table.get('battle') and not table.get('inline'))]
    fields = {k: relocate(v) if isinstance(v, int) and v > 0x10000 else v for k, v in meta['fields'].items()}
    # Zambrakas' Powder Jar label uses 14 glyphs, with EOS at byte 14.
    # Read its terminator, while retaining the US item IDs and gameplay data.
    fields['ITEM_NAME_LENGTH'] = 15
    for i in range(fields['STD_STRING_COUNT']):
        texts[f'stdstring:{i}'] = [pointer(fields['STD_STRING_PTRS'] + 4 * i), False]
    missing = sorted(set(keys) - texts.keys())
    assert not missing, missing
    profile = dict(game='emerald', sha1=PT_SHA, md5=hashlib.md5(pt).hexdigest(), size=len(pt), fields=fields,
                   renderGlyphs={'Ã':0xF1,'Õ':0xF2,'ã':0xF4,'õ':0xF5,'Í':0x0C,'í':0x21})
    out = ROOT / 'mod/profiles/emerald_ptbr.lua'
    rows = ''.join(f'{k}\t{v[0]}\t{int(v[1])}\t{v[2] if len(v)>2 else "-"}\n' for k,v in sorted(texts.items()))
    out.write_text('-- Generated address metadata; no ROM payload.\nlocal p=' + lua(profile) + '\np.texts={}\nlocal rows=[==[\n' + rows + ']==]\nfor key,off,battle,kind in rows:gmatch("([^\\t\\n]+)\\t(%d+)\\t([01])\\t([^\\t\\n]+)\\n") do\n p.texts[key]={tonumber(off),battle=="1",kind~="-" and kind or nil}\nend\nreturn p\n')
    def export(path):
        return json.loads(subprocess.check_output([args.luajit, str(args.engine/'tools/lua_to_json.lua'), str(path)]))
    def move(value):
        if isinstance(value, dict): return {k: move(v) for k,v in value.items()}
        if isinstance(value, list): return [move(v) for v in value]
        if isinstance(value, int) and value > 0x10000 and value in relocations: return relocations[value]
        return value
    assets = export(args.assets)
    assets['fields'] = move(assets['fields'])
    for name in ('off',):
        if name in assets['symbols']: assets['symbols'][name] = move(assets['symbols'][name])
    for method in ('namesAt', 'at', 'nameAt'):
        if method in assets['symbols']:
            assets['symbols'][method] = {str(relocations.get(int(k), int(k))):v for k,v in assets['symbols'][method].items()}
    (ROOT/'mod/profiles/emerald_ptbr_assets.lua').write_text('return '+lua(assets)+'\n')
    (ROOT/'mod/profiles/emerald_ptbr_world.lua').write_text('return '+lua(move(export(args.world)))+'\n')
    report = {'sourceSha1':US_SHA,'targetSha1':PT_SHA,'keys':len(keys),'mapped':len(set(keys)&texts.keys()),'relocated':sum(relocations.get(int(k[3:],16)-BASE,int(k[3:],16)-BASE)!=int(k[3:],16)-BASE for k in keys if k.startswith('g3:')),'missing':missing}
    (ROOT/'build/ptbr-qa/profile-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base','translation','engine','metadata','texts','assets','world'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--luajit', default='luajit')
    build(parser.parse_args())
