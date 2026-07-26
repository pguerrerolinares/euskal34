#!/usr/bin/env python3
"""?Es voz humana de verdad o nos lo estamos imaginando? Test objetivo:
F0 estable en rango de voz + formantes por LPC. Control: un tramo de musica pura."""
import numpy as np
from scipy import signal
from scipy.linalg import toeplitz
from scipy.io import wavfile

fs, L = wavfile.read("hifi2_L.wav"); L = L.astype(float) / 32768

def f0(x, fs):
    x = x - x.mean()
    ac = np.correlate(x, x, "full")[x.size-1:]
    ac /= max(ac[0], 1e-12)
    lo, hi = int(fs/400), int(fs/70)
    k = lo + int(np.argmax(ac[lo:hi]))
    return fs / k, ac[k]

def formants(x, fs, order=12):
    x = x * np.hanning(x.size)
    x = signal.lfilter([1, -0.97], 1, x)           # pre-enfasis
    r = np.correlate(x, x, "full")[x.size-1:][:order+1]
    R = toeplitz(r[:order])
    try:
        a = np.linalg.solve(R, -r[1:order+1])
    except np.linalg.LinAlgError:
        return []
    roots = np.roots(np.r_[1, a])
    roots = roots[np.imag(roots) > 0.01]
    frq = np.sort(np.angle(roots) * fs / (2*np.pi))
    bw = -0.5 * (fs/(2*np.pi)) * np.log(np.abs(roots[np.argsort(np.angle(roots))]))
    return [(f, b) for f, b in zip(frq, bw) if 200 < f < 4000 and b < 500]

for tag, (t0, t1) in (("EVENTO  ", (4.60, 5.08)), ("control1", (2.00, 2.48)),
                      ("control2", (7.00, 7.48)), ("control3", (0.30, 0.78))):
    seg = L[int(t0*fs):int(t1*fs)]
    print(f"\n=== {tag} t={t0:.2f}-{t1:.2f}s ===")
    f0s, conf = [], []
    for i in range(0, seg.size - int(0.03*fs), int(0.01*fs)):
        p, c = f0(seg[i:i+int(0.03*fs)], fs)
        f0s.append(p); conf.append(c)
    f0s, conf = np.array(f0s), np.array(conf)
    good = conf > 0.35
    if good.sum() > 3:
        v = f0s[good]
        print(f"  F0: mediana={np.median(v):6.1f} Hz  IQR={np.percentile(v,75)-np.percentile(v,25):5.1f} Hz"
              f"  tramas sonoras={good.mean():.0%}")
        print(f"      -> {'RANGO DE VOZ' if 70 < np.median(v) < 260 else 'fuera de rango de voz'}"
              f", {'estable' if np.percentile(v,75)-np.percentile(v,25) < 40 else 'inestable'}")
    else:
        print("  F0: sin tramas sonoras claras")
    fm = formants(seg[:int(0.04*fs)], fs)
    print("  formantes:", ", ".join(f"{f:.0f}Hz(bw{b:.0f})" for f, b in fm[:4]) or "ninguno claro")
