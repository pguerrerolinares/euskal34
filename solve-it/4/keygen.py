"""Keygen de la contrasena de Solve It 4 (EE34, "Moviplaya 2005").

La contrasena NO esta guardada como texto en la ROM: la genera en runtime la
special 0x1F4 (gSpecials[0x1F4] = 0x08179b3d) cuando derrotas al entrenador de
la cueva oculta.  Este script reproduce ESE algoritmo, byte a byte, SIN necesitar
la ROM: las cuatro tablas de sustitucion (4 x 19 = 76 bytes) van embebidas abajo.

Esos 76 bytes son datos inyectados por el autor del reto, no de la Emerald
comercial; publicarlos es publicar la solucion, que es el objeto del writeup.
La ROM sigue sin redistribuirse.

Algoritmo (tal como esta compilado en la ROM):
  seed  = (VarGet(0x404E) & 0xFFFF) | (VarGet(0x4083) << 16)
  gate  : dos flags puestos  Y  seed == 0x3D40563B  (si no, no genera)
  state = seed ^ 0xC3A5F17D
  para i = 0..12 (13 chars):
      state   = xorshift32(state)                 # shifts 13, 17, 5
      buf[i]  = (state >> 24)                      # byte alto del estado
              ^ TABLES[i & 3][ index(i) % 19 ]     # sustitucion por posicion
              ^ ((29*i + 0x37) & 0xFF)             # mascara dependiente de i
  buf[13] = 0xFF                                   # terminador
  index(i) segun i & 3:  0 -> 7*i+3   1 -> 11*i+5   2 -> 13*i+7   3 -> 17*i+9

El resultado, decodificado con el charset Gen 3, es la contrasena.
"""

# --- las cuatro tablas de sustitucion, 19 bytes cada una (ROM @ 0x5F14A0) -----
TABLES = [
    bytes.fromhex('54 e6 26 99 ee 82 68 56 0f 6d 84 6d 8c e1 c9 90 dd 8b 1c'),
    bytes.fromhex('cf 93 fa ac 1a db fa c3 8a b1 11 70 5f c0 61 54 45 41 ce'),
    bytes.fromhex('30 c4 4b ec ee dc ac d6 83 62 6b e8 d4 ff bd 03 c2 bd 84'),
    bytes.fromhex('f4 bd 46 60 33 07 4d a7 2d c3 3e 73 e9 f2 e2 99 9d ea a1'),
]

SEED = 0x3D40563B          # el valor que exige el gate (seed == 0x3D40563B)
XOR_KEY = 0xC3A5F17D
ROM_TABLES_OFFSET = 0x5F14A0
ROM_SPECIAL_0x1F4 = 0x08179B3D

# --- charset Gen 3 (solo lo que necesita la contrasena) -----------------------
_CH = {0x00: ' '}
for _i, _c in enumerate('0123456789'):                 _CH[0xA1 + _i] = _c
for _i, _c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'): _CH[0xBB + _i] = _c
for _i, _c in enumerate('abcdefghijklmnopqrstuvwxyz'): _CH[0xD5 + _i] = _c


def xorshift32(x):
    x &= 0xFFFFFFFF
    x ^= (x << 13) & 0xFFFFFFFF
    x ^= x >> 17
    x ^= (x << 5) & 0xFFFFFFFF
    return x & 0xFFFFFFFF


def _index(i):
    k = i & 3
    v = (7 * i + 3, 11 * i + 5, 13 * i + 7, 17 * i + 9)[k]
    return v % 19


def generate(seed=SEED, tables=TABLES):
    """Reproduce el bucle de la special 0x1F4.  Devuelve los 13 bytes Gen 3."""
    state = seed ^ XOR_KEY
    out = []
    for i in range(13):
        state = xorshift32(state)
        b = ((state >> 24) ^ tables[i & 3][_index(i)] ^ ((29 * i + 0x37) & 0xFF)) & 0xFF
        out.append(b)
    return bytes(out)


def decode_gen3(bs):
    return ''.join(_CH.get(b, '<%02X>' % b) for b in bs)


def extract_tables_from_rom(path, offset=ROM_TABLES_OFFSET):
    """Saca las 76 bytes de la ROM para quien la tenga, y confirma que las
    tablas embebidas arriba son las de verdad.  No redistribuye nada."""
    rom = open(path, 'rb').read()
    blob = rom[offset:offset + 76]
    return [blob[j * 19:(j + 1) * 19] for j in range(4)]


if __name__ == '__main__':
    import sys

    raw = generate()
    print('bytes Gen 3 :', raw.hex(' '))
    print('contrasena  :', decode_gen3(raw))
    print()
    print('mapa byte -> char:')
    print('  ' + '  '.join(f'{b:02x}={decode_gen3(bytes([b]))}' for b in raw))

    # comprobacion opcional contra la ROM: python3 keygen.py pokemon-esmeralda.gba
    rom_path = sys.argv[1] if len(sys.argv) > 1 else None
    if rom_path:
        print()
        rom_tables = extract_tables_from_rom(rom_path)
        ok = rom_tables == TABLES
        print(f'tablas de la ROM (@{ROM_TABLES_OFFSET:#x}) == embebidas: {ok}')
        if ok:
            print(f'contrasena regenerada con las de la ROM: '
                  f'{decode_gen3(generate(tables=rom_tables))}')
        else:
            for j, (a, b) in enumerate(zip(TABLES, rom_tables)):
                print(f'  tab{j}: embebida={a.hex()} rom={b.hex()} '
                      f'{"OK" if a == b else "DISTINTA"}')
