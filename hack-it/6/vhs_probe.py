#!/usr/bin/env python3
"""Hipotesis VHS: si esto es una cinta y no PAL banda base, el luma va en FM
(3.8-4.8 MHz) y la CROMA va 'color-under' a 40*fH = 625 kHz, por debajo, en AM.
Nunca miramos la banda baja del crudo. Buscar el pico a ~40 ciclos/linea."""
import numpy as np

W, FS = 2011, 31415926.0
raw = np.memmap("out.wav", dtype=np.int16, mode="r", offset=44)
print(f"muestras crudas: {raw.size}")

# bloque en mitad del fichero, multiplo de linea
n = 2011 * 4096
off = (raw.size // 2 // W) * W
x = np.asarray(raw[off:off + n], dtype=np.float64)
x -= x.mean()

sp = np.abs(np.fft.rfft(x))
f = np.fft.rfftfreq(n, 1 / FS)

print("\n--- espectro del CRUDO, banda baja (0-2 MHz) ---")
lo = (f > 50e3) & (f < 2.0e6)
idx = np.flatnonzero(lo)
top = idx[np.argsort(sp[idx])[::-1][:10]]
for t in sorted(top):
    print(f"  {f[t]/1e3:9.1f} kHz   {f[t]/FS*W:7.2f} c/linea   energia={sp[t]/sp[idx].max():.3f}")

print("\n--- energia en multiplos exactos de fH (15625 Hz) en la banda baja ---")
fH = FS / W
for mult in (40, 44, 47, 80, 160):
    fc = mult * fH
    k = int(round(fc * n / FS))
    win = sp[k-3:k+4].max()
    base = np.median(sp[max(0,k-400):k+400])
    print(f"  {mult:4d}*fH = {fc/1e3:8.1f} kHz  pico/mediana_local = {win/base:6.2f}"
          + ("   <-- DESTACA" if win / base > 4 else ""))

print("\n--- banda completa: los 8 picos mayores de todo el espectro ---")
sel = f > 20e3
idx = np.flatnonzero(sel)
top = idx[np.argsort(sp[idx])[::-1][:8]]
for t in sorted(top):
    print(f"  {f[t]/1e6:8.4f} MHz   {f[t]/FS*W:8.2f} c/linea   energia={sp[t]/sp[idx].max():.3f}")

# perfil de energia por bandas, para ver donde vive la senal
print("\n--- reparto de energia por banda ---")
for a, b in ((0, .3e6), (.3e6, 1e6), (1e6, 2e6), (2e6, 3e6), (3e6, 5e6), (5e6, 8e6), (8e6, 15.7e6)):
    m = (f >= a) & (f < b)
    print(f"  {a/1e6:5.1f}-{b/1e6:5.1f} MHz : {100*np.sum(sp[m]**2)/np.sum(sp**2):6.2f} %")
