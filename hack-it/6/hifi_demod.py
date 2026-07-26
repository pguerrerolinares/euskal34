#!/usr/bin/env python3
"""VHS HiFi: demodular la portadora de audio FM a 1.4 MHz (canal L en PAL) y,
si existe, la de 1.8 MHz (canal R). Salida a WAV de 48 kHz para escuchar."""
import numpy as np
from scipy import signal

FS, W = 31415926.0, 2011
raw = np.memmap("out.wav", dtype=np.int16, mode="r", offset=44)
N = raw.size

# --- 1. localizar con precision las portadoras candidatas -------------------
n = 1 << 22
x = np.asarray(raw[N // 2: N // 2 + n], dtype=np.float64)
x -= x.mean()
sp = np.abs(np.fft.rfft(x * np.hanning(n)))
f = np.fft.rfftfreq(n, 1 / FS)
for lo, hi, tag in ((1.2e6, 1.6e6, "L?"), (1.6e6, 2.0e6, "R?"), (0.5e6, 0.8e6, "croma?")):
    m = (f > lo) & (f < hi)
    k = np.flatnonzero(m)[np.argmax(sp[m])]
    base = np.median(sp[m])
    print(f"{tag:7s} banda {lo/1e6:.1f}-{hi/1e6:.1f} MHz -> pico {f[k]/1e6:.6f} MHz, "
          f"pico/mediana={sp[k]/base:8.1f}" + ("   *** PORTADORA ***" if sp[k]/base > 50 else ""))

# --- 2. demodular FM en torno a una portadora, por bloques ------------------
def demod(fc, dec=32, out_fs=48000, tag="L"):
    step = 1 << 23
    guard = 4096
    chunks = []
    for start in range(0, N, step):
        a = max(0, start - guard)
        b = min(N, start + step + guard)
        seg = np.asarray(raw[a:b], dtype=np.float64)
        t = np.arange(a, b) / FS
        bb = seg * np.exp(-2j * np.pi * fc * t)           # mezcla a banda base
        bb = signal.decimate(bb, dec, ftype="fir", zero_phase=True)   # ~982 kHz
        lo = (a - a) if a == start else (start - a) // dec
        hi = lo + (min(N, start + step) - start) // dec
        chunks.append(bb[lo:hi])
    bb = np.concatenate(chunks)
    inst = np.angle(bb[1:] * np.conj(bb[:-1]))            # frecuencia instantanea
    fs2 = FS / dec
    aud = signal.resample_poly(inst, int(out_fs), int(round(fs2)))
    aud = signal.sosfilt(signal.butter(4, 30, "hp", fs=out_fs, output="sos"), aud)
    aud /= max(np.abs(aud).max(), 1e-12)
    from scipy.io import wavfile
    wavfile.write(f"hifi_{tag}.wav", out_fs, (aud * 32000).astype(np.int16))
    print(f"  -> hifi_{tag}.wav  ({aud.size/out_fs:.2f} s)  rms={np.sqrt((aud**2).mean()):.4f}")
    return aud, out_fs

print("\ndemodulando 1.4 MHz ...")
aud, ofs = demod(1.400e6, tag="L")
aud2, _ = demod(1.797319e6, tag="R")

# espectrograma resumido: ?esto suena a voz/tonos o a ruido?
fr, tt, S = signal.spectrogram(aud, ofs, nperseg=2048)
band = S[(fr > 80) & (fr < 4000)].mean()
hiband = S[fr > 8000].mean()
print(f"\nenergia 80-4000 Hz vs >8 kHz: {band:.3e} / {hiband:.3e}  ratio={band/max(hiband,1e-20):.1f}")
print("perfil temporal (energia de voz por 0.5 s):")
for i in range(0, len(tt), max(1, len(tt)//20)):
    e = S[(fr > 80) & (fr < 4000), i].mean()
    print(f"  t={tt[i]:5.2f}s  {'#' * int(60 * e / max(S[(fr>80)&(fr<4000)].max(), 1e-20))}")
