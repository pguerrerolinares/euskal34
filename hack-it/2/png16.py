"""Minimal 16-bit RGB PNG decoder (numpy only)."""
import struct
import zlib

import numpy as np


def read16(path):
    d = open(path, 'rb').read()
    i = 8
    idat = b''
    w = h = None
    while i < len(d):
        ln = struct.unpack('>I', d[i:i + 4])[0]
        typ = d[i + 4:i + 8]
        data = d[i + 8:i + 8 + ln]
        if typ == b'IHDR':
            w, h, depth, color = struct.unpack('>IIBB', data[:10])
            assert depth == 16 and color == 2, (depth, color)
        elif typ == b'IDAT':
            idat += data
        i += 12 + ln
    raw = zlib.decompress(idat)
    bpp = 6
    stride = w * bpp
    out = np.zeros((h, stride), dtype=np.uint8)
    prev = np.zeros(stride, dtype=np.uint8)
    pos = 0
    for y in range(h):
        ft = raw[pos]
        pos += 1
        line = np.frombuffer(raw[pos:pos + stride], dtype=np.uint8).copy()
        pos += stride
        if ft == 0:
            cur = line
        elif ft == 1:
            cur = line
            for x in range(bpp, stride):
                cur[x] = (cur[x] + cur[x - bpp]) & 0xFF
        elif ft == 2:
            cur = (line + prev) & 0xFF
        elif ft == 3:
            cur = line
            for x in range(stride):
                a = cur[x - bpp] if x >= bpp else 0
                cur[x] = (cur[x] + ((int(a) + int(prev[x])) >> 1)) & 0xFF
        elif ft == 4:
            cur = line
            for x in range(stride):
                a = int(cur[x - bpp]) if x >= bpp else 0
                b = int(prev[x])
                c = int(prev[x - bpp]) if x >= bpp else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[x] = (cur[x] + pr) & 0xFF
        else:
            raise ValueError(ft)
        out[y] = cur
        prev = cur
    arr = out.view(np.dtype('>u2')).reshape(h, w, 3)
    return arr.astype(np.uint16)


if __name__ == '__main__':
    import sys
    a = read16(sys.argv[1])
    print(a.shape, a.dtype, a.min(), a.max())
