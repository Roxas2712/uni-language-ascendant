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

from lua_literal import lua


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
        # The source appends a Japanese alphabet using the same byte values.
        # It is not the font selected by this Latin translation. Never let
        # those later aliases silently replace A/B/etc with kana.
        if any(0x3000 <= ord(ch) <= 0x30ff or 0xff00 <= ord(ch) <= 0xffef
               or 0x4e00 <= ord(ch) <= 0x9fff for ch in seq):
            continue
        value = int(code, 16)
        if value not in result or len(seq) == 1:
            result[value] = seq
    result.update({0x49:'\f',0x4a:'POKéMON',0x64:'N',0xe1:'POKé',0xe2:'MON',0x4b:'\v',0x4c:'\v',0x4e:'\n',0x4f:'\n',
                   0x51:'\f',0x52:'{PLAYER}',0x53:'{RIVAL}',0x54:'POKé',
                   0x55:'\v',0x56:'……',0x59:'{TARGET}',0x5a:'{USER}',
                   0x5b:'PC',0x5c:'TM',0x5d:'TREINADOR',0x5e:'ROCKET',
                   0xc3:'ADV.',0xc4:'',0xc5:'',0xc7:'Á',0xd7:'á',0xd0:'PO',0xd1:'Ké',
                   0xd2:'',0xd3:'',0xd4:'',0xd5:'',0xe9:'',0xea:'',0xeb:'',
                   0xf0:'¥',0x6d:':'})
    return result


def recipe(rom, start, dynamic, syms, cmap):
    parts, used, visited = [], set(), set()
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
            ram = int.from_bytes(rom[pos:pos+2],'little')
            candidates=[]
            for i,(expected,token) in enumerate(dynamic):
                ram_name = re.search(r':([^,}]+)',token)[1]
                if i not in used and command==expected and ram_name in syms and syms[ram_name][1]==ram:
                    candidates.append((i,token))
            if not candidates:
                raise ValueError(f'Unmatched dynamic operand: command {command}, RAM {ram:04x}')
            i,token=candidates[0]
            # The engine's RomText also substitutes positional arguments.
            # Correct ROM RAM identities alone do not make a reversed order
            # safe. Those lines need an authored, order-preserving correction.
            if i != len(used):
                raise ValueError('Changed dynamic operand order')
            used.add(i)
            parts.append({'token':token})
            pos += 2 if command == 1 else 3
        elif command == 0x17:
            address = int.from_bytes(rom[pos:pos+2],'little')
            bank = rom[pos+2]
            pos = offset(bank,address)
        else:
            raise ValueError(f'Unsupported command {command:02x}')
    else:
        raise ValueError('Unterminated command stream')
    if len(used) != len(dynamic):
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
