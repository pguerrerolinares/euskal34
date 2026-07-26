#!/usr/bin/env python3
"""t=5.0s es el frame 125, donde esta el caption 'Part 1/3'. En el audio pasa algo
justo ahi. Diseccionar 4.4-5.4 s en cada canal: ?voz, tonos, DTMF, datos?"""
import numpy as np
from scipy import signal
from scipy.io import wavfile
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

fs, L = wavfile.read("hifi2_L.wav")
_,  R = wavfile.read("hifi2_R.wav")
_,  res = wavfile.read("hifi_residual2.wav")
L = L.astype(float)/32768; R = R.astype(float)/32768; res = res.astype(float)/32768

a, b = int(4.4*fs), int(5.4*fs)
for tag, x in (("L", L), ("R", R), ("res", res)):
    seg = x[a:b] / max(abs(x[a:b]).max(), 1e-9)
    wavfile.write(f"ev_{tag}.wav", fs, (seg*30000).astype(np.int16))
    # y una version ralentizada 4x para oir detalle
    slow = signal.resample_poly(seg, 4, 1)
    wavfile.write(f"ev_{tag}_slow.wav", fs, (slow/max(abs(slow).max(),1e-9)*30000).astype(np.int16))

print("recortes 4.4-5.4s -> ev_L/ev_R/ev_res .wav (+ _slow 4x)")

fig, axes = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
for ax, (tag, x) in zip(axes, (("L", L), ("R", R), ("residual", res))):
    seg = x[a:b]
    fr, tt, S = signal.spectrogram(seg, fs, nperseg=512, noverlap=480)
    ax.pcolormesh(tt+4.4, fr, 10*np.log10(S+1e-14), shading="auto", cmap="magma")
    ax.set_ylim(0, 3000); ax.set_ylabel(f"{tag} (Hz)")
    ax.axvline(5.0, color="cyan", ls="--", lw=1)
axes[-1].set_xlabel("s")
plt.tight_layout(); plt.savefig("event5s.png", dpi=120); plt.close()
print("-> event5s.png")

# tonos dominantes en ventanas de 50 ms alrededor de 5.0 s
print("\ntonos dominantes por ventana de 50 ms (canal residual):")
for t0 in np.arange(4.6, 5.3, 0.05):
    s = res[int(t0*fs):int((t0+0.05)*fs)]
    if s.size < 64: break
    sp = np.abs(np.fft.rfft(s*np.hanning(s.size)))
    f = np.fft.rfftfreq(s.size, 1/fs)
    top = np.argsort(sp)[::-1][:3]
    print(f"  t={t0:5.2f}s  " + "  ".join(f"{f[t]:7.1f}Hz" for t in sorted(top)))
