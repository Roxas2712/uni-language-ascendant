"""Reviewed FRLG summary loader with expanded translated name buffers.

Breno 1.1 moves summary struct fields by 28 bytes. GCC replaces two
shifted-immediate address calculations with literal loads. Consequently a
whole-function byte match cannot recover its page tilemaps. These fingerprints
pin the reviewed 748-byte dispatch function, including its 16-state jump table,
conditions, calls and register choices. The normalized shapes are identical
between FireRed and LeafGreen. Only pointers and BL destinations are normalized.
"""
import hashlib
import struct
from gba_relocation import BASE, normalize

SOURCE_SHAPE = 'e7ef07137fa25fed561cd0eaf8c42bc033979b3c785a2e5ead81384e907ca8e8'
TARGET_SHAPE = 'af2c4701744233cde0833413889e5a81f9fbf50fadb284f590ecaecb834e35be'
# Source and translated literal offsets in CB2_SetUpPSS state 11. Egg and
# normal/move pages still reach CopyToBgTilemapBuffer through the same branches.
PAGES = {
    'gSummaryScreen_PageEgg_Tilemap': (0x11c, 0x11c),
    'gSummaryScreen_PageMoves_Tilemap': (0x154, 0x150),
    'gSummaryScreen_PageMovesInfo_Tilemap': (0x158, 0x158),
    'gSummaryScreen_PageInfo_Tilemap': (0x188, 0x184),
    'gSummaryScreen_PageSkills_Tilemap': (0x18c, 0x18c),
}


def extract(source, target, symbols, mapped):
    row = symbols['CB2_SetUpPSS']
    old, size = row['off'], row['size']
    assert size == 748
    assert hashlib.sha256(normalize(source[old:old+size], True)).hexdigest() == SOURCE_SHAPE
    prefix = source[old:old+32]
    new = target.find(prefix)
    assert new >= 0 and new % 4 == 0 and target.find(prefix, new+1) < 0
    assert hashlib.sha256(normalize(target[new:new+size], True)).hexdigest() == TARGET_SHAPE
    out, proof, anchors = {}, [], 0
    for name, (before, after) in PAGES.items():
        src = struct.unpack_from('<I', source, old+before)[0] - BASE
        dst = struct.unpack_from('<I', target, new+after)[0] - BASE
        assert src == symbols[name]['off'], name
        assert 0 <= dst <= len(target)-4
        # Every page is a GBA LZ77 tilemap with the same decompressed size.
        assert source[src] == target[dst] == 0x10
        assert source[src+1:src+4] == target[dst+1:dst+4], name
        if str(src) in mapped:
            assert mapped[str(src)] == dst, ('Independent page anchor disagrees', name)
            anchors += 1
        else:
            block = source[src:src+symbols[name]['size']]
            if (len(block) >= 24 and target.find(block) == dst
                    and target.find(block, dst+1) < 0
                    and source.find(block) == src and source.find(block, src+1) < 0):
                anchors += 1
        out[src] = dst
        proof.append([name, src, dst, old+before, new+after])
    assert anchors >= 2, 'Need two independently mapped page references'
    return out, dict(kind='reviewed-summary-state-11', source_function=old,
                     target_function=new, size=size, source_shape=SOURCE_SHAPE,
                     target_shape=TARGET_SHAPE, anchors=anchors, pages=proof)
