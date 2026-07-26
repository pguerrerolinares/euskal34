#!/usr/bin/env python3
"""Barrido sistematico: TODAS las portadoras estrechas del espectro, no solo las
que ya conociamos. Y sonda de la croma color-under (~688 kHz): si tiene burst con
estructura de linea, hay COLOR -> un texto en color puro es invisible en el luma."""
import numpy as np

FS, W = 31415926.0, 2011
raw = np.memmap("out.wav", dtype=np.int16, mode="r", offset=44)
N = raw.size

n = 1 << 23
off = (N // 2 // W) * W
x = np.asarray(raw[off:off + n], dtype=np.float64)
x -= x.mean()
sp = np.abs(np.fft.rfft(x * np.hanning(n)))
f = np.fft.rfftfreq(n, 1 / FS)

# portadora estrecha = pico muy por encima de la mediana local
print("--- portadoras estrechas en todo el espectro (pico/mediana local > 20) ---")
win = 4000
found = []
i = 100
while i < sp.size - win:
    seg = sp[i:i + win]
    k = i + int(np.argmax(seg))
    med = np.median(sp[max(0, k - 4 * win):k + 4 * win])
    if sp[k] / max(med, 1e-9) > 20:
        if not found or abs(f[k] - found[-1][0]) > 50e3:
            found.append((f[k], sp[k] / med))
    i += win
for fq, r in found:
    print(f"  {fq/1e6:9.5f} MHz   {fq/FS*W:8.2f} c/linea   pico/mediana={r:9.1f}")

# --- croma color-under: ?tiene estructura de linea (burst en el back porch)? ---
print("\n--- sonda croma color-under ---")
for fc, tag in ((626.95e3, "VHS PAL 626.95k"), (688.8e3, "pico medido 688.8k"),
                (743.44e3, "Video8 743.4k")):
    NB = 1 << 21
    seg = np.asarray(raw[off:off + NB], dtype=np.float64)
    t = np.arange(NB) / FS
    bb = seg * np.exp(-2j * np.pi * fc * t)
    # filtro paso bajo grosero por FFT a +-300 kHz y decimar a nivel de linea
    Sp = np.fft.fft(bb)
    k = int(300e3 * NB / FS)
    Sp[k:-k] = 0
    bb = np.fft.ifft(Sp)
    amp = np.abs(bb)
    nl = amp.size // W
    lines = amp[:nl * W].reshape(nl, W)
    prof = lines.mean(axis=0)
    # el burst vive en el back porch (muestras ~150-300); comparar con el activo
    bp, act = prof[150:300].mean(), prof[400:].mean()
    print(f"  {tag:22s} backporch={bp:.1f} activo={act:.1f} ratio={bp/max(act,1e-9):.3f}"
          + ("   <-- BURST" if bp / max(act, 1e-9) > 1.5 else ""))
