#!/usr/bin/env python3
"""Si la parte 3 esta en R, no esta 'en claro' (whisper no la saca). Probar el
repertorio del autor: backmasking, inversion de banda, cambios de velocidad.
Y ademas extraer los OTROS picos de energia de R, no solo el de t=5s."""
import numpy as np
from scipy import signal
from scipy.io import wavfile
import os

fs, L = wavfile.read("L_solo_full.wav"); L = L.astype(float)/32768
_,  R = wavfile.read("R_solo_full.wav"); R = R.astype(float)/32768
os.makedirs("var", exist_ok=True)

def w(name, x, rate=fs):
    x = x - x.mean(); x /= max(np.abs(x).max(), 1e-12)
    wavfile.write(f"var/{name}.wav", int(rate), (x*30000).astype(np.int16))

sos = signal.butter(4, [150, 3800], "bp", fs=fs, output="sos")

def specinv(x):
    """inversion de banda: multiplicar por (-1)^n refleja el espectro."""
    return signal.sosfilt(sos, x * np.cos(np.pi*np.arange(x.size)))

# tramos candidatos: el evento principal y los otros picos que salieron en R
TRAMOS = {"ev": (4.30, 5.35), "p2": (1.85, 2.25), "p6": (5.80, 6.45),
          "p93": (9.15, 9.55), "p99": (9.75, 10.0)}

n = 0
for tag, (a, b) in TRAMOS.items():
    for ch, x in (("L", L), ("R", R)):
        seg = x[int(a*fs):int(b*fs)]
        if seg.size < 1000: continue
        base = f"{ch}_{tag}"
        w(f"{base}", seg)
        w(f"{base}_rev", seg[::-1])
        w(f"{base}_inv", specinv(seg))
        w(f"{base}_revinv", specinv(seg[::-1]))
        w(f"{base}_slow", signal.resample_poly(seg, 2, 1))
        w(f"{base}_fast", signal.resample_poly(seg, 1, 2))
        n += 6
print(f"{n} variantes en var/")
print("tramos:", ", ".join(f"{k}={v[0]:.2f}-{v[1]:.2f}s" for k, v in TRAMOS.items()))
