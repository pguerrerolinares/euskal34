#!/usr/bin/env python3
"""Parsea la cadena de bloques WavPack de classical_music.wv y busca canal encubierto
en la estructura del contenedor (tamanos, block_samples, flags, crc)."""
import struct, sys, collections

f = open(sys.argv[1] if len(sys.argv) > 1 else "classical_music.wv", "rb")
blocks = []
off = 0
while True:
    f.seek(off)
    hdr = f.read(32)
    if len(hdr) < 32 or hdr[:4] != b"wvpk":
        break
    _id, ck, ver, bidx8, tot8, tot, bidx, bsamp, flags, crc = struct.unpack("<4sIHBBIIIII", hdr)
    blocks.append((off, ck, ver, bidx, bsamp, flags, crc))
    off += ck + 8

print(f"bloques: {len(blocks)}  ultimo offset: {off}  filesize: {f.seek(0,2)}")
sizes  = [b[1] for b in blocks]
samps  = [b[4] for b in blocks]
flags  = [b[5] for b in blocks]
crcs   = [b[6] for b in blocks]

print(f"block_samples distintos: {collections.Counter(samps).most_common(6)}")
print(f"flags distintos        : {[hex(x) for x,_ in collections.Counter(flags).most_common(6)]}")
print(f"ckSize  min/max/media  : {min(sizes)} / {max(sizes)} / {sum(sizes)//len(sizes)}")

# canal encubierto por paridad del tamano de bloque -> bits -> ASCII
for name, seq in (("size", sizes), ("crc", crcs)):
    bits = "".join(str(v & 1) for v in seq)
    for order in ("msb", "lsb"):
        bb = bits if order == "msb" else "".join(
            bits[i:i+8][::-1] for i in range(0, len(bits) - len(bits) % 8, 8))
        txt = "".join(chr(int(bb[i:i+8], 2)) for i in range(0, len(bb) - len(bb) % 8, 8))
        printable = sum(32 <= ord(c) < 127 for c in txt) / max(len(txt), 1)
        print(f"paridad {name:4s} {order}: {printable:.0%} imprimible | {txt[:60]!r}")
