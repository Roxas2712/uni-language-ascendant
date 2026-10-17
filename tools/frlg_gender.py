"""Recover the PT-BR patch's gender choices from verified Thumb routines.

The routine must read SaveBlock2.playerGender (byte 8), branch on zero,
and return exactly one of two ROM strings. No emulation or guessed wording.
"""
import struct
BASE=0x08000000
PREFIX=bytes.fromhex('00b503480068007a002805d0014804e0')
SUFFIX=bytes.fromhex('014802bc08470000')

def extract(rom, function):
    # GetExpandedPlaceholder: bounds check, indirect function table call.
    assert rom[function:function+14]==bytes.fromhex('00b5202808d80349800040180068'), 'Unexpected placeholder dispatcher'
    assert rom[function+18:function+20]==bytes.fromhex('02e0')
    table=struct.unpack_from('<I',rom,function+20)[0]-BASE
    assert 0<=table<=len(rom)-33*4
    rows={};save_ptr=None
    for code in range(14,33):
        ptr=struct.unpack_from('<I',rom,table+code*4)[0]
        assert ptr&1,'Expected Thumb function'
        at=ptr-BASE-1
        assert 0<=at<=len(rom)-36
        block=rom[at:at+36]
        assert block[:16]==PREFIX and block[24:32]==SUFFIX, ('Unexpected gender routine',code,hex(at))
        ram=struct.unpack_from('<I',block,16)[0]
        assert 0x03000000<=ram<0x03008000
        if save_ptr is None:save_ptr=ram
        assert ram==save_ptr
        values={}
        for name,offset in [('female',20),('male',32)]:
            address=struct.unpack_from('<I',block,offset)[0]-BASE
            assert 0<=address<len(rom)
            end=rom.find(b'\xff',address,address+64)
            assert end>address and not any(x in rom[address:end] for x in (0xfc,0xfd,0xfe)), ('Invalid gender word',code,name)
            values[name]=address
        rows[code]=values
    return rows
