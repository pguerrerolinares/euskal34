#!/usr/bin/env python3
"""Sonda PAL: la senal demodulada, ?tiene estructura de linea real (sync/blanking/burst)
y subportadora de color con V-switch? Nunca lo comprobamos: buscamos captions en el luma.
"""
import numpy as np

W = 2011                      # muestras por linea
FS = 31415926.0
msg = np.load("msg_full.npy", mmap_mode="r")
NL = msg.shape[0] // W
lines = np.lib.stride_tricks.as_strided(msg, (NL, W), (W * msg.itemsize, msg.itemsize))
print(f"lineas: {NL}  muestras/linea: {W}")

# --- 1. perfil medio de linea: ?hay sync y blanking? -------------------------
prof = np.asarray(lines[:20000], dtype=np.float64).mean(axis=0)
lo, hi = prof.min(), prof.max()
print(f"\nperfil de linea: min={lo:.4f} max={hi:.4f}")
# el sync es la zona sostenida mas baja; el activo, el resto
thr = lo + 0.15 * (hi - lo)
below = prof < thr
# tramos contiguos por debajo del umbral
edges = np.flatnonzero(np.diff(below.astype(int)))
runs = []
start = 0 if below[0] else None
for e in edges:
    if below[e]:            # fin de tramo
        runs.append((start, e + 1)); start = None
    else:
        start = e + 1
if start is not None:
    runs.append((start, W))
runs = [r for r in runs if r[1] - r[0] > 20]
print("tramos bajos (candidatos a sync/blanking):",
      [(a, b, f"{(b-a)/W*64:.1f}us") for a, b in runs][:6])

# --- 2. espectro por linea: TODOS los picos, no solo los que ya conociamos ---
seg = np.asarray(lines[10000:10000 + 4096], dtype=np.float64)
seg = seg - seg.mean(axis=1, keepdims=True)
spec = np.abs(np.fft.rfft(seg, axis=1)).mean(axis=0)
k = np.arange(spec.size)
top = np.argsort(spec)[::-1][:12]
print("\npicos (ciclos/linea -> MHz, energia):")
for t in sorted(top):
    if t < 3:
        continue
    print(f"  {t:5d} c/linea  {t/W*FS/1e6:7.3f} MHz  {spec[t]/spec.max():.3f}")

# --- 3. la firma PAL: subportadora a 283.75 c/linea + V-switch --------------
# resolucion fina alrededor de 283.75 usando muchas lineas (DFT directa)
n = 8192
blk = np.asarray(lines[20000:20000 + n], dtype=np.float64)
blk = blk - blk.mean(axis=1, keepdims=True)
print("\nzoom espectral (energia relativa al maximo de la banda 270-300):")
band = {}
for c in np.arange(270.0, 300.01, 0.25):
    ph = np.exp(-2j * np.pi * c * np.arange(W) / W)
    band[c] = np.abs(blk @ ph).mean()
mx = max(band.values())
for c, v in sorted(band.items(), key=lambda x: -x[1])[:6]:
    print(f"  {c:7.2f} c/linea  {c/W*FS/1e6:7.3f} MHz  {v/mx:.3f}")

# V-switch: en PAL la fase de V se invierte linea a linea -> correlacion
# entre lineas consecutivas a fsc debe ser negativa en la componente V.
for c in (283.75, 176.0, 201.1):
    ph = np.exp(-2j * np.pi * c * np.arange(W) / W)
    z = blk @ ph
    d = np.angle(z[1:] * np.conj(z[:-1]))
    print(f"  fase linea-a-linea @ {c:7.2f} c/linea: media={np.degrees(np.mean(d)):+7.1f}deg "
          f"disp={np.degrees(np.std(d)):6.1f}deg")
