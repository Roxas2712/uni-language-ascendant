"""Apply a local BPS patch to a user-supplied ROM, checking all three CRCs."""
import argparse
import struct
import zlib
from pathlib import Path


def apply(source: bytes, patch: bytes) -> bytes:
    if len(patch) < 19 or patch[:4] != b'BPS1':
        raise ValueError('Not a BPS1 patch')
    source_crc, target_crc, patch_crc = struct.unpack('<III', patch[-12:])
    if zlib.crc32(patch[:-4]) != patch_crc:
        raise ValueError('Patch CRC mismatch')
    if zlib.crc32(source) != source_crc:
        raise ValueError('Source ROM CRC mismatch')
    pos, end = 4, len(patch) - 12

    def number():
        nonlocal pos
        value, shift = 0, 1
        for _ in range(10):
            if pos >= end:
                raise ValueError('Truncated BPS number')
            byte = patch[pos]
            pos += 1
            value += (byte & 127) * shift
            if byte & 128:
                return value
            shift <<= 7
            value += shift
        raise ValueError('BPS number too large')

    source_size, target_size, metadata_size = number(), number(), number()
    if source_size != len(source) or target_size > 64 * 1024 * 1024:
        raise ValueError('Unexpected ROM size')
    pos += metadata_size
    output = bytearray()
    source_relative = target_relative = 0
    while len(output) < target_size:
        command = number()
        action, length = command & 3, (command >> 2) + 1
        if len(output) + length > target_size:
            raise ValueError('BPS output overflow')
        if action == 0:
            chunk = source[len(output):len(output) + length]
            if len(chunk) != length:
                raise ValueError('BPS source read overflow')
            output.extend(chunk)
        elif action == 1:
            if pos + length > end:
                raise ValueError('Truncated BPS literal')
            output.extend(patch[pos:pos + length])
            pos += length
        else:
            encoded = number()
            delta = -(encoded >> 1) if encoded & 1 else encoded >> 1
            if action == 2:
                source_relative += delta
                if source_relative < 0 or source_relative + length > len(source):
                    raise ValueError('BPS source copy overflow')
                output.extend(source[source_relative:source_relative + length])
                source_relative += length
            else:
                target_relative += delta
                for _ in range(length):
                    if not 0 <= target_relative < len(output):
                        raise ValueError('BPS target copy overflow')
                    output.append(output[target_relative])
                    target_relative += 1
    if pos != end or zlib.crc32(output) != target_crc:
        raise ValueError('Target ROM CRC mismatch or trailing patch data')
    return bytes(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('patch', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = apply(args.source.read_bytes(), args.patch.read_bytes())
    with args.output.open('xb') as destination:
        destination.write(result)
