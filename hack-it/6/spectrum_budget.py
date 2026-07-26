import os

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))

FS = 31_415_926
N = 314_218_750
x = np.memmap(os.path.join(D, 'out.wav'), dtype='<i2', mode='r', offset=44, shape=(N,))

SEG = 1 << 20  # ~1M puntos -> df ~30 Hz
nseg = 64      # 64 segmentos repartidos por el fichero
w = np.hanning(SEG).astype(np.float64)
acc = np.zeros(SEG // 2 + 1)
starts = np.linspace(0, N - SEG, nseg).astype(np.int64)
for s in starts:
    seg = x[s:s+SEG].astype(np.float64)
    seg -= seg.mean()
    acc += np.abs(np.fft.rfft(seg * w)) ** 2
acc /= nseg
f = np.fft.rfftfreq(SEG, 1 / FS)

tot = acc.sum()
bands = [(0, 20e3), (20e3, 100e3), (100e3, 300e3), (300e3, 1.0e6),
         (1.0e6, 1.3e6), (1.3e6, 1.5e6), (1.5e6, 1.7e6), (1.7e6, 1.9e6),
         (1.9e6, 2.5e6), (2.5e6, 3.0e6), (3.0e6, 5.5e6), (5.5e6, 7e6),
         (7e6, 9e6), (9e6, 12e6), (12e6, FS/2)]
print('== presupuesto de energia ==')
for lo, hi in bands:
    m = (f >= lo) & (f < hi)
    print(f'{lo/1e6:7.3f}-{hi/1e6:7.3f} MHz : {100*acc[m].sum()/tot:8.4f} %')

# picos: mediana local como suelo, listar picos prominentes fuera de 3.0-5.5 MHz
from scipy.signal import find_peaks
logp = 10*np.log10(acc + 1e-30)
# suavizado del suelo
k = 501
floor = np.convolve(logp, np.ones(k)/k, mode='same')
exc = logp - floor
pk, props = find_peaks(exc, height=8, distance=200)
print('\n== picos >8 dB sobre suelo local (fuera de 2.5-5.6 MHz) ==')
for i in pk:
    if 2.5e6 < f[i] < 5.6e6:
        continue
    print(f'{f[i]/1e6:10.6f} MHz  +{exc[i]:5.1f} dB  abs {logp[i]:7.1f}')
np.save(os.path.join(D, 'psd_f.npy'), f)
np.save(os.path.join(D, 'psd.npy'), acc)
