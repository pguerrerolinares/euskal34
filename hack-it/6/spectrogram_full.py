#!/usr/bin/env python3
"""Todo nuestro analisis espectral fue Welch PROMEDIADO sobre el fichero entero:
eso aplasta el eje temporal. Si el autor dibujo algo en el espectro (el truco
Aphex Twin, clasico donde los haya y coherente con el titulo 'Classical Music')
un Welch promediado lo ve como energia difusa, no como imagen.

Aqui: espectrograma completo de la RF cruda, 0-15.7 MHz x 10 s. Las bandas
1.9-3.0 MHz y 5.5-15.7 MHz estan practicamente vacias -> son el lienzo obvio.
Se resta el suelo POR BANDA para que la luma FM (91% de la energia) no lo tape."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

FS = 31415926.0
raw = np.memmap("out.wav", dtype=np.int16, mode="r", offset=44)
N = raw.size

NCOL = 1600            # columnas de tiempo -> 6.25 ms cada una
NFFT = 8192            # 3835 Hz/bin, 4096 bins hasta 15.7 MHz
PER = N // NCOL
NAVG = max(1, min(16, PER // NFFT))
w = np.hanning(NFFT)
print(f"{NCOL} columnas x {NFFT//2+1} bins, {NAVG} FFT promediadas por columna")

S = np.zeros((NFFT // 2 + 1, NCOL), dtype=np.float32)
for c in range(NCOL):
    base = c * PER
    acc = np.zeros(NFFT // 2 + 1)
    for j in range(NAVG):
        a = base + j * (PER // NAVG)
        if a + NFFT > N:
            break
        s = raw[a:a + NFFT].astype(np.float64)
        acc += np.abs(np.fft.rfft((s - s.mean()) * w)) ** 2
    S[:, c] = acc / NAVG
    if c % 400 == 0:
        print(f"  {c}/{NCOL}")

np.save("spec_full.npy", S)
f = np.fft.rfftfreq(NFFT, 1 / FS)
L = 10 * np.log10(S + 1e-30)

# resta del suelo por banda: la mediana temporal de cada bin.
# lo que quede es lo que VARIA en el tiempo dentro de esa frecuencia.
med = np.median(L, axis=1, keepdims=True)
D = L - med


def draw(ax, lo, hi, img, title, pct=(2, 99.8)):
    m = (f >= lo) & (f < hi)
    x = img[m]
    a, b = np.percentile(x, pct[0]), np.percentile(x, pct[1])
    ax.imshow(np.clip((x - a) / max(b - a, 1e-9), 0, 1), cmap="inferno",
              aspect="auto", origin="lower",
              extent=[0, N / FS, lo / 1e6, hi / 1e6])
    ax.set_title(title, fontsize=10)
    ax.set_ylabel("MHz")


fig, axes = plt.subplots(4, 1, figsize=(18, 20))
draw(axes[0], 0, FS / 2, D, "espectrograma COMPLETO 0-15.7 MHz (suelo por bin restado)")
draw(axes[1], 1.9e6, 3.1e6, D, "banda vacia 1.9-3.1 MHz")
draw(axes[2], 5.5e6, 15.7e6, D, "banda vacia 5.5-15.7 MHz")
draw(axes[3], 0, 1.3e6, D, "banda baja 0-1.3 MHz")
axes[-1].set_xlabel("segundos")
plt.tight_layout(); plt.savefig("spectrogram_full.png", dpi=115); plt.close()

# --- deteccion objetiva: bins cuya energia VARIA mucho en el tiempo ----------
print("\n== bins con mayor variacion temporal fuera de las bandas conocidas ==")
var = D.std(axis=1)
known = ((f > 3.0e6) & (f < 5.5e6)) | ((f > 1.35e6) & (f < 1.45e6)) | \
        ((f > 1.75e6) & (f < 1.85e6)) | (f < 50e3)
cand = np.where(~known)[0]
top = cand[np.argsort(var[cand])[::-1][:25]]
for i in sorted(top, key=lambda j: -var[j]):
    print(f"  {f[i]/1e6:9.4f} MHz  variacion temporal {var[i]:6.2f} dB  "
          f"nivel {med[i,0]:7.1f} dB")
print(f"\n  (variacion mediana en zona vacia: {np.median(var[cand]):.2f} dB)")
print("-> spectrogram_full.png / spec_full.npy")
