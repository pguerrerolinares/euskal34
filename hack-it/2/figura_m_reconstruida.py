#!/usr/bin/env python3
"""
figura_m_reconstruida.py - genera la imagen del post (m-reconstruida.png):
el render real del despeje canonico de solve_inversa.py, con un retoque.

  python3 figura_m_reconstruida.py [destino.png]     # 'm-reconstruida.png' si se omite

Corre desde este directorio (challenges/hackit2/): importa reconstruye_m() de
solve_inversa.py sin tocarlo, y esa funcion necesita p.png y v.png en el
directorio de trabajo (los lee con read16(), rutas relativas).

ESTO NO ES EL RENDER CRUDO, es un retoque deliberado, y hay que decirlo alto:
la diagonal de M vale ~126 sigma (es el tiempo de Hubble del reto, 1/H, no el
mensaje) y si se dibuja tal cual tapa visualmente el texto -- una linea que
cruza la imagen de esquina a esquina y distrae de las cuatro palabras. Antes
de dibujar, las 256 celdas M[i,i] se sustituyen por la mediana del resto de
la tabla (fondo + texto, sin la diagonal): ese valor cae justo en el centro
del ruido de fondo, asi que la diagonal desaparece sin dejar ni rastro claro
ni oscuro, en vez de reventar a un extremo y dejar una linea negra donde antes
habia una blanca. El pie de foto del post tiene que decir esto explicitamente;
este script es la prueba reproducible de como se hizo.

El recorte de escala, [-3.5, 6.0] sigmas, es el mismo que se eligio para la
version CON diagonal: -3.5 es el minimo real del ruido de fondo (no aplasta
a negro ninguna celda), y 6.0 es donde el texto ya sale blanco solido y
legible sin que el fondo pierda su moteado. Probado contra 9, 12 y 20: a
partir de 12 el texto se ve gris apagado.

Salida: 768x768 RGB, escalado NEAREST x3 desde la matriz 256x256 (cada celda,
un bloque de 3x3 pixeles exactos, sin interpolar nada encima del antialiasing
real que ya trae el dato).
"""
import sys

import numpy as np
from PIL import Image

from solve_inversa import reconstruye_m

LOW, HIGH = -3.5, 6.0


def genera():
    """Devuelve la imagen PIL final (768x768 RGB) y los numeros de control."""
    m, alpha = reconstruye_m()
    fuera = ~np.eye(256, dtype=bool)

    relleno = np.median(m[fuera])   # mediana del resto de la tabla, sin la diagonal
    m_sin_diag = m.copy()
    np.fill_diagonal(m_sin_diag, relleno)

    z = np.clip((m_sin_diag - LOW) / (HIGH - LOW), 0, 1)
    img = Image.fromarray((255 * z).astype(np.uint8), mode='L').convert('RGB')
    img = img.resize((768, 768), Image.NEAREST)

    info = {
        'diag_original_media': np.diag(m).mean(),
        'diag_original_min': np.diag(m).min(),
        'diag_original_max': np.diag(m).max(),
        'relleno': relleno,
        'fuera_media': m[fuera].mean(),
        'fuera_std': m[fuera].std(),
    }
    return img, info


def main():
    destino = sys.argv[1] if len(sys.argv) > 1 else 'm-reconstruida.png'

    img, info = genera()
    print('diagonal original (sigma): media=%.4f min=%.4f max=%.4f' % (
        info['diag_original_media'], info['diag_original_min'], info['diag_original_max']))
    print('relleno usado para la diagonal (mediana de m[fuera]): %.6f' % info['relleno'])
    print('  (referencia: media de m[fuera] = %.6f, std = %.6f)' % (
        info['fuera_media'], info['fuera_std']))
    print('imagen final:', img.size, img.mode)

    img.save(destino)
    print('guardado en', destino)


if __name__ == '__main__':
    main()
