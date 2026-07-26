#!/usr/bin/env python3
"""En hackit6_part1_caption.png el '3' final de v1nTag3 queda pegado al borde
derecho del recorte. Ese borde lo pusimos NOSOTROS (crop col 530..1755). Si el
caption seguia mas a la derecha, nos comimos texto.

Aqui: localizar la banda de lineas del caption midiendo bordes verticales, y
renderizarla a ANCHURA COMPLETA 0..2011 a resolucion nativa."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import ndimage

W, LPF = 2011, 625
msg = np.load("msg_full.npy", mmap_mode="r")
NOTCH = [(160, 190), (192, 215)]


def frame(k):
    f = np.asarray(msg[k * LPF * W:(k + 1) * LPF * W], dtype=np.float64).reshape(LPF, W)
    F = np.fft.rfft(f, axis=1)
    for a, b in NOTCH:
        F[:, a:b + 1] = 0
    return np.fft.irfft(F, W, axis=1)


CAP = list(range(117, 132))
acc = None
for k in CAP:
    f = frame(k)
    acc = f if acc is None else acc + f
cap = acc / len(CAP)
print(f"media de {len(CAP)} frames del caption")

# el texto es brillante y de bordes duros: energia de gradiente horizontal por fila
g = np.abs(np.diff(cap, axis=1))
rowe = ndimage.uniform_filter1d(g.mean(axis=1), 9)
print("\nfilas con mas energia de borde (top 12):")
for r in np.argsort(rowe)[::-1][:12]:
    print(f"  linea {r:3d}: {rowe[r]:.5f}")
r_peak = int(np.argmax(rowe))
r0, r1 = max(0, r_peak - 45), min(LPF, r_peak + 45)
print(f"\nbanda del caption: lineas {r0}..{r1} (pico en {r_peak})")

band = cap[r0:r1, :]
# ¿hasta donde llega el texto por la derecha? energia de borde por columna
cole = ndimage.uniform_filter1d(np.abs(np.diff(band, axis=1)).mean(axis=0), 15)
base = np.median(cole)
hot = np.where(cole > base * 1.8)[0]
print(f"columnas con texto (borde > 1.8x mediana): "
      f"{hot.min() if hot.size else '-'}..{hot.max() if hot.size else '-'}  "
      f"(crop antiguo: 530..1755)")
print("\nperfil de borde por columna, paso 50:")
for a in range(0, W - 1, 50):
    b = min(a + 50, W - 1)
    v = cole[a:b].mean()
    bar = "#" * int(40 * v / max(cole.max(), 1e-9))
    mark = " FUERA" if (b <= 530 or a >= 1755) else ""
    print(f"  {a:4d}: {v:.5f} {bar}{mark}")


def show(ax, x, title, hp=None, pct=(1.5, 98.5)):
    x = x.astype(np.float64)
    if hp:
        x = x - ndimage.uniform_filter(x, size=hp)
    lo, hi = np.percentile(x, pct[0]), np.percentile(x, pct[1])
    ax.imshow(np.clip((x - lo) / max(hi - lo, 1e-12), 0, 1), cmap="gray",
              aspect="auto", interpolation="lanczos")
    ax.set_title(title, fontsize=10)


fig, axes = plt.subplots(4, 1, figsize=(26, 12))
show(axes[0], band, f"caption lineas {r0}-{r1}, ANCHURA COMPLETA 0-2011")
show(axes[1], band, "idem, realce local 21px", hp=21)
show(axes[2], band[:, 1600:], "zoom borde DERECHO (col 1600-2011)")
show(axes[3], band[:, :700], "zoom borde IZQUIERDO (col 0-700)")
for ax in axes[:2]:
    for x in (530, 1755):
        ax.axvline(x, color="r", lw=.8, ls="--")
plt.tight_layout(); plt.savefig("caption_edges.png", dpi=150); plt.close()
print("\n-> caption_edges.png")
