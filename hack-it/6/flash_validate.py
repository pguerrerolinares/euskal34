#!/usr/bin/env python3
"""Validacion honesta del detector de flashes: inyectar un caption sintetico de
UN solo frame, con el mismo contraste que el caption real, y ver si lo detecta.
Si no lo detecta, el ranking anterior no prueba nada."""
import numpy as np

W, LPF, NFR = 2011, 625, 250
msg = np.load("msg_full.npy", mmap_mode="r")
NL = msg.shape[0] // W
lines = np.lib.stride_tricks.as_strided(msg, (NL, W), (W*msg.itemsize, msg.itemsize))
NOTCH = [(160, 190), (192, 215)]
R = 3

def clean(k):
    f = np.asarray(lines[k*LPF:min((k+1)*LPF, NL)], dtype=np.float32)
    F = np.fft.rfft(f, axis=1)
    for a, b in NOTCH: F[:, a:b+1] = 0
    return np.fft.irfft(F, W, axis=1)[:624, 500:1600]

# --- 1. cuanto dura el caption real y que contraste tiene -------------------
print("brillo de la banda del caption (filas 330-390) por frame:")
base = np.median([np.median(clean(k)[330:390]) for k in (100, 110, 140, 150)])
prof = []
for k in range(112, 142):
    f = clean(k)
    v = np.percentile(f[330:390], 99.5) - np.median(f)
    prof.append((k, v))
mx = max(v for _, v in prof)
for k, v in prof:
    print(f"  frame {k:3d}  {v:.4f} {'#'*int(45*v/mx)}")
dur = [k for k, v in prof if v > 0.6*mx]
print(f"\n-> el caption es visible en los frames {dur[0]}..{dur[-1]} ({len(dur)} frames)")

contrast = mx
print(f"-> contraste del caption real: {contrast:.4f}")

# --- 2. inyectar un caption sintetico de 1 frame en el frame 50 -------------
def clean_inj(k, target=50, amp=contrast):
    f = clean(k)
    if k == target:
        f = f.copy()
        # simular texto: barras verticales en la misma banda que el caption real
        for x in range(120, 900, 34):
            f[335:385, x:x+16] += amp
    return f

buf = {k: clean_inj(k) for k in range(2*R+1)}
scores = []
for k in range(R, NFR-R-1):
    if k+R not in buf:
        buf[k+R] = clean_inj(k+R); buf.pop(k-R-1, None)
    nb = np.stack([buf[j] for j in range(k-R, k+R+1) if j != k and j in buf])
    d = buf[k] - np.median(nb, axis=0)
    band = np.convolve(d.mean(axis=1), np.ones(25)/25, mode="same")
    scores.append((k, float(band.max())))

arr = sorted(scores, key=lambda x: -x[1])
pos = [i for i, (k, _) in enumerate(arr) if k == 50][0]
print(f"\nel caption sintetico (frame 50) sale en posicion {pos+1} de {len(arr)}"
      f"  pico={dict(scores)[50]:+.5f}")
print("-> DETECTOR VALIDO: si hubiera un flash de 1 frame, lo veriamos"
      if pos == 0 else "-> detector ciego a flashes de 1 frame: el barrido anterior no prueba nada")
print("\ntop 5 con la inyeccion:", [(k, round(s,5)) for k, s in arr[:5]])
