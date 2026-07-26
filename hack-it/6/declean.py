#!/usr/bin/env python3
"""El 'herringbone' que ensucia todos los frames es intermodulacion del audio HiFi
(4.1-1.4=2.7 MHz -> ~176 c/linea ; 1.4+1.8=3.2 MHz -> ~201 c/linea). No son datos:
es basura filtrable. Quitarla y rehacer la busqueda de captions con SNR limpia."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

W, LPF, NFR = 2011, 625, 250
msg = np.load("msg_full.npy", mmap_mode="r")
NL = msg.shape[0] // W
lines = np.lib.stride_tricks.as_strided(msg, (NL, W), (W*msg.itemsize, msg.itemsize))

NOTCH = [(160, 190), (192, 215)]     # bandas de intermodulacion, en ciclos/linea

def clean_frame(k):
    f = np.asarray(lines[k*LPF:(k+1)*LPF], dtype=np.float32)
    F = np.fft.rfft(f, axis=1)
    for a, b in NOTCH:
        F[:, a:b+1] = 0
    return np.fft.irfft(F, W, axis=1)[:, 300:]

def norm(x):
    lo, hi = np.percentile(x, 2), np.percentile(x, 98)
    return np.clip((x-lo)/max(hi-lo, 1e-9), 0, 1)

# validacion: frame 125 sucio vs limpio
raw = np.asarray(lines[125*LPF:126*LPF, 300:], dtype=np.float32)
cln = clean_frame(125)
fig, ax = plt.subplots(2, 1, figsize=(15, 11))
ax[0].imshow(norm(raw), cmap="gray", aspect="auto"); ax[0].set_title("frame 125 ORIGINAL"); ax[0].axis("off")
ax[1].imshow(norm(cln), cmap="gray", aspect="auto"); ax[1].set_title("frame 125 SIN intermodulacion"); ax[1].axis("off")
plt.tight_layout(); plt.savefig("clean125.png", dpi=100); plt.close()
print(f"-> clean125.png   ruido rms: {raw.std():.4f} -> {cln.std():.4f}")

# barrido: detectar en que frames hay un caption (texto = detalle horizontal
# concentrado en pocas filas, que NO esta en los frames vecinos)
print("\nbarrido de los 250 frames (puntuacion de caption):")
prev = clean_frame(0)
scores = []
for k in range(1, NFR):
    cur = clean_frame(k)
    m = min(cur.shape[0], prev.shape[0])
    d = np.abs(cur[:m] - prev[:m])
    rowscore = d.mean(axis=1)
    # un caption afecta a un bloque contiguo de filas, no a todo el frame
    top = np.sort(rowscore)[::-1][:40].mean() / max(np.median(rowscore), 1e-9)
    scores.append((k, top))
    prev = cur
mx = max(s for _, s in scores)
med = np.median([s for _, s in scores])
print(f"  mediana={med:.2f}  maximo={mx:.2f}")
for k, s in sorted(scores, key=lambda x: -x[1])[:15]:
    print(f"    frame {k:3d}  score={s:5.2f}  {'#'*int(30*s/mx)}")
np.save("caption_scores.npy", np.array(scores))
