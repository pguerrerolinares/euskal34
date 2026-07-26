#!/usr/bin/env python3
"""La zona con imagen ocupa ~40 us de los ~52 us activos de PAL. Sobran franjas
laterales (col ~330-530 y ~1755-1900) y las lineas 600-625, que el crop de siempre
descartaba. Ahi cabe texto.

Truco: la media de 249 frames baja el ruido /sqrt(249) = x15.8, asi que diferencias
de 0.005 (invisibles en un frame) se ven. Cada franja se normaliza POR SEPARADO,
porque su rango es 20x menor que el de la imagen y si no queda toda plana."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import ndimage

mean = np.load("geo_mean.npy").astype(np.float64)
std = np.load("geo_std.npy").astype(np.float64)
LPF, W = mean.shape


def show(ax, img, title, hp=None):
    x = img.astype(np.float64)
    if hp:
        x = x - ndimage.uniform_filter(x, size=hp)
    lo, hi = np.percentile(x, 0.5), np.percentile(x, 99.5)
    ax.imshow(np.clip((x - lo) / max(hi - lo, 1e-12), 0, 1), cmap="gray",
              aspect="auto", interpolation="nearest")
    ax.set_title(title, fontsize=10)


ZONAS = [
    ("sync 0-140", 0, 140, 0, LPF),
    ("blanking A 140-330", 140, 330, 0, LPF),
    ("blanking B / lienzo izq 330-540", 330, 540, 0, LPF),
    ("lienzo der 1740-2011", 1740, 2011, 0, LPF),
]

fig, axes = plt.subplots(len(ZONAS), 2, figsize=(16, 4 * len(ZONAS)))
for i, (name, c0, c1, r0, r1) in enumerate(ZONAS):
    show(axes[i][0], mean[r0:r1, c0:c1], f"MEDIA {name}")
    show(axes[i][1], mean[r0:r1, c0:c1], f"MEDIA {name} (realce local 31px)", hp=31)
    rng = mean[r0:r1, c0:c1]
    print(f"{name:34s} min={rng.min():+.4f} max={rng.max():+.4f} "
          f"rango={rng.max()-rng.min():.4f} std_espacial={rng.std():.5f}")
plt.tight_layout(); plt.savefig("margins_zonas.png", dpi=120); plt.close()

# franja inferior (lineas 595-625), toda la anchura
fig, axes = plt.subplots(3, 1, figsize=(20, 9))
show(axes[0], mean[595:LPF, :], "MEDIA lineas 595-625, anchura completa")
show(axes[1], mean[595:LPF, :], "idem, realce local", hp=15)
show(axes[2], std[595:LPF, :], "STD lineas 595-625")
plt.tight_layout(); plt.savefig("margins_bottom.png", dpi=130); plt.close()

# franja superior 0-25
fig, axes = plt.subplots(3, 1, figsize=(20, 9))
show(axes[0], mean[0:28, :], "MEDIA lineas 0-28, anchura completa")
show(axes[1], mean[0:28, :], "idem, realce local", hp=15)
show(axes[2], std[0:28, :], "STD lineas 0-28")
plt.tight_layout(); plt.savefig("margins_top.png", dpi=130); plt.close()

# y el frame entero con realce, para ver de golpe si algo salta fuera del crop
fig, ax = plt.subplots(figsize=(22, 8))
show(ax, mean, "MEDIA de 249 frames, FRAME COMPLETO, realce local 41px", hp=41)
for x in (530, 1755):
    ax.axvline(x, color="r", lw=.7, ls="--")
plt.tight_layout(); plt.savefig("margins_full.png", dpi=130); plt.close()
print("\n-> margins_zonas.png / margins_bottom.png / margins_top.png / margins_full.png")
