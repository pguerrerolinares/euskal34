#!/usr/bin/env python3
"""La mejor extraccion posible de la voz: partir del residuo (musica ya cancelada),
substraccion espectral, y time-stretch con phase vocoder (ralentiza SIN bajar el
tono, que es lo que de verdad hace inteligible una palabra corta)."""
import numpy as np
from scipy import signal
from scipy.io import wavfile

fs, res = wavfile.read("hifi_residual2.wav"); res = res.astype(float) / 32768
_,  L   = wavfile.read("hifi2_L.wav");        L   = L.astype(float) / 32768

NF, HOP = 1024, 256
win = np.hanning(NF)

def stft(x):
    m = 1 + (x.size - NF) // HOP
    return np.array([np.fft.rfft(x[i*HOP:i*HOP+NF] * win) for i in range(m)])

def istft(X, ln, hop=HOP):
    y = np.zeros(ln + NF); a = np.zeros(ln + NF)
    for i, fr in enumerate(X):
        s = i * hop
        y[s:s+NF] += np.fft.irfft(fr, NF) * win
        a[s:s+NF] += win ** 2
    return (y / np.maximum(a, 1e-9))[:ln]

def denoise(x, quiet_a, quiet_b, over=2.5):
    X = stft(x); mag, ph = np.abs(X), np.angle(X)
    t = np.arange(X.shape[0]) * HOP / fs
    m = ((t > quiet_a[0]) & (t < quiet_a[1])) | ((t > quiet_b[0]) & (t < quiet_b[1]))
    prof = np.median(mag[m], axis=0)
    return istft(np.maximum(mag - over * prof, 0.04 * mag) * np.exp(1j * ph), x.size)

def stretch(x, factor):
    """phase vocoder: alarga x por 'factor' manteniendo el tono."""
    X = stft(x)
    nfr = int(X.shape[0] * factor)
    out = np.zeros((nfr, X.shape[1]), dtype=complex)
    acc = np.angle(X[0])
    dphi_exp = 2 * np.pi * HOP * np.arange(X.shape[1]) / NF
    for i in range(nfr):
        p = i / factor
        i0 = min(int(p), X.shape[0] - 2)
        fr = (1 - (p - i0)) * np.abs(X[i0]) + (p - i0) * np.abs(X[i0 + 1])
        d = np.angle(X[i0 + 1]) - np.angle(X[i0]) - dphi_exp
        d = np.mod(d + np.pi, 2 * np.pi) - np.pi
        acc = acc + dphi_exp + d
        out[i] = fr * np.exp(1j * acc)
    return istft(out, int(x.size * factor))

def w(name, x):
    x = x - x.mean(); x /= max(np.abs(x).max(), 1e-12)
    wavfile.write(name, fs, (x * 30000).astype(np.int16))
    print(f"  {name}")

sos = signal.butter(4, [200, 3600], "bp", fs=fs, output="sos")
a, b = int(4.45 * fs), int(5.25 * fs)

for src, tag in ((res, "res"), (L, "L")):
    d = signal.sosfilt(sos, denoise(src, (3.0, 4.4), (5.3, 6.8)))
    seg = d[a:b]
    w(f"best_{tag}.wav", seg)
    w(f"best_{tag}_x2.wav", stretch(seg, 2.0))     # 2x lento, MISMO tono
    w(f"best_{tag}_x3.wav", stretch(seg, 3.0))
    w(f"best_{tag}_rev.wav", seg[::-1])
    w(f"best_{tag}_rev_x2.wav", stretch(seg[::-1], 2.0))
print("\nEscuchar en este orden: best_res_x2, best_L_x2, best_res, best_L_rev_x2")
