#!/usr/bin/env python3
"""Discriminador objetivo que NO depende del ASR: contar NUCLEOS VOCALICOS.

'rickroll' y 'brickwall' tienen 2 (dos picos de energia sonora separados por una
consonante); 'troll' tiene 1. El nucleo vocalico se mide como energia en la banda
de formantes (300-3000 Hz) que ademas sea SONORA (armonica), no ruido.

Se valida el instrumento con un control: la misma medida sobre trozos de la voz
cantada del clip (donde sabemos que hay varias silabas) tiene que dar >1."""
import numpy as np
from scipy.io import wavfile
from scipy import signal, ndimage
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt


def voicing_envelope(x, sr):
    """energia en banda de formantes, y grado de armonicidad por ventana."""
    sos = signal.butter(4, [300, 3000], "bp", fs=sr, output="sos")
    b = signal.sosfiltfilt(sos, x)
    w, hop = int(0.025 * sr), int(0.005 * sr)
    e, hnr = [], []
    for i in range(0, len(b) - w, hop):
        s = b[i:i + w]
        e.append(np.sqrt(np.mean(s ** 2)))
        # armonicidad: pico de autocorrelacion en el rango de F0 humano (70-350 Hz)
        s = s - s.mean()
        ac = np.correlate(s, s, "full")[len(s) - 1:]
        ac = ac / max(ac[0], 1e-12)
        lo, hi = int(sr / 350), int(sr / 70)
        hnr.append(ac[lo:hi].max() if hi < len(ac) else 0.0)
    return np.array(e), np.array(hnr), hop / sr


def count_nuclei(x, sr, name):
    e, hnr, dt = voicing_envelope(x, sr)
    e = e / max(e.max(), 1e-12)
    es = ndimage.uniform_filter1d(e, 5)
    voiced = (es > 0.25) & (hnr > 0.30)
    lab, n = ndimage.label(voiced)
    nuclei = []
    for i in range(1, n + 1):
        idx = np.where(lab == i)[0]
        if len(idx) * dt >= 0.040:          # un nucleo dura >=40 ms
            nuclei.append((idx[0] * dt, len(idx) * dt, es[idx].max()))
    print(f"\n{name}: duracion {len(x)/sr*1000:.0f} ms -> {len(nuclei)} nucleo(s) vocalico(s)")
    for t0, d, pk in nuclei:
        print(f"    nucleo en t={t0*1000:6.1f} ms, dura {d*1000:5.1f} ms, pico {pk:.2f}")
    return len(nuclei), es, hnr, dt


sr, v = wavfile.read("voz_limpia.wav")
v = v.astype(np.float64) / 32768
n_voice, es_v, hnr_v, dt = count_nuclei(v, sr, "LA VOZ DEL RETO")

# --- control del instrumento: musica cantada del mismo fichero --------------
sr2, L = wavfile.read("hifi2_L.wav")
L = L.astype(np.float64) / 32768
print("\n--- control: el instrumento tiene que contar >1 en trozos con varias silabas ---")
for t0, t1 in [(1.5, 2.2), (6.0, 6.7), (7.5, 8.2)]:
    count_nuclei(L[int(t0 * sr2):int(t1 * sr2)], sr2, f"control musica {t0}-{t1}s")

print("""
LECTURA:
  1 nucleo -> palabra de UNA silaba  ('troll', 'roll', 'crawl')
  2 nucleos -> DOS silabas           ('rick-roll', 'brick-wall', 'rick-hell')""")

fig, axes = plt.subplots(2, 1, figsize=(13, 7))
t = np.arange(len(es_v)) * dt * 1000
axes[0].plot(t, es_v, lw=1.2, label="energia banda de formantes")
axes[0].axhline(0.25, color="r", ls="--", lw=.8, label="umbral")
axes[0].set_title(f"voz del reto: {n_voice} nucleo(s) vocalico(s)")
axes[0].set_xlabel("ms"); axes[0].legend(); axes[0].grid(alpha=.3)
axes[1].plot(t, hnr_v, lw=1.2, color="g", label="armonicidad (sonoridad)")
axes[1].axhline(0.30, color="r", ls="--", lw=.8)
axes[1].set_xlabel("ms"); axes[1].legend(); axes[1].grid(alpha=.3)
plt.tight_layout(); plt.savefig("syllables.png", dpi=120)
print("-> syllables.png")
