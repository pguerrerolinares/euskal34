#!/usr/bin/env python3
"""Un caption que dure 1 solo frame es invisible a 25 fps para el ojo humano.
Detector transitorio: cada frame contra la MEDIANA de sus vecinos (que cancela
el movimiento del video), sobre frames YA LIMPIOS de intermodulacion.
Validacion obligatoria: el frame 125 tiene que salir el primero."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

W, LPF, NFR = 2011, 625, 250
msg = np.load("msg_full.npy", mmap_mode="r")
NL = msg.shape[0] // W
lines = np.lib.stride_tricks.as_strided(msg, (NL, W), (W*msg.itemsize, msg.itemsize))
NOTCH = [(160, 190), (192, 215)]
R = 3                                     # radio de la ventana de vecinos

def clean(k):
    f = np.asarray(lines[k*LPF:min((k+1)*LPF, NL)], dtype=np.float32)
    F = np.fft.rfft(f, axis=1)
    for a, b in NOTCH: F[:, a:b+1] = 0
    return np.fft.irfft(F, W, axis=1)[:624, 500:1600]   # zona activa de imagen

buf = {k: clean(k) for k in range(2*R+1)}
scores = []
for k in range(R, NFR-R-1):
    if k+R not in buf:
        buf[k+R] = clean(k+R); buf.pop(k-R-1, None)
    nb = np.stack([buf[j] for j in range(k-R, k+R+1) if j != k and j in buf])
    d = buf[k] - np.median(nb, axis=0)
    # un caption = filas contiguas con desviacion positiva fuerte (texto claro)
    rows = d.mean(axis=1)
    band = np.convolve(rows, np.ones(25)/25, mode="same")   # bloque de ~25 filas
    scores.append((k, float(band.max()), float(np.abs(d).mean())))

arr = sorted(scores, key=lambda x: -x[1])
print("ranking por transitorio positivo (texto claro que aparece y desaparece):")
for k, s, m in arr[:15]:
    mark = "   <== CAPTION CONOCIDO" if abs(k-125) <= 2 else ""
    print(f"  frame {k:3d}  pico={s:+.5f}  dif_media={m:.5f}{mark}")

pos = [i for i, (k, *_) in enumerate(arr) if abs(k-125) <= 2]
print(f"\nfotograma del caption conocido en posicion {pos[0]+1} de {len(arr)}"
      if pos else "\nel caption conocido NO aparece")
print("-> detector VALIDO" if pos and pos[0] < 5 else "-> detector NO valido")

ks = [k for k, *_ in arr[:8]]
fig, axes = plt.subplots(4, 2, figsize=(19, 14))
for ax, k in zip(axes.ravel(), ks):
    nb = np.stack([clean(j) for j in range(k-R, k+R+1) if j != k])
    d = clean(k) - np.median(nb, axis=0)
    lo, hi = np.percentile(d, .5), np.percentile(d, 99.5)
    ax.imshow(np.clip((d-lo)/max(hi-lo,1e-9), 0, 1), cmap="gray", aspect="auto")
    ax.set_title(f"frame {k} menos vecinos", fontsize=10); ax.axis("off")
plt.tight_layout(); plt.savefig("flash_candidates.png", dpi=90)
print("-> flash_candidates.png")
