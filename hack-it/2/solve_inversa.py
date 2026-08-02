#!/usr/bin/env python3
"""
solve_inversa.py - el mismo reto por el despeje literal de la formula: m = p / v.

  python3 solve_inversa.py      # imprime el bitmap y deja m_inversa.png

El titulo del reto es Physics -> p = m*v, el momento lineal. Despejar esa
ecuacion, sin mas astucia, es:

    m = p / v        <->        M = P @ pinv(V)

con P y V de 256x768 (256 filas de 768 componentes, igual que en solve.py) y
M la tabla 256x256 que el HTML anunciaba como m.png. Esta version escribe la
formula tal cual la dicta el reto -- "p entre v", no "v entre p" -- y pinv(V)
le pide a numpy justo eso: la M que reproduce P a partir de V. V tiene rango
256 y 768 columnas, asi que la solucion es exacta; no hay portadora que
cancelar ni umbral que ajustar a ojo.

  La formula p = m*v es el gancho del enunciado -- la que te lleva a hacer
  esta operacion y de donde sale la contrasena --, pero no se sostiene pixel
  a pixel: p no tiene ni un valor negativo (0 de 196608) y v si (88368, un
  44.95%). Con m > 0 constante eso es imposible. Lo que M reconstruye de
  verdad es otra cosa: cumple M @ V = Q, asi que sus unidades son
  posicion/velocidad, o sea TIEMPO, no masa. La diagonal sale 10.2327 y es el
  tiempo de Hubble del universo de juguete del reto, 1/H (el mismo H que en
  solve.py, o que en la version vieja de este mismo fichero, sale 0.0996 al
  despejar "v entre p": 1/10.2327 = 0.09773, la constante 0.1 de la ley
  v = 0.1*q del WRITEUP, con el bug de eje de la columna metido dentro, que
  es por lo que no da 10.00 redondo).

  El mensaje aparece en casillas de valor ALTO, no bajo: las letras quedan en
  claro sobre fondo oscuro, asi que el umbral de deteccion va en +3.5 sigma
  (en solve.py y en la version vieja de este fichero iba en -3.5, porque alli
  las letras quedaban en negativo). Verificado: 237 casillas sobre umbral en
  la ventana del texto, de 972, y el bitmap se lee: M4dF0rmUL4.

  Controles: en las filas de fondo (todo lo que no es ROWS), mismas columnas
  que la ventana, 0 falsos positivos de 5931. En las filas del texto,
  columnas fuera de la ventana, 19 de 8244 -- y de esas 19, 18 son la propia
  diagonal (las filas 105-113 y 144-152 quedan fuera de COLS, asi que su
  M[i,i] se cuela ahi tal cual -- 10.2327 en crudo, el tiempo de Hubble, pero
  ~126 sigmas del fondo, dos varas distintas para el mismo numero; solo 1
  celda es ruido de verdad). Nota sobre el control de fondo: aqui no se
  cancela la diagonal en ningun paso (ver diferencia con solve.py mas abajo),
  asi que las 9 filas de fondo que caen dentro del rango de COLS (los huecos
  114-117, 127-130, 140 entre bandas de texto) chocan con su propio M[i,i]
  al mirar las columnas de la ventana -- 9 celdas puntuales a 125-128 sigma
  que son el tiempo de Hubble, no ruido. El control las excluye de una en
  una por su mascara diagonal (fila==columna), no descartando las 9 filas
  enteras: eso conservaria las otras 234 celdas de esas mismas filas
  (5940 - 9 = 5931) en vez de tirar 243 celdas de control por 9 valores
  identificados. Medir sobre la maxima poblacion valida, no sobre la que da
  el numero comodo, es justo el tema de este writeup.

  La cuantizacion (v_min=-0.2, v_max=0.2, el chunk oculto en v.png) SI
  importa aqui: sin desnormalizar, con los enteros crudos de 16 bits, el
  mensaje tambien se lee (219 casillas, verificado), pero la diagonal sale
  3.9410 en vez de 10.2327. A diferencia de solve.py, donde el -0.2 es
  cosmetico porque proyecta() centra cada fila y el offset se cancela solo,
  aqui no hay centrado: la desnormalizacion completa es lo que convierte la
  diagonal en un tiempo interpretable (el de Hubble, 1/0.1) en vez de un
  escalar que depende de la escala arbitraria de 16 bits.

Diferencia con solve.py (el atajo): alli se multiplica v por la TRANSPUESTA
de q en vez de por su inversa -- preguntarle a cada fila de q "cuanto de ti
hay aqui", una a una. Eso solo es exacto si las filas de q son ortogonales, y
no lo son (se parecen ~1/sqrt(768) = 0.036), asi que hace falta un paso extra
(restar alpha*q) para cancelar el derrame antes de la segunda proyeccion.
Aqui, al pedir la inversa de verdad, ese derrame no existe: pinv ya devuelve
la M exacta y no hay paso de cancelacion que dar.

Mismo resultado, misma contrasena: M4dF0rmUL4.
"""
import numpy as np

from png16 import read16

BANDS = [range(105, 114), range(118, 127), range(131, 140), range(144, 153)]
ROWS = [i for b in BANDS for i in b]          # 36 filas = 4 lineas de 9 px
COLS = range(114, 141)                        # 27 columnas = 3 caracteres
THRESHOLD = 3.5                               # en sigmas -- aqui las letras salen en claro
ESPERADO = "M4dF0rmUL4"


def reconstruye_m():
    """m = p / v, el despeje literal: M = P @ pinv(V)."""
    q = read16('p.png').astype(np.float64) / 65535.0
    v = read16('v.png').astype(np.float64) / 65535.0 * 0.4 - 0.2

    Q = q.reshape(256, -1)                    # 256 filas x 768 componentes
    V = v.reshape(256, -1)
    M = Q @ np.linalg.pinv(V)                 # <- el despeje, entero: p entre v

    fuera = ~np.eye(256, dtype=bool)          # la diagonal es la fisica (1/H~10), no el mensaje
    return (M - M[fuera].mean()) / M[fuera].std(), np.diag(M).mean()


def main():
    m, alpha = reconstruye_m()
    print("M = P @ pinv(V)   ->", m.shape, "(el HTML anunciaba m.png de 256x256)")
    print("diagonal (la fisica del reto, es el tiempo de Hubble 1/H): %.6f\n" % alpha)

    glyph = m[np.ix_(ROWS, COLS)] > THRESHOLD
    for n in range(len(ROWS)):
        if n and n % 9 == 0:
            print()
        print(''.join('#' if x else '.' for x in glyph[n]))

    # Fondo = todo lo que no es ROWS (igual que en solve.py). Al no cancelar
    # la diagonal (ver docstring), las filas de fondo que caen dentro del
    # rango de COLS chocan con su propio M[i,i] al mirar esas columnas -- 9
    # celdas puntuales a 125-128 sigma que son el tiempo de Hubble, no ruido. Se excluyen
    # una a una por su mascara diagonal (fila==columna), no descartando las 9
    # filas enteras: eso mide sobre 5931 celdas en vez de tirar 243 por 9
    # valores identificados.
    fondo = [i for i in range(256) if i not in ROWS]
    fondo_cols = np.array(fondo)[:, None] != np.array(list(COLS))[None, :]
    fondo_sub = m[np.ix_(fondo, COLS)]
    print("\ncontrol (celdas sobre %.1f sigma):" % THRESHOLD)
    print("  ventana del texto          : %4d de %d" % (glyph.sum(), glyph.size))
    print("  esas filas, otras columnas : %4d de %d" % (
        (np.delete(m[ROWS], COLS, axis=1) > THRESHOLD).sum(), 36 * (256 - len(COLS))))
    print("  filas de fondo, mismas cols: %4d de %d  (excluida la diagonal, fisica no ruido)" % (
        (fondo_sub[fondo_cols] > THRESHOLD).sum(), fondo_cols.sum()))

    try:
        from PIL import Image
    except ImportError:
        return
    z = np.clip(m, 0, 6) / 6.0
    Image.fromarray((255 * z).astype(np.uint8)).save('m_inversa.png')
    print("\nm_inversa.png escrito (render real: letras claras sobre fondo oscuro) ->", ESPERADO)


if __name__ == '__main__':
    main()
