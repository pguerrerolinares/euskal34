#!/usr/bin/env python3
"""Aislar e inteligibilizar la voz de t~4.6-5.1s:
  1) substraccion espectral usando la musica vecina como perfil de ruido
  2) variantes: lenta, invertida en el tiempo (backmasking), invertida en banda
  3) barrido de los 10 s por si hay MAS eventos de voz (partes 2 y 3)"""
import numpy as np
from scipy import signal
from scipy.io import wavfile
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

fs, L = wavfile.read("hifi2_L.wav"); L = L.astype(float) / 32768
_,  R = wavfile.read("hifi2_R.wav"); R = R.astype(float) / 32768
n = min(L.size, R.size); L, R = L[:n], R[:n]

NF, HOP = 1024, 256
win = np.hanning(NF)

def stft(x):
    m = 1 + (x.size - NF) // HOP
    return np.array([np.fft.rfft(x[i*HOP:i*HOP+NF] * win) for i in range(m)])

def istft(X, ln):
    y = np.zeros(ln); a = np.zeros(ln)
    for i, fr in enumerate(X):
        s = i * HOP
        y[s:s+NF] += np.fft.irfft(fr, NF) * win
        a[s:s+NF] += win ** 2
    return y / np.maximum(a, 1e-9)

X = stft(L)
mag, ph = np.abs(X), np.angle(X)
t = np.arange(X.shape[0]) * HOP / fs

# perfil de "ruido" = la musica, estimada FUERA del evento
noise_m = ((t > 3.0) & (t < 4.4)) | ((t > 5.3) & (t < 6.8))
prof = np.median(mag[noise_m], axis=0)
clean = np.maximum(mag - 2.2 * prof, 0.05 * mag)          # substraccion espectral
y = istft(clean * np.exp(1j * ph), L.size)

sos = signal.butter(4, [180, 3800], "bp", fs=fs, output="sos")
y = signal.sosfilt(sos, y)

def w(name, x, rate=fs):
    x = x - x.mean()
    x = x / max(np.abs(x).max(), 1e-12)
    wavfile.write(name, int(rate), (x * 30000).astype(np.int16))
    print(f"  {name}")

a, b = int(4.45 * fs), int(5.25 * fs)
seg = y[a:b]
print("variantes del evento:")
w("v_clean.wav", seg)
w("v_clean_slow2.wav", signal.resample_poly(seg, 2, 1))
w("v_clean_rev.wav", seg[::-1])                            # backmasking
w("v_clean_rev_slow.wav", signal.resample_poly(seg[::-1], 2, 1))
# inversion en banda (scrambling tipo Nagravision): x * (-1)^k desplaza fs/2
inv = seg * np.cos(np.pi * np.arange(seg.size))
w("v_clean_specinv.wav", signal.sosfilt(sos, inv))
w("v_clean_x3.wav", np.clip(seg / max(abs(seg).max(), 1e-9) * 3, -1, 1))

# --- barrido: ?hay mas eventos de voz en los 10 s? --------------------------
# medida de "vocalidad": armonicidad via autocorrelacion en banda 80-320 Hz
print("\nbarrido de vocalidad (autocorrelacion normalizada, pitch 80-320 Hz):")
step = int(0.05 * fs); wl = int(0.05 * fs)
scores = []
for i in range(0, y.size - wl, step):
    s = y[i:i+wl] * np.hanning(wl)
    ac = np.correlate(s, s, "full")[wl-1:]
    ac /= max(ac[0], 1e-12)
    lo, hi = int(fs/320), int(fs/80)
    scores.append((i/fs, ac[lo:hi].max() if hi < ac.size else 0))
mx = max(v for _, v in scores)
for tt, v in scores:
    if v > 0.45 * mx:
        print(f"  t={tt:5.2f}s  armonicidad={v:.3f}  {'#'*int(40*v/mx)}")

plt.figure(figsize=(15, 5))
plt.plot([s[0] for s in scores], [s[1] for s in scores], lw=.8)
plt.xlabel("s"); plt.ylabel("armonicidad"); plt.grid(alpha=.3)
plt.title("busqueda de eventos de voz en los 10 s")
plt.tight_layout(); plt.savefig("voice_scan.png", dpi=110)
print("\n-> voice_scan.png")
