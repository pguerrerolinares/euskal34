#!/usr/bin/env python3
"""El nucleo es /r/+/oU/+/l/ ('-roll'). Falta la consonante inicial, que decide entre
   roll  (nada delante)
   troll / kroll / droll  (oclusiva: silencio + BURST corto de banda ancha)
   scroll / stroll        (fricativa /s/: ruido sostenido de 4-8 kHz, 60-120 ms)
Cada tipo deja una firma distinta en los primeros 100 ms."""
import numpy as np
from scipy.io import wavfile
from scipy import signal
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sr, L = wavfile.read("hifi2_L.wav")
L = L.astype(np.float64) / 32768
# ventana amplia: desde el silencio previo hasta bien entrado el nucleo
A, B = 4.775, 5.090
x = L[int(A * sr):int(B * sr)]

w, hop = int(0.010 * sr), int(0.002 * sr)


def band_energy(lo, hi):
    sos = signal.butter(4, [lo, hi], "bp", fs=sr, output="sos")
    y = signal.sosfiltfilt(sos, x)
    return np.array([np.sqrt(np.mean(y[i:i+w] ** 2))
                     for i in range(0, len(y) - w, hop)])


lo_e = band_energy(200, 1000)      # sonoridad (voz)
mid_e = band_energy(1000, 4000)
hi_e = band_energy(4000, 12000)    # fricativa / burst
t = A * 1000 + np.arange(len(lo_e)) * 2

print("  t(ms)   200-1k   1k-4k   4k-12k   ratio alta/baja")
for i in range(len(t)):
    r = hi_e[i] / max(lo_e[i], 1e-9)
    mark = ""
    if hi_e[i] > 3 * np.median(hi_e[:10]) and r > 0.5:
        mark = "  <== energia ALTA dominante"
    print(f"  {t[i]:6.0f}  {lo_e[i]:.5f}  {mid_e[i]:.5f}  {hi_e[i]:.5f}   {r:6.2f}{mark}")

# firma de fricativa: tramo largo (>40 ms) con alta > baja
fric = (hi_e > lo_e) & (hi_e > 2 * np.median(hi_e[:8]))
from scipy import ndimage
lab, n = ndimage.label(fric)
print("\ntramos donde la energia ALTA supera a la baja:")
longest = 0
for i in range(1, n + 1):
    idx = np.where(lab == i)[0]
    d = len(idx) * 2
    longest = max(longest, d)
    if d >= 6:
        print(f"  t={t[idx[0]]:.0f}-{t[idx[-1]]:.0f} ms  ({d} ms)")
if longest == 0:
    print("  (ninguno)")

print(f"\nVEREDICTO sobre la consonante inicial:")
if longest >= 40:
    print(f"  tramo de {longest} ms de ruido de alta frecuencia -> FRICATIVA /s/"
          f" -> 'scroll' / 'stroll'")
elif longest >= 4:
    print(f"  transitorio corto de {longest} ms -> BURST de OCLUSIVA"
          f" -> 'troll' / 'kroll' / 'droll'")
else:
    print(f"  sin energia de alta frecuencia destacada -> NO hay consonante"
          f" inicial sorda -> 'roll' (o una sonora suave)")

fig, ax = plt.subplots(figsize=(13, 6))
ax.plot(t, lo_e, label="200-1000 Hz (sonoridad)", lw=1.3)
ax.plot(t, mid_e, label="1-4 kHz", lw=1.1)
ax.plot(t, hi_e, label="4-12 kHz (fricativa/burst)", lw=1.3)
ax.set_xlabel("ms"); ax.set_title("ataque de la palabra: que hay antes del nucleo")
ax.legend(); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig("onset.png", dpi=120)
print("-> onset.png")
