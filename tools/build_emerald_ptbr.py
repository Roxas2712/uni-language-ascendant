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
SPECS = {'emerald': (US_SHA, PT_SHA), 'ruby': ('f28b6ffc97847e94a6c21a63cacf633ee5c8df1e', '90f1464f77c57b4eef45ee07df140d402162eee3')}


def build(args):
    game = args.game
    us_sha, pt_sha = SPECS[game]
    us, pt = args.base.read_bytes(), args.translation.read_bytes()
    assert hashlib.sha1(us).hexdigest() == us_sha
    assert hashlib.sha1(pt).hexdigest() == pt_sha
    meta = json.loads(args.metadata.read_text())
    syms = lua_symbols(args.engine / f'src/import/gba/syms/{game}.lua')
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
    # Imported table slots have stronger semantic identity than stale code
    # pointers in older fan patches. Use their exact slot-to-slot mapping.
    table_targets = collections.defaultdict(set)
    for table in meta['tables']:
        start = table['addr']
        translated_start = relocations.get(start, start)
        for i in range(table['count'] * table.get('inner', 1)):
            a, b = start+i*table['stride'], translated_start+i*table['stride']
            if table.get('inline'):
                before, after = a, b
            else:
                before = int.from_bytes(us[a:a+4], 'little')-BASE
                after = int.from_bytes(pt[b:b+4], 'little')-BASE
            if 0 <= before < len(us) and 0 <= after < len(pt):
                table_targets[before].add(after)
    for off, targets in table_targets.items():
        if len(targets) == 1:
            relocations[off] = next(iter(targets))
            conflicts.pop(off, None)
    if game == 'ruby':
        # OJ Abreu updates the field-menu pointer at 0x376D44 but leaves
        # the duplicate at 0x376D6C stale. 0x42C48A is the exact FD01 FF
        # player-name string; the stale address lands inside SALVAR.
        relocations[0x42C48E] = 0x42C48A
        conflicts.pop(0x42C48E, None)
        # The active link prompt is relocated; its second reference is stale.
        relocations[0x42CEAF] = 0x42CEB2
        conflicts.pop(0x42CEAF, None)
        # Two call sites use gendered versions of NONE. The shared engine
        # key has no gender parameter; use the generic masculine label.
        relocations[0x40E66F] = 0xFD003B
        conflicts.pop(0x40E66F, None)
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
                texts[key].append('braille_'+game)
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
    if game == 'emerald': fields['ITEM_NAME_LENGTH'] = 15
    for i in range(fields['STD_STRING_COUNT']):
        texts[f'stdstring:{i}'] = [pointer(fields['STD_STRING_PTRS'] + 4 * i), False]
    missing = sorted(set(keys) - texts.keys())
    assert not missing, missing
    if game == 'ruby' and 'gUnknown_083CC59C' in texts:
        texts['gUnknown_083CC59C'] = [relocate(syms['gUnknown_083CC59C'][0]), False, 'fragment', syms['gUnknown_083CC59C'][1]]
    profile = dict(game=game, sha1=pt_sha, md5=hashlib.md5(pt).hexdigest(), size=len(pt), fields=fields,
                   renderGlyphs={'Ã':0xF1,'Õ':0xF2,'ã':0xF4,'õ':0xF5,'Í':0x0C,'í':0x21})
    if game == 'ruby':
        # OJ Abreu's native font 3: inspected cells and complete word witnesses.
        # Some letters straddle two cells (MA/R); expand their text once.
        profile['decodeGlyphs']={0x2F:'â',0x36:'AP',0x37:'RO',0x38:'FU',0x39:'MA',0x3A:'R',
            0x3B:'PO',0x3C:'Ké',0x3D:'do',0x3E:'da',0x3F:'de',0x40:'CI',0x41:'DA',0x42:'DE',
            0x43:'DO',0x44:'VE',0x45:'LO',0x46:'(A)',0x47:'CO',0x48:'LÉ',0x49:'FA',0x4A:'TA',
            0x57:'BLO',0x58:'C',0x59:'K'}
    out = ROOT / f'mod/profiles/{game}_ptbr.lua'
    rows = ''.join(f'{k}\t{v[0]}\t{int(v[1])}\t{v[2] if len(v)>2 else "-"}\t{v[3] if len(v)>3 else "-"}\n' for k,v in sorted(texts.items()))
    out.write_text('-- Generated address metadata; no ROM payload.\nlocal p=' + lua(profile) + '\np.texts={}\nlocal rows=[==[\n' + rows + ']==]\nfor key,off,battle,kind,length in rows:gmatch("([^\\t\\n]+)\\t(%d+)\\t([01])\\t([^\\t\\n]+)\\t([^\\t\\n]+)\\n") do\n p.texts[key]={tonumber(off),battle=="1",kind~="-" and kind or nil,tonumber(length)}\nend\nreturn p\n')
    def export(path):
        return json.loads(subprocess.check_output([args.luajit, str(args.engine/'tools/lua_to_json.lua'), str(path)]))
    def move(value):
        if isinstance(value, dict): return {k: move(v) for k,v in value.items()}
        if isinstance(value, list): return [move(v) for v in value]
        if isinstance(value, int) and value > 0x10000 and value in relocations: return relocations[value]
        return value
    assets = export(args.assets)
    assets['fields'] = move(assets['fields'])
    if game == 'ruby':
        assets['fields']['RS_FONT_SOURCES'] = {str(relocations.get(int(k), int(k))):v for k,v in assets['fields']['RS_FONT_SOURCES'].items()}
    for name in ('off',):
        if name in assets['symbols']: assets['symbols'][name] = move(assets['symbols'][name])
    for method in ('namesAt', 'at', 'nameAt'):
        if method in assets['symbols']:
            assets['symbols'][method] = {str(relocations.get(int(k), int(k))):v for k,v in assets['symbols'][method].items()}
    def numeric_keys(value):
        if isinstance(value, list): return [numeric_keys(v) for v in value]
        if isinstance(value, dict): return {int(k) if str(k).isdigit() else k: numeric_keys(v) for k,v in value.items()}
        return value
    assets['fields'] = numeric_keys(assets['fields'])
    (ROOT/f'mod/profiles/{game}_ptbr_assets.lua').write_text('return '+lua(assets)+'\n')
    (ROOT/f'mod/profiles/{game}_ptbr_world.lua').write_text('return '+lua(move(export(args.world)))+'\n')
    report = {'sourceSha1':us_sha,'targetSha1':pt_sha,'keys':len(keys),'mapped':len(set(keys)&texts.keys()),'relocated':sum(relocations.get(int(k[3:],16)-BASE,int(k[3:],16)-BASE)!=int(k[3:],16)-BASE for k in keys if k.startswith('g3:')),'missing':missing}
    (ROOT/f'build/ptbr-qa/{game}-profile-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base','translation','engine','metadata','texts','assets','world'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--game', choices=list(SPECS), default='emerald')
    parser.add_argument('--luajit', default='luajit')
    build(parser.parse_args())
