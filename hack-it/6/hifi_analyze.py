#!/usr/bin/env python3
"""?Que hay en los canales HiFi? Voz, musica, tonos, o datos (SSTV/morse/cinta)?"""
import numpy as np
from scipy import signal
from scipy.io import wavfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

for tag in ("L", "R"):
    try:
        fs, a = wavfile.read(f"hifi_{tag}.wav")
    except FileNotFoundError:
        print(f"[{tag}] no generado aun"); continue
    a = a.astype(np.float64) / 32768
    a = a[int(0.05 * fs):]                      # descartar transitorio de arranque
    a /= max(np.abs(a).max(), 1e-12)
    print(f"\n===== canal {tag}: {a.size/fs:.2f} s, rms={np.sqrt((a**2).mean()):.4f} =====")

    sp = np.abs(np.fft.rfft(a * np.hanning(a.size)))
    f = np.fft.rfftfreq(a.size, 1 / fs)
    top = np.argsort(sp)[::-1][:400]
    seen, peaks = set(), []
    for t in top:                                # agrupar picos cercanos
        fq = f[t]
        if any(abs(fq - s) < 25 for s in seen):
            continue
        seen.add(fq); peaks.append((fq, sp[t] / sp.max()))
        if len(peaks) >= 12:
            break
    print("  tonos dominantes:", ", ".join(f"{fq:.0f}Hz({e:.2f})" for fq, e in peaks))

    # ?tonos discretos (datos) o espectro continuo (voz/musica)?
    tot = np.sum(sp ** 2)
    conc = sum(sp[max(0, np.argmin(abs(f - fq)) - 30):np.argmin(abs(f - fq)) + 30].sum() ** 2
               for fq, _ in peaks[:4]) / tot
    print(f"  energia en los 4 tonos principales: {conc:.1%}"
          f"  -> {'TONOS DISCRETOS (datos)' if conc > .3 else 'espectro continuo (voz/musica)'}")

    for a1, b1 in ((0, 300), (300, 1000), (1000, 3000), (3000, 8000), (8000, 24000)):
        m = (f >= a1) & (f < b1)
        print(f"    {a1:5d}-{b1:5d} Hz: {100*np.sum(sp[m]**2)/tot:5.1f} %")

    fr, tt, S = signal.spectrogram(a, fs, nperseg=1024, noverlap=768)
    plt.figure(figsize=(16, 6))
    plt.pcolormesh(tt, fr, 10 * np.log10(S + 1e-14), shading="auto", cmap="magma")
    plt.ylim(0, 6000); plt.colorbar(label="dB")
    plt.title(f"VHS HiFi canal {tag}"); plt.xlabel("s"); plt.ylabel("Hz")
    plt.tight_layout(); plt.savefig(f"hifi_{tag}_spec.png", dpi=110); plt.close()
    print(f"  espectrograma -> hifi_{tag}_spec.png")
