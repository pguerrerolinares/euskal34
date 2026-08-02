#!/usr/bin/env python3
"""
solve_inversa.py - el mismo reto por el camino canonico: m = p * v^-1.

  python3 solve_inversa.py      # imprime el bitmap y deja m_inversa.png

Es la version que se conto en la charla post-evento, y para leerla no hace falta
entender ninguna astucia: se escribe la ecuacion y se despeja.

  Cada fila i de v es una combinacion lineal de las filas de q:

      v[i] = suma_j  m[i,j] * q[j]        <->        V = M @ Q

  con V y Q de 256x768 (256 filas de 768 componentes) y M la tabla 256x256 de
  coeficientes -- el m.png que el HTML anunciaba. Despejar M es una linea:

      M = V @ pinv(Q)

  Q tiene rango 256 y 768 columnas, asi que el sistema tiene solucion exacta:
  pinv le pide a numpy justo eso, "la M que reproduce V". No hay modelo que
  ajustar, ni portadora que cancelar, ni umbral que elegir. La diagonal sale
  0.0996 (la fisica del reto: cada fila de v es 0.1 veces la suya de q) y el
  mensaje esta fuera de la diagonal, ya limpio.

Aqui la cuantizacion (v_min=-0.2, v_max=0.2) SI hace falta -- al reves que en
solve.py, donde daba exactamente igual. No por la escala (el 0.4 sigue siendo
cosmetico) sino por el OFFSET: restar 0.2 es lo que deja la media de v en cero.
El atajo centra cada fila antes de proyectar, asi que se lo fabrica solo; aqui no
hay centrado, y si dejas el DC dentro, pinv tiene que reproducirlo con
combinaciones de filas de q y eso mete varianza en M. Medido: con el -0.2, la
señal esta a 5.8 sigma (203 celdas); sin el, a 3.8 (124 celdas, aun legible pero
degradado). Centrar las filas a mano lo arregla igual de bien (201 celdas).

Diferencia con solve.py (el atajo): alli se multiplica por la TRANSPUESTA en vez
de por la inversa -- preguntarle a cada fila de q "cuanto de ti hay aqui", una a
una. Eso solo es exacto si las filas de q son ortogonales, y no lo son (se
parecen ~1/sqrt(768) = 0.036). Ese 3.6% de parecido hace que la diagonal, que
vale 10 veces el mensaje, se derrame por toda la tabla y lo tape; por eso el
atajo necesita el paso extra de restar alpha*q antes de la segunda proyeccion.
La inversa descuenta ese parecido por construccion y se ahorra el paso.

Mismo resultado, misma contrasena: M4dF0rmUL4.
"""
import numpy as np

from png16 import read16

BANDS = [range(105, 114), range(118, 127), range(131, 140), range(144, 153)]
ROWS = [i for b in BANDS for i in b]          # 36 filas = 4 lineas de 9 px
COLS = range(114, 141)                        # 27 columnas = 3 caracteres
THRESHOLD = -3.5                              # en sigmas
ESPERADO = "M4dF0rmUL4"


def reconstruye_m():
    """m = p / v, despejada tal cual: M = V @ pinv(Q)."""
    q = read16('p.png').astype(np.float64) / 65535.0
    v = read16('v.png').astype(np.float64) / 65535.0 * 0.4 - 0.2

    Q = q.reshape(256, -1)                    # 256 filas x 768 componentes
    V = v.reshape(256, -1)
    M = V @ np.linalg.pinv(Q)                 # <- el despeje, entero

    fuera = ~np.eye(256, dtype=bool)          # la diagonal es la fisica, no el mensaje
    return (M - M[fuera].mean()) / M[fuera].std(), np.diag(M).mean()


def main():
    m, alpha = reconstruye_m()
    print("M = V @ pinv(Q)   ->", m.shape, "(el HTML anunciaba m.png de 256x256)")
    print("diagonal (la fisica del reto): %.6f\n" % alpha)

    glyph = m[np.ix_(ROWS, COLS)] < THRESHOLD
    for n in range(len(ROWS)):
        if n and n % 9 == 0:
            print()
        print(''.join('#' if x else '.' for x in glyph[n]))

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
    Image.fromarray((255 * (1 - z)).astype(np.uint8)).save('m_inversa.png')
    print("\nm_inversa.png escrito ->", ESPERADO)


if __name__ == '__main__':
    main()
