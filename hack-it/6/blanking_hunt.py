#!/usr/bin/env python3
"""Buscar en lo que NUNCA se mira: la zona de blanking (sync + back porch, muestras
0-300 de cada linea), invisible en cualquier render. Dos canales posibles:
  (a) datos dibujados en el back porch de algunas lineas
  (b) modulacion de la ANCHURA del pulso de sync (PWM) linea a linea"""
import numpy as np

W = 2011
msg = np.load("msg_full.npy", mmap_mode="r")
NL = msg.shape[0] // W
lines = np.lib.stride_tricks.as_strided(msg, (NL, W), (W * msg.itemsize, msg.itemsize))
print(f"lineas: {NL}")

CH = 20000
sync_lo, sync_hi, bp_lo, bp_hi = 0, 147, 155, 300
anom, widths, bp_energy = [], [], []
for c0 in range(0, NL, CH):
    blk = np.asarray(lines[c0:c0 + CH], dtype=np.float32)
    sync_lvl = blk[:, 20:120].mean(axis=1, keepdims=True)
    blank_lvl = blk[:, 200:290].mean(axis=1, keepdims=True)
    # (a) rugosidad del back porch: desviacion respecto a su propio nivel
    bp = blk[:, bp_lo:bp_hi]
    rough = bp.std(axis=1)
    bp_energy.append(rough)
    # (b) anchura del sync: cruce del punto medio entre nivel sync y nivel blanking
    thr = (sync_lvl + blank_lvl) / 2
    below = blk[:, :400] < thr
    widths.append(below[:, :400].sum(axis=1).astype(np.int16))

rough = np.concatenate(bp_energy)
widths = np.concatenate(widths)

print(f"\n--- (a) rugosidad del back porch ---")
print(f"  media={rough.mean():.4f} mediana={np.median(rough):.4f} p99={np.quantile(rough,.99):.4f} max={rough.max():.4f}")
out = np.flatnonzero(rough > np.median(rough) + 6 * rough.std())
print(f"  lineas con back porch anomalo (>6 sigma): {out.size}")
if out.size:
    print(f"    primeras: {out[:20].tolist()}")
    print(f"    frames implicados: {sorted(set((out//625).tolist()))[:20]}")

print(f"\n--- (b) anchura del pulso de sync (muestras) ---")
vals, cnt = np.unique(widths, return_counts=True)
order = np.argsort(cnt)[::-1]
print("  valores mas frecuentes:", [(int(vals[i]), int(cnt[i])) for i in order[:8]])
print(f"  distintos: {vals.size}  min={vals.min()} max={vals.max()}")
if vals.size == 2:
    a, b = sorted(vals.tolist())
    bits = (widths == b).astype(np.uint8)
    print(f"  BINARIO: {a}->0, {b}->1  ({bits.sum()} unos de {bits.size})")
    bs = "".join(map(str, bits[: (bits.size // 8) * 8]))
    txt = "".join(chr(int(bs[i:i+8], 2)) for i in range(0, min(len(bs), 8000), 8))
    print(f"  como ASCII: {txt[:120]!r}")
np.save("sync_widths.npy", widths)
np.save("bp_rough.npy", rough)
print("\nguardado sync_widths.npy / bp_rough.npy")
