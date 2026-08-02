#!/usr/bin/env python3
"""
whitespace.py - decodifica el programa Whitespace escondido en el chunk tEXt de v.png.

  python3 whitespace.py [fichero.png]     # v.png por defecto

Whitespace es un lenguaje esoterico donde el codigo son solo espacio, tabulador
y salto de linea (todo lo demas es comentario y se ignora); por eso cabe entero
dentro de un chunk `tEXt` de un PNG sin que se note nada raro en el fichero.

Cada instruccion empieza con un IMP (Instruction Modification Parameter) que
dice a que familia pertenece:

    espacio           -> Manipulacion de pila
    tabulador espacio -> Aritmetica
    tabulador tabulador -> Acceso a heap
    salto de linea    -> Control de flujo
    tabulador salto   -> Entrada/salida

Este fichero solo trae las tres instrucciones que hacen falta para leer LO QUE
HAY en v.png -- no un interprete de Whitespace completo. Si aparece cualquier
otra, lo dice y para; no se la salta en silencio.

1. PUSH (pila: espacio espacio) -- empuja un numero. Al comando le sigue el
   numero en si: un bit de signo (espacio = positivo, tabulador = negativo) y
   luego los bits del valor absoluto, mas significativo primero, con espacio =
   0 y tabulador = 1, cerrados con un salto de linea. Ej.: espacio(signo +),
   tabulador tabulador tabulador espacio espacio espacio tabulador = 1110001
   en binario = 113 = 'q'.

2. OUTPUT CHAR (E/S: tabulador salto, comando espacio espacio) -- saca el
   valor de la cima de la pila y lo imprime como caracter (su punto de codigo
   Unicode / ASCII).

3. END (control de flujo: salto, comando salto salto) -- termina el programa.
   Es la instruccion de cierre estandar de Whitespace y es justo lo que hay al
   final del chunk, tres saltos de linea seguidos.

El contenido de v.png es una repeticion de PUSH seguido de OUTPUT CHAR: un par
por caracter del mensaje, mas el END final. Cada caracter invisible se dibuja
aqui como simbolo visible para poder seguir la traza:

    espacio   -> ·   (tambien: bit 0 dentro de un numero)
    tabulador -> ->  (tambien: bit 1 dentro de un numero)
    salto     -> ↵

Verificado corriendo este mismo fichero contra v.png: 392 bytes de contenido
(215 espacios, 120 tabuladores, 57 saltos), 27 pares push+output, la primera
instruccion son los bits 1110001 = 113 = 'q', y la salida completa es
"q v_min = -0.2, v_max = 0.2" -- la desnormalizacion que usan solve.py y
solve_inversa.py para leer v.png.
"""
import struct
import sys

PUNTO = '·'   # · -- espacio, o bit 0
FLECHA = '→'  # -> -- tabulador, o bit 1
VUELTA = '↵'  # ↵ -- salto de linea


def visible(s):
    """Cada caracter invisible de Whitespace, dibujado como simbolo visible."""
    out = []
    for c in s:
        if c == ' ':
            out.append(PUNTO)
        elif c == '\t':
            out.append(FLECHA)
        elif c == '\n':
            out.append(VUELTA)
        else:
            out.append('?')
    return ''.join(out)


def lee_chunk_texto(path):
    """Recorre los chunks del PNG a mano (sin PIL) y devuelve (keyword,
    contenido) del primer tEXt que encuentra. Igual que el snippet del
    WRITEUP.md, pero separando keyword y contenido por el byte nulo."""
    d = open(path, 'rb').read()
    i = 8  # firma PNG
    while i < len(d):
        ln = struct.unpack('>I', d[i:i + 4])[0]
        typ = d[i + 4:i + 8]
        data = d[i + 8:i + 8 + ln]
        if typ == b'tEXt':
            nul = data.index(b'\x00')
            keyword = data[:nul].decode('latin1')
            contenido = data[nul + 1:].decode('latin1')
            return keyword, contenido
        i += 12 + ln
    raise ValueError('no hay ningun chunk tEXt en %r' % path)


def decodifica(contenido):
    """Interpreta el programa Whitespace y devuelve (lineas_de_traza, salida).

    Cada linea de traza corresponde a un par PUSH+OUTPUT (un caracter del
    mensaje). Si aparece una instruccion que no sea PUSH, OUTPUT CHAR o END,
    se detiene ahi mismo y lo dice -- no hay intento de adivinar que hace."""
    pos = 0
    n = len(contenido)
    pila = []
    salida = []
    trazas = []
    pendiente = None  # (raw_push, sign_ch, bits, valor) del ultimo push

    while pos < n:
        c = contenido[pos]

        if c == ' ':                              # IMP: Manipulacion de pila
            inicio = pos
            pos += 1
            if pos >= n or contenido[pos] != ' ':
                cmd = contenido[pos:pos + 1]
                print("PARADA en byte %d: IMP de pila con comando %r "
                      "(%s) -- solo 'push' (espacio espacio) esta "
                      "implementado" % (pos, cmd, visible(cmd)))
                break
            pos += 1                               # comando 'push'
            if pos >= n:
                print("PARADA en byte %d: push sin signo (fin de chunk)" % pos)
                break
            sign_ch = contenido[pos]
            if sign_ch not in (' ', '\t'):
                print("PARADA en byte %d: signo invalido %r" % (pos, sign_ch))
                break
            pos += 1
            bits = ''
            while pos < n and contenido[pos] != '\n':
                if contenido[pos] == ' ':
                    bits += '0'
                elif contenido[pos] == '\t':
                    bits += '1'
                else:
                    print("PARADA en byte %d: caracter %r dentro de un "
                          "numero (solo espacio/tabulador validos)" % (pos, contenido[pos]))
                    bits = None
                    break
                pos += 1
            if bits is None:
                break
            if pos >= n:
                print("PARADA en byte %d: numero sin salto de linea de cierre" % pos)
                break
            pos += 1                               # consume el LF de cierre
            valor = (1 if sign_ch == ' ' else -1) * int(bits, 2)
            pila.append(valor)
            pendiente = (contenido[inicio:pos - 1], sign_ch, bits, valor)

        elif c == '\t' and pos + 1 < n and contenido[pos + 1] == '\n':
            # IMP: Entrada/salida (tabulador + salto)
            pos += 2
            cmd = contenido[pos:pos + 2]
            if cmd != '  ':
                print("PARADA en byte %d: IMP de E/S con comando %r (%s) "
                      "-- solo 'output char' (espacio espacio) esta "
                      "implementado" % (pos, cmd, visible(cmd)))
                break
            pos += 2
            if not pila:
                print("PARADA en byte %d: output char con la pila vacia" % pos)
                break
            valor = pila.pop()
            car = chr(valor)
            salida.append(car)
            raw_push, sign_ch, bits, pval = pendiente
            trazas.append("%-14s push  %s = %3d  ->  %r" % (
                visible(raw_push), bits, pval, car))
            pendiente = None

        elif c == '\n' and pos + 2 < n and contenido[pos + 1:pos + 3] == '\n\n':
            # IMP: Control de flujo, comando END (salto salto) -- fin de programa
            pos += 3
            trazas.append("%-14s end   (fin de programa)" % visible('\n\n\n'))
            break

        else:
            resto = contenido[pos:pos + 4]
            print("PARADA en byte %d: IMP no soportado, empieza por %r (%s)"
                  " -- solo push, output-char y end estan implementados"
                  % (pos, resto, visible(resto)))
            break

    return trazas, ''.join(salida)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'v.png'

    keyword, contenido = lee_chunk_texto(path)
    espacios = contenido.count(' ')
    tabs = contenido.count('\t')
    saltos = contenido.count('\n')
    print("chunk tEXt en %s: keyword=%r, %d bytes de contenido" % (path, keyword, len(contenido)))
    print("  espacios=%d  tabuladores=%d  saltos=%d  (total=%d)\n" % (
        espacios, tabs, saltos, espacios + tabs + saltos))

    trazas, mensaje = decodifica(contenido)
    for linea in trazas:
        print(linea)

    print("\nsalida completa: %r" % mensaje)


if __name__ == '__main__':
    main()
