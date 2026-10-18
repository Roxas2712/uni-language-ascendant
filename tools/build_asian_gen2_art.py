"""Native Korean title artwork, decoded from the exact retail load routine.

Only addresses and rendering metadata are emitted. No cartridge pixels are
embedded. Korean title maps use repeat/increment runs, unlike the US tilemap.
"""
import hashlib,json,sys
from pathlib import Path
from asian_gen2 import symbols,offset
from gb_lz import decompress
from build_gb_profiles import export,lua
R=Path(__file__).resolve().parents[1]

def title_map(rom,start):
    out=[];pos=start
    while True:
        count=rom[pos];pos+=1
        if count==255:break
        value=rom[pos];pos+=1
        assert count&127,'Zero-length title run'
        out.extend(range(value,value+(count&127)) if count&128 else [value]*count)
        assert len(out)<=32*18,'Title map exceeds VRAM region'
    assert len(out)==32*18
    return out,pos-start

def build(game):
    folder=R/f'mod/gb/profiles/{game}_ko';profile=export(folder/'profile.lua')
    rom=(R/f'build/pokegold-kr/poke{game}.gbc').read_bytes();sy=symbols(R/f'build/pokegold-kr/poke{game}.sym')
    assert hashlib.sha1(rom).hexdigest()==profile['sha1']
    gfx=offset(*sy['TitleScreenGFX1']);raw,size=decompress(rom,gfx)
    cells,consumed=title_map(rom,offset(*sy['TitleScreenTilemap']))
    assert max(cells)*16+16<=len(raw)
    palettes=[];pal=offset(*sy['GSTitleBGPals'])
    for i in range(5):
        colors=[]
        for j in range(4):
            value=int.from_bytes(rom[pal+i*8+j*2:pal+i*8+j*2+2],'little')
            colors.append([round(((value>>shift)&31)*255/31)for shift in (0,5,10)]+[255])
        palettes.append(colors)
    # FillTitleScreenPals rectangles from the matching Korean disassembly.
    def palette_at(x,y):
        if y>=12 and y<=16:return 4
        if 16<=x<=18 and 2<=y<=4:return 3
        if 1<=x<=15 and y==5:return 2
        if 1<=x<=16 and y<=4:return 1
        return 0
    assets=export(folder/'assets.lua')
    shades=[255,85,170,0] # rBGP=%11011000 in the native DMG branch
    def image(name,y0,height,gray=False):
        tiles=[]
        for y in range(y0,y0+height):
            for x in range(20):
                tile=cells[y*32+x]
                if gray and y==11:tile=8 # native non-CGB cloud border
                colors=[[v,v,v,255]for v in shades]if gray else palettes[palette_at(x,y)]
                tiles.append({'off':gfx,'size':size,'lz':True,'start':tile*16,'length':16,'palette':colors})
        assets['assets/title/'+name+'.png']={'width':160,'height':height*8,'bits':2,'palettes':True,'tiles':tiles}
    image('title_screen',0,18);image('title_screen_gray',0,18,True)
    image('pokemon_logo',0,7);image('clouds',11,6);image('clouds_gray',11,6,True)
    # Localize only the source-bearing title layers; animation/mechanics stay
    # with the base. The native bird/trail are independently byte-equal.
    usroot=R.parent/'Uni-Language-Ascendant-Europe/build/pokegold'
    us=(usroot/f'poke{game}.gbc').read_bytes();ussym=symbols(usroot/f'poke{game}.sym')
    assert decompress(us,offset(*ussym['TitleScreenGFX4']))[0]==decompress(rom,offset(*sy['TitleScreenGFX3']))[0]
    native_trail=offset(*sy['TitleScreenGFX2']);base_trail=offset(*ussym['TitleScreenGFX3']);n=64 if game=='silver'else 128
    assert us[base_trail:base_trail+n]==rom[native_trail:native_trail+n]
    layouts={'title':{key:'assets/generated/title/'+value+'.png'for key,value in {'screen':'title_screen','screenGray':'title_screen_gray','image':'pokemon_logo','clouds':'clouds','cloudsGray':'clouds_gray'}.items()}}
    (folder/'assets.lua').write_text('return '+lua(assets)+'\n')
    (folder/'layouts.lua').write_text('return '+lua({'value':layouts})+'\n')
    if 'layouts.lua'not in profile['catalogs']:profile['catalogs'].append('layouts.lua')
    (folder/'profile.lua').write_text('return '+lua(profile)+'\n')
    (R/f'build/asian-gen2/{game}-ko-art.json').write_text(json.dumps({'sha1':profile['sha1'],'titleGfx':gfx,'tilemap':offset(*sy['TitleScreenTilemap']),'mapBytes':consumed,'palette':pal,'framesAndTrail':'exact US/native byte equality','assets':list(layouts['title'].values())},indent=2)+'\n')
    print('ASIAN_TITLE_ART_OK',game)

def build_crystal():
    folder=R/'mod/gb/profiles/crystal_ja';profile=export(folder/'profile.lua')
    rom=(R.parent/'Pocket Monsters - Crystal Version (Japan).gbc').read_bytes();assert hashlib.sha1(rom).hexdigest()==profile['sha1']
    usroot=R.parent/'Uni-Language-Ascendant-Europe/build/pokecrystal';us=(usroot/'pokecrystal.gbc').read_bytes();sy=symbols(usroot/'pokecrystal.sym')
    from relocate_gb_refs import recover
    logo,proof=recover(us,rom,*sy['TitleLogoGFX']);pal,_=recover(us,rom,*sy['TitleScreenPalettes'])
    assert logo==0x10f32b and pal==0x10fb3b
    raw,size=decompress(rom,logo);assert len(raw)==144*16
    # Native DrawTitleGraphic increments the row start by 16 tiles.
    assert rom[0x10eef3:0x10ef0b]==bytes.fromhex('d5c5e57a22140d20fae101140009c1d13e1082570520e9c9')
    for name,at in [('TitleSuicuneGFX',0x10ef4b),('TitleCrystalGFX',0x10f94b)]:
        assert decompress(rom,at)[0]==decompress(us,offset(*sy[name]))[0]
    uspal=offset(*sy['TitleScreenPalettes'])
    assert rom[pal:pal+8]==us[uspal:uspal+8] # Suicune
    assert rom[pal+64:pal+128]==us[uspal+64:uspal+128] # gem sprites
    pals=[]
    for i in range(8):
        row=[]
        for j in range(4):
            val=int.from_bytes(rom[pal+8*i+2*j:pal+8*i+2*j+2],'little');row.append([round(((val>>shift)&31)*255/31)for shift in(0,5,10)]+[0 if j==0 else 255])
        pals.append(row)
    blank=next(i for i in range(144)if raw[16*i:16*i+16]==bytes(16));cells=[blank]*360
    for x,y,w,h,start in [(3,3,14,1,1),(2,4,16,5,16),(5,9,10,2,99),(3,17,13,1,128)]:
        for yy in range(h):
            for xx in range(w):cells[(y+yy)*20+x+xx]=start+yy*16+xx
    def palat(y):return 1 if y==3 else 3 if 4<=y<=6 else 4 if 7<=y<=8 else 2 if 9<=y<=10 else 5 if y==17 else 0
    assets=export(folder/'assets.lua')
    def make(name,x0,y0,w,h,gray=False):
        tiles=[]
        for y in range(y0,y0+h):
            for x in range(x0,x0+w):
                colors=[[v,v,v,0 if i==0 else 255]for i,v in enumerate([255,170,85,0])]if gray else pals[palat(y)]
                tiles.append({'off':logo,'size':size,'lz':True,'start':cells[y*20+x]*16,'length':16,'palette':colors})
        assets['assets/title/'+name+'.png']={'width':w*8,'height':h*8,'bits':2,'palettes':True,'tiles':tiles}
    make('crystal_screen',0,0,20,18);make('crystal_screen_gray',0,0,20,18,True)
    make('crystal_logo',0,3,20,8);make('crystal_wordmark',5,9,10,2)
    title={key:'assets/generated/title/'+name+'.png'for key,name in {'screen':'crystal_screen','screenGray':'crystal_screen_gray','image':'crystal_logo','wordmark':'crystal_wordmark'}.items()}
    # The native copyright palette is 5, while the renderer expects slot 7.
    title['palettes']={'bg':[[c[:3]for c in row]for row in pals]};title['palettes']['bg'][7]=[c[:3]for c in pals[5]]
    (folder/'assets.lua').write_text('return '+lua(assets)+'\n');(folder/'layouts.lua').write_text('return '+lua({'value':{'title':title}})+'\n')
    if 'layouts.lua'not in profile['catalogs']:profile['catalogs'].append('layouts.lua')
    (folder/'profile.lua').write_text('return '+lua(profile)+'\n')
    (R/'build/asian-gen2/crystal-ja-art.json').write_text(json.dumps({'sha1':profile['sha1'],'titleGfx':logo,'palettes':pal,'evidence':proof,'animation':'Exact native/US tile and palette equality'},indent=2)+'\n')
    print('ASIAN_TITLE_ART_OK crystal')

if __name__=='__main__':
    for game in sys.argv[1:]or ('gold','silver','crystal'):
        build_crystal()if game=='crystal'else build(game)
