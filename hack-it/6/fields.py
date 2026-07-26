#!/usr/bin/env python3
"""PAL es ENTRELAZADO: cada frame = campo par + campo impar, mostrados en
instantes distintos. Si hay un caption por campo, en el frame progresivo salen
intercalados linea a linea y solo se lee el dominante. Separar los campos."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

W, LPF = 2011, 625
msg = np.load("msg_full.npy", mmap_mode="r")
NL = msg.shape[0] // W
lines = np.lib.stride_tricks.as_strided(msg, (NL, W), (W*msg.itemsize, msg.itemsize))

def frame(k):
    return np.asarray(lines[k*LPF:(k+1)*LPF, 300:], dtype=np.float32)

def norm(img):
    lo, hi = np.percentile(img, 1), np.percentile(img, 99)
    return np.clip((img - lo) / max(hi - lo, 1e-9), 0, 1)

for k in (124, 125, 126):
    f = frame(k)
    fa, fb = f[0::2], f[1::2]           # campo A (pares), campo B (impares)
    fig, ax = plt.subplots(3, 1, figsize=(15, 16))
    for a, img, tag in ((ax[0], f, f"frame {k} completo"),
                        (ax[1], fa, f"frame {k} CAMPO A (lineas pares)"),
                        (ax[2], fb, f"frame {k} CAMPO B (lineas impares)")):
        a.imshow(norm(img), cmap="gray", aspect="auto")
        a.set_title(tag); a.axis("off")
    plt.tight_layout(); plt.savefig(f"field_{k}.png", dpi=95); plt.close()
    print(f"-> field_{k}.png")

    # diferencia entre campos: si llevan captions distintos, salta aqui
    m = min(fa.shape[0], fb.shape[0])
    d = np.abs(fa[:m] - fb[:m])
    print(f"   frame {k}: dif media entre campos = {d.mean():.4f}, max = {d.max():.4f}")
