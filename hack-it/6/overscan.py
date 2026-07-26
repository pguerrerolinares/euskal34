#!/usr/bin/env python3
"""El MP4 revisado estaba recortado a la zona visible. Mirar el OVERSCAN: las
primeras y ultimas lineas de cada frame, y los bordes laterales, que ninguna TV
muestra y que un render normal recorta."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

W, LPF, NFR = 2011, 625, 250
msg = np.load("msg_full.npy", mmap_mode="r")
NL = msg.shape[0] // W
lines = np.lib.stride_tricks.as_strided(msg, (NL, W), (W*msg.itemsize, msg.itemsize))
NOTCH = [(160, 190), (192, 215)]

def clean(k):
    f = np.asarray(lines[k*LPF:min((k+1)*LPF, NL)], dtype=np.float32)
    F = np.fft.rfft(f, axis=1)
    for a, b in NOTCH: F[:, a:b+1] = 0
    return np.fft.irfft(F, W, axis=1)

def norm(x):
    lo, hi = np.percentile(x, 1), np.percentile(x, 99.5)
    return np.clip((x-lo)/max(hi-lo, 1e-9), 0, 1)

# banda superior e inferior de todos los frames, apiladas
tops, bots, lefts, rights = [], [], [], []
for k in range(NFR):
    f = clean(k)
    if f.shape[0] < 620: continue
    tops.append(f[:45, 300:].mean(axis=0))
    bots.append(f[-45:, 300:].mean(axis=0))
    lefts.append(f[:, 300:420].mean(axis=1))
    rights.append(f[:, -120:].mean(axis=1))

for tag, arr in (("overscan_superior", tops), ("overscan_inferior", bots)):
    m = np.array(arr)
    plt.figure(figsize=(18, 7))
    plt.imshow(norm(m), cmap="gray", aspect="auto")
    plt.xlabel("columna"); plt.ylabel("frame"); plt.title(tag)
    plt.tight_layout(); plt.savefig(f"{tag}.png", dpi=110); plt.close()
    print(f"-> {tag}.png   contraste={m.std():.4f}")

# y un frame concreto con TODAS las lineas, marcando la zona no visible
f = clean(125)
plt.figure(figsize=(16, 9))
plt.imshow(norm(f), cmap="gray", aspect="auto")
plt.axhline(45, color="r", lw=1); plt.axhline(f.shape[0]-45, color="r", lw=1)
plt.axvline(300, color="c", lw=1)
plt.title("frame 125 COMPLETO (rojo: limite de overscan, cian: fin del blanking)")
plt.tight_layout(); plt.savefig("frame125_full.png", dpi=110); plt.close()
print("-> frame125_full.png")
