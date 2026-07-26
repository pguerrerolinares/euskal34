#!/usr/bin/env python3
"""Descarte las barras de las lineas 5-21 mirando la MEDIA de 249 frames: salian
iguales en todas las lineas -> parecia artefacto. Pero ese razonamiento esta MAL:
si fueran datos distintos frame a frame, la media los borraria y solo dejaria lo
comun. El test correcto es UN FRAME SUELTO.

Hipotesis a batir: adaptador PCM EIAJ (Sony PCM-F1 y similares) graba audio digital
como video B/N de barras sobre cinta. Nuestra cinta ES B/N (0% de croma). Encaja con
'dispositivo vintage en el que reproducir/grabar'.

Firma de datos: (a) el patron CAMBIA entre frames, (b) las transiciones caen en una
rejilla de periodo constante (el reloj de bit), (c) el histograma es bimodal (2 niveles)."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

W, LPF = 2011, 625
msg = np.load("msg_full.npy", mmap_mode="r")


def frame(k):
    return np.asarray(msg[k * LPF * W:(k + 1) * LPF * W],
                      dtype=np.float64).reshape(LPF, W)


FR = [40, 41, 100, 125, 200]
fs = {k: frame(k) for k in FR}

# (a) ¿el patron de VBI cambia entre frames?
print("== (a) ¿cambia la franja de VBI (lineas 0-25) entre frames? ==")
ref = fs[40][0:25, 145:2011]
for k in FR[1:]:
    o = fs[k][0:25, 145:2011]
    c = np.corrcoef(ref.ravel(), o.ravel())[0, 1]
    print(f"  frame 40 vs {k:3d}: corr={c:+.4f}  rms_dif={np.std(ref-o):.4f}")
# control: dos franjas de IMAGEN de los mismos frames
ref_i = fs[40][300:325, 600:1700]
print("  (control, franja de imagen 300-325):")
for k in FR[1:]:
    o = fs[k][300:325, 600:1700]
    print(f"     frame 40 vs {k:3d}: corr={np.corrcoef(ref_i.ravel(), o.ravel())[0,1]:+.4f}")

# (b) ¿el patron cambia entre LINEAS del mismo frame?
print("\n== (b) ¿cambia entre lineas del mismo frame (125)? ==")
f = fs[125]
for a, b in [(5, 6), (5, 10), (5, 15), (5, 20), (10, 20)]:
    c = np.corrcoef(f[a, 145:2011], f[b, 145:2011])[0, 1]
    print(f"  linea {a:2d} vs {b:2d}: corr={c:+.4f}")

# (c) reloj de bit: autocorrelacion y espectro de una linea de VBI
print("\n== (c) ¿hay reloj de bit en las lineas de VBI? ==")
for ln in (5, 8, 12, 18):
    x = f[ln, 530:1755]
    x = x - x.mean()
    sp = np.abs(np.fft.rfft(x * np.hanning(x.size)))
    fr = np.fft.rfftfreq(x.size, 1.0)  # ciclos por muestra
    k = int(np.argmax(sp[3:])) + 3
    print(f"  linea {ln:2d}: pico espectral en {fr[k]*x.size:6.1f} ciclos/linea "
          f"({1/max(fr[k],1e-9):5.1f} muestras/ciclo), "
          f"prominencia {sp[k]/np.median(sp):5.1f}x")
    # bimodalidad: un tren de bits tiene 2 niveles claros
    h, _ = np.histogram(x, bins=40)
    print(f"           bimodalidad (2 modas separadas): kurtosis={((x-x.mean())**4).mean()/x.var()**2:.2f} "
          f"(gaussiano=3.0, cuadrada=1.0)")


def show(ax, x, title, pct=(1, 99)):
    lo, hi = np.percentile(x, pct[0]), np.percentile(x, pct[1])
    ax.imshow(np.clip((x - lo) / max(hi - lo, 1e-12), 0, 1), cmap="gray",
              aspect="auto", interpolation="nearest")
    ax.set_title(title, fontsize=9)


fig, axes = plt.subplots(len(FR) + 1, 1, figsize=(22, 3 * (len(FR) + 1)))
for ax, k in zip(axes, FR):
    show(ax, fs[k][0:30, :], f"frame {k} SUELTO, lineas 0-30, anchura completa")
show(axes[-1], fs[125][0:30, :] - fs[40][0:30, :],
     "DIFERENCIA frame125 - frame40 en la VBI (si son datos, no se cancela)")
plt.tight_layout(); plt.savefig("vbi_singleframe.png", dpi=140); plt.close()
print("\n-> vbi_singleframe.png")
