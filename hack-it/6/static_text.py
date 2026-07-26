#!/usr/bin/env python3
"""Un caption es ESTATICO mientras el video detras se mueve. Promediando bloques
de frames, el video se difumina y el texto estatico se refuerza (ruido /sqrt(N)).
Aplicado por bloques a todo el video, no al conjunto entero (eso fue el error de
la vez anterior: promediar los 250 borra lo que dura solo 30)."""
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
    return np.fft.irfft(F, W, axis=1)[:624, 450:1850]

def enhance(img):
    """realce local: quitar la iluminacion de fondo con un paso alto espacial."""
    from scipy import ndimage
    bg = ndimage.uniform_filter(img, size=(31, 31))
    d = img - bg
    lo, hi = np.percentile(d, 1), np.percentile(d, 99)
    return np.clip((d - lo)/max(hi-lo, 1e-9), 0, 1)

BLK = 30
blocks = [(a, min(a+BLK, NFR)) for a in range(0, NFR, BLK//2)]
print(f"{len(blocks)} bloques de {BLK} frames (solapados)")

results = []
for a, b in blocks:
    acc = None
    for k in range(a, b):
        f = clean(k)
        acc = f if acc is None else acc + f
    avg = acc / (b - a)
    e = enhance(avg)
    # medida de "hay texto": bordes verticales concentrados en pocas filas
    gx = np.abs(np.diff(e, axis=1)).mean(axis=1)
    score = np.sort(gx)[::-1][:50].mean() / max(np.median(gx), 1e-9)
    results.append((a, b, score, e))
    print(f"  frames {a:3d}-{b:3d}  score={score:5.2f}")

results.sort(key=lambda r: -r[2])
fig, axes = plt.subplots(4, 1, figsize=(17, 15))
for ax, (a, b, s, e) in zip(axes, results[:4]):
    ax.imshow(e, cmap="gray", aspect="auto")
    ax.set_title(f"media de frames {a}-{b}  (score {s:.2f})", fontsize=11); ax.axis("off")
plt.tight_layout(); plt.savefig("static_top.png", dpi=100); plt.close()
print("-> static_top.png")

# y el bloque del caption conocido, como referencia de que tiene que verse
for a, b, s, e in results:
    if a <= 120 <= b:
        plt.figure(figsize=(17, 7))
        plt.imshow(e, cmap="gray", aspect="auto"); plt.axis("off")
        plt.title(f"bloque del caption conocido: frames {a}-{b}")
        plt.tight_layout(); plt.savefig("static_ref.png", dpi=110); plt.close()
        print("-> static_ref.png")
        break
