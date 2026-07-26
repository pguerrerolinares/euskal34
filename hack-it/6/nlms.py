#!/usr/bin/env python3
"""R = referencia de la musica sin voz. Cancelar la musica de L usando R como
referencia, con filtros FIR cortos por bloque (64 taps / 0.25 s: demasiado pocos
grados de libertad para borrar la voz, suficientes para seguir a la musica)."""
import numpy as np
from scipy import signal
from scipy.io import wavfile

fs, L = wavfile.read("hifi2_L.wav"); L = L.astype(float)/32768
_,  R = wavfile.read("hifi2_R.wav"); R = R.astype(float)/32768
n = min(L.size, R.size); L, R = L[:n], R[:n]

TAPS = 64
BLK = int(0.25*fs)
out = np.zeros(n)
for i in range(0, n - BLK, BLK//2):
    d = L[i:i+BLK]
    # matriz de retardos de la referencia
    Xm = np.lib.stride_tricks.sliding_window_view(R[max(0,i-TAPS+1):i+BLK], TAPS)
    if Xm.shape[0] < d.size:
        continue
    Xm = Xm[:d.size]
    h, *_ = np.linalg.lstsq(Xm, d, rcond=None)
    out[i:i+BLK] = d - Xm @ h

print(f"energia residual: {100*np.sum(out**2)/np.sum(L**2):.2f} % de L")

sos = signal.butter(4, [150, 3800], "bp", fs=fs, output="sos")
v = signal.sosfilt(sos, out)

def w(name, x, rate=fs):
    x = x-x.mean(); x /= max(np.abs(x).max(), 1e-12)
    wavfile.write(name, int(rate), (x*30000).astype(np.int16))
    print(f"  {name}")

print("\nperfil de energia del residuo por 0.1 s (200-3500 Hz):")
vals = []
for t0 in np.arange(0, n/fs - .1, .1):
    s = v[int(t0*fs):int((t0+.1)*fs)]
    sp = np.abs(np.fft.rfft(s)); f = np.fft.rfftfreq(s.size, 1/fs)
    vals.append((t0, np.sqrt(np.mean(sp[(f>200)&(f<3500)]**2))))
mx = max(x for _, x in vals)
for t0, x in vals:
    if x > .35*mx:
        print(f"  t={t0:5.2f}s {'#'*int(50*x/mx)}")

w("nlms_full.wav", v)
a, b = int(4.35*fs), int(5.30*fs)
seg = v[a:b]
w("nlms_event.wav", seg)
w("nlms_event_x2.wav", signal.resample_poly(seg, 2, 1))
w("nlms_event_x3.wav", signal.resample_poly(seg, 3, 1))
