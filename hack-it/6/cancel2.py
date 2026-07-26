#!/usr/bin/env python3
"""Cancelacion con UN filtro global fijo (Wiener sobre la senal entera).
Un filtro fijo puede borrar lo que L y R comparten (la musica), pero no puede
borrar algo que solo existe en un canal. Lo que sobreviva es real."""
import numpy as np
from scipy import signal
from scipy.io import wavfile
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

fs, L = wavfile.read("hifi2_L.wav")
_,  R = wavfile.read("hifi2_R.wav")
n = min(L.size, R.size)
L = L[:n].astype(np.float64) / 32768
R = R[:n].astype(np.float64) / 32768

# Wiener global en frecuencia: G = <Sxy> / <Syy>, promediado sobre todos los bloques
NF = 8192
hop = NF // 2
Sxy = np.zeros(NF // 2 + 1, dtype=complex)
Syy = np.zeros(NF // 2 + 1)
win = np.hanning(NF)
for i in range(0, n - NF, hop):
    A = np.fft.rfft(L[i:i+NF] * win)
    B = np.fft.rfft(R[i:i+NF] * win)
    Sxy += A * np.conj(B)
    Syy += np.abs(B) ** 2
G = Sxy / (Syy + 1e-12)
print(f"ganancia media |G| = {np.abs(G).mean():.3f}  (1.0 = canales identicos)")

res = np.zeros(n); acc = np.zeros(n)
for i in range(0, n - NF, hop):
    A = np.fft.rfft(L[i:i+NF] * win)
    B = np.fft.rfft(R[i:i+NF] * win)
    res[i:i+NF] += np.fft.irfft(A - G * B, NF)
    acc[i:i+NF] += win
res /= np.maximum(acc, 1e-6)
res[:NF] = res[-NF:] = 0

print(f"energia residual: {100*np.sum(res**2)/np.sum(L**2):.2f} % de L")
rn = res / max(np.abs(res).max(), 1e-12)
wavfile.write("hifi_residual2.wav", fs, (rn * 30000).astype(np.int16))

fr, tt, S = signal.spectrogram(rn, fs, nperseg=1024, noverlap=768)
plt.figure(figsize=(16, 6))
plt.pcolormesh(tt, fr, 10*np.log10(S+1e-14), shading="auto", cmap="magma")
plt.ylim(0, 4000); plt.title("residual (filtro global) - lo que solo esta en un canal")
plt.xlabel("s"); plt.ylabel("Hz"); plt.tight_layout()
plt.savefig("hifi_residual2_spec.png", dpi=115); plt.close()
print("-> hifi_residual2.wav / hifi_residual2_spec.png")

print("\nenergia del residuo por 0.25 s (200-3500 Hz), normalizada:")
vals = []
for t0 in np.arange(0, 10, 0.25):
    s = res[int(t0*fs):int((t0+0.25)*fs)]
    if s.size < 100: break
    sp = np.abs(np.fft.rfft(s)); f = np.fft.rfftfreq(s.size, 1/fs)
    vals.append((t0, np.sqrt(np.mean(sp[(f>200)&(f<3500)]**2))))
mx = max(v for _, v in vals)
for t0, v in vals:
    print(f"  t={t0:5.2f}s {'#'*int(60*v/mx)}")
