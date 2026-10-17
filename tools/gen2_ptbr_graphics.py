"""Native PT-BR tileset recipes; US metatiles and collision data stay intact."""
from gen1_ptbr_dialogue import offset
from gb_lz import decompress

def world_assets(manifest, base, rom, crystal=False):
    syms=manifest['symbols'];headers=offset(*syms['Tilesets']);out={};proof={}
    order=manifest['constants']['tilesetOrder'];blank=rom.find(bytes(16));assert blank>=0
    def stream(data,index):
        pos=headers+(index+1)*15;row=data[pos:pos+15]
        at=offset(row[0],int.from_bytes(row[1:3],'little'));raw,size=decompress(data,at)
        return at,size,raw,row
    _,_,johto,_=stream(base,order.index('TILESET_JOHTO'))
    gym=johto[0x23*16:0x25*16]
    for name in ['johto','johto_modern','kanto']:
        index=order.index('TILESET_'+name.upper());at,size,raw,row=stream(rom,index)
        _,_,original,base_row=stream(base,index)
        assert row[3:9]==base_row[3:9],(name,'Native metatile/collision pointers moved')
        assert len(raw)==len(original),(name,'Native tile count changed')
        changed=[i for i in range(len(raw)//16) if raw[i*16:i*16+16]!=original[i*16:i*16+16]]
        # A translation may alter signs, not the shape/order of whole regions.
        assert len(changed)<=12,(name,'Unexpected broad tileset changes',changed)
        n=256 if crystal else 96;tiles=[]
        for i in range(n):
            source=i if i<96 else i-32 if crystal and 128<=i<224 else None
            if source is None or (source+1)*16>len(raw):tiles.append(dict(off=blank,size=16))
            else:tiles.append(dict(off=at,size=size,lz=True,start=source*16,length=16))
        recipe=dict(width=128,height=n//16*8,bits=2,tiles=tiles)
        # Kanto stores the two plaque halves in separate sheet rows.
        ids=[0x2f,0x3f] if name=='kanto' else [0x23,0x24]
        standard=['1111111111111111','0000000000000000',
                  '0333303003030003','3300003003033033','3303303333033333',
                  '3300300330030303','0333300330030303','0000000000000000']
        gold_translated=[
                  '1111111111111111','0000000000000000','0333330330330033',
                  '3300000000333033','3303330330333333','3300330330330333',
                  '0333330330330033','0000000000000000']
        for data in (original,raw):
            expected=gold_translated if data is raw and not crystal and name!='kanto' else standard
            for y in range(8):
                actual=''.join(str(((data[ids[x//8]*16+y*2]>>(7-x%8))&1)|
                    (((data[ids[x//8]*16+y*2+1]>>(7-x%8))&1)<<1)) for x in range(16))
                assert actual==expected[y],(name,'GYM plaque differs',y)
        letters=[['111','100','101','101','111'],['111','010','010','010','111'],
                 ['101','111','111','101','101'],['000','000','000','000','010']]
        rows=['0'*16]+[''.join(letter[y]+'0' for letter in letters) for y in range(5)]+['0'*16]
        positions=[dict(x=tile%16*8,y=tile//16*8+1,
            rows=[row[half*8:half*8+8] for row in rows],
            colors=[[1,1,1,1],[0,0,0,1]]) for half,tile in enumerate(ids)]
        recipe['authoredPixels']=positions;out['assets/tilesets/'+name+'.png']=recipe
        proof[name]=dict(compressed_offset=at,compressed_length=size,translated_tiles=changed,gym_plaques=1)
    return out,proof

def dex_labels():
    """Own 4x5 labels in the original four-tile OPTION/SEARCH slots."""
    alphabet={
        'O':['0110','1001','1001','1001','0110'],
        'P':['1110','1001','1110','1000','1000'],
        'C':['0111','1000','1000','1000','0111'],
        'E':['1111','1000','1110','1000','1111'],
        'S':['0111','1000','0110','0001','1110'],
        'B':['1110','1001','1110','1001','1110'],
        'U':['1001','1001','1001','1001','0110'],
        'A':['0110','1001','1111','1001','1001'],
        'R':['1110','1001','1110','1010','1001'],
    }
    out=[]
    for text,x in [('OPÇÕES',24),('BUSCAR',80)]:
        rows=[list('0'*32) for _ in range(8)]
        for i,letter in enumerate(text):
            glyph=alphabet[{'Ç':'C','Õ':'O'}.get(letter,letter)]
            for y,line in enumerate(glyph,2):rows[y][i*5:i*5+4]=line
            if letter=='Õ':rows[0][i*5:i*5+4]='0101';rows[1][i*5:i*5+4]='1010'
            if letter=='Ç':rows[7][i*5+1]='1'
        out.append(dict(x=x,y=8,rows=[''.join(r) for r in rows],colors=[[0,0,0,1],[1,1,1,1]]))
    return out

def certificate_labels():
    # Own letters in the original ten-tile congratulations caption. The
    # certificate's page maps and Pokémon illustrations keep their layout.
    alphabet={
        'P':['1110','1001','1110','1000','1000'],
        'A':['0110','1001','1111','1001','1001'],
        'R':['1110','1001','1110','1010','1001'],
        'B':['1110','1001','1110','1001','1110'],
        'E':['1111','1000','1110','1000','1111'],
        'N':['1001','1101','1011','1001','1001'],
        'S':['0111','1000','0110','0001','1110'],
    }
    rows=[list('0'*80) for _ in range(8)];start=20
    for i,char in enumerate('PARABÉNS'):
        for y,line in enumerate(alphabet['E' if char=='É' else char],2):rows[y][start+i*5:start+i*5+4]=line
        if char=='É':rows[0][start+i*5+2]='1';rows[1][start+i*5+1]='1'
    return [dict(x=0,y=0,rows=[''.join(r) for r in rows],colors=[[0,0,0,1],[1,1,1,1]])]

def end_labels():
    alphabet={'O':['0110','1001','1001','1001','0110'],
      'F':['1111','1000','1110','1000','1000'],
      'I':['1111','0110','0110','0110','1111'],
      'M':['1001','1111','1111','1001','1001'],' ':['0000']*5}
    rows=[list('0'*64) for _ in range(16)]
    for i,char in enumerate('O FIM'):
        for y,line in enumerate(alphabet[char]):
            wide=''.join(c*2 for c in line)
            for yy in (2+y*2,3+y*2):rows[yy][8+i*10:16+i*10]=wide
    return [dict(x=0,y=0,rows=[''.join(r) for r in rows],colors=[[1,1,1,1],[0,0,0,1]])]
