#!/usr/bin/env python3
"""El canal L tiene SILENCIO ABSOLUTO (-45 dB respecto al fondo) en 5.10-5.30 s y
caidas en 4.80-4.85, mientras R sigue normal. Eso no lo produce ni la musica ni la
demodulacion FM (perder portadora daria RUIDO, no silencio): es silencio insertado.

Ráfaga / silencio / ráfaga es como codifican los dispositivos vintage que 'graban
y reproducen' datos sobre audio: Morse, carga de cinta (ZX Spectrum, C64), FSK.
Aqui se mide el tren de ráfagas con resolucion de 1 ms y se busca su reloj."""
import numpy as np
from scipy.io import wavfile
from scipy import ndimage
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sr, L = wavfile.read("hifi2_L.wav")
_, R = wavfile.read("hifi2_R.wav")
L = L.astype(np.float64); R = R.astype(np.float64)
n = min(L.size, R.size); L, R = L[:n], R[:n]

# envolvente de energia con resolucion de 1 ms
w = sr // 1000
nb = n // w
eL = 10 * np.log10(np.array([np.mean(L[i*w:(i+1)*w]**2) for i in range(nb)]) + 1e-12)
eR = 10 * np.log10(np.array([np.mean(R[i*w:(i+1)*w]**2) for i in range(nb)]) + 1e-12)
t = np.arange(nb) / 1000.0

floor = np.median(eL)
SIL = floor - 25          # umbral generoso de "silencio"
sil = eL < SIL
print(f"fondo de L = {floor:.1f} dB, umbral de silencio = {SIL:.1f} dB")
print(f"muestras de 1 ms en silencio: {sil.sum()} de {nb} ({100*sil.mean():.2f} %)")

# tramos contiguos de silencio en L
lab, k = ndimage.label(sil)
print(f"\n== tramos de SILENCIO en L ({k} en total) ==")
runs = []
for i in range(1, k + 1):
    idx = np.where(lab == i)[0]
    dur = len(idx)
    if dur >= 3:
        runs.append((t[idx[0]], dur))
        print(f"  t={t[idx[0]]:6.3f}s  duracion {dur:4d} ms   "
              f"(R en ese tramo: {eR[idx].mean():.1f} dB)")
if not runs:
    print("  (ninguno de >=3 ms)")

# lo mismo en R, como control
silR = eR < np.median(eR) - 25
labR, kR = ndimage.label(silR)
print(f"\n== control: tramos de silencio en R ==")
found = False
for i in range(1, kR + 1):
    idx = np.where(labR == i)[0]
    if len(idx) >= 3:
        found = True
        print(f"  t={t[idx[0]]:6.3f}s  duracion {len(idx):4d} ms")
if not found:
    print("  (ninguno de >=3 ms)  -> el silencio es EXCLUSIVO de L")

# ¿hay reloj? duraciones de ráfaga y de silencio en la zona del evento
z = (t >= 4.4) & (t <= 5.7)
seq = sil[z]
lab2, k2 = ndimage.label(~seq)      # ráfagas (no-silencio)
print(f"\n== estructura en 4.4-5.7 s: alternancia ráfaga/silencio ==")
segs = []
cur = seq[0]; c = 1
for v in seq[1:]:
    if v == cur:
        c += 1
    else:
        segs.append(("SIL" if cur else "RAF", c)); cur = v; c = 1
segs.append(("SIL" if cur else "RAF", c))
for kind, d in segs:
    print(f"  {kind}  {d:4d} ms")
durs = [d for kind, d in segs if d >= 2]
if len(durs) >= 3:
    g = durs[0]
    for d in durs[1:]:
        while d:
            g, d = d, g % d
    print(f"\n  MCD de las duraciones = {g} ms"
          f"  -> {'posible reloj de bit' if g >= 2 else 'sin reloj evidente'}")

fig, axes = plt.subplots(3, 1, figsize=(16, 12))
axes[0].plot(t, eL, lw=.7, label="L"); axes[0].plot(t, eR, lw=.7, alpha=.7, label="R")
axes[0].axhline(SIL, color="r", ls="--", lw=.8)
axes[0].set_title("energia 1 ms, fichero completo"); axes[0].legend(); axes[0].grid(alpha=.3)
m = (t >= 4.3) & (t <= 5.9)
axes[1].plot(t[m], eL[m], lw=1, label="L"); axes[1].plot(t[m], eR[m], lw=1, alpha=.7, label="R")
axes[1].axhline(SIL, color="r", ls="--", lw=.8)
axes[1].set_title("zoom 4.3-5.9 s"); axes[1].legend(); axes[1].grid(alpha=.3)
a0, a1 = int(4.3 * sr), int(5.9 * sr)
axes[2].specgram(L[a0:a1], NFFT=1024, Fs=sr, noverlap=896, cmap="inferno")
axes[2].set_ylim(0, 8000); axes[2].set_title("espectrograma de L, 4.3-5.9 s")
plt.tight_layout(); plt.savefig("burst_L.png", dpi=115)

y = L[a0:a1] / max(np.abs(L[a0:a1]).max(), 1e-12)
wavfile.write("burst_L_event.wav", sr, (y * 30000).astype(np.int16))
wavfile.write("burst_L_event_slow.wav", sr // 3, (y * 30000).astype(np.int16))
print("\n-> burst_L.png / burst_L_event.wav (+ _slow)")
