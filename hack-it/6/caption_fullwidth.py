#!/usr/bin/env python3
"""El caption siempre se leyo dentro del crop [20:600, 530:1755]. Si el texto se
extendia mas alla de la columna 1755 o por debajo de la 530, nos comimos parte.
Aqui se promedian los frames del caption a ANCHURA COMPLETA (0-2011) y altura
completa (0-625), y se resta la media de los frames vecinos SIN caption para
quitar la imagen de fondo y dejar solo lo que el autor sobreimprimio."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import ndimage

W, LPF = 2011, 625
msg = np.load("msg_full.npy", mmap_mode="r")
NOTCH = [(160, 190), (192, 215)]


def frame(k, notch=True):
    f = np.asarray(msg[k * LPF * W:(k + 1) * LPF * W], dtype=np.float64).reshape(LPF, W)
    if notch:
        F = np.fft.rfft(f, axis=1)
        for a, b in NOTCH:
            F[:, a:b + 1] = 0
        f = np.fft.irfft(F, W, axis=1)
    return f


def avg(rng):
    acc = None
    for k in rng:
        f = frame(k)
        acc = f if acc is None else acc + f
    return acc / len(rng)


# ventana del caption (medida por el consultor: 117-131) y vecinos limpios
CAP = range(117, 132)
BEF = range(95, 110)
AFT = range(140, 155)
print(f"caption: frames {CAP.start}-{CAP.stop-1}  ({len(CAP)} frames)")

cap = avg(CAP)
bg = (avg(BEF) + avg(AFT)) / 2
dif = cap - bg
print(f"contraste del residuo: std={dif.std():.5f}  rango={dif.min():+.4f}..{dif.max():+.4f}")

# donde esta la energia del residuo, por franjas: ¿se sale del crop?
print("\nenergia del residuo por franja de columnas (crop antiguo = 530..1755):")
for a in range(0, W, 100):
    b = min(a + 100, W)
    e = np.abs(dif[:, a:b]).mean()
    mark = "  <-- FUERA del crop" if (b <= 530 or a >= 1755) else ""
    print(f"  col {a:4d}-{b:4d}: |residuo| medio = {e:.5f}{mark}")
print("\nenergia del residuo por franja de lineas (crop antiguo = 20..600):")
for a in range(0, LPF, 40):
    b = min(a + 40, LPF)
    e = np.abs(dif[a:b, :]).mean()
    mark = "  <-- FUERA del crop" if (b <= 20 or a >= 600) else ""
    print(f"  lin {a:4d}-{b:4d}: |residuo| medio = {e:.5f}{mark}")


def show(ax, x, title, hp=None, pct=(1, 99)):
    x = x.astype(np.float64)
    if hp:
        x = x - ndimage.uniform_filter(x, size=hp)
    lo, hi = np.percentile(x, pct[0]), np.percentile(x, pct[1])
    ax.imshow(np.clip((x - lo) / max(hi - lo, 1e-12), 0, 1), cmap="gray",
              aspect="auto", interpolation="nearest")
    ax.set_title(title, fontsize=10)


fig, axes = plt.subplots(3, 1, figsize=(20, 16))
show(axes[0], cap, "MEDIA frames 117-131, FRAME COMPLETO 625x2011")
show(axes[1], dif, "RESIDUO (caption - vecinos): solo lo sobreimpreso, anchura completa")
show(axes[2], dif, "idem con realce local 25px", hp=25)
for ax in axes:
    for x in (530, 1755):
        ax.axvline(x, color="r", lw=.7, ls="--")
plt.tight_layout(); plt.savefig("caption_fullwidth.png", dpi=130); plt.close()

# recorte a la banda de lineas donde este el texto, a resolucion nativa
rowe = np.abs(dif).mean(axis=1)
r0 = max(0, int(np.argmax(ndimage.uniform_filter1d(rowe, 20))) - 60)
r1 = min(LPF, r0 + 140)
print(f"\nbanda de lineas con mas residuo: {r0}..{r1}")
fig, axes = plt.subplots(2, 1, figsize=(24, 8))
show(axes[0], dif[r0:r1, :], f"residuo lineas {r0}-{r1}, ANCHURA COMPLETA")
show(axes[1], dif[r0:r1, :], f"idem, realce local", hp=15)
plt.tight_layout(); plt.savefig("caption_fullwidth_zoom.png", dpi=160); plt.close()
print("-> caption_fullwidth.png / caption_fullwidth_zoom.png")
