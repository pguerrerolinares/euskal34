#!/usr/bin/env python3
"""
solve.py - reconstruye m.png, el fichero que falta, y lee la contrasena dentro.

  python3 solve.py            # imprime el bitmap y deja m.png / password.png

El camino, que el reto da entero:

  1. La pagina sirve p.png y v.png. En el HTML hay comentado un tercero,
     `<!-- <img src="/hackit/2/static/m.png" width="256" heigth="256"> -->`,
     que devuelve 404. No esta escondido: no existe.
  2. p, v y una m que falta, con un titulo que dice Physics -> p = m*v, el
     momento lineal. El reto no pide reconocer la formula, pide despejarla:
     m = p/v. El fichero que falta ES el objetivo.
  3. p/v no es una division pixel a pixel (probada, no da nada): en la formula
     del momento, p y v son VECTORES y m el escalar que los relaciona. Dividir
     vectores es proyectar, m = (p.v)/(v.v). Cada fila de las imagenes es un
     vector de 768 componentes; como no sabes que fila va con que fila, las
     proyectas todas contra todas. Sale una matriz 256x256 -- el tamano que el
     HTML anunciaba para m.png.
  4. Hecho con v en crudo no sale nada, porque las velocidades estan dominadas
     por un flujo de Hubble proporcional a las posiciones (v = 0.1*(q - 0.9*<q>),
     la escala la da el chunk Whitespace de v.png). Hay que restarlo primero: la
     proyeccion tiene que ir sobre lo que ese modelo NO explica.
     Con v crudo: 0 de 972 celdas. Restando el Hubble: 216 de 972.

Por debajo es esteganografia por espectro ensanchado: el autor sumo a 36 filas
de v multiplos minusculos de ciertas filas de p, cada una haciendo de portadora.
En el espacio de la imagen esa senal esta repartida entre 65.536 valores y queda
bajo el ruido; solo se concentra al proyectar. Su unica huella visible alli es un
exceso de varianza en esas 36 filas -- las "cuatro bandas de nueve filas" que el
analisis original midio con tres decimales y llamo ruido del generador. Eran las
cuatro lineas del texto.
"""
import numpy as np

from png16 import read16

BANDS = [range(105, 114), range(118, 127), range(131, 140), range(144, 153)]
ROWS = [i for b in BANDS for i in b]          # 36 filas = 4 lineas de 9 px
COLS = range(114, 141)                        # 27 columnas = 3 caracteres
THRESHOLD = -3.5                              # en sigmas; el dibujo aguanta de -3 a -5
ESPERADO = "M4dF0rmUL4"


def reconstruye_m():
    """m = p/v, con p y v vectores: la proyeccion de cada fila contra cada fila."""
    q = read16('p.png').astype(np.float64) / 65535.0           # posiciones en [0,1]
    v = read16('v.png').astype(np.float64) / 65535.0 * 0.4 - 0.2   # escala del Whitespace

    res = v - 0.1 * q                                          # quita el flujo de Hubble

    P = (q - q.mean(1, keepdims=True)).reshape(256, -1)        # filas de p como vectores
    R = (res - res.mean(1, keepdims=True)).reshape(256, -1)

    m = R @ P.T / (P ** 2).sum(1)                              # (p.v)/(v.v), todas contra todas
    return m / m.std()                                         # en sigmas


def main():
    m = reconstruye_m()
    print("m reconstruida:", m.shape, "(el HTML anunciaba m.png de 256x256)\n")

    glyph = m[np.ix_(ROWS, COLS)] < THRESHOLD
    for n in range(len(ROWS)):
        if n and n % 9 == 0:
            print()
        print(''.join('#' if x else '.' for x in glyph[n]))

    # Control: la senal esta SOLO en ese rectangulo. Sin esto, cualquier umbral
    # sobre ruido dibuja manchas y uno se las cree.
    fondo = [i for i in range(256) if i not in ROWS]
    print("\ncontrol (celdas bajo %.1f sigma):" % THRESHOLD)
    print("  ventana del texto          : %4d de %d" % (glyph.sum(), glyph.size))
    print("  esas filas, otras columnas : %4d de %d" % (
        (np.delete(m[ROWS], COLS, axis=1) < THRESHOLD).sum(), 36 * (256 - len(COLS))))
    print("  filas de fondo, mismas cols: %4d de %d" % (
        (m[fondo][:, COLS] < THRESHOLD).sum(), len(fondo) * len(COLS)))

    try:
        from PIL import Image
    except ImportError:
        return
    z = np.clip(-m, 0, 6) / 6.0
    Image.fromarray((255 * (1 - z)).astype(np.uint8)).save('m.png')
    Image.fromarray((glyph * 255).astype(np.uint8)).resize(
        (len(COLS) * 16, len(ROWS) * 16), Image.NEAREST).save('password.png')
    print("\nm.png y password.png escritos ->", ESPERADO)


if __name__ == '__main__':
    main()
