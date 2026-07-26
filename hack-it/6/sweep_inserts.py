#!/usr/bin/env python3
"""Ahora se cual es la FIRMA de una insercion del autor: el canal se vacia y la
correlacion L/R se rompe. Con eso puedo barrer los 10 s enteros buscando mas clips.
El barrido anterior usaba ventanas de 0.5 s y se le escaparia cualquier cosa corta.

Se valida el detector inyectando un clip sintetico de 150 ms en un instante conocido
y comprobando que lo encuentra."""
import numpy as np
from scipy.io import wavfile
from scipy import ndimage

sr, L = wavfile.read("hifi2_L.wav")
_, R = wavfile.read("hifi2_R.wav")
L = L.astype(np.float64); R = R.astype(np.float64)
n = min(L.size, R.size); L, R = L[:n], R[:n]


def scan(L, R, tag, W=0.050):
    w = int(W * sr)
    hits = []
    rows = []
    for i in range(0, n - w, w // 2):
        a, b = L[i:i+w], R[i:i+w]
        c = np.corrcoef(a, b)[0, 1]
        d = 10*np.log10((np.mean(a**2)+1e-12)/(np.mean(b**2)+1e-12))
        rows.append((i/sr, c, d))
        if c < 0.35 or abs(d) > 10:
            hits.append((i/sr, c, d))
    print(f"\n== {tag}: ventanas de {W*1000:.0f} ms ==")
    cs = np.array([r[1] for r in rows])
    print(f"   correlacion L/R: mediana={np.median(cs):.3f} "
          f"p5={np.percentile(cs,5):.3f} min={cs.min():.3f}")
    if not hits:
        print("   sin ventanas anomalas")
    else:
        # agrupar ventanas contiguas
        ts = [h[0] for h in hits]
        groups, cur = [], [ts[0]]
        for t in ts[1:]:
            if t - cur[-1] <= W:
                cur.append(t)
            else:
                groups.append(cur); cur = [t]
        groups.append(cur)
        for g in groups:
            sel = [h for h in hits if g[0] <= h[0] <= g[-1]]
            print(f"   t={g[0]:5.3f}-{g[-1]+W:5.3f} s  ({len(sel)} ventanas)  "
                  f"corr_min={min(s[1] for s in sel):+.3f}  "
                  f"|L/R|_max={max(abs(s[2]) for s in sel):5.1f} dB")
    return hits


scan(L, R, "SENAL REAL")

# --- validacion del detector: inyectar un clip donde sabemos que no hay nada ---
Li = L.copy()
t0 = int(2.300 * sr)
d = int(0.150 * sr)
Li[t0:t0+d] = 0.0                      # vaciar, igual que hace el autor
tone = np.sin(2*np.pi*300*np.arange(int(0.080*sr))/sr) * np.abs(L).max()*0.5
Li[t0+int(0.03*sr):t0+int(0.03*sr)+tone.size] = tone
h = scan(Li, R, "CONTROL POSITIVO (clip inyectado en t=2.300 s)")
found = any(2.20 <= x[0] <= 2.50 for x in h)
print(f"\n   -> el detector {'SI' if found else 'NO'} encuentra la insercion sintetica"
      f"  ({'instrumento valido' if found else 'INSTRUMENTO INVALIDO: no concluir nada'})")
