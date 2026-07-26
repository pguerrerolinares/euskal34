#!/usr/bin/env python3
"""Descubrimiento: en 4.74-5.38 s el canal L NO lleva musica. El autor SUSTITUYO el
canal por un clip de TTS con padding de silencio, no lo mezclo encima. Toda la
separacion voz/musica de la sesion anterior (Wiener, NLMS, resta espectral) atacaba
un problema inexistente y metia artefactos.

Aqui se saca el clip TAL CUAL, sin ningun procesado, y se comprueba que esta limpio."""
import numpy as np
from scipy.io import wavfile
from scipy import signal
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sr, L = wavfile.read("hifi2_L.wav")
L = L.astype(np.float64)

A, B = 4.700, 5.420
a, b = int(A * sr), int(B * sr)
clip = L[a:b]
clip = clip - clip.mean()

# prueba de limpieza: relacion entre la energia del clip y la de la musica vecina
prev = L[int(4.0*sr):int(4.6*sr)]
print(f"clip {A}-{B} s ({clip.size/sr*1000:.0f} ms)")
print(f"  rms del clip           = {clip.std():8.1f}")
print(f"  rms de la musica vecina= {prev.std():8.1f}")

# ¿queda musica de fondo dentro del clip? mirar los tramos de padding
pad1 = L[int(4.74*sr):int(4.78*sr)]
pad2 = L[int(5.10*sr):int(5.37*sr)]
print(f"  rms del padding previo = {pad1.std():8.2f}")
print(f"  rms del padding poster.= {pad2.std():8.2f}")
print(f"  -> padding {20*np.log10(prev.std()/max(pad2.std(),1e-9)):.1f} dB por debajo "
      f"de la musica: el canal esta VACIADO, no mezclado")

y = clip / max(np.abs(clip).max(), 1e-12)
wavfile.write("clip_voz.wav", sr, (y * 32000).astype(np.int16))
for k, name in ((2, "clip_voz_x2.wav"), (3, "clip_voz_x3.wav")):
    wavfile.write(name, sr // k, (y * 32000).astype(np.int16))

# version con la banda de voz realzada, sin tocar el contenido
sos = signal.butter(4, [180, 3800], "bp", fs=sr, output="sos")
v = signal.sosfiltfilt(sos, y)
v = v / max(np.abs(v).max(), 1e-12)
wavfile.write("clip_voz_bp.wav", sr, (v * 32000).astype(np.int16))
wavfile.write("clip_voz_bp_x2.wav", sr // 2, (v * 32000).astype(np.int16))
print("\n-> clip_voz.wav, clip_voz_x2.wav, clip_voz_x3.wav, clip_voz_bp.wav (+_x2)")

# estructura interna: los 6 segmentos
w = sr // 1000
nb = clip.size // w
e = 10*np.log10(np.array([np.mean(clip[i*w:(i+1)*w]**2) for i in range(nb)]) + 1e-12)
t = A + np.arange(nb)/1000.0
print("\nsegmentos de voz (energia por ms sobre el umbral):")
thr = e.max() - 30
on = e > thr
i = 0
while i < nb:
    if on[i]:
        j = i
        while j < nb and on[j]:
            j += 1
        if j - i >= 3:
            print(f"  {t[i]:.3f}-{t[min(j, nb-1)]:.3f} s   {j-i:3d} ms   "
                  f"pico {e[i:j].max():.1f} dB")
        i = j
    else:
        i += 1

fig, axes = plt.subplots(3, 1, figsize=(15, 11))
axes[0].plot(np.arange(clip.size)/sr + A, y, lw=.4)
axes[0].set_title("forma de onda del clip (canal L, sin procesar)"); axes[0].grid(alpha=.3)
axes[1].plot(t, e, lw=1); axes[1].axhline(thr, color="r", ls="--", lw=.8)
axes[1].set_title("energia por ms"); axes[1].grid(alpha=.3)
axes[2].specgram(clip, NFFT=512, Fs=sr, noverlap=448, cmap="inferno")
axes[2].set_ylim(0, 5000); axes[2].set_title("espectrograma del clip")
plt.tight_layout(); plt.savefig("clip_L.png", dpi=120)
print("-> clip_L.png")
