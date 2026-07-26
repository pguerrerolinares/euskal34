#!/usr/bin/env python3
"""Busqueda de captions sobre los frames YA LIMPIOS de intermodulacion.
Detector validado: si no pone el frame 125 (caption conocido) arriba, no vale."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

W, LPF, NFR = 2011, 625, 250
msg = np.load("msg_full.npy", mmap_mode="r")
NL = msg.shape[0] // W
lines = np.lib.stride_tricks.as_strided(msg, (NL, W), (W*msg.itemsize, msg.itemsize))
NOTCH = [(160, 190), (192, 215)]

def clean_frame(k):
    f = np.asarray(lines[k*LPF:min((k+1)*LPF, NL)], dtype=np.float32)
    F = np.fft.rfft(f, axis=1)
    for a, b in NOTCH:
        F[:, a:b+1] = 0
    return np.fft.irfft(F, W, axis=1)[:, 300:]

scores = []
for k in range(NFR):
    f = clean_frame(k)
    if f.shape[0] < 400: continue
    band = f[150:450]                       # banda central, donde van los captions
    # texto claro = cola alta de brillo muy por encima del cuerpo de la imagen
    s = (np.percentile(band, 99.7) - np.median(band)) / max(band.std(), 1e-9)
    # y concentrado en pocas filas
    rows = np.percentile(band, 99.7, axis=1) - np.median(band)
    conc = np.sort(rows)[::-1][:60].mean() / max(np.median(np.abs(rows)), 1e-9)
    scores.append((k, s, conc, s*conc))

scores.sort(key=lambda x: -x[3])
print("ranking (score combinado):")
for k, s, c, tot in scores[:20]:
    mark = "   <== CAPTION CONOCIDO" if k == 125 else ""
    print(f"  frame {k:3d}  brillo={s:5.2f}  concentracion={c:5.2f}  total={tot:6.2f}{mark}")

rank125 = [i for i, (k, *_ ) in enumerate(scores) if k == 125]
print(f"\nposicion del frame 125 en el ranking: {rank125[0]+1} de {len(scores)}")
print("-> detector VALIDO" if rank125[0] < 10 else "-> detector NO valido, ignorar el ranking")

# hoja de contactos de los 12 mejores para revision visual
best = [k for k, *_ in scores[:12]]
fig, axes = plt.subplots(6, 2, figsize=(20, 22))
for ax, k in zip(axes.ravel(), best):
    f = clean_frame(k)[150:450]
    lo, hi = np.percentile(f, 2), np.percentile(f, 99.8)
    ax.imshow(np.clip((f-lo)/max(hi-lo,1e-9), 0, 1), cmap="gray", aspect="auto")
    ax.set_title(f"frame {k}", fontsize=10); ax.axis("off")
plt.tight_layout(); plt.savefig("caption_candidates.png", dpi=85); plt.close()
print("-> caption_candidates.png")
