#!/usr/bin/env python3
"""Cancelacion optima entre canales: buscar ganancia y retardo que minimizan
|L - a*R(d)|. Lo que sobreviva a la cancelacion de la musica es contenido que
solo esta en un canal (= lo que alguien escondio ahi)."""
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

# retardo optimo por correlacion cruzada
xc = signal.correlate(L, R, mode="same")
lag = int(np.argmax(np.abs(xc)) - n // 2)
print(f"retardo optimo L vs R: {lag} muestras ({lag/fs*1000:.2f} ms)")
Rs = np.roll(R, lag)

# filtro de cancelacion adaptativo (Wiener, por bloques en frecuencia)
NF = 4096
win = np.hanning(NF)
res = np.zeros(n)
acc = np.zeros(n)
for i in range(0, n - NF, NF // 2):
    a, b = L[i:i+NF] * win, Rs[i:i+NF] * win
    A, B = np.fft.rfft(a), np.fft.rfft(b)
    g = (A * np.conj(B)) / (np.abs(B) ** 2 + 1e-9)      # ganancia compleja por bin
    r = np.fft.irfft(A - g * B, NF)
    res[i:i+NF] += r
    acc[i:i+NF] += win
res /= np.maximum(acc, 1e-9)

print(f"energia residual tras cancelar: {100*np.sum(res**2)/np.sum(L**2):.3f} % de L")
res /= max(np.abs(res).max(), 1e-12)
wavfile.write("hifi_residual.wav", fs, (res * 30000).astype(np.int16))
print("-> hifi_residual.wav")

fr, tt, S = signal.spectrogram(res, fs, nperseg=1024, noverlap=768)
plt.figure(figsize=(16, 6))
plt.pcolormesh(tt, fr, 10*np.log10(S+1e-14), shading="auto", cmap="magma")
plt.ylim(0, 4000); plt.title("residual tras cancelar lo comun a L y R")
plt.xlabel("s"); plt.ylabel("Hz"); plt.tight_layout()
plt.savefig("hifi_residual_spec.png", dpi=115); plt.close()
print("-> hifi_residual_spec.png")

print("\nenergia del residuo por 0.5 s (banda 200-3500 Hz):")
for t0 in np.arange(0, 10, 0.5):
    s = res[int(t0*fs):int((t0+0.5)*fs)]
    if s.size < 100: break
    sp = np.abs(np.fft.rfft(s)); f = np.fft.rfftfreq(s.size, 1/fs)
    e = np.sqrt(np.mean(sp[(f>200)&(f<3500)]**2))
    print(f"  t={t0:4.1f}s {'#'*int(e*4000):s}")
