"""Recover Gen-1 dialogue recipes from a locally built PT-BR ROM and symbols.

No text payload is emitted: literal runs refer to ROM bytes and dynamic fields
retain the stock engine's semantic identifiers. Unsupported commands and changed
substitutions are reported, never treated as successful translation.
Symbol-name matches are candidates only: renamed/reused script labels still
need semantic review before a profile can be activated.
"""
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

from build_profiles import lua


def symbols(path):
    result = {}
    for line in path.read_text().splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]+):([0-9a-fA-F]+) (\S+)', line)
        if match:
            bank, address, name = match.groups()
            result[name] = (int(bank, 16), int(address, 16))
    return result


def offset(bank, address):
    if bank == 0 and address < 0x4000:
        return address
    if bank > 0 and 0x4000 <= address < 0x8000:
        return bank * 0x4000 + address - 0x4000
    raise ValueError('Not a ROM address')


def charmap(path):
    # Deliberate text alphabet: the ROM reuses several cells in special UIs.
    result = {}
    for seq, code in re.findall(r'^\s*charmap "([^"\n]+)",\s*\$([0-9a-fA-F]+)', path.read_text(), re.M):
        value = int(code, 16)
        if value not in result or len(seq) == 1:
            result[value] = seq
    result.update({0x4b:'{_CONT}',0x4c:'{SCROLL}',0x4e:'{NEXT}',0x4f:'{LINE}',
                   0x51:'{PARA}',0x52:'{PLAYER}',0x53:'{RIVAL}',0x54:'POKé',
                   0x55:'{CONT}',0x56:'……',0x59:'{TARGET}',0x5a:'{USER}',
                   0x5b:'PC',0x5c:'TM',0x5d:'TREINADOR',0x5e:'ROCKET',
                   0xc7:'Á',0xd7:'á',0xd0:'PO',0xd1:'Ké',
                   0xd2:'',0xd3:'',0xd4:'',0xd5:'',0xe9:'',0xea:'',0xeb:'',
                   0xf0:'¥',0x6d:'{COLON}'})
    return result


def recipe(rom, start, dynamic, syms, cmap):
    parts, substitutions, visited = [], 0, set()
    bank, address = start
    pos = offset(bank, address)
    for _ in range(8192):
        if pos in visited:
            raise ValueError('Text command cycle')
        visited.add(pos)
        command = rom[pos]
        pos += 1
        if command == 0:
            begin = pos
            while pos < len(rom) and rom[pos] not in (0x50,0x57,0x58,0x5f):
                value = rom[pos]
                if value not in cmap:
                    raise ValueError(f'Undefined glyph {value:02x}')
                pos += 1
            if pos == len(rom):
                raise ValueError('Unterminated literal')
            if pos > begin:
                parts.append({'off':begin,'size':pos-begin})
            end = rom[pos]
            pos += 1
            if end == 0x50:
                continue
            if end != 0x5f:
                parts.append({'token':'{PROMPT}' if end == 0x58 else '{DONE}'})
            break
        if command == 0x50:
            if parts:
                parts.append({'token':'{DONE}'})
            break
        if command in (1,2,9):
            if substitutions >= len(dynamic):
                raise ValueError('Additional dynamic operand')
            expected, token = dynamic[substitutions]
            if command != expected:
                raise ValueError('Changed dynamic command order')
            ram_name = re.search(r':([^,}]+)',token)[1]
            ram = int.from_bytes(rom[pos:pos+2],'little')
            if ram_name not in syms or syms[ram_name][1] != ram:
                raise ValueError(f'Dynamic address mismatch: {ram_name}')
            parts.append({'token':token})
            substitutions += 1
            pos += 2 if command == 1 else 3
        elif command == 0x17:
            address = int.from_bytes(rom[pos:pos+2],'little')
            bank = rom[pos+2]
            pos = offset(bank,address)
        else:
            raise ValueError(f'Unsupported command {command:02x}')
    else:
        raise ValueError('Unterminated command stream')
    if substitutions != len(dynamic):
        raise ValueError('Missing dynamic operands')
    return {'parts':parts}


def main(args):
    rom = args.rom.read_bytes()
    assert hashlib.sha1(rom).hexdigest() == args.sha1, 'Unrecognized ROM build'
    syms, cmap = symbols(args.symbols), charmap(args.charmap)
    if args.ram_aliases:
        for engine_name,source_name in json.loads(args.ram_aliases.read_text()).items():
            value=syms[source_name]
            if value[1]<0x8000:raise ValueError('RAM alias points into ROM: '+engine_name)
            if engine_name in syms and syms[engine_name]!=value:
                raise ValueError('RAM alias conflicts with source symbol: '+engine_name)
            syms[engine_name]=value
    manifest = json.loads(args.manifest.read_text())
    rows, missing = {}, {}
    aliases = json.loads(args.aliases.read_text()) if args.aliases else {}
    for label in manifest['text']['labels']:
        target = aliases.get(label,label)
        if target not in syms:
            missing[label] = 'No matching symbol'
            continue
        try:
            rows[label] = recipe(rom,syms[target],manifest['text']['dynamic'].get(label,[]),syms,cmap)
        except (ValueError,IndexError) as error:
            missing[label] = str(error)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'dialogue.lua').write_text('return '+lua({'table':[[k,v] for k,v in sorted(rows.items())]})+'\n')
    metadata = dict(sha1=args.sha1,md5=hashlib.md5(rom).hexdigest(),size=len(rom),charmap={str(k):v for k,v in cmap.items()})
    (args.output/'source.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    report = dict(mapped=len(rows),total=len(manifest['text']['labels']),missing=missing,
                  failure_counts=dict(collections.Counter(missing.values())),runtime_enabled=False,
                  semantic_alignment_verified=False)
    (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='missing'},ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('rom','symbols','charmap','manifest','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--sha1',required=True)
    parser.add_argument('--aliases',type=Path)
    parser.add_argument('--ram-aliases',type=Path)
    main(parser.parse_args())
