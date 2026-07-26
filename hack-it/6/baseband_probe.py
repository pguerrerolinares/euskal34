#!/usr/bin/env python3
"""HUECO: hifi_demod2.py filtraba 40-15000 Hz ANTES de escribir el wav. El baseband
demodulado tiene +-245 kHz de ancho: todo lo que hubiera entre 15 kHz y 245 kHz
nunca lo miramos. Aqui se demodula igual pero SIN de-enfasis ni filtro de audio y
se saca el PSD completo del baseband (frecuencia instantanea Y envolvente AM).

Un dispositivo vintage que 'graba/emite' datos sobre audio (carga de cinta, FSK,
SSTV, modem) dejaria una portadora discreta ahi arriba."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

FS = 31415926.0
raw = np.memmap("out.wav", dtype=np.int16, mode="r", offset=44)
N = raw.size
NB, M, G = 1 << 23, 1 << 17, 1 << 16
DEC = NB // M
FS2 = FS / DEC
print(f"baseband: fs={FS2:.1f} Hz  -> ancho util +-{FS2/2/1e3:.1f} kHz")


def baseband(fc):
    out = []
    for start in range(0, N, NB - 2 * G):
        a, b = start, min(N, start + NB)
        seg = np.zeros(NB)
        seg[:b - a] = raw[a:b]
        Sp = np.fft.rfft(seg)
        k0 = int(round(fc * NB / FS))
        half = M // 2
        sl = Sp[k0 - half:k0 + half]
        if sl.size < M:
            sl = np.pad(sl, (0, M - sl.size))
        bb = np.fft.ifft(np.fft.ifftshift(sl)) * M
        g = G // DEC
        keep = bb[g:-g] if b == start + NB else bb[g:g + (b - a) // DEC]
        out.append(keep)
        if b >= N:
            break
    return np.concatenate(out)


def psd(x, fs, seg=1 << 16):
    """Welch, ventana Hann, promedio sobre todo el registro."""
    w = np.hanning(seg)
    nseg = x.size // seg
    acc = np.zeros(seg // 2 + 1)
    for i in range(nseg):
        s = x[i * seg:(i + 1) * seg].astype(np.float64)
        s = s - s.mean()
        acc += np.abs(np.fft.rfft(s * w)) ** 2
    return np.fft.rfftfreq(seg, 1 / fs), acc / max(nseg, 1)


def report(name, f, p):
    logp = 10 * np.log10(p + 1e-30)
    k = 201
    floor = np.convolve(logp, np.ones(k) / k, mode="same")
    exc = logp - floor
    pk, _ = find_peaks(exc[10:], height=6, distance=20)
    pk = pk + 10
    hi = [i for i in pk if f[i] > 18e3]           # por encima de la banda de audio
    print(f"\n-- {name}: picos >6 dB sobre suelo, f > 18 kHz --")
    if not hi:
        print("   (ninguno)")
    for i in sorted(hi, key=lambda j: -exc[j])[:20]:
        print(f"   {f[i]/1e3:9.3f} kHz  +{exc[i]:5.1f} dB")
    # reparto de energia
    tot = p.sum()
    for lo, up in [(0, 20e3), (20e3, 50e3), (50e3, 100e3), (100e3, 245e3)]:
        m = (f >= lo) & (f < up)
        print(f"   banda {lo/1e3:6.0f}-{up/1e3:6.0f} kHz : {100*p[m].sum()/tot:7.3f} %")
    return logp


fig, axes = plt.subplots(4, 1, figsize=(14, 14))
for ax, (fc, tag) in zip(axes.ravel()[:2], [(1.400005e6, "L"), (1.800001e6, "R")]):
    bb = baseband(fc)
    inst = np.angle(bb[1:] * np.conj(bb[:-1]))    # FM: frecuencia instantanea
    env = np.abs(bb)                              # AM: envolvente
    f1, p1 = psd(inst, FS2)
    f2, p2 = psd(env, FS2)
    l1 = report(f"{tag} FM (freq. instantanea)", f1, p1)
    l2 = report(f"{tag} AM (envolvente)", f2, p2)
    ax.plot(f1 / 1e3, l1, lw=.5, label="FM")
    ax.plot(f2 / 1e3, l2 - 40, lw=.5, alpha=.7, label="AM (-40 dB)")
    ax.set_title(f"baseband canal {tag} @ {fc/1e6:.6f} MHz")
    ax.set_xlabel("kHz"); ax.legend(); ax.grid(alpha=.3)
    np.save(f"bbinst_{tag}.npy", inst.astype(np.float32))

# zoom a la zona alta, donde viviria una subportadora de datos
for ax, tag in zip(axes.ravel()[2:], ["L", "R"]):
    inst = np.load(f"bbinst_{tag}.npy")
    f1, p1 = psd(inst, FS2)
    m = f1 > 15e3
    ax.plot(f1[m] / 1e3, 10 * np.log10(p1[m] + 1e-30), lw=.6)
    ax.set_title(f"zoom {tag}: 15-245 kHz (zona nunca mirada)")
    ax.set_xlabel("kHz"); ax.grid(alpha=.3)

plt.tight_layout(); plt.savefig("baseband_probe.png", dpi=110)
print("\n-> baseband_probe.png")
