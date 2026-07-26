#!/usr/bin/env python3
"""El test anterior no tenia control -> no valia. Aqui, con controles:
  (1) el mismo procedimiento de cancelacion aplicado a tramos de control
  (2) correlacion L/R ventana a ventana: si el evento es algo puesto en un solo
      canal, la correlacion se hunde ahi y no en el resto."""
import numpy as np
from scipy.io import wavfile
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

fs, L = wavfile.read("hifi2_L.wav"); L = L.astype(float)/32768
_,  R = wavfile.read("hifi2_R.wav"); R = R.astype(float)/32768
n = min(L.size, R.size); L, R = L[:n], R[:n]

print("=== (1) cancelacion contra el resto del audio: evento vs controles ===")
def best_cancel(t0, t1):
    a, b = int(t0*fs), int(t1*fs)
    ev = L[a:b]; out = []
    for off in np.arange(-4.5, 4.6, 0.01):
        j = int(a + off*fs)
        if j < 0 or j + ev.size > L.size or abs(off) < 0.2: continue
        o = L[j:j+ev.size]
        g = np.dot(ev, o)/max(np.dot(o, o), 1e-12)
        out.append(np.sqrt(np.mean((ev-g*o)**2))/np.sqrt(np.mean(ev**2)))
    return min(out)

for tag, (t0, t1) in (("EVENTO ", (4.60, 5.08)), ("ctrl 1.5", (1.50, 1.98)),
                      ("ctrl 2.5", (2.50, 2.98)), ("ctrl 6.0", (6.00, 6.48)),
                      ("ctrl 7.5", (7.50, 7.98)), ("ctrl 8.5", (8.50, 8.98))):
    print(f"  {tag}: mejor residuo = {best_cancel(t0, t1):.4f}")
print("  -> si el evento da un valor parecido a los controles, NO es anomalo")

print("\n=== (2) correlacion L/R por ventana de 100 ms ===")
wl = int(0.1*fs)
ts, cs = [], []
for i in range(0, n - wl, wl//2):
    a, b = L[i:i+wl], R[i:i+wl]
    c = np.corrcoef(a, b)[0, 1]
    ts.append(i/fs); cs.append(c)
cs = np.array(cs); ts = np.array(ts)
m = (ts > 4.5) & (ts < 5.15)
print(f"  correlacion media global : {np.nanmean(cs):+.3f}  (desv {np.nanstd(cs):.3f})")
print(f"  correlacion en el EVENTO : {np.nanmean(cs[m]):+.3f}")
z = (np.nanmean(cs[m]) - np.nanmean(cs)) / max(np.nanstd(cs), 1e-9)
print(f"  z-score del evento: {z:+.2f} sigma"
      + ("   <-- ANOMALIA REAL" if abs(z) > 2.5 else "   (dentro de lo normal)"))

print("\n  ventanas con correlacion mas baja de todo el audio:")
for i in np.argsort(cs)[:8]:
    print(f"    t={ts[i]:5.2f}s  corr={cs[i]:+.3f}")

plt.figure(figsize=(15,4))
plt.plot(ts, cs, lw=.9); plt.axvspan(4.6, 5.08, color="red", alpha=.2)
plt.axhline(np.nanmean(cs), color="k", ls="--", lw=.8)
plt.xlabel("s"); plt.ylabel("corr L/R"); plt.grid(alpha=.3)
plt.title("correlacion entre canales (el evento marcado en rojo)")
plt.tight_layout(); plt.savefig("corr_lr.png", dpi=110)
print("\n-> corr_lr.png")
