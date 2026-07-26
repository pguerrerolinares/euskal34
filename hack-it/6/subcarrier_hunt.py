#!/usr/bin/env python3
"""El canal de audio FM demodulado ocupa 245 kHz pero la musica solo llega a 15 kHz.
?Hay una subportadora de datos por encima del audio (como el RDS en FM comercial)?
Nadie ha mirado ahi."""
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

FS = 31415926.0
raw = np.memmap("out.wav", dtype=np.int16, mode="r", offset=44)
N = raw.size
NB, M = 1 << 23, 1 << 17
DEC = NB // M
FS2 = FS / DEC
print(f"tasa del canal demodulado: {FS2/1e3:.1f} kHz  (banda util 0-{FS2/2/1e3:.1f} kHz)")

for fc, tag in ((1.400005e6, "L"), (1.797319e6, "R")):
    off = (N // 2 // NB) * NB
    seg = np.asarray(raw[off:off + NB], dtype=np.float64)
    Sp = np.fft.rfft(seg)
    k0 = int(round(fc * NB / FS)); half = M // 2
    bb = np.fft.ifft(np.fft.ifftshift(Sp[k0 - half:k0 + half])) * M
    inst = np.angle(bb[1:] * np.conj(bb[:-1]))
    inst -= inst.mean()

    sp = np.abs(np.fft.rfft(inst * np.hanning(inst.size)))
    f = np.fft.rfftfreq(inst.size, 1 / FS2)
    print(f"\n=== canal {tag}: reparto de energia del baseband demodulado ===")
    for a, b in ((0, 15e3), (15e3, 30e3), (30e3, 60e3), (60e3, 100e3), (100e3, 245e3)):
        m = (f >= a) & (f < b)
        print(f"  {a/1e3:6.1f}-{b/1e3:6.1f} kHz : {100*np.sum(sp[m]**2)/np.sum(sp**2):7.3f} %")

    m = f > 18e3
    idx = np.flatnonzero(m)
    top = idx[np.argsort(sp[idx])[::-1][:6]]
    print("  picos por encima de 18 kHz:")
    for t in sorted(top):
        med = np.median(sp[max(0, t-2000):t+2000])
        print(f"    {f[t]/1e3:8.2f} kHz  pico/mediana={sp[t]/max(med,1e-9):7.2f}"
              + ("   <-- SUBPORTADORA" if sp[t]/max(med,1e-9) > 8 else ""))

    plt.figure(figsize=(15, 5))
    plt.semilogy(f / 1e3, sp + 1e-9, lw=.4)
    plt.xlabel("kHz"); plt.ylabel("|X|"); plt.title(f"baseband demodulado canal {tag}")
    plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(f"baseband_{tag}.png", dpi=110); plt.close()
    print(f"  -> baseband_{tag}.png")
