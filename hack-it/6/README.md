# Hack It EE34 — Nivel 6 "Classical Music" (rickroll en señal PAL/FM)

Autor del reto: **ontza**. URL: `hackit.party.eus/hackit/6/`.

**Estado: parcialmente resuelto.** `Part 1/3 = v1nTag3`. Partes 2/3 sin encontrar tras ~20 enfoques.

El writeup del nivel, con el análisis de la señal y todo lo que se descartó, está en
[`WRITEUP.md`](WRITEUP.md).

## Qué hay en este directorio

| Fichero | Qué es |
|---|---|
| `WRITEUP.md` | El writeup completo del nivel. |
| `h6-frame125-raw.png` | El frame 125 recién demodulado, antes de limpiarlo. |
| `h6-part1-caption.png` | El rótulo que aparece en ese frame: `Part 1/3: v1nTag3`. |
| `page.html`, `page6_now.html`, `p5.html` | La página del reto tal como la servía el concurso. |
| `*.py` | Los scripts de análisis: demodulación FM, presupuesto espectral, búsqueda de portadoras, extracción de rótulos, diferencias entre frames. |

## Lo que no está aquí, y por qué

El fichero del reto (`classical_music.wv`, 395 MB) no se redistribuye: es material de *ontza*. Todo
lo demás que se generó durante el reto —el vídeo PAL demodulado, los 250 frames, ocho ficheros
`.npy` de 1,2 GB cada uno, los renders para free-viewing y los `.deb` extraídos de `wvunpack` y
`zbarimg`— suma unos 11 GB y **se regenera desde el `.wv`**. Nada de eso tiene sentido en un repo.

También quedaron fuera diez scripts que llevaban rutas absolutas de la máquina donde se resolvió:
no corren en ningún otro sitio, y publicarlos como reproducibles sería mentir.

## Regenerar el pipeline básico

Necesita `numpy` y `scipy`. El entorno de `vhs-teletext` **no** se conservó.

```
wvunpack -y classical_music.wv -o out.wav   # ffmpeg lo rechaza: sample rate no estándar
# señal analítica (Hilbert) -> dφ/dt -> reshape a ancho 2011 = 625 líneas × 250 frames PAL
```
