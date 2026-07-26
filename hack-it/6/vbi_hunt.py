#!/usr/bin/env python3
"""Ahora que sabemos que hay SYNC horizontal real (4.7us), mapear la estructura
de linea y de campo: donde esta el back porch/burst, y que lineas son VBI.
Clave: NO promediar entre frames (eso fue lo que engano la vez anterior)."""
import numpy as np

W, LPF = 2011, 625            # muestras/linea, lineas/frame
msg = np.load("msg_full.npy", mmap_mode="r")
NL = msg.shape[0] // W
lines = np.lib.stride_tricks.as_strided(msg, (NL, W), (W * msg.itemsize, msg.itemsize))

blk = np.asarray(lines[:40000], dtype=np.float64)
mu, sd = blk.mean(axis=0), blk.std(axis=0)

print("perfil de linea (primeras 340 muestras, paso 20): pos media desv")
for p in range(0, 340, 20):
    bar = "#" * int(40 * (mu[p] - mu.min()) / (mu.max() - mu.min()))
    print(f"  {p:4d} ({p/W*64:5.2f}us) media={mu[p]:+.4f} desv={sd[p]:.4f} {bar}")
print(f"\ndesv media en sync(0-147)={sd[:147].mean():.4f} "
      f"backporch(150-300)={sd[150:300].mean():.4f} activo(350+)={sd[350:].mean():.4f}")

# --- estructura de campo: energia por numero de linea dentro del frame ------
nfr = NL // LPF
act = np.abs(np.asarray(lines[:nfr * LPF, 350:], dtype=np.float64)).mean(axis=1)
act = act.reshape(nfr, LPF)
per_line = act.mean(axis=0)
q = np.quantile(per_line, 0.2)
quiet = np.flatnonzero(per_line < q * 0.6)
print(f"\nframes: {nfr}  lineas 'silenciosas' (candidatas a VBI): {len(quiet)}")
print("  indices:", quiet[:40].tolist())

# varianza ENTRE frames de cada linea: una linea VBI con datos varia por frame,
# una linea de blanking puro no varia nada.
var_across = act.std(axis=0)
order = np.argsort(var_across[quiet])[::-1] if len(quiet) else []
print("\nlineas silenciosas ordenadas por variacion ENTRE frames (las de arriba llevan datos):")
for i in list(order)[:12]:
    ln = quiet[i]
    print(f"  linea {ln:4d}  energia={per_line[ln]:.5f}  var_entre_frames={var_across[ln]:.5f}")

np.save("per_line_energy.npy", per_line)
np.save("act_energy.npy", act)
print("\nguardado per_line_energy.npy / act_energy.npy")
