#!/usr/bin/env python3
"""
solve.py - saca la contrasena de hackit2, que esta DIBUJADA dentro de los datos.

  python3 solve.py            # imprime el bitmap y deja password.png

La contrasena no esta cifrada ni codificada: es un bitmap de 36x27 escrito en la
matriz de correlacion entre las filas del residuo de velocidades y las filas de
posiciones. Cuatro lineas de 9 pixeles de alto -- M4d / F0r / mUL / 4.

Por que no se ve mirando las imagenes: el autor sumo a 36 filas de `v` multiplos
minusculos de ciertas filas de `p`. Cada fila de `p` actua como portadora, y el
patron de que portadora se suma a que fila dibuja el texto. En el espacio de la
imagen esa senal esta repartida entre 65.536 valores y queda muy por debajo del
ruido; solo se concentra al proyectar contra las portadoras. Es esteganografia
por espectro ensanchado.

La huella que deja en el espacio de la imagen es un exceso de VARIANZA en esas 36
filas -- las "cuatro bandas de nueve filas" que el analisis original midio con tres
decimales y llamo ruido del generador. Estaban en el sitio exacto del texto.
"""
import numpy as np

from png16 import read16

BANDS = [range(105, 114), range(118, 127), range(131, 140), range(144, 153)]
ROWS = [i for b in BANDS for i in b]          # 36 filas = 4 lineas de 9 px
COLS = range(114, 141)                        # 27 columnas = 3 caracteres
THRESHOLD = -3.5                              # en sigmas; el dibujo aguanta de -3 a -5
ESPERADO = "M4dF0rmUL4"


def correlacion():
    """Matriz C[i,k] = parecido entre la fila i del residuo y la fila k de posiciones."""
    q = read16('p.png').astype(np.float64) / 65535.0
    v = read16('v.png').astype(np.float64) / 65535.0 * 0.4 - 0.2

    res = v - 0.1 * q                                    # quita la parte lineal en q

    A = q - q.mean(1, keepdims=True)                     # filas de p, centradas
    A = A.reshape(256, -1)
    A /= np.linalg.norm(A, axis=1, keepdims=True)        # ...y normalizadas
    B = (res - res.mean(1, keepdims=True)).reshape(256, -1)

    C = B @ A.T
    return C / C.std()                                   # en sigmas


def main():
    C = correlacion()
    glyph = C[np.ix_(ROWS, COLS)] < THRESHOLD

    for n in range(len(ROWS)):
        if n and n % 9 == 0:
            print()
        print(''.join('#' if x else '.' for x in glyph[n]))

    # Control: la senal esta SOLO en ese rectangulo. Sin esto, cualquier umbral
    # sobre ruido dibuja manchas y uno se las cree.
    fondo = [i for i in range(256) if i not in ROWS]
    dentro = (glyph).sum()
    fuera_cols = (np.delete(C[ROWS], COLS, axis=1) < THRESHOLD).sum()
    fuera_filas = (C[fondo][:, COLS] < THRESHOLD).sum()
    print("\ncontrol (celdas bajo %.1f sigma):" % THRESHOLD)
    print("  ventana del texto      : %4d de %d" % (dentro, glyph.size))
    print("  esas filas, otras cols : %4d de %d" % (fuera_cols, 36 * (256 - len(COLS))))
    print("  filas de fondo, mismas cols: %d de %d" % (fuera_filas, len(fondo) * len(COLS)))

    try:
        from PIL import Image
    except ImportError:
        return
    Image.fromarray((glyph * 255).astype(np.uint8)).resize(
        (len(COLS) * 16, len(ROWS) * 16), Image.NEAREST).save('password.png')
    print("\npassword.png escrito ->", ESPERADO)


if __name__ == '__main__':
    main()
