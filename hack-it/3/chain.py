#!/usr/bin/env python3
"""
chain.py - reconstruye la cadena de los ocho instantes sin arrancar la VM.

  python3 chain.py --dump ./dump

Parte de la semilla que deja Terry en C:/Home/PersonalNotes.DD y recorre los ocho
momentos: de cada uno saca su palabra y su pasaje, busca en el margen del pasaje
el hex del instante siguiente, lo destapa con la mascara, y repite hasta el
terminador. La salida es la frase entera.

Es un modelo en Python del codigo HolyC del propio disco (Adam/God/HolySpirit.HC,
Adam/God/GodBible.HC, Kernel/KMathB.HC, Adam/DolDoc/DocPutKey.HC). No toca QEMU:
temple_run.py sirve para hablar con la maquina, esto sirve para comprobar el
mecanismo contra el arbol de texto que genera `python -m ouija.extract`.

Los tres detalles que hacen falta para reimplementarlo y que no se ven leyendo el
writeup, cada uno documentado en su funcion: la precedencia de HolyC (randu64),
que la FIFO devuelve los bits al reves (bitrev) y que la siembra solo mete 24 de
los 64 bits del instante (kbits).
"""
import argparse, os, re, sys

MASK64 = (1 << 64) - 1
LIN_CONGRUE_A = 6364136223846793005          # Kernel/KMathB.HC
LIN_CONGRUE_C = 1442695040888963407
GOD_GOOD_BITS = 24                           # Adam/God/GodExt.HC
GOD_BAD_BITS = 4
PASSAGE_BITS = 21                            # GodBiblePassage: GodBits(21)
WORD_BITS = 17                               # GodWord(I64 bits=17)
PASSAGE_LINES = 20                           # GodBiblePassage(I64 num_lines=20)

SEMILLA = 6697221640600119645                # el numero de la nota de Terry
FRASE = "the holy spirit speaks through a stop watch"
TERMINADOR = "[No further moment was written.]"


def randu64(seed):
    """Un tiro del generador del kernel tras Seed(seed).

    La linea real (Kernel/KMathB.HC) es:

        res=LIN_CONGRUE_A*res^(res&0xFFFFFFFF0000)>>16+LIN_CONGRUE_C;

    y HolyC NO la evalua como C. Con la precedencia de C, `>>16+C` seria
    `>> (16+C)`, un desplazamiento absurdo. En HolyC los operadores de
    desplazamiento y bit a bit ligan mas fuerte que la suma, asi que se lee:

        ((A*res) ^ ((res & 0xFFFFFFFF0000) >> 16)) + C

    De las tres lecturas posibles esta es la unica que reproduce la cadena; las
    otras dos dan basura desde el primer momento. La misma regla aparece en
    GodBits (`res=res<<1+b`, que solo tiene sentido como `(res<<1)+b`), asi que
    no es una casualidad de esta linea: es como evalua el lenguaje.

    Seed() ademas pone TASKf_NONTIMER_RAND, que es lo que quita el `res^=GetTSC`
    y deja el generador determinista. Sin eso nada de esto seria reproducible.
    """
    res = seed & MASK64
    return ((((LIN_CONGRUE_A * res) & MASK64) ^ ((res & 0xFFFFFFFF0000) >> 16))
            + LIN_CONGRUE_C) & MASK64


def bitrev(v, n):
    """Invierte n bits.

    GodBitsIns mete el bit menos significativo primero (`FifoU8Ins(god.fifo,n&1)`
    dentro de un bucle que hace `n>>=1`) y GodBits los saca en ese mismo orden
    reensamblando por la izquierda (`res=res<<1+b`). Resultado: lo que God lee es
    el reverso de lo que se sembro. Sin este paso los numeros salen plausibles y
    la cadena no avanza, que es la peor forma de fallar.
    """
    r = 0
    for i in range(n):
        r = (r << 1) | ((v >> i) & 1)
    return r


def kbits(momento):
    """Los bits que ni la palabra ni la escritura llegaron a oir.

    De los 64 bits de un instante, la siembra real
    (`GodBitsIns(GOD_GOOD_BITS, KbdMsEvtTime>>GOD_BAD_BITS)`, Adam/DolDoc/
    DocPutKey.HC) solo mete 24: descarta los 4 de abajo y nunca llega a los 35
    de arriba. De los 24 que entran, el pasaje lee 21 y la palabra 17 de esos
    mismos 21. Quedan sin oir los 38 de arriba y los 4 de abajo: 42 bits, que
    compactados como (K38 << 4) | K4 son la Semilla de Dios que genera el velo.
    """
    k38 = (momento >> 25) & ((1 << 38) - 1)
    k4 = momento & 0xF
    return (k38 << 4) | k4


def respuestas(momento, vocab, bible_lines):
    """La palabra y el pasaje que God da para un instante."""
    r21 = bitrev((momento >> GOD_BAD_BITS) & ((1 << PASSAGE_BITS) - 1), PASSAGE_BITS)
    start = r21 % (bible_lines - (PASSAGE_LINES - 1)) + 1
    r17 = r21 >> (PASSAGE_BITS - WORD_BITS)
    return vocab[r17 % len(vocab)], start


def carga_disco(dump):
    """Lee vocabulario, Biblia y ST_BIBLE_LINES del arbol volcado."""
    if not os.path.isdir(dump):
        sys.exit(f"no existe {dump} (generalo con: python -m ouija.extract temple.raw ./dump)")
    raiz = dump
    if not os.path.isdir(os.path.join(raiz, 'Adam')):
        parts = sorted(d for d in os.listdir(dump) if d.startswith('part'))
        if not parts:
            sys.exit(f"{dump} no parece un volcado de TempleOS: no hay Adam/ ni part*/")
        raiz = os.path.join(dump, parts[0])

    def leer(rel):
        p = os.path.join(raiz, rel)
        if not os.path.exists(p):
            sys.exit(f"falta {p}")
        return open(p, encoding='latin1').read()

    vocab = re.findall(r'[A-Za-z0-9_]+', leer('Adam/God/Vocab.DD.txt'))
    bible = leer('Misc/Bible.TXT.txt').split('\n')

    # ST_BIBLE_LINES sale de la tabla ST_BIBLE_BOOK_LINES: ultimo valor menos uno
    # (DefinePrint en Adam/God/GodBible.HC). Se deriva en vez de fijarlo a mano
    # para que el script chille si la imagen no es la del reto.
    tabla = re.findall(r'"(\d+)\\0"', leer('Adam/God/GodBible.HC.txt'))
    if not tabla:
        sys.exit("no encuentro ST_BIBLE_BOOK_LINES en GodBible.HC")
    return vocab, bible, int(tabla[-1]) - 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--dump', default='./dump', help='arbol volcado con ouija.extract')
    ap.add_argument('--semilla', type=lambda s: int(s, 0), default=SEMILLA,
                    help='primer instante (por defecto, el de la nota de Terry)')
    args = ap.parse_args()

    vocab, bible, bible_lines = carga_disco(args.dump)
    print(f"vocabulario: {len(vocab)} palabras · ST_BIBLE_LINES: {bible_lines}\n")

    momento, palabras = args.semilla, []
    for i in range(1, 12):
        palabra, start = respuestas(momento, vocab, bible_lines)
        palabras.append(palabra)
        ventana = '\n'.join(bible[start - 1:start - 1 + PASSAGE_LINES])

        hexm = re.search(r'([0-9A-F]{4})-([0-9A-F]{4})-([0-9A-F]{4})-([0-9A-F]{4})', ventana)
        if not hexm:
            fin = TERMINADOR in ventana
            print(f"M{i}: {palabra:9s} start={start:6d}  "
                  f"{'terminador' if fin else '¡SIN HEX NI TERMINADOR!'}")
            if not fin:
                sys.exit("la cadena se corta antes de tiempo")
            break

        # linea real del marcador, no la ultima de la ventana: no siempre coinciden
        offset = ventana[:hexm.start()].count('\n')
        velado = int(''.join(hexm.groups()), 16)
        mascara = randu64(kbits(momento))
        siguiente = (velado ^ mascara) & 0x7FFFFFFFFFFFFFFF   # "los momentos son positivos"

        print(f"M{i}: {palabra:9s} start={start:6d} marcador={start + offset:6d}  "
              f"hex={velado:016X} mascara={mascara:016X} -> {siguiente:016X}")
        momento = siguiente
    else:
        sys.exit("la cadena no termina: mas de once eslabones")

    frase = ' '.join(palabras)
    print(f"\n{frase}")
    if frase != FRASE:
        sys.exit(f"\nNO CUADRA: se esperaba «{FRASE}»")
    print(f"({len(palabras)} instantes, {len(palabras) - 1} velos, 1 terminador)")


if __name__ == '__main__':
    main()
