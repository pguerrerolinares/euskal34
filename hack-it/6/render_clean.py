#!/usr/bin/env python3
"""Renderizar los 250 frames SIN la intermodulacion del audio, para revisarlos a
ojo. Tambien un 'mapa de captions': cada frame colapsado a una fila, los 250
apilados -> un caption aparece como una banda brillante."""
import numpy as np, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

W, LPF, NFR = 2011, 625, 250
msg = np.load("msg_full.npy", mmap_mode="r")
NL = msg.shape[0] // W
lines = np.lib.stride_tricks.as_strided(msg, (NL, W), (W*msg.itemsize, msg.itemsize))
NOTCH = [(160, 190), (192, 215)]
os.makedirs("clean_frames", exist_ok=True)

def clean_frame(k):
    f = np.asarray(lines[k*LPF:min((k+1)*LPF, NL)], dtype=np.float32)
    F = np.fft.rfft(f, axis=1)
    for a, b in NOTCH:
        F[:, a:b+1] = 0
    return np.fft.irfft(F, W, axis=1)[:, 300:]

rows = []
for k in range(NFR):
    f = clean_frame(k)
    if f.shape[0] < 600: continue
    lo, hi = np.percentile(f, 1), np.percentile(f, 99.5)
    img = np.clip((f - lo)/max(hi-lo, 1e-9), 0, 1)
    Image.fromarray((img*255).astype(np.uint8)).resize((856, 625)).save(
        f"clean_frames/f{k:03d}.png")
    rows.append(img[150:450].max(axis=0))
    if k % 50 == 0: print(f"  frame {k}")

print(f"{len(rows)} frames -> clean_frames/")
m = np.array(rows)
plt.figure(figsize=(18, 9))
plt.imshow(m, cmap="gray", aspect="auto",
           extent=[0, m.shape[1], m.shape[0], 0], vmin=np.percentile(m,5), vmax=np.percentile(m,99.9))
plt.xlabel("columna"); plt.ylabel("frame")
plt.title("mapa de captions: banda central de cada frame colapsada (un caption = banda brillante)")
plt.tight_layout(); plt.savefig("caption_map.png", dpi=110)
print("-> caption_map.png")
