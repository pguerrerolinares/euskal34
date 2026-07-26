#!/usr/bin/env python3
"""Dentro de cada bloque WavPack hay metadata sub-blocks con ID. Los que el
decodificador no reconoce (o ID_DUMMY=0x00) se IGNORAN al decodificar: escondite
perfecto. Mi analisis anterior solo miro las cabeceras de 32 bytes."""
import struct, collections, sys

NAMES = {0x00:"DUMMY", 0x01:"ENCODER_INFO", 0x02:"DECORR_TERMS", 0x03:"DECORR_WEIGHTS",
         0x04:"DECORR_SAMPLES", 0x05:"ENTROPY_VARS", 0x06:"HYBRID_PROFILE",
         0x07:"SHAPING_WEIGHTS", 0x08:"FLOAT_INFO", 0x09:"INT32_INFO",
         0x0a:"WV_BITSTREAM", 0x0b:"WVC_BITSTREAM", 0x0c:"WVX_BITSTREAM",
         0x0d:"CHANNEL_INFO", 0x0e:"DSD_BLOCK",
         0x21:"RIFF_HEADER", 0x22:"RIFF_TRAILER", 0x23:"ALT_HEADER",
         0x24:"ALT_TRAILER", 0x25:"CONFIG_BLOCK", 0x26:"MD5_CHECKSUM",
         0x27:"SAMPLE_RATE", 0x28:"ALT_EXTENSION", 0x29:"ALT_MD5",
         0x2a:"NEW_CONFIG", 0x2b:"CHANNEL_IDENTITIES", 0x2c:"BS_1BIT"}

f = open("classical_music.wv", "rb")
off = 0
stats = collections.Counter()
payloads = collections.defaultdict(list)
nblocks = 0
while True:
    f.seek(off)
    hdr = f.read(32)
    if len(hdr) < 32 or hdr[:4] != b"wvpk":
        break
    ck = struct.unpack("<I", hdr[4:8])[0]
    body = f.read(ck + 8 - 32)
    nblocks += 1
    p = 0
    while p + 2 <= len(body):
        idb = body[p]; p += 1
        large = bool(idb & 0x80)      # ID_LARGE
        odd = bool(idb & 0x40)        # ID_ODD_SIZE
        func = idb & 0x3f             # el ID son 6 bits
        if large:
            if p + 3 > len(body): break
            words = body[p] | (body[p+1] << 8) | (body[p+2] << 16); p += 3
        else:
            if p + 1 > len(body): break
            words = body[p]; p += 1
        size = words * 2 - (1 if odd else 0)
        data = body[p:p+size]; p += words * 2
        key = func
        name = NAMES.get(key, f"DESCONOCIDO_0x{key:02x}")
        stats[(key, name)] += 1
        if name in ("DUMMY",) or name.startswith("DESCONOCIDO"):
            if len(payloads[(key, name)]) < 8:
                payloads[(key, name)].append((nblocks-1, data))
    off += ck + 8

print(f"bloques: {nblocks}\n")
print("sub-bloques de metadata encontrados:")
for (key, name), c in sorted(stats.items(), key=lambda x: -x[1]):
    print(f"  0x{key:02x} {name:22s} x{c}")

print("\ncontenido de DUMMY / desconocidos:")
found = False
for (key, name), lst in payloads.items():
    for blk, data in lst:
        found = True
        printable = "".join(chr(b) if 32 <= b < 127 else "." for b in data[:80])
        print(f"  bloque {blk:5d}  {name}  {len(data)} bytes  {printable!r}")
if not found:
    print("  (ninguno con contenido)")
