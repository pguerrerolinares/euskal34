#!/usr/bin/env python3
"""Zoom en el evento anomalo de t=4.3-5.6s: ?formantes de voz o instrumento?"""
import numpy as np
from scipy import signal
from scipy.io import wavfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fs, x = wavfile.read("hifi_mid.wav")
x = x.astype(np.float64) / 32768

a, b = int(4.0 * fs), int(6.0 * fs)
seg = x[a:b]
wavfile.write("hifi_event.wav", fs, (seg / max(abs(seg).max(), 1e-9) * 30000).astype(np.int16))
print(f"recorte 4.0-6.0 s -> hifi_event.wav")

fr, tt, S = signal.spectrogram(seg, fs, nperseg=2048, noverlap=1792)
plt.figure(figsize=(16, 7))
plt.pcolormesh(tt + 4.0, fr, 10 * np.log10(S + 1e-14), shading="auto", cmap="magma")
plt.ylim(0, 3500); plt.xlabel("s"); plt.ylabel("Hz")
plt.title("evento 4.0-6.0 s (mid) - alta resolucion")
plt.tight_layout(); plt.savefig("hifi_event_spec.png", dpi=120); plt.close()
print("-> hifi_event_spec.png")

# energia por 100 ms en la banda de voz, para localizar el evento exacto
print("\nenergia banda 300-3000 Hz por 100 ms:")
for t0 in np.arange(3.5, 6.5, 0.1):
    s = x[int(t0 * fs):int((t0 + 0.1) * fs)]
    if s.size < 100:
        break
    sp = np.abs(np.fft.rfft(s * np.hanning(s.size)))
    f = np.fft.rfftfreq(s.size, 1 / fs)
    e = np.sum(sp[(f > 300) & (f < 3000)] ** 2)
    tot = np.sum(sp ** 2)
    print(f"  t={t0:4.1f}s  ratio={e/tot:6.3f}  {'#' * int(e/tot*80)}")
