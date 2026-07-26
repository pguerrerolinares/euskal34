#!/usr/bin/env python3
"""Hipotesis de Paul: una parte por CAPA de la cinta, todas en el mismo instante.
  luma FM        -> 'Part 1/3: v1nTag3'   (caption, frame 125 = t=5.0s)
  audio HiFi L   -> voz 'rickroll'        (t=4.6-5.0s)
  audio HiFi R   -> ??? nunca lo hemos aislado
Cancelacion INVERSA: que hay en R que no este en L."""
import numpy as np
from scipy import signal
from scipy.io import wavfile

fs, L = wavfile.read("hifi2_L.wav"); L = L.astype(float)/32768
_,  R = wavfile.read("hifi2_R.wav"); R = R.astype(float)/32768
n = min(L.size, R.size); L, R = L[:n], R[:n]

TAPS, BLK = 64, int(0.25*fs)
def cancel(target, ref):
    out = np.zeros(n)
    for i in range(0, n - BLK, BLK//2):
        d = target[i:i+BLK]
        Xm = np.lib.stride_tricks.sliding_window_view(ref[max(0,i-TAPS+1):i+BLK], TAPS)
        if Xm.shape[0] < d.size: continue
        Xm = Xm[:d.size]
        h, *_ = np.linalg.lstsq(Xm, d, rcond=None)
        out[i:i+BLK] = d - Xm @ h
    return out

sos = signal.butter(4, [150, 3800], "bp", fs=fs, output="sos")
def w(name, x, rate=fs):
    x = x-x.mean(); x /= max(np.abs(x).max(), 1e-12)
    wavfile.write(name, int(rate), (x*30000).astype(np.int16))
    print(f"  {name}")

for tag, (tgt, ref) in (("R_solo", (R, L)), ("L_solo", (L, R))):
    v = signal.sosfilt(sos, cancel(tgt, ref))
    print(f"\n=== {tag}: energia residual {100*np.sum(v**2)/np.sum(tgt**2):.2f}% ===")
    vals = []
    for t0 in np.arange(0, n/fs - .1, .1):
        s = v[int(t0*fs):int((t0+.1)*fs)]
        sp = np.abs(np.fft.rfft(s)); f = np.fft.rfftfreq(s.size, 1/fs)
        vals.append((t0, np.sqrt(np.mean(sp[(f>200)&(f<3500)]**2))))
    mx = max(x for _, x in vals)
    print("  picos (>50% del maximo):")
    for t0, x in vals:
        if x > .5*mx:
            print(f"    t={t0:5.2f}s {'#'*int(45*x/mx)}")
    w(f"{tag}_full.wav", v)
    a, b = int(4.30*fs), int(5.35*fs)
    w(f"{tag}_event.wav", v[a:b])
    w(f"{tag}_event_x2.wav", signal.resample_poly(v[a:b], 2, 1))
