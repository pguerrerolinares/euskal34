#!/usr/bin/env python3
"""Identificar los fonemas por FORMANTES (LPC), que es medida fisica y no depende
del ASR ni de mi oido.

Discriminadores:
  - la /r/ inglesa hunde F3 hasta ~1600-1800 Hz (marca inequivoca).
  - la /l/ tiene F2 bajo (~900-1100) y F3 alto (~2600).
  - la vocal se identifica por (F1,F2):
        /oU/ boat  450  900     /O/ bought 570  840
        /eI/ tape  450 2000     /E/ rec    530 1840
        /ae/ track 660 1720     /A/ father 730 1090
        /I/  bit   390 1990     /^/ but    640 1190
Validacion del instrumento: se corre sobre trozos de voz cantada del mismo fichero
y los formantes tienen que caer en rangos humanos plausibles."""
import numpy as np
from scipy.io import wavfile
from scipy import signal
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

FS2 = 10000          # remuestrear: los formantes viven por debajo de 5 kHz
ORDER = 14


def formants(x, fs, win=0.025, hop=0.005):
    x = signal.resample_poly(x, FS2, fs)
    x = signal.lfilter([1, -0.97], [1], x)          # pre-enfasis
    w, h = int(win * FS2), int(hop * FS2)
    out = []
    for i in range(0, len(x) - w, h):
        s = x[i:i + w] * np.hamming(w)
        if np.sqrt(np.mean(s ** 2)) < 1e-5:
            out.append([np.nan] * 4); continue
        # autocorrelacion -> Levinson (LPC)
        r = np.correlate(s, s, "full")[w - 1:w - 1 + ORDER + 1]
        if r[0] <= 0:
            out.append([np.nan] * 4); continue
        try:
            from scipy.linalg import toeplitz
            a = np.linalg.solve(toeplitz(r[:ORDER]) + np.eye(ORDER) * r[0] * 1e-7,
                                r[1:ORDER + 1])
        except np.linalg.LinAlgError:
            out.append([np.nan] * 4); continue
        rts = np.roots(np.concatenate([[1], -a]))
        rts = rts[np.imag(rts) > 0]
        f = np.sort(np.abs(np.angle(rts)) * FS2 / (2 * np.pi))
        bw = -0.5 * (FS2 / (2 * np.pi)) * np.log(np.abs(rts))
        ok = [ff for ff, bb in sorted(zip(f, bw[np.argsort(np.abs(np.angle(rts)))]))
              if 200 < ff < 4500 and bb < 500]
        out.append((ok + [np.nan] * 4)[:4])
    return np.array(out, dtype=float), hop


sr, v = wavfile.read("voz_limpia.wav")
v = v.astype(np.float64) / 32768
F, hop = formants(v, sr)
t = np.arange(len(F)) * hop * 1000

print("== formantes de LA VOZ DEL RETO (ms, Hz) ==")
print("   t      F1     F2     F3     F4")
for i in range(len(F)):
    r = F[i]
    print(f"  {t[i]:5.0f}  " + "  ".join("  ---" if np.isnan(x) else f"{x:5.0f}" for x in r))

core = (t >= 70) & (t <= 250)
med = np.nanmedian(F[core], axis=0)
print(f"\nmediana en el nucleo vocalico (70-250 ms):")
print(f"  F1={med[0]:.0f}  F2={med[1]:.0f}  F3={med[2]:.0f}  F4={med[3]:.0f}")

f3min = np.nanmin(F[core, 2])
print(f"\nF3 minimo en el nucleo = {f3min:.0f} Hz")
print("  -> " + ("HAY /r/: F3 por debajo de 2000 Hz es la firma de la r inglesa"
                 if f3min < 2000 else
                 "NO hay /r/: F3 se mantiene alto, no hay retroflexion"))

REF = {"/oU/ (roll, boat)": (450, 900), "/O/ (call, bought)": (570, 840),
       "/A/ (father)": (730, 1090), "/^/ (but)": (640, 1190),
       "/eI/ (tape)": (450, 2000), "/E/ (rec)": (530, 1840),
       "/ae/ (track)": (660, 1720), "/I/ (bit, VHS)": (390, 1990)}
print("\ndistancia de (F1,F2) medidos a cada vocal de referencia:")
for k, (a, b) in sorted(REF.items(),
                        key=lambda kv: (np.log(med[0]/kv[1][0])**2 + np.log(med[1]/kv[1][1])**2)):
    d = np.sqrt(np.log(med[0]/a)**2 + np.log(med[1]/b)**2)
    print(f"  {k:22s} F1={a:4d} F2={b:4d}   distancia={d:.3f}")

print("\n== control del instrumento: voz cantada del mismo fichero ==")
sr2, L = wavfile.read("hifi2_L.wav")
L = L.astype(np.float64) / 32768
for t0, t1 in [(1.5, 1.9), (6.0, 6.4)]:
    Fc, _ = formants(L[int(t0*sr2):int(t1*sr2)], sr2)
    m = np.nanmedian(Fc, axis=0)
    print(f"  musica {t0}-{t1}s: F1={m[0]:.0f} F2={m[1]:.0f} F3={m[2]:.0f} "
          f"{'(rango humano plausible)' if 200<m[0]<900 and 700<m[1]<2600 else '(FUERA de rango)'}")

fig, ax = plt.subplots(figsize=(13, 7))
for i, c in enumerate(["C0", "C1", "C2", "C3"]):
    ax.plot(t, F[:, i], ".-", color=c, ms=4, lw=.8, label=f"F{i+1}")
ax.axhspan(0, 2000, color="red", alpha=.06)
ax.axvspan(70, 250, color="orange", alpha=.12)
ax.set_xlabel("ms"); ax.set_ylabel("Hz"); ax.set_ylim(0, 4500)
ax.set_title("formantes de la voz del reto (banda roja: zona donde F3 delata una /r/)")
ax.legend(); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig("formants.png", dpi=120)
print("-> formants.png")
