"""Compile symbol-verified PT-BR Red/Blue ROM recipes, without ROM payloads.

Profiles remain development inputs until their actual gameplay QA is reviewed.
A symbol match alone is not a semantic or linguistic completion certificate.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from gen1_ptbr_dialogue import charmap, symbols, offset, recipe

ROOT = Path(__file__).resolve().parents[1]
SHA = {'red': 'a2a0e2a3d6ef4d5771aa33682d31eaefd03c32ba',
       'blue': 'ec9e33447d9bdbf95c2d57f487e25a57854a1adf',
       'yellow': '2b94c64b1944fb6866fd0c28149f86c11bc86253'}


from lua_literal import lua


def authored_corrections():
    return json.loads((ROOT/'translations/pt-BR/gen1-corrections.json').read_text())


def build(args):
    game = args.game
    rom = args.rom.read_bytes()
    assert hashlib.sha1(rom).hexdigest() == SHA[game], 'Unrecognized PT-BR ROM'
    syms = symbols(args.symbols)
    cmap = charmap(args.charmap)
    ram_path=args.bridge/'ram.json' if args.bridge else ROOT/'translations/pt-BR/gen1-ram-aliases.json'
    for source, target in json.loads(ram_path.read_text()).items():
        assert syms[target][1] >= 0x8000
        syms[source] = syms[target]
    alias_path=args.bridge/'labels.json' if args.bridge else ROOT/'translations/pt-BR/gen1-label-aliases.json'
    aliases = json.loads(alias_path.read_text())
    m = json.loads(args.manifest.read_text())
    corrections = authored_corrections()
    extra=ROOT/('translations/pt-BR/'+game+'-corrections.json')
    if extra.exists():corrections.update(json.loads(extra.read_text()))
    rows, missing = {}, {}
    for label in m['text']['labels']:
        if label in corrections:
            value = corrections[label]
            expected = [t for _, t in m['text']['dynamic'].get(label, [])]
            actual = re.findall(r'\{(?:RAM|NUM|BCD):[^}]+\}', value)
            assert expected == actual, (label, 'Authored operand order changed')
            rows[label] = {'value': value}
        else:
            try:
                rows[label] = recipe(rom, syms[aliases.get(label, label)], m['text']['dynamic'].get(label, []), syms, cmap)
            except (ValueError, KeyError, IndexError) as error:
                missing[label] = str(error)
    assert not missing, missing
    catalogs = {'dialogue.lua': rows}

    def at(label): return offset(*syms[label])
    def terminated(pos, limit=100, fixed=False):
        end = rom.find(0x50, pos, pos + limit)
        if end < 0:
            assert fixed, "Missing string terminator"
            end = pos + limit
        # Trim padding used by cartridge menus without embedding their text.
        while pos < end and cmap[rom[pos]] in (' ', '\n'): pos += 1
        while end > pos and cmap[rom[end-1]] in (' ', '\n'): end -= 1
        return {'parts': [{'off': pos, 'size': end-pos}]} if end > pos else {'empty': True}
    def table_names(label, ids, stride=None):
        pos = at(label); result = {}
        for key in ids:
            result[key] = terminated(pos, stride or 100, fixed=bool(stride))
            pos = pos + stride if stride else rom.index(0x50, pos) + 1
        return result

    species = table_names('MonsterNames', m['constants']['speciesOrder'], 10)
    catalogs['species_names.lua'] = {k: v for k,v in species.items() if k in m['dexOrder']}
    catalogs['item_names.lua'] = table_names('ItemNames', m['items'][:83])
    catalogs['trainer_names.lua'] = table_names('TrainerNames', ['OPP_'+s for s in m['trainers']])
    catalogs['type_names.lua'] = {}
    types=json.loads((ROOT/'translations/pt-BR/type-names.json').read_text())
    for label in m['typeNameLabels']:
        key = label.split('.')[-1].upper()
        if key == 'PSYCHIC': key = 'PSYCHIC_TYPE'
        catalogs['type_names.lua'][key] = {'value': types[key]}
    moves = json.loads((ROOT/'translations/pt-BR/move-names.json').read_text())['moves']
    catalogs['move_names.lua'] = {key: {'value': moves[str(i)]} for i,key in enumerate(m['constants']['moveOrder'], 1)}
    kinds, metrics = {}, {}
    short_kinds=json.loads((ROOT/'translations/pt-BR/gen1-dex-kinds.json').read_text())
    for key, label in m['dexEntryLabels'].items():
        pos = at(label[1:]); end = rom.index(0x50, pos)
        kinds[key] = {'value': short_kinds[key]} if key in short_kinds else terminated(pos)
        metrics[key] = {'value': {'heightM': rom[end+1]/10, 'weightKg': int.from_bytes(rom[end+2:end+4], 'little')/10}}
        assert 0 < metrics[key]['value']['heightM'] < 20
        assert 0 < metrics[key]['value']['weightKg'] < 1000
    catalogs['dex_kinds.lua'], catalogs['dex_metrics.lua'] = kinds, metrics
    # The engines share formatted UI/battle strings. Reuse only exact keys,
    # with the Gen-1 wording taking precedence where its layout differs.
    ui = json.loads((ROOT/'translations/pt-BR/gen2-ui.json').read_text())
    ui.update(json.loads((ROOT/'translations/pt-BR/gen1-ui.json').read_text()))
    catalogs['strings.lua'] = {k: {'value': v} for k,v in ui.items()}
    catalogs['status_labels.lua'] = {k: {'value': v} for k,v in {'PSN':'ENV','BRN':'QUE','FRZ':'CON','PAR':'PAR','SLP':'SON','FNT':'DES'}.items()}
    from gen1_ptbr_credits import credits
    catalogs['credits.lua'] = credits(rom, syms, cmap, m['field']['credits'])
    fontmap = {v:k for k,v in cmap.items() if k >= 0x80 and len(v) == 1}
    fontmap.update({' ': 0x7f, 'é':0xd9, 'á':0xd7, 'Á':0xc7, '_':0x100})
    font = at('FontGraphics')
    # Cartridge accent extensions occupy a second cell. Compose those two
    # existing ROM rows into one glyph; all glyph pixels still come from ROM.
    accents = {0xd6:0xd3,0xd7:0xd2,0xd8:0xd5,0xd9:0xd2,0xda:0xd5,
               0xdb:0xd2,0xdc:0xd2,0xdd:0xd3,0xde:0xd5,0xdf:0xd2}
    fonttiles=[]
    for code in range(0x80, 0x100):
        pos=font+(code-0x80)*8
        if code in accents:
            fonttiles.extend([{'off':font+(accents[code]-0x80)*8+7,'size':1},
                              {'off':pos,'size':1},{'off':pos+2,'size':6}])
        else: fonttiles.append({'off':pos,'size':8})
    assets = {
        'assets/fonts/font.png': {'width':128,'height':64,'bits':1,'transparent':True,'tiles':fonttiles},
        'assets/fonts/underscore.png': {'width':8,'height':8,'bits':2,'transparent':True,
            'tiles':[{'off':at('TextBoxGraphics')+5*16,'size':16}]},
        'assets/battle/font_battle_extra.png': {'width':120,'height':16,'bits':2,'transparent':True,'tiles':[{'off':at('HpBarAndStatusGraphics'),'size':480}]},
        'assets/tilesets/overworld.png': {'width':128,'height':48,'bits':2,'tiles':[{'off':at('Overworld_GFX'),'size':1536}]},
        'assets/title/'+game+'_version.png': {'width':80,'height':8,'bits':1,'transparent':True,'tiles':[{'off':at('Version_GFX'),'size':80}]},
        'assets/credits/the_end.png': {'width':40,'height':16,'bits':2,'tiles':[
            {'off':at('TheEndGfx')+column*32+row*16,'size':16}
            for row in range(2) for column in range(5)]},
    }
    if game=='yellow':
        assets.pop('assets/title/yellow_version.png')
        blank=at('TextBoxGraphics')+31*16
        assert rom[blank:blank+16]==bytes(16),'Title background tile is not empty'
        diploma = at('SurfingPikachu3Graphics')
        assert at('SurfingPikachu3GraphicsEnd')-diploma == 127*16
        assets['assets/diploma/yellow_tiles.png']={'width':128,'height':64,'bits':2,
            'tiles':[{'off':diploma,'size':127*16},{'off':blank,'size':16}]}
        catalogs['diploma.lua']={
            'pikachu':{'value':list(rom[at('Tilemap_e9b3e'):at('Tilemap_e9b3e')+120])},
            'congrats':{'value':list(rom[at('Tilemap_e9bb6'):at('Tilemap_e9bb6')+11])},
            'mew':{'value':list(rom[at('TileMap_e9bc1'):at('TileMap_e9bc1')+20])},
        }
        # The stock renderer uses the US coordinates, with seven cells before
        # the player name. Keep the translated certificate inside that layout.
        catalogs['diploma_text.lua']={k:{'value':v} for k,v in {
            'DiplomaText':'Diploma','DiplomaPlayer':'Trein.',
            'DiplomaCongrats':'Parabéns! Este\ndiploma atesta\nque você\ncompletou a\nPOKéDEX.',
            'DiplomaGameFreak':'GAME FREAK','DiplomaPlayTime':'TEMPO:',
        }.items()}
        def title_tile(index):
            if index<0x80:
                address=at('PokemonLogoGraphics')+index*16
                return address if address<at('PokemonLogoGraphicsEnd') else blank
            if index<0xf0:return at('TitlePikachuBGGraphics')+(index-0x80)*16
            if index<0xfd:return at('TitlePikachuOBGraphics')+(index-0xf0)*16
            return at('PokemonLogoCornerGraphics')+(index-0xfd)*16
        for name,label,width,height in [('pokemon_logo','TitleScreenPokemonLogoTilemap',16,7),('pika_bubble','TitleScreenPikaBubbleTilemap',7,4)]:
            ids=list(rom[at(label):at(label)+width*height])
            tiles=[{'off':title_tile(i),'size':16} for i in ids]
            if name=='pika_bubble':
                tiles += [{'off':title_tile(i) if i is not None else blank,'size':16} for i in [None,None,None,0x64,0x65,None,None]]
                height+=1
            assets['assets/title/'+name+'.png']={'width':width*8,'height':height*8,'bits':2,'tiles':tiles,'matte':name=='pika_bubble'}
    profile = {'game':game,'language':'pt-BR','sha1':SHA[game],'md5':hashlib.md5(rom).hexdigest(),'size':len(rom),
               'charmap':{str(k):v for k,v in cmap.items()},'fontmap':fontmap,'catalogs':sorted(catalogs)}
    args.output.mkdir(parents=True,exist_ok=True)
    for filename, rows in catalogs.items():
        (args.output/filename).write_text('return '+lua({'table':[[k,v] for k,v in sorted(rows.items())]})+'\n')
    for filename, data in [('profile.lua',profile),('assets.lua',assets)]:
        (args.output/filename).write_text('return '+lua(data)+'\n')
    report={'game':game,'sha1':SHA[game],'catalogs':{k:len(v) for k,v in catalogs.items()},
            'authored_dialogues':len(corrections),'runtime_enabled':False,'semantic_alignment_verified':False}
    (args.output/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',choices=sorted(SHA),required=True)
    p.add_argument('--bridge',type=Path)
    for field in ['rom','symbols','charmap','manifest','output']:p.add_argument('--'+field,type=Path,required=True)
    build(p.parse_args())
