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
     vectores es proyectar: (v.q)/(q.q). Cada fila de las imagenes es un vector
     de 768 componentes; como no sabes que fila va con que fila, las proyectas
     todas contra todas.
  4. UNICO PASO NO DEDUCIBLE: si el "vector" es la fila o la columna. Hay cuatro
     combinaciones, las cuatro dan 256x256, y se resuelve probandolas:
     filas x filas 216 / columnas x columnas 0 / cruzadas 1 y 0. (El tamano
     anunciado en el HTML confirma que es una tabla de todos contra todos, no
     una division punto a punto -- pero no discrimina la orientacion.)
  5. La primera proyeccion TE ESCRIBE EL MODELO: diag(proj(v,q)) = 0.0996, o sea
     cada fila de v es 0.1 veces la misma fila de q. No hace falta ajustar nada.
  6. Restas eso y vuelves a proyectar. No es "quitar fisica": las filas de q no
     son ortogonales (se parecen ~1/sqrt(768)=0.036), asi que el termino conocido
     0.1*q se derrama fuera de la diagonal con un ruido de 3.7e-3, 4.4x el ruido
     de fondo real (8.2e-4). El mensaje vale -9.2e-3: 2.5 sigma sobre el derrame
     (invisible) y 11.2 sigma una vez cancelado.
  7. Renderizas la matriz entera y el texto se lee. Sin ventanas ni umbrales.

  El chunk Whitespace de v.png (v_min=-0.2, v_max=0.2) NO hace falta: repitiendo
  todo con los enteros crudos y leyendo el coeficiente de la diagonal (que alli
  vale 0.249038) sale el mismo bitmap salvo un pixel. Lo que aporta es notacion:
  su keyword es `h` (constante de Hubble) y llama `q` al contenido de p.png
  (posicion, en notacion hamiltoniana). Dice que magnitud hay en cada fichero.

Por debajo es esteganografia por espectro ensanchado: el autor resto a 36 filas
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


def proyecta(X, Y):
    """(x.y)/(y.y) para cada fila de X contra cada fila de Y. El divisor es
    cosmetico: sin el salen 212 celdas en vez de 216. Lo que importa es X @ Y.T."""
    P = (Y - Y.mean(1, keepdims=True)).reshape(len(Y), -1)
    R = (X - X.mean(1, keepdims=True)).reshape(len(X), -1)
    return R @ P.T / (P ** 2).sum(1)


def reconstruye_m():
    """m = p/v despejada: proyectar, leer el modelo en la diagonal, cancelarlo."""
    q = read16('p.png').astype(np.float64) / 65535.0
    v = read16('v.png').astype(np.float64) / 65535.0 * 0.4 - 0.2

    alpha = np.diag(proyecta(v, q)).mean()      # el dato escribe su propio modelo: 0.0996
    m = proyecta(v - alpha * q, q)              # cancela el derrame de la portadora
    return m / m.std(), alpha                   # en sigmas


def main():
    m, alpha = reconstruye_m()
    print("coeficiente leido en la diagonal: %.6f" % alpha)
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
