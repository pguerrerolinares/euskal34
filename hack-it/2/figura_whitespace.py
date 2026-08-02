#!/usr/bin/env python3
"""
figura_whitespace.py - genera whitespace.png, la figura de dos columnas del
post que ensena el programa Whitespace escondido en v.png.

  python3 figura_whitespace.py [destino.png]     # 'whitespace.png' si se omite

Corre desde este directorio (challenges/hackit2/): reutiliza whitespace.py sin
tocarlo -- importa lee_chunk_texto() y decodifica() de ahi, que a su vez leen
v.png con png16-style parsing manual de chunks. Nada de texto escrito a mano:
lo que se dibuja es exactamente lo que whitespace.py extrae y decodifica del
PNG real, caracter a caracter.

El concepto es el mismo que en la version anterior de esta figura (perdida,
sin script que la generara): dos columnas.

  LO QUE SE VE    -- la columna se queda vacia a proposito. Es literalmente
                     lo que ves si abres v.png con un editor de texto: nada,
                     solo espacios en blanco indistinguibles del vacio.

  LO QUE HAY DENTRO -- los mismos bytes, con cada caracter invisible pintado
                     como simbolo visible (espacio -> punto, tabulador ->
                     flecha roja, salto de linea -> el simbolo de retorno),
                     una fila por instruccion Whitespace: 27 pares push+output
                     (uno por caracter del mensaje) mas la instruccion final
                     de fin de programa. Es la salida real de
                     whitespace.decodifica(), no una reconstruccion a mano.

Abajo, el pie: la salida completa al ejecutar el programa.

A diferencia de la version anterior (que, segun se pudo comprobar, no tenia
generador y no reproducia todas las instrucciones), esta enseña las 27 mas la
de cierre -- 28 filas -- en vez de una muestra parcial: mas completa y mas
honesta, aunque no sea pixel a pixel la misma imagen.
"""
import sys

from PIL import Image, ImageDraw, ImageFont

from whitespace import lee_chunk_texto, decodifica, PUNTO, FLECHA, VUELTA

FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
FONT_BOLD_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
FONT_SIZE = 16
CHAR_W = 9.640625            # ancho de caracter monoespaciado a FONT_SIZE=16
LINE_H = 24

BG = (239, 234, 224)              # crema, igual que el resto de figuras del post
DIVISOR = (214, 207, 196)         # linea divisoria entre columnas y el pie
HEADER_GRIS = (150, 143, 132)     # titulo "LO QUE SE VE"
HEADER_ROJO = (193, 54, 42)       # titulo "LO QUE HAY DENTRO"
DOT_COLOR = (176, 169, 158)       # espacio -> punto
ARROW_COLOR = (193, 54, 42)       # tabulador -> flecha
RETURN_COLOR = (176, 110, 95)     # salto de linea -> simbolo de retorno (solo en la fila final)
TEXT_MUTED = (120, 112, 100)      # resto del texto de cada fila (push, bits, decimal, comilla, char)
TEXT_FUERTE = (28, 26, 24)        # pie de foto: la salida real

MARGEN = 30
COL_IZQ_X = MARGEN
COL_DER_X = 230


def color_de(caracter):
    if caracter == PUNTO:
        return DOT_COLOR
    if caracter == FLECHA:
        return ARROW_COLOR
    if caracter == VUELTA:
        return RETURN_COLOR
    return TEXT_MUTED


def dibuja_fila(draw, font, x, y, texto):
    """Dibuja una fila caracter a caracter, coloreando segun el simbolo."""
    cx = x
    for ch in texto:
        draw.text((cx, y), ch, font=font, fill=color_de(ch))
        cx += CHAR_W


def genera(path_v='v.png'):
    """Extrae y decodifica el chunk real de v.png (via whitespace.py, sin
    tocarlo) y devuelve la imagen final mas los datos usados."""
    _, contenido = lee_chunk_texto(path_v)
    trazas, mensaje = decodifica(contenido)

    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    font_bold = ImageFont.truetype(FONT_BOLD_PATH, FONT_SIZE)

    ancho_max = max(len(t) for t in trazas)
    ancho = int(COL_DER_X + ancho_max * CHAR_W + MARGEN)
    alto_contenido = len(trazas) * LINE_H
    y_header = MARGEN
    y_contenido = y_header + 40
    y_divisor_h = y_contenido + alto_contenido + 20
    y_pie = y_divisor_h + 20
    alto = int(y_pie + 70)

    img = Image.new('RGB', (ancho, alto), BG)
    draw = ImageDraw.Draw(img)

    draw.text((COL_IZQ_X, y_header), 'LO QUE SE VE', font=font_bold, fill=HEADER_GRIS)
    draw.text((COL_DER_X, y_header), 'LO QUE HAY DENTRO', font=font_bold, fill=HEADER_ROJO)
    # la columna izquierda se queda vacia a proposito -- ver docstring

    draw.line([(COL_DER_X - 20, y_header), (COL_DER_X - 20, y_divisor_h)], fill=DIVISOR, width=1)

    y = y_contenido
    for fila in trazas:
        dibuja_fila(draw, font, COL_DER_X, y, fila)
        y += LINE_H

    draw.line([(MARGEN, y_divisor_h), (ancho - MARGEN, y_divisor_h)], fill=DIVISOR, width=1)

    draw.text((MARGEN, y_pie), 'AL EJECUTARLO:', font=font, fill=HEADER_GRIS)
    draw.text((MARGEN, y_pie + LINE_H), mensaje, font=font_bold, fill=TEXT_FUERTE)

    return img, {'filas': len(trazas), 'mensaje': mensaje}


def main():
    destino = sys.argv[1] if len(sys.argv) > 1 else 'whitespace.png'

    img, info = genera()
    print('filas dibujadas (27 push+output + 1 fin de programa): %d' % info['filas'])
    print('mensaje decodificado: %r' % info['mensaje'])
    print('imagen final:', img.size, img.mode)

    img.save(destino)
    print('guardado en', destino)


if __name__ == '__main__':
    main()
