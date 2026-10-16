"""Audit locale-dependent Emerald structures by their original table schema."""
import json,struct,sys
from pathlib import Path
from map_emerald_languages import ROOT,BASE
from build_profiles import lua_symbols
from asset_emerald_languages import lz_end

def run(lang):
    path=ROOT/f'build/emerald-{lang}-relocation.json';r=json.loads(path.read_text())
    spec=next(x for x in json.loads((ROOT/'build/emerald-new-language-inputs.json').read_text())['roms'] if x['language']==lang)
    src=(ROOT/'build/test-gba-roms/Pokemon - Smaragd-Edition (Germany).gba').read_bytes();dst=Path(spec['staged_file']).read_bytes()
    maps={int(k):v for k,v in r['mapped'].items()}
    rows=lua_symbols(ROOT/'build/profile-engine/src/import/gba/syms/emeraldde.lua')
    def off(name):return rows[name][0]
    def mapped(name):return maps[off(name)]
    # The 289 eight-byte palette records sit between the picture records and
    # backgrounds. Validate both boundaries, every tag, and each LZ palette.
    a,size=rows['gBattleAnimPaletteTable']
    b=mapped('gBattleAnimPicTable')+rows['gBattleAnimPicTable'][1]
    assert b+size==mapped('gBattleAnimBackgroundTable')
    for i in range(size//8):
        assert src[a+i*8+4:a+i*8+8]==dst[b+i*8+4:b+i*8+8]
        ptr=struct.unpack_from('<I',dst,b+i*8)[0]-BASE
        original=struct.unpack_from('<I',src,a+i*8)[0]-BASE
        assert 0<=ptr<len(dst) and dst[ptr:ptr+4]==src[original:original+4]
        assert dst[ptr]==16 and int.from_bytes(dst[ptr+1:ptr+4],'little') in (32,160)
        assert lz_end(dst,ptr) is not None
    maps[a]=b
    # IT/ES keyboards have eight columns; DE/FR have nine. Derive the span
    # between the window templates and column counts, not the German size.
    start=mapped('naming_screen.o:sWindowTemplates')+rows['naming_screen.o:sWindowTemplates'][1]
    end=mapped('sPageColumnCounts');size=end-start
    assert size in (96,108)
    cols=size//12
    assert all(1<=n<=cols for n in dst[end:end+3])
    assert mapped('sPageToNextGfxId')-mapped('sPageColumnXPos')==cols*3
    maps[off('sKeyboardChars')]=start
    r['size_overrides']={'naming_screen.o:sKeyboardChars':size}
    r['mapped']={str(k):v for k,v in maps.items()}
    r['counts']['structure-audit']={'palette_records':289,'keyboard_columns':cols}
    path.write_text(json.dumps(r));print(lang,'STRUCTURES_OK',289,'palettes;',cols,'keyboard columns')

if __name__=='__main__':run(sys.argv[1])
