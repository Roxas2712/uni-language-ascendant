"""Read native credit order/layout and emit ROM-address recipes, not text dumps."""
from gen1_ptbr_dialogue import offset


def credits(rom, syms, cmap, manifest):
    def at(label): return offset(*syms[label])
    def value(v): return {'value': v}
    def table(v): return {'table': [[k,r] for k,r in v.items()]}
    pointers = at('CreditsTextPointers')
    bank = syms['CreditsTextPointers'][0]
    pos, screens, lines, copyright = at('CreditsOrder'), [], [], False
    for _ in range(512):
        command = rom[pos]; pos += 1
        if command == 0xfa:
            assert not lines and not copyright, 'Unterminated credit screen'
            break
        if command == 0xfb:
            copyright = True
        elif command >= 0xfc:
            reference = manifest['screens'][len(screens)]
            fade, mon = command in (0xfd, 0xff), command in (0xfe, 0xff)
            assert reference['fade'] == fade and bool(reference.get('mon')) == mon
            row = {'lines': {'array': lines}, 'fade': value(fade)}
            if mon: row['mon'] = value(reference['mon'])
            if copyright: row['copyright'] = value(True)
            assert len(lines) <= 4, 'Credit text overlaps the lower black bar'
            screens.append(table(row)); lines, copyright = [], False
        else:
            assert command < 128
            pointer = int.from_bytes(rom[pointers+command*2:pointers+command*2+2], 'little')
            start = offset(bank, pointer)
            column = 9 + int.from_bytes(rom[start:start+1], 'little', signed=True)
            stop = rom.index(0x50, start+1, start+250)
            for raw in rom[start+1:stop].split(b'\x4e'):
                parts, chars = [], []
                for i, code in enumerate(raw):
                    # Native credits use an extra cell for uppercase accents.
                    accent = {0xea: {'A':'Ã','O':'Õ'}, 0xeb: {'A':'Á','E':'É','I':'Í','O':'Ó','U':'Ú'},
                              0xe9: {'A':'Â','E':'Ê','O':'Ô'}}.get(code, {})
                    if chars and chars[-1] in accent:
                        chars[-1] = accent[chars[-1]]
                        parts[-1] = {'token': chars[-1]}
                    elif code == 0x65:
                        chars.append('_'); parts.append({'token':'_'})
                    else:
                        text = cmap[code]
                        chars.append(text); parts.append({'off':start+1+i, 'size':1})
                text = ''.join(chars)
                recipe = {'parts': parts}
                # Remaining English job title in the native translation.
                if text == 'GAME DESIGN':
                    recipe = value('DESIGN DO JOGO'); text = 'DESIGN DO JOGO'
                assert 0 <= column and column+len(text) <= 20, (text, column)
                lines.append(table({'column':value(column), 'text':recipe}))
                start += len(raw)+1
    else:
        raise ValueError('Unterminated credits order')
    assert len(screens) == len(manifest['screens'])
    start = at('TheEndTextString')
    stop = rom.index(0x50, start, start+24)
    top = rom[start:stop]
    bottom = rom[stop+1:stop+1+len(top)]
    pattern = []
    for a,b in zip(top,bottom):
        assert (a == b == 0x7f) or (a in range(0x60,0x69,2) and b == a+1)
        pattern.append(-1 if a == 0x7f else (a-0x60)//2)
    assert len(pattern) <= 12
    return {'screens':{'array':screens}, 'pattern':value(pattern)}
