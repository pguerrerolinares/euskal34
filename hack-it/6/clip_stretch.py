#!/usr/bin/env python3
"""La voz dura 260 ms para dos silabas: muy rapido. Bajar el sample rate (clip_voz_x2)
tambien baja el tono y whisper alucina. Aqui phase vocoder: estira el tiempo SIN
tocar el tono, sobre el clip ya limpio (sin musica que separar)."""
import numpy as np
from scipy.io import wavfile
from scipy import signal
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sr, x = wavfile.read("clip_voz.wav")
x = x.astype(np.float64) / 32768.0


def stretch(x, factor, n_fft=1024, hop=256):
    """phase vocoder clasico: mantiene el tono, alarga la duracion."""
    w = np.hanning(n_fft)
    hop_out = int(hop * factor)
    n_frames = 1 + (len(x) - n_fft) // hop
    out = np.zeros(n_frames * hop_out + n_fft)
    win = np.zeros_like(out)
    phase = np.angle(np.fft.rfft(x[:n_fft] * w))
    omega = 2 * np.pi * hop * np.arange(n_fft // 2 + 1) / n_fft
    for i in range(n_frames):
        a = i * hop
        S = np.fft.rfft(x[a:a + n_fft] * w)
        mag = np.abs(S)
        if i:
            d = np.angle(S) - prev_ang - omega
            d = np.mod(d + np.pi, 2 * np.pi) - np.pi
            phase = phase + omega + d
        prev_ang = np.angle(S)
        o = i * hop_out
        out[o:o + n_fft] += np.fft.irfft(mag * np.exp(1j * phase), n_fft) * w
        win[o:o + n_fft] += w ** 2
    return out / np.maximum(win, 1e-6)


for f in (1.5, 2.0, 3.0, 4.0):
    y = stretch(x, f)
    y = y / max(np.abs(y).max(), 1e-12)
    name = f"clip_pv_x{f:g}.wav".replace(".", "_", 1) if False else f"clip_pv_{f:g}x.wav"
    wavfile.write(name, sr, (y * 32000).astype(np.int16))
    print(f"{name}  {y.size/sr:.2f} s")

# espectrograma de alta resolucion del clip original: contar silabas y ver formantes
fig, axes = plt.subplots(3, 1, figsize=(15, 12))
axes[0].specgram(x, NFFT=256, Fs=sr, noverlap=224, cmap="inferno")
axes[0].set_ylim(0, 4000); axes[0].set_title("clip limpio, NFFT=256 (resolucion temporal)")
axes[1].specgram(x, NFFT=1024, Fs=sr, noverlap=960, cmap="inferno")
axes[1].set_ylim(0, 4000); axes[1].set_title("NFFT=1024 (resolucion frecuencial: armonicos)")
# envolvente y F0
w = sr // 200
nb = x.size // w
e = np.array([np.sqrt(np.mean(x[i*w:(i+1)*w]**2)) for i in range(nb)])
axes[2].plot(np.arange(nb) * 5, e, lw=1)
axes[2].set_xlabel("ms desde 4.700 s"); axes[2].set_title("envolvente (5 ms): silabas")
axes[2].grid(alpha=.3)
plt.tight_layout(); plt.savefig("clip_stretch.png", dpi=120)
print("-> clip_stretch.png")
