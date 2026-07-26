"""hackit2 - modelo completo verificado de p.png / v.png.

Uso:  python3 model.py
Deja en memoria (y por pantalla) el payload real: a_i (256) y sigma_i (36).

Modelo exacto (residuo cero, ver comprobaciones al final):

    q[i,j,c] ~ U(0,1) iid
    v[i,j,c] = 0.1*q[i,j,c] - 0.09*<q>_col[j,c] + n[i,j,c]

    = 0.1 * ( q - 0.9*q.mean(axis=0) )

El termino -0.09*<q>_col es un bug de broadcasting del autor: queria
0.45 = 0.9*q.mean() (escalar) y le salio 0.9*q.mean(axis=0) (medias por
columna). O sea: la fisica pretendida es un flujo de Hubble puro
v = 0.1*(q - 0.45), Big Bang en t = -10.

n es gaussiano isotropo iid salvo dos modulaciones POR FILA:
    - media  a_i  (las 256 filas llevan senal, ~2.9 sigma en el fondo)
    - sigma_i     (plano salvo 36 filas: 4 bandas de 9, pitch 13)
"""
import numpy as np

from png16 import read16

BANDS = [range(105, 114), range(118, 127), range(131, 140), range(144, 153)]
BAND_ROWS = [i for b in BANDS for i in b]
BG_ROWS = [i for i in range(256) if i not in BAND_ROWS]


def load():
    q = read16('p.png').astype(np.float64) / 65535.0
    v = read16('v.png').astype(np.float64) / 65535.0 * 0.4 - 0.2
    return q, v


def residual(q, v):
    colmean = np.broadcast_to(q.mean(0)[None, :, :], q.shape)
    r = v - (0.1 * q - 0.09 * colmean)
    return r - r.mean()


def payload(r):
    se = r.std() / np.sqrt(256)
    a = (r.mean(1) / se).mean(1) * np.sqrt(3)          # media por fila, en sigmas
    s = np.array([r[i].std() for i in range(256)])
    exc = (s / np.median(s[BG_ROWS])) ** 2 - 1.0       # exceso de varianza por fila
    err = (1 + exc) * np.sqrt(2 / 768)
    return a, exc, err


if __name__ == '__main__':
    q, v = load()
    r = residual(q, v)
    a, exc, err = payload(r)

    print("residuo sigma = %.6f" % r.std())
    print()
    print("36 valores de banda (exceso de varianza +- error):")
    for b, lab in zip(BANDS, "ABCD"):
        print("  %s: %s" % (lab, " ".join("%.2f+-%.2f" % (exc[i], err[i]) for i in b)))
    print()
    print("pesos totales por banda, normalizados a la banda D:")
    tot = np.array([exc[list(b)].sum() for b in BANDS])
    e = np.array([np.sqrt((err[list(b)] ** 2).sum()) for b in BANDS])
    ratio = tot / tot[3]
    er = ratio * np.sqrt((e / tot) ** 2 + (e[3] / tot[3]) ** 2)
    print("  " + "  ".join("%.2f+-%.2f" % (x, y) for x, y in zip(ratio, er)))
    print()
    print("media por fila a_i (sigmas), bandas:")
    for b, lab in zip(BANDS, "ABCD"):
        print("  %s: %s" % (lab, " ".join("%+6.1f" % a[i] for i in b)))

    # --- comprobaciones de que no queda nada mas ---
    print()
    print("comprobaciones de residuo cero:")
    bj = r.mean(0) / (r.std() / np.sqrt(256))
    print("  DC por columna: std %.3f (1.0 = ruido) -> absorbido por el modelo" % bj.std())
    m = r.mean(2)
    for k in (4, 8, 16):
        n = 256 // k
        blk = m.reshape(n, k, n, k).mean(axis=(1, 3))
        # quitando DC de fila y columna antes
        d = r.copy()
        for c in range(3):
            x = d[:, :, c]
            d[:, :, c] = x - x.mean(1, keepdims=True) - x.mean(0, keepdims=True) + x.mean()
        md = d.mean(2)
        blkd = md.reshape(n, k, n, k).mean(axis=(1, 3))
        print("  bloque %2d tras quitar DC fila+col: std/esperado %.3f" % (
            k, blkd.std() / (d.std() / np.sqrt(k * k * 3))))
