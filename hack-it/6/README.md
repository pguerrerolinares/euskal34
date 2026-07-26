# Hack It EE34 — Nivel 6 "Classical Music" (rickroll en señal PAL/FM)

Archivo del scratchpad de la sesión del 2026-07-25 (movido aquí desde `/tmp`, que es efímero).
Autor del reto: **ontza**. URL: `hackit.party.eus/hackit/6/`.

**Estado: parcialmente resuelto.** `Part 1/3 = v1nTag3`. Partes 2/3 sin encontrar tras ~20 enfoques.

El writeup público del nivel, con el análisis de la señal y lo que se descartó, está en
[`WRITEUP.md`](WRITEUP.md).

## Origen

Este directorio es el scratchpad de aquella sesión, movido desde `/tmp` antes de que se lo llevara
un reinicio. Los scripts que dependían de rutas absolutas de esa ruta efímera no se versionan: no
corren en otra máquina, y venderlos como reproducibles sería mentir. Los que quedan son
autocontenidos.

## Qué hay aquí

| Fichero | Qué es |
|---|---|
| `classical_music.wv` | **El original** (395 MB, WavPack, sample rate falso π×10⁷ Hz). Todo lo demás sale de aquí. |
| `classical_music_decoded.mp4` | El vídeo PAL demodulado = Rick Astley, *Never Gonna Give You Up*. |
| `hackit6_part1_caption.png` | El caption del frame 125: `Part 1/3: v1nTag3`. |
| `hackit6_caption_hunter.mp4`, `caption_hunter.mp4` | Renders para cazar captions (realce de transitorios). |
| `freeview_*.png` | Renders para free-viewing (la pista falsa del autostereograma). |
| `frames/`, `tframes/` | Los 250 frames PAL (luma) y su versión de textura/subcarrier. |
| `*.npy` (8 × 1,2 GB) | Intermedios de señal: `msg_full` (demod FM), `pi_I/Q/amp`, `sep_176`, `sep_201pi`, `am_env`, `subimg_amp`. **Regenerables.** |
| `out.wav`, `raw.pcm` | Salida cruda de `wvunpack`. Regenerable. |
| `wvpkg/`, `zbarpkg/` | `.deb` extraídos para tener `wvunpack` y `zbarimg` sin instalar nada. |
| `vbi_capture.bin`, `barsig.npy` | La pista falsa del "teletexto" (era el artefacto del subcarrier). |
| `page.html`, `headers.txt`, `wv_headers.txt` | La web del reto y cabeceras HTTP/WavPack. |

Regenerar el pipeline básico (necesita `numpy`/`scipy`; el venv de `vhs-teletext` **no** se conservó):

```
wvpkg/usr/bin/wvunpack -y classical_music.wv -o out.wav   # ffmpeg lo rechaza: sample rate no estándar
# señal analítica (Hilbert) -> dφ/dt -> reshape a ancho 2011 = 625 líneas × 250 frames PAL
```

## Nota de git

Del directorio solo se versionan este README, el writeup y los scripts autocontenidos. Todo el
binario (~11 GB) está en `.gitignore`, así que la tabla de arriba describe el directorio **en
local**: buena parte de lo que enumera no está en el repo y se regenera desde el `.wv` con el
pipeline de abajo.
