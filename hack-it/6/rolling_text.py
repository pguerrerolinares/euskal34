#!/usr/bin/env python3
"""HUECO REAL: todos los detectores de caption promediaban frames para reforzar lo
ESTATICO. Eso es justo lo que BORRA un texto en movimiento. Y 'roll' en video es
precisamente texto que rueda (credit roll). El detector se valido inyectando un
caption FIJO, asi que nunca se comprobo si veia uno que se desplaza.

Aqui: promediar en el MARCO MOVIL. Para cada velocidad (dy,dx) en px/frame se
desplaza cada frame -k*(dy,dx) antes de acumular; si existe texto rodando a esa
velocidad, se congela y se refuerza como lo hace uno estatico a velocidad 0.

Validacion obligatoria: se inyecta un texto sintetico que rueda a una velocidad
conocida y el barrido tiene que encontrarla."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import ndimage

W, LPF, NFR = 2011, 625, 249
Y0, Y1, X0, X1 = 20, 600, 530, 1755
SUB = 2                                   # submuestreo horizontal
NOTCH = [(160, 190), (192, 215)]
msg = np.load("msg_full.npy", mmap_mode="r")

print("cargando 250 frames en memoria...")
H = Y1 - Y0
Wd = len(range(X0, X1, SUB))
cube = np.empty((NFR, H, Wd), dtype=np.float32)
for k in range(NFR):
    f = np.asarray(msg[k*LPF*W:(k+1)*LPF*W], dtype=np.float64).reshape(LPF, W)
    F = np.fft.rfft(f, axis=1)
    for a, b in NOTCH:
        F[:, a:b+1] = 0
    f = np.fft.irfft(F, W, axis=1)[Y0:Y1, X0:X1:SUB]
    cube[k] = f - f.mean()
print(f"cubo {cube.shape}, {cube.nbytes/1e6:.0f} MB")


def textness(img):
    """cuanto 'parece texto': bordes verticales concentrados en pocas filas."""
    e = img - ndimage.uniform_filter(img, size=25)
    gx = np.abs(np.diff(e, axis=1)).mean(axis=1)
    return float(np.sort(gx)[::-1][:25].mean() / max(np.median(gx), 1e-9))


def scan(cube, tag):
    res = []
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            acc = np.zeros((H, Wd), dtype=np.float64)
            for k in range(NFR):
                acc += np.roll(np.roll(cube[k], -k*dy, axis=0), -k*dx, axis=1)
            res.append((textness(acc / NFR), dy, dx, acc / NFR))
    res.sort(key=lambda r: -r[0])
    print(f"\n== {tag}: top 8 velocidades de {len(res)} probadas ==")
    for s, dy, dx, _ in res[:8]:
        star = "  <== ESTATICO" if (dy, dx) == (0, 0) else ""
        print(f"   dy={dy:+3d} dx={dx:+3d} px/frame   score={s:6.3f}{star}")
    base = np.median([r[0] for r in res])
    print(f"   mediana del barrido = {base:.3f}")
    return res, base


# ---------- 1. validacion del instrumento -----------------------------------
print("\n### VALIDACION: inyecto texto que rueda a dy=+2, dx=-3 px/frame ###")
test = cube.copy()
amp = 3.0 * cube.std()
pat = np.zeros((14, 260), dtype=np.float32)     # bloque tipo texto
for c in range(0, 260, 18):
    pat[2:12, c:c+9] = 1.0
for k in range(NFR):
    y = 120 + 2*k
    x = 700 - 3*k
    y %= (H - 20); x %= (Wd - 300)
    test[k, y:y+14, x:x+260] += amp * pat
res_t, base_t = scan(test, "CONTROL con texto rodando a (dy=+2, dx=-3)")
top = res_t[0]
ok = (top[1], top[2]) == (2, -3)
print(f"   -> el barrido {'SI' if ok else 'NO'} recupera la velocidad inyectada "
      f"(gano dy={top[1]:+d} dx={top[2]:+d})")
print(f"   -> instrumento {'VALIDO' if ok else 'INVALIDO: no concluir nada del barrido real'}")

# ---------- 2. la senal real -------------------------------------------------
res, base = scan(cube, "SENAL REAL")
best = res[0]
print(f"\n   mejor velocidad real: dy={best[1]:+d} dx={best[2]:+d}, "
      f"score {best[0]:.3f} = {best[0]/base:.2f}x la mediana")
if best[0] / base < 1.25 or (best[1], best[2]) == (0, 0):
    print("   -> NO hay texto rodando: el maximo es el estatico o no destaca del fondo")
else:
    print("   -> CANDIDATO a texto rodando, revisar la imagen")

fig, axes = plt.subplots(4, 1, figsize=(19, 13))
for ax, (s, dy, dx, img) in zip(axes, res[:4]):
    e = img - ndimage.uniform_filter(img, size=25)
    lo, hi = np.percentile(e, 1), np.percentile(e, 99)
    ax.imshow(np.clip((e-lo)/max(hi-lo, 1e-9), 0, 1), cmap="gray", aspect="auto")
    ax.set_title(f"media en marco movil dy={dy:+d} dx={dx:+d} px/frame (score {s:.3f})",
                 fontsize=10)
    ax.axis("off")
plt.tight_layout(); plt.savefig("rolling_text.png", dpi=115)
print("-> rolling_text.png")
