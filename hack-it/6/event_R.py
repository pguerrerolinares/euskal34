#!/usr/bin/env python3
"""HALLAZGO: en t=5.00-5.50 s la correlacion L/R cae a 0.19 y R esta 9 dB por
ENCIMA de L. La sesion anterior dio R por plano y solo trabajo el evento de voz de
L (4.6-5.2 s). Hay un segundo evento, en el otro canal, inmediatamente despues.

Tres portadoras, tres partes: luma -> Part 1/3. Si L lleva la 2 y R la 3, encaja.

Aqui: energias absolutas con resolucion fina, y aislamiento del evento de R usando
L como referencia de la musica (filtro FIR por minimos cuadrados, igual que nlms.py
pero al reves)."""
import numpy as np
from scipy.io import wavfile
from scipy.linalg import toeplitz
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sr, L = wavfile.read("hifi2_L.wav")
_, R = wavfile.read("hifi2_R.wav")
L = L.astype(np.float64); R = R.astype(np.float64)
n = min(L.size, R.size); L, R = L[:n], R[:n]

# --- energias absolutas, ventanas de 50 ms --------------------------------
w = sr // 20
t, eL, eR = [], [], []
for i in range(0, n - w, w):
    t.append(i / sr)
    eL.append(10 * np.log10(np.mean(L[i:i+w] ** 2) + 1e-12))
    eR.append(10 * np.log10(np.mean(R[i:i+w] ** 2) + 1e-12))
t, eL, eR = np.array(t), np.array(eL), np.array(eR)
print("energias absolutas (dB) en la zona critica 4.2-6.0 s:")
m = (t >= 4.2) & (t <= 6.0)
for tt, a, b in zip(t[m], eL[m], eR[m]):
    d = b - a
    mark = "  <== R domina" if d > 4 else ("  <== L domina" if d < -4 else "")
    print(f"  t={tt:5.2f}s  L={a:7.2f}  R={b:7.2f}  R-L={d:+6.2f}{mark}")

base = np.median(eR[(t < 4.0) | (t > 6.5)])
print(f"\nnivel de fondo de R fuera del evento: {base:.2f} dB")
pk = t[(t > 4.8) & (t < 6.0)][np.argmax(eR[(t > 4.8) & (t < 6.0)])]
print(f"pico de R en t={pk:.2f}s, {eR[(t>4.8)&(t<6.0)].max()-base:+.2f} dB sobre fondo")


# --- aislar lo que hay en R y no en L -------------------------------------
def cancel(target, ref, taps=128):
    """filtro FIR global que mejor predice target a partir de ref; devuelve residuo."""
    N = min(target.size, ref.size)
    tg, rf = target[:N], ref[:N]
    r = np.correlate(rf, rf, "full")[N - 1:N - 1 + taps]
    p = np.correlate(tg, rf, "full")[N - 1:N - 1 + taps]
    h = np.linalg.solve(toeplitz(r) + np.eye(taps) * r[0] * 1e-6, p)
    return tg - np.convolve(rf, h, "same"), h


resR, _ = cancel(R, L)      # lo que hay en R y NO en L
resL, _ = cancel(L, R)      # lo que hay en L y NO en R  (la voz ya conocida)
print(f"\ncancelacion: R con L de referencia -> residuo {100*resR.std()/R.std():.1f}%")
print(f"             L con R de referencia -> residuo {100*resL.std()/L.std():.1f}%")

for tag, x in (("R_solo", resR), ("L_solo", resL)):
    e = []
    for i in range(0, n - w, w):
        e.append(10 * np.log10(np.mean(x[i:i+w] ** 2) + 1e-12))
    e = np.array(e)
    b = np.median(e)
    top = np.argsort(e)[::-1][:6]
    print(f"\n  {tag}: picos del residuo sobre fondo ({b:.1f} dB):")
    for i in sorted(top):
        print(f"    t={t[i]:5.2f}s  {e[i]-b:+6.2f} dB")

# guardar el evento de R aislado, tal cual y ralentizado
a0, a1 = int(4.6 * sr), int(6.2 * sr)
for tag, x in (("Rsolo_event", resR[a0:a1]), ("Rraw_event", R[a0:a1])):
    y = x / max(np.abs(x).max(), 1e-12)
    wavfile.write(f"{tag}.wav", sr, (y * 30000).astype(np.int16))
    wavfile.write(f"{tag}_slow.wav", sr // 2, (y * 30000).astype(np.int16))
print("\n-> Rsolo_event.wav / Rraw_event.wav (+ _slow)")

fig, axes = plt.subplots(2, 1, figsize=(15, 9))
axes[0].plot(t, eL, label="L"); axes[0].plot(t, eR, label="R")
axes[0].axvspan(4.5, 5.6, color="orange", alpha=.2)
axes[0].set_title("energia por canal (50 ms)"); axes[0].legend(); axes[0].grid(alpha=.3)
axes[1].specgram(resR, NFFT=2048, Fs=sr, noverlap=1536, cmap="inferno")
axes[1].set_ylim(0, 6000); axes[1].set_xlim(4.0, 6.5)
axes[1].set_title("espectrograma del residuo R (lo que hay en R y no en L)")
plt.tight_layout(); plt.savefig("event_R.png", dpi=115)
print("-> event_R.png")
