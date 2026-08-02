#!/usr/bin/env python3
"""
figura_password_bitmap.py - genera password-bitmap.png, la ampliacion en
tinta sobre papel de las cuatro lineas de la contrasena.

  python3 figura_password_bitmap.py [destino.png]     # 'password-bitmap.png' si se omite

Corre desde este directorio (challenges/hackit2/): reutiliza solve.py sin
tocarlo -- importa BANDS, COLS, THRESHOLD y reconstruye_m() de ahi en vez de
copiar los numeros. El bitmap no se dibuja a mano: sale de umbralizar la
matriz reconstruida exactamente como hace solve.py para su propio password.png,
con el mismo criterio (`m < THRESHOLD`, letras en negativo).

OJO, no confundir con password.png (el que ya escribe solve.py): ese es un
escalado x16 en blanco y negro puro de las 36 filas seguidas, seco y sin
espacio entre lineas -- pensado para comprobar el glifo, no para publicar.
Esta figura es otra cosa: las mismas 36 filas, pero separadas en sus 4 bandas
(una por linea de texto, BANDS lo dice) con hueco entre ellas para que se
lean como cuatro trozos, en tinta oscura sobre fondo papel (la paleta crema
del resto de figuras del post) y con el pixel bien marcado -- NEAREST, sin
antialiasing, cada celda de la matriz como un bloque cuadrado nitido.
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

from solve import BANDS, COLS, THRESHOLD, reconstruye_m

PIXEL = 16          # lado de cada celda de la matriz, en pixeles de salida
GAP_LINEAS = 32      # hueco vertical entre bandas (lineas de texto)
MARGEN = 24

BG = (239, 234, 224)     # crema, la misma paleta que whitespace.png y el resto del post
TINTA = (28, 26, 24)     # casi negro, igual que el texto fuerte de las otras figuras


def genera():
    """Umbraliza la matriz reconstruida (solve.py, sin tocarlo) y dibuja las
    4 bandas por separado, con hueco entre ellas. Devuelve la imagen y el
    numero de celdas encendidas por banda, para poder verificarlo."""
    m, alpha = reconstruye_m()
    cols = list(COLS)

    anchura = MARGEN * 2 + len(cols) * PIXEL
    altura_bandas = sum(len(b) for b in BANDS) * PIXEL
    altura = MARGEN * 2 + altura_bandas + GAP_LINEAS * (len(BANDS) - 1)

    img = Image.new('RGB', (anchura, altura), BG)
    draw = ImageDraw.Draw(img)

    celdas_por_banda = []
    y = MARGEN
    for banda in BANDS:
        filas = list(banda)
        glyph = m[np.ix_(filas, cols)] < THRESHOLD     # mismo criterio que solve.py
        celdas_por_banda.append(int(glyph.sum()))
        for i, _fila in enumerate(filas):
            for j, _col in enumerate(cols):
                if glyph[i, j]:
                    x0 = MARGEN + j * PIXEL
                    y0 = y + i * PIXEL
                    draw.rectangle([x0, y0, x0 + PIXEL - 1, y0 + PIXEL - 1], fill=TINTA)
        y += len(filas) * PIXEL + GAP_LINEAS

    return img, {'alpha': alpha, 'celdas_por_banda': celdas_por_banda}


def main():
    destino = sys.argv[1] if len(sys.argv) > 1 else 'password-bitmap.png'

    img, info = genera()
    print('coeficiente leido en la diagonal: %.6f' % info['alpha'])
    print('celdas encendidas por banda (< %.1f sigma):' % THRESHOLD, info['celdas_por_banda'])
    print('imagen final:', img.size, img.mode)

    img.save(destino)
    print('guardado en', destino)


if __name__ == '__main__':
    main()
