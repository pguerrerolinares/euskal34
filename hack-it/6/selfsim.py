#!/usr/bin/env python3
"""Prueba objetiva sin depender del oido: la intro de NGGYU es ciclica.
Si el evento de t~4.8s es PARTE de la musica, se cancelara al restarle el mismo
punto del ciclo anterior/siguiente. Si es algo SUPERPUESTO, sobrevivira."""
import numpy as np
from scipy import signal
from scipy.io import wavfile
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

fs, L = wavfile.read("hifi2_L.wav"); L = L.astype(float) / 32768
_,  R = wavfile.read("hifi2_R.wav"); R = R.astype(float) / 32768

# 1. periodo del ciclo musical via autocorrelacion de la envolvente
env = np.abs(signal.hilbert(signal.sosfilt(
    signal.butter(4, 400, "lp", fs=fs, output="sos"), L)))
env = signal.decimate(env, 100, ftype="fir")
fse = fs / 100
env -= env.mean()
ac = np.correlate(env, env, "full")[env.size-1:]
ac /= max(ac[0], 1e-12)
lo, hi = int(0.8 * fse), int(5.0 * fse)
k = lo + int(np.argmax(ac[lo:hi]))
period = k / fse
print(f"periodo del ciclo musical: {period:.4f} s  (autocorr={ac[k]:.3f})"
      f"  -> {60/period*4:.1f} BPM si es un compas 4/4")

# 2. restar el ciclo vecino en toda la senal y ver donde NO cancela
P = int(round(period * fs))
n = min(L.size - P, L.size)
diff_prev = L[P:P+n-P] - L[:n-P]
t_axis = np.arange(diff_prev.size) / fs + period

print("\nresiduo tras restar el ciclo anterior (energia por 0.25 s):")
vals = []
for t0 in np.arange(period, period + (diff_prev.size/fs) - .25, .25):
    i = int((t0 - period) * fs)
    s = diff_prev[i:i+int(.25*fs)]
    if s.size < 100: break
    vals.append((t0, np.sqrt(np.mean(s**2))))
mx = max(v for _, v in vals)
for t0, v in vals:
    mark = "  <<<" if 4.4 <= t0 <= 5.1 else ""
    print(f"  t={t0:5.2f}s {'#'*int(50*v/mx)}{mark}")

# 3. lo mismo pero comparando L consigo mismo a distintos desfases, centrado en el evento
print("\ncancelacion del EVENTO (4.60-5.08 s) contra otros puntos del audio:")
a, b = int(4.60*fs), int(5.08*fs)
ev = L[a:b]
best = []
for off in np.arange(-4.5, 4.6, 0.01):
    j = int(a + off*fs)
    if j < 0 or j + ev.size > L.size or abs(off) < 0.2: continue
    o = L[j:j+ev.size]
    g = np.dot(ev, o) / max(np.dot(o, o), 1e-12)
    r = np.sqrt(np.mean((ev - g*o)**2)) / np.sqrt(np.mean(ev**2))
    best.append((r, off))
best.sort()
print("  mejores cancelaciones (residuo relativo, desfase):")
for r, off in best[:6]:
    print(f"    residuo={r:.3f}  desfase={off:+.2f}s")
print(f"  -> {'el evento NO se explica por la musica ciclica' if best[0][0] > .8 else 'el evento SI se parece a otro punto de la musica (probablemente es la propia cancion)'}")

plt.figure(figsize=(15,4))
plt.plot([v[0] for v in vals], [v[1] for v in vals], marker="o", ms=3)
plt.axvspan(4.6, 5.08, color="red", alpha=.2)
plt.xlabel("s"); plt.ylabel("residuo rms"); plt.grid(alpha=.3)
plt.title("residuo tras restar el ciclo musical anterior")
plt.tight_layout(); plt.savefig("selfsim.png", dpi=110)
print("\n-> selfsim.png")
