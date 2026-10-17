"""Resolve translated tilesets through independently identical palette/attributes."""
import re
import struct
from gba_identical_relocation import unique_copy
from gba_relocation import BASE


def extract(source, target, symbols):
    name = 'DepartmentStore'
    header = symbols['gTileset_' + name]['off']
    assert symbols['gTileset_' + name]['size'] == 24
    anchors = {}
    for label, rel in [('gTilesetPalettes_', 8), ('gMetatileAttributes_', 20)]:
        row = symbols[label + name]
        assert struct.unpack_from('<I', source, header+rel)[0] == BASE+row['off']
        match = unique_copy(source, target, row['off'], row['size'])
        assert match is not None, ('Tileset anchor is not unique', label+name)
        anchors[rel] = match
    # Preserve compression/secondary flags and callback. Only tile pointers vary.
    pattern = (re.escape(source[header:header+4]) + b'[\x00-\xff]{3}\x08'
               + re.escape(struct.pack('<I', BASE+anchors[8])) + b'[\x00-\xff]{3}\x08'
               + re.escape(source[header+16:header+20])
               + re.escape(struct.pack('<I', BASE+anchors[20])))
    hits = list(re.finditer(pattern, target))
    assert len(hits) == 1 and hits[0].start() % 4 == 0
    new = hits[0].start()
    mapped = {header: new}
    for label, rel in [('gTilesetTiles_', 4), ('gTilesetPalettes_', 8),
                       ('gMetatiles_', 12), ('gMetatileAttributes_', 20)]:
        old = symbols[label+name]['off']
        assert struct.unpack_from('<I', source, header+rel)[0] == BASE+old
        ptr = struct.unpack_from('<I', target, new+rel)[0] - BASE
        assert 0 <= ptr < len(target)
        mapped[old] = ptr
    return mapped, dict(kind='typed-tileset-header', name=name, source=header,
                        target=new, independent_anchors=anchors)
