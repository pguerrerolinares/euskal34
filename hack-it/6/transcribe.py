#!/usr/bin/env python3
"""Lectura independiente de la voz: transcripcion automatica de todas las
extracciones, en castellano y en ingles, con varios modelos."""
import sys, os, numpy as np
from scipy.io import wavfile
from faster_whisper import WhisperModel

FILES = ["nlms_event.wav", "nlms_event_x2.wav", "tts_voice.wav", "best_L_x2.wav",
         "best_res_x2.wav", "ev_L.wav", "nlms_full.wav", "hifi2_L.wav", "hifi2_mid.wav"]

def padded(path, pad=1.0):
    """whisper funciona fatal con clips de <1s: rellenar con silencio."""
    fs, x = wavfile.read(path)
    x = x.astype(np.float32) / 32768
    if x.ndim > 1:
        x = x.mean(axis=1)
    # resamplear a 16 kHz que es lo que espera el modelo
    from scipy import signal as sg
    x = sg.resample_poly(x, 16000, fs)
    z = np.zeros(int(pad * 16000), dtype=np.float32)
    return np.concatenate([z, x, z])

size = sys.argv[1] if len(sys.argv) > 1 else "small"
print(f"modelo: {size}")
model = WhisperModel(size, device="cpu", compute_type="int8")

for fn in FILES:
    if not os.path.exists(fn):
        continue
    audio = padded(fn)
    print(f"\n=== {fn} ({audio.size/16000:.2f}s) ===")
    for lang in ("es", "en", None):
        segs, info = model.transcribe(audio, language=lang, beam_size=5,
                                      temperature=0.0, vad_filter=False,
                                      condition_on_previous_text=False)
        txt = " ".join(s.text.strip() for s in segs).strip()
        tag = lang or f"auto({info.language},{info.language_probability:.2f})"
        if txt:
            print(f"  [{tag}] {txt!r}")
