#!/usr/bin/env python3
"""Todos nuestros renders recortan [20:600, 530:1755] de 625x2011. Ese crop es una
SUPOSICION: 1225 columnas cuando la zona activa PAL deberia rondar 1634. Si el autor
escribio algo fuera del area segura de TV (bordes laterales, VBI, ultimas lineas),
lo hemos estado tirando sin mirar.

Aqui no se asume geometria: se mide, para cada posicion (linea, columna) del frame,
la MEDIA y la DESVIACION a lo largo de los 250 frames. Donde hay senal viva, hay
varianza. Donde hay algo estatico escrito, la media lo ensena."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

W, LPF, NFR = 2011, 625, 250
msg = np.load("msg_full.npy", mmap_mode="r")
NL = msg.shape[0] // W
print(f"{msg.shape[0]} muestras -> {NL} lineas -> {NL/LPF:.2f} frames")

acc = np.zeros((LPF, W), dtype=np.float64)
acc2 = np.zeros((LPF, W), dtype=np.float64)
n = 0
for k in range(NFR):
    a, b = k * LPF, (k + 1) * LPF
    if b * W > msg.shape[0]:
        break
    f = np.asarray(msg[a * W:b * W], dtype=np.float64).reshape(LPF, W)
    acc += f
    acc2 += f * f
    n += 1
mean = acc / n
std = np.sqrt(np.maximum(acc2 / n - mean ** 2, 0))
print(f"promediados {n} frames")
np.save("geo_mean.npy", mean.astype(np.float32))
np.save("geo_std.npy", std.astype(np.float32))

# --- perfiles: donde empieza y acaba de verdad la zona activa ---------------
col_std = std.mean(axis=0)
row_std = std.mean(axis=1)
col_mean = mean.mean(axis=0)

thr = 0.15 * col_std.max()
active_cols = np.where(col_std > thr)[0]
thr_r = 0.15 * row_std.max()
active_rows = np.where(row_std > thr_r)[0]
print(f"\ncolumnas con actividad >15% del max: {active_cols.min()}..{active_cols.max()}"
      f"  (crop usado: 530..1755)")
print(f"lineas   con actividad >15% del max: {active_rows.min()}..{active_rows.max()}"
      f"  (crop usado: 20..600)")

print("\nactividad media por franja de columnas (fuera del crop = sospechoso):")
for a in range(0, W, 100):
    b = min(a + 100, W)
    tag = "  <-- FUERA del crop" if (b <= 530 or a >= 1755) else ""
    print(f"  col {a:4d}-{b:4d}: std={col_std[a:b].mean():8.4f} "
          f"mean={col_mean[a:b].mean():9.4f}{tag}")

print("\nactividad media por franja de lineas:")
for a in range(0, LPF, 25):
    b = min(a + 25, LPF)
    tag = "  <-- FUERA del crop" if (b <= 20 or a >= 600) else ""
    print(f"  lin {a:4d}-{b:4d}: std={row_std[a:b].mean():8.4f}{tag}")


def norm(x, lo=1, hi=99):
    a, b = np.percentile(x, lo), np.percentile(x, hi)
    return np.clip((x - a) / max(b - a, 1e-9), 0, 1)


fig, axes = plt.subplots(3, 1, figsize=(18, 15))
axes[0].imshow(norm(mean), cmap="gray", aspect="auto")
axes[0].set_title("MEDIA de los 250 frames, FRAME COMPLETO 625x2011 (sin crop). "
                  "Lo estatico se refuerza")
axes[1].imshow(norm(std), cmap="gray", aspect="auto")
axes[1].set_title("DESVIACION a lo largo de los 250 frames. Negro = zona muerta")
for x in (530, 1755):
    for ax in axes[:2]:
        ax.axvline(x, color="r", lw=.8, ls="--")
for y in (20, 600):
    for ax in axes[:2]:
        ax.axhline(y, color="r", lw=.8, ls="--")
axes[2].plot(col_std, lw=.7); axes[2].axvline(530, color="r", ls="--")
axes[2].axvline(1755, color="r", ls="--")
axes[2].set_title("perfil de actividad por columna (rojo = limites del crop que usabamos)")
axes[2].set_xlabel("columna (muestra dentro de la linea)"); axes[2].grid(alpha=.3)
plt.tight_layout(); plt.savefig("geometry_map.png", dpi=110)
print("\n-> geometry_map.png  (+ geo_mean.npy / geo_std.npy)")
