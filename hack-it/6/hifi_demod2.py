#!/usr/bin/env python3
"""Demod HiFi bien hecho: filtro brickwall por FFT (+-245 kHz) para que el canal
vecino (separado 400 kHz) NO se cuele. Overlap-save por bloques."""
import numpy as np
from scipy import signal
from scipy.io import wavfile

FS = 31415926.0
raw = np.memmap("out.wav", dtype=np.int16, mode="r", offset=44)
N = raw.size
NB, M, G = 1 << 23, 1 << 17, 1 << 16      # bloque, bins de salida (dec=64), guarda
DEC = NB // M

def demod(fc, tag):
    out = []
    for start in range(0, N, NB - 2 * G):
        a, b = start, min(N, start + NB)
        seg = np.zeros(NB)
        seg[:b - a] = raw[a:b]
        Sp = np.fft.rfft(seg)
        k0 = int(round(fc * NB / FS))
        half = M // 2
        sl = Sp[k0 - half:k0 + half]           # banda +-245 kHz en torno a fc
        if sl.size < M:
            sl = np.pad(sl, (0, M - sl.size))
        bb = np.fft.ifft(np.fft.ifftshift(sl)) * M   # banda base, dec=64
        g = G // DEC
        keep = bb[g:-g] if b == start + NB else bb[g:g + (b - a) // DEC]
        out.append(keep)
        if b >= N:
            break
    bb = np.concatenate(out)
    inst = np.angle(bb[1:] * np.conj(bb[:-1]))       # frecuencia instantanea
    fs2 = FS / DEC
    # de-enfasis 50us + banda de audio, y a 48 kHz
    aud = signal.resample_poly(inst, 48000, int(round(fs2)))
    fs3 = 48000
    al = np.exp(-1 / (fs3 * 50e-6))
    aud = signal.lfilter([1 - al], [1, -al], aud)
    aud = signal.sosfilt(signal.butter(4, [40, 15000], "bp", fs=fs3, output="sos"), aud)
    aud -= aud.mean()
    aud /= max(np.abs(aud).max(), 1e-12)
    wavfile.write(f"hifi2_{tag}.wav", fs3, (aud * 30000).astype(np.int16))
    # SNR aproximada: energia en banda de voz vs banda alta (solo ruido)
    sp = np.abs(np.fft.rfft(aud)); f = np.fft.rfftfreq(aud.size, 1 / fs3)
    v = np.sum(sp[(f > 100) & (f < 5000)] ** 2); nz = np.sum(sp[(f > 12000)] ** 2)
    print(f"hifi2_{tag}.wav  {aud.size/fs3:.2f}s  voz/ruido = {10*np.log10(v/max(nz,1e-20)):5.1f} dB")
    return aud

L = demod(1.400005e6, "L")
R = demod(1.797319e6, "R")
n = min(L.size, R.size)
print(f"\ncorrelacion L/R = {np.corrcoef(L[:n], R[:n])[0,1]:+.4f}")
for tag, x in (("mid", L[:n] + R[:n]), ("side", L[:n] - R[:n])):
    x = x / max(np.abs(x).max(), 1e-12)
    wavfile.write(f"hifi2_{tag}.wav", 48000, (x * 30000).astype(np.int16))
    print(f"hifi2_{tag}.wav  rms={np.sqrt((x**2).mean()):.4f}")
