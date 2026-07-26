#!/usr/bin/env python3
"""Idea de Paul: 250 frames exactos = quiza el canal son los frames, no la imagen.
Medir parametros de la senal PROMEDIADOS sobre las 625 lineas de cada frame
(el promedio divide el ruido por 25) y ver si las series de 250 valores llevan datos."""
import numpy as np

W, LPF, NFR = 2011, 625, 250
msg = np.load("msg_full.npy", mmap_mode="r")
NL = msg.shape[0] // W
lines = np.lib.stride_tricks.as_strided(msg, (NL, W), (W*msg.itemsize, msg.itemsize))

series = {k: [] for k in ("sync_lvl", "blank_lvl", "amplitud", "sync_ancho",
                          "activo_lvl", "activo_std", "sync_pos")}
for k in range(NFR):
    f = np.asarray(lines[k*LPF:min((k+1)*LPF, NL)], dtype=np.float64)
    if f.shape[0] < 600: break
    sync = f[:, 20:120].mean(axis=1)
    blank = f[:, 200:290].mean(axis=1)
    act = f[:, 400:]
    thr = (sync + blank) / 2
    ancho = (f[:, :400] < thr[:, None]).sum(axis=1)
    # posicion del flanco de subida del sync, con interpolacion subpixel
    pos = []
    for i in range(0, f.shape[0], 8):
        row = f[i, :400]
        t = thr[i]
        idx = np.flatnonzero((row[:-1] < t) & (row[1:] >= t))
        if idx.size:
            j = idx[-1]
            d = row[j+1] - row[j]
            pos.append(j + ((t - row[j]) / d if abs(d) > 1e-9 else 0))
    series["sync_lvl"].append(sync.mean())
    series["blank_lvl"].append(blank.mean())
    series["amplitud"].append((blank - sync).mean())
    series["sync_ancho"].append(ancho.mean())
    series["activo_lvl"].append(act.mean())
    series["activo_std"].append(act.std())
    series["sync_pos"].append(np.mean(pos) if pos else np.nan)

for name, v in series.items():
    v = np.array(v, dtype=float)
    v = v[~np.isnan(v)]
    if v.size < 10: continue
    c = v - v.mean()
    # ?bimodal? separacion entre los dos grupos frente a la dispersion interna
    med = np.median(v)
    a, b = v[v <= med], v[v > med]
    sep = (b.mean() - a.mean()) / max(np.sqrt((a.std()**2 + b.std()**2)/2), 1e-12)
    print(f"{name:11s} media={v.mean():10.5f} desv={v.std():.6f} "
          f"rango={v.max()-v.min():.6f} separacion_bimodal={sep:6.2f}"
          + ("   <-- BINARIO?" if sep > 4 else ""))
    np.save(f"pf_{name}.npy", v)

print("\nprimeros 60 valores de cada serie (normalizados a 0-9):")
for name, v in series.items():
    v = np.array(v, dtype=float); v = v[~np.isnan(v)]
    if v.size < 10: continue
    q = np.clip(((v - v.min()) / max(v.max()-v.min(), 1e-12) * 9).round().astype(int), 0, 9)
    print(f"  {name:11s} {''.join(map(str, q[:60]))}")
