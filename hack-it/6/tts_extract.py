#!/usr/bin/env python3
"""Es una voz TTS (tipo Loquendo): F0 casi constante y armonicos regulares.
Eso permite (a) detectar TODOS los tramos donde habla y (b) extraerla de la musica
con un tamiz armonico sintonizado a su F0, en vez de filtrados genericos."""
import numpy as np
from scipy import signal
from scipy.io import wavfile

fs, L = wavfile.read("hifi2_L.wav"); L = L.astype(float)/32768
_,  R = wavfile.read("hifi2_R.wav"); R = R.astype(float)/32768
NF, HOP = 2048, 256
win = np.hanning(NF)

def stft(x):
    m = 1 + (x.size-NF)//HOP
    return np.array([np.fft.rfft(x[i*HOP:i*HOP+NF]*win) for i in range(m)])

def istft(X, ln):
    y = np.zeros(ln+NF); a = np.zeros(ln+NF)
    for i, fr in enumerate(X):
        y[i*HOP:i*HOP+NF] += np.fft.irfft(fr, NF)*win
        a[i*HOP:i*HOP+NF] += win**2
    return (y/np.maximum(a, 1e-9))[:ln]

X = stft(L)
mag = np.abs(X)
freqs = np.fft.rfftfreq(NF, 1/fs)
t = np.arange(X.shape[0])*HOP/fs

# --- (a) detector de TTS: puntuacion de peine armonico para F0 en 80-110 Hz ---
def comb_score(fr_mag, f0, nh=25):
    ks = np.round(np.arange(1, nh+1)*f0/(fs/NF)).astype(int)
    ks = ks[ks < fr_mag.size]
    on = fr_mag[ks].sum()
    off = fr_mag[np.clip(ks + int(round(0.5*f0/(fs/NF))), 0, fr_mag.size-1)].sum()
    return on/max(off, 1e-9)

f0_grid = np.arange(84, 104, 0.5)
score = np.zeros(len(t)); f0hat = np.zeros(len(t))
for i in range(len(t)):
    ss = [comb_score(mag[i], f0) for f0 in f0_grid]
    j = int(np.argmax(ss)); score[i] = ss[j]; f0hat[i] = f0_grid[j]

thr = np.median(score) + 2.0*np.std(score)
print(f"puntuacion peine: mediana={np.median(score):.2f} umbral={thr:.2f}")
act = score > thr
# agrupar en tramos
tr, st = [], None
for i, v in enumerate(act):
    if v and st is None: st = i
    elif not v and st is not None:
        if (i-st)*HOP/fs > 0.05: tr.append((t[st], t[i]))
        st = None
if st is not None: tr.append((t[st], t[-1]))
print(f"\ntramos con estructura de voz TTS ({len(tr)}):")
for a, b in tr:
    m = (t >= a) & (t <= b)
    print(f"  t={a:5.2f}-{b:5.2f}s ({b-a:.2f}s)  F0 medio={f0hat[m].mean():5.1f} Hz  score={score[m].mean():.2f}")

# --- (b) tamiz armonico: quedarse solo con los armonicos del F0 de la voz ----
F0 = float(np.median(f0hat[act])) if act.any() else 93.0
print(f"\nF0 de la voz = {F0:.1f} Hz -> tamiz armonico")
mask = np.zeros(mag.shape[1])
for h in range(1, 40):
    k = h*F0/(fs/NF)
    lo, hi = int(np.floor(k-1.5)), int(np.ceil(k+1.5))
    if hi < mask.size: mask[lo:hi+1] = 1.0
mask = signal.convolve(mask, np.hanning(5)/np.hanning(5).sum(), mode="same")
Y = X * mask[None, :]
voice = istft(Y, L.size)

def w(name, x, rate=fs):
    x = x-x.mean(); x /= max(np.abs(x).max(), 1e-12)
    wavfile.write(name, int(rate), (x*30000).astype(np.int16))
    print(f"  {name}")

lo_t = max(0, min(a for a, _ in tr) - 0.2) if tr else 4.4
hi_t = min(L.size/fs, max(b for _, b in tr) + 0.2) if tr else 5.3
print(f"\nrecorte del habla: {lo_t:.2f}-{hi_t:.2f}s")
seg = voice[int(lo_t*fs):int(hi_t*fs)]
w("tts_voice.wav", seg)
w("tts_voice_slow.wav", signal.resample_poly(seg, 3, 1))   # 3x lento (baja tono)
w("tts_full.wav", voice)
