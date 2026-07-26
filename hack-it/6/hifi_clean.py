#!/usr/bin/env python3
"""Dejar los canales HiFi escuchables (de-enfasis + LPF) y sacar el canal
diferencia L-R, donde se esconde lo que no quieres que se oiga en mono."""
import numpy as np
from scipy import signal
from scipy.io import wavfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fs, L = wavfile.read("hifi_L.wav")
_,  R = wavfile.read("hifi_R.wav")
n = min(L.size, R.size)
L = L[:n].astype(np.float64) / 32768
R = R[:n].astype(np.float64) / 32768

def deemph(x, tau=50e-6):
    a = np.exp(-1 / (fs * tau))
    return signal.lfilter([1 - a], [1, -a], x)

def norm(x):
    x = x - x.mean()
    return x / max(np.abs(x).max(), 1e-12)

sos = signal.butter(6, 15000, "lp", fs=fs, output="sos")
Ld = norm(signal.sosfilt(sos, deemph(L)))
Rd = norm(signal.sosfilt(sos, deemph(R)))
mid  = norm(Ld + Rd)
side = norm(Ld - Rd)

for name, x in (("hifi_L_clean", Ld), ("hifi_R_clean", Rd),
                ("hifi_mid", mid), ("hifi_side", side)):
    wavfile.write(f"{name}.wav", fs, (x * 30000).astype(np.int16))
    print(f"{name}.wav  rms={np.sqrt((x**2).mean()):.4f}")

corr = np.corrcoef(Ld, Rd)[0, 1]
print(f"\ncorrelacion L/R = {corr:+.4f}  -> "
      f"{'canales casi identicos (mono)' if corr > .9 else 'canales DISTINTOS: hay contenido independiente' if corr < .5 else 'estereo normal'}")

for tag, x in (("side (L-R)", side), ("mid (L+R)", mid)):
    fr, tt, S = signal.spectrogram(x, fs, nperseg=1024, noverlap=768)
    plt.figure(figsize=(16, 5))
    plt.pcolormesh(tt, fr, 10 * np.log10(S + 1e-14), shading="auto", cmap="magma")
    plt.ylim(0, 5000); plt.title(f"VHS HiFi {tag}"); plt.xlabel("s"); plt.ylabel("Hz")
    plt.tight_layout()
    fn = f"hifi_{'side' if 'side' in tag else 'mid'}_spec.png"
    plt.savefig(fn, dpi=110); plt.close()
    print(f"  -> {fn}")
