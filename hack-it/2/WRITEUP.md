# Hack It EE34 — Nivel 2: "Bowling Physics"

> ## ⚠️ Corrección de fondo (2026-07-27)
>
> **La primera versión de este writeup se equivocaba en lo principal.** Decía que el dataset era
> decoración, que las cuatro bandas del residuo eran ruido del generador y que la contraseña era
> solo un juego de palabras del título.
>
> **La contraseña está escrita con letras dentro de los datos.** Es un bitmap de 36×27 en la matriz
> de correlación entre las filas del residuo de velocidades y las filas de posiciones: cuatro líneas
> de 9 píxeles —`M4d` / `F0r` / `mUL` / `4`—. Las "cuatro bandas de nueve filas" que medimos con tres
> decimales y llamamos ruido **son exactamente esas cuatro líneas de texto**.
>
> Reproducible con `python3 solve.py`. El análisis de abajo se conserva íntegro porque es correcto
> hasta donde llega —y porque el error de interpretación es la parte más instructiva del nivel—,
> pero léelo sabiendo cómo acaba. Detalle en §6 y §7.

Contraseña: **`M4dF0rmUL4`**.

Lo que hace raro a este writeup: acertamos la contraseña por un camino (un juego de palabras) que
no tenía nada que ver con el mecanismo real, y el acierto nos hizo archivar el análisis con una
conclusión falsa dentro. Caracterizamos el dataset hasta el residuo, encontramos un bug del
generador, corregimos un error de método propio, localizamos la señal al píxel… y escribimos que
ahí no había nada.

---

## 1. Qué te dan

El nivel, de `ontza`, **no tiene enunciado**. Ni una frase. En la página solo hay el título
—*Bowling Physics*—, el formulario de contraseña y dos ficheros:

```
/hackit/2/static/p.png      256 x 256, 16-bit/color RGB
/hackit/2/static/v.png      256 x 256, 16-bit/color RGB
```

Y en el HTML, comentado, un tercero:

```html
<!-- <img src="/hackit/2/static/m.png" width="256" heigth="256"> -->
```

`m.png` devuelve **404**. No es que esté escondido: no está. El autor lo comentó a propósito y dejó
la referencia a la vista.

Así que tenemos `p`, `v`, y una `m` que falta. Retén eso, que es literalmente la solución del reto.

## 2. Los PNG: 65.536 partículas

256×256 píxeles × 3 canales de 16 bits = **196.608 valores** por imagen, o **65.536 partículas con
tres componentes** cada una. Es el formato clásico de "meter un dataset físico en una textura".

`v.png` trae además un chunk `tEXt` con keyword `h` cuyo contenido son solo espacios, tabuladores y
saltos de línea: es **Whitespace**, el lenguaje esotérico. Cuarenta líneas de push+print que dan:

```
q v_min = -0.2, v_max = 0.2
```

O sea, la escala de desnormalización. Con eso:

```python
q = read16('p.png') / 65535.0                 # posiciones en [0,1]
v = read16('v.png') / 65535.0 * 0.4 - 0.2     # velocidades en [-0.2, 0.2]
```

Comprobado: `q` es **uniforme** (media 0,50021, desviación 0,28869 frente al 1/√12 = 0,28868 de una
uniforme, histograma plano en 16 bins). Las posiciones son puro relleno: la portadora sobre la que
va montada la señal, no la señal.

## 3. El modelo, a residuo cero

Ajustando `v` contra `q` sale una ley limpia. Regresión por mínimos cuadrados sobre las 196.608
muestras:

```
v = a*q + b*<q>_columna + c    ->    a = 0.099996   b = -0.089906   c = -0.000029
```

Es decir, con coeficientes redondos:

```
v = 0.1 * ( q - 0.9 * <q>_columna )
```

Un **flujo de Hubble**: velocidad proporcional a la distancia al centro. Con 0,1 de constante, el
"Big Bang" queda en t = −10. Muy bonito para un reto que se llama *Bowling Physics*.

Restando el modelo queda un residuo gaussiano de σ ≈ 0,00437 con **dos modulaciones por fila**: una
media `a_i` y una desviación `σ_i`. Y la σ no es plana: hay **36 filas** con exceso de varianza,
agrupadas en **cuatro bandas de nueve filas con pitch 13**:

```
banda A: filas 105-113
banda B: filas 118-126
banda C: filas 131-139
banda D: filas 144-152
```

Los pesos por banda, normalizados a la D, salen `3,93 / 1,88 / 2,51 / 1,00`. Cuatro bandas, con
pesos distintos, perfectamente regulares. Cualquiera diría que ahí hay un payload.

## 4. Trampa nº 1: un bug de eje del autor fabrica física falsa

El término `<q>_columna` es raro. Un flujo de Hubble se define contra **un** centro, no contra 256
centros distintos, uno por columna. Y ahí está la explicación: el autor escribió

```python
0.9 * q.mean(axis=0)      # medias por columna (256 valores)
```

donde quería

```python
0.9 * q.mean()            # la media global (un escalar)
```

Un fallo de broadcasting. La física pretendida era `v = 0.1*(q − 0.45)`, un Hubble puro. Lo que hay
en el fichero es esa misma ley con un centro distinto por columna.

Se ve numéricamente: si ajustas con la media escalar, el residuo queda en σ = 0,004680; con la media
por columna, baja a σ = 0,004369. El segundo modelo es el correcto porque es el que el código del
autor ejecutó, no el que quería ejecutar.

Y el efecto secundario es el peligroso: ese bug **crea un "centro" y un "foco temporal" aparentes**
que parecen diseño intencionado. Pasamos un buen rato interpretando como semántica lo que era un
`axis=0` de más.

> **Regla**: cuando un término del modelo aparece **en un solo eje** (filas XOR columnas) y no en el
> otro, sospecha del generador antes que de la semántica. La física real casi nunca distingue entre
> el eje X y el eje Y de una textura; el broadcasting de NumPy, siempre.

## 5. Trampa nº 2: la autocorrelación no responde a la pregunta que le haces

Esta es la que más caro sale, porque el test parece el adecuado.

La pregunta es: *¿la estructura está en las filas o en las columnas?* El reflejo es mirar la
autocorrelación a lo largo de una fila. Sobre el residuo, da esto:

```
lag1=+0.0760  lag2=+0.0600  lag3=+0.0704  lag5=+0.0836  lag13=+0.0670
```

Un valor pequeño, **plano en todos los lags, sin ningún pico**. Leído a la ligera: "no hay
estructura horizontal". Y es exactamente la conclusión equivocada.

Un conjunto de offsets **independientes por columna** no produce ningún pico de autocorrelación:
produce una constante minúscula repartida por igual en todos los lags, indistinguible del suelo de
ruido. La autocorrelación busca *periodicidad*, y unos offsets arbitrarios no son periódicos.

El test que sí responde es una **descomposición ANOVA fila-contra-columna**: comparar la dispersión
de las medias marginales con la que tendrían si todo fuera ruido.

```python
x = r.mean(2)                       # colapsa canales
esperado = x.std() / sqrt(N)        # sigma de una media de N valores i.i.d.
print(x.mean(1).std() / esperado)   # filas   -> 4.5
print(x.mean(0).std() / esperado)   # columnas-> 5.8
```

**4,5× y 5,8× el ruido esperado.** Las dos marginales gritan, y la autocorrelación no había dicho
ni mu.

> **Regla**: la autocorrelación detecta periodicidad, no estructura por eje. Si la pregunta es
> "¿filas o columnas?", el instrumento es ANOVA. Y `autocorr ≈ 0` **no** descarta offsets por eje.

## 6. El payload SÍ era un payload

> Esta sección decía lo contrario. Se conserva el diagnóstico original tachado porque el error es
> lo instructivo.

~~Con el modelo cerrado y las bandas aisladas, quedaba extraer el mensaje. No lo hay. Las cuatro
bandas son exceso de varianza, no de media: filas donde el generador metió más ruido. El contenido
es de máxima entropía y resiste todo lo que se le eche encima porque es exactamente lo que parece:
ruido.~~

**Falso.** Las cuatro bandas de nueve filas son las cuatro líneas del texto, y el exceso de varianza
es la huella que deja el mecanismo: el autor sumó a esas 36 filas de `v` múltiplos minúsculos de
ciertas filas de `p`, y sumar portadoras sube la varianza de la fila. Medimos la sombra del mensaje
con tres decimales y le pusimos el nombre equivocado.

El fallo se puede señalar con el dedo. La comprobación de "no queda nada" medía la estructura por
columna promediando sobre las **256 filas**:

```
DC por columna, promediando las 256 filas : std = 0,134   <- "ruido, absorbido por el modelo"
DC por columna, solo las 36 filas de banda: std = 2,661   <- x20
```

La señal vivía en el 14% de las filas. Diluida entre las otras 220 daba 0,134 y parecía nada. No fue
un test tramposo: fue **medir sobre la población equivocada**, que es difícil de ver precisamente
porque el número que sale es real y está bien calculado — solo que no responde a la pregunta.

Dos cosas más que también se midieron mal en la primera versión, por si sirven de calibración:

- Normalizar por la σ **global** infla el z de las bandas por su propio exceso de varianza
  (σ_local/σ_global = 1,43 en la banda A). Hay que usar la σ local del bloque.
- El residuo tiene la suma por columna forzada a cero, así que bandas y fondo salen anticorrelados
  a −0,995 por construcción. Cualquier evidencia de payload tiene que sobrevivir a quitar el perfil
  común. La de aquí sobrevive: tras quitarlo quedan 54/23/48/9 columnas por encima de 3σ en las
  bandas contra 0-3 en bloques equivalentes del fondo.

## 6b. Dónde estaba: el bitmap

El texto no está en ninguna de las dos imágenes, sino en la relación entre ambas:

```python
res = v - 0.1*q                              # quita la parte lineal
A   = normaliza_filas(centra(q))             # las 256 filas de p, unitarias
C   = centra(res) @ A.T                      # C[i,k] = <fila i del residuo, fila k de p>
glyph = C[filas_de_banda, 114:141] < -3.5    # bitmap 36x27
```

```
..##....##.....##.......#..      ......#####...####.........
..##....##.....##.......#..      ......#.......#..#.........
..##...###....###...#####..      ......#......#....#.#.#....
..#.#..#.#....#.#..##..##..      ......#......#....#.#......
..#.#..#.#...#..#..#....#..  M4d ......#####.##....#.#......  F0r
..#.#..#.#..#...#..#....#..      ......#......#....#.#......
..#.#.##.#..######.#....#..      ......#......#....#.#......
..#..##..#......#..##..##..      ......#.......#..#..#......
..#..#...#.....##...#####..      ......#.......####..#......
```

Control, celdas bajo −3,5σ: **215 de 972** en la ventana del texto, 14 de 8.244 en esas mismas filas
fuera de la ventana, y **0 de 5.940** en las filas de fondo dentro de la misma ventana. El dibujo
aguanta cualquier umbral entre −3 y −5σ.

Es esteganografía por espectro ensanchado, y explica por qué mirar los píxeles no sirve: en el
espacio de la imagen la señal está repartida entre 65.536 valores y queda bajo el ruido. Solo se
concentra al proyectar contra las portadoras.

## 7. Cómo la acertamos igual (por el camino de al lado)

`p`, `v`, y una `m` que el autor comentó para que la echaras de menos. Son los tres ingredientes de
**una fórmula**. El reto se llama *Bowling Physics* y el chiste remata en:

```
M4dF0rmUL4          =  "Mad Formula"
```

Acertó. Pero conviene ser exacto sobre qué fue esto: **una adivinanza afortunada, no la solución
del nivel**. El mecanismo real (§6b) no lo tocamos, y el paso de `p = m·v` a "*Mad* Formula" nunca
hemos sabido reconstruirlo del todo. Que la contraseña entrara nos hizo dar el reto por cerrado y
archivar el análisis con la conclusión falsa de §6 dentro.

Corrección menor de la primera versión: decía que el 404 de `m.png` era enunciado, porque suelta un
*"¿Dónde lo habré puesto? Parece ser que me falta algo…"*. No lo es — esa página lleva el menú
completo del sitio y el pie del framework, y sale igual con cualquier URL inexistente. El enunciado
de verdad es el comentario del HTML, que sí es el único propio de este nivel.

Dos cosas del acierto que sí son reproducibles y no golpe de suerte:

**El leet es la norma de la casa.** En esta misma edición: `C4M1NOS`, `4roM4Noc7urNo`, `h0LyGr4IL`,
`t4pF1gHtINg1nINmELEEiSLAND`. Si en este concurso te sale un candidato-frase, la forma en que se
envía es **en leet**, con mayúsculas intercaladas. Generar la variante leet de cada candidato
temático debería ser automático, no una ocurrencia.

~~**El dataset barroco era decoración.** 65.536 partículas, un flujo de Hubble, cuatro bandas
regulares y un texto en un lenguaje esotérico: todo eso es *flavor* alrededor de un concepto. El
error de marco fue tratar el dato como algo a decodificar en vez de como atrezzo de una idea.~~

> ~~**Regla**: en un reto con nombre temático fuerte y assets que resisten todos los decodes, prueba
> la hipótesis "los assets son decoración de una frase temática" **en paralelo** a la de extracción,
> no después de agotarla.~~

**Justo al revés.** El dataset **era** el puzle: la contraseña estaba escrita dentro con letras. La
hipótesis "esto es decoración" fue la que cerró el nivel en falso, y la regla que salía de ella
recomendaba abandonar antes la vía que sí llevaba a la solución. Se deja tachada porque el objeto de
estudio de este writeup ya no es el reto, es cómo se llega a escribir eso con toda la confianza.

Las reglas que sí quedan en pie, sustituyendo a la anterior:

> **Acertar la respuesta no valida el razonamiento.** Si el resultado llega por una vía y la
> investigación iba por otra, el acierto tapa el error en vez de corregirlo — y le da autoridad,
> porque ahora el análisis viene firmado por un reto resuelto.

> **Detectar una anomalía y explicarla no es lo mismo.** "El generador metió más ruido ahí" no dice
> por qué en cuatro bloques, por qué de nueve filas, ni por qué con ese espaciado. Una explicación
> que no predice ninguno de los detalles que ya has medido no es una explicación, es una etiqueta.

> **Antes de más potencia estadística, cambia de representación.** La señal era invisible en el
> espacio de la imagen y legible a simple vista en el espacio de correlación entre filas. Entre "aquí
> no hay nada" y leerlo con los ojos no hay ningún cálculo difícil: hay un cambio de base.

## 8. Reproducir

```bash
python3 solve.py          # la contraseña, dibujada: M4d / F0r / mUL / 4 (+ deja password.png)
python3 model.py          # modelo completo + las 4 bandas + comprobaciones de residuo cero
python3 png16.py p.png    # (256, 256, 3) uint16
```

Aviso sobre `model.py`: sus "comprobaciones de residuo cero" son las que dieron el falso negativo
de §6. Se conservan tal cual estaban, sin arreglar, porque forman parte de lo que hay que ver.

```python
# el texto oculto en Whitespace de v.png
import struct
d = open('v.png','rb').read(); i = 8
while i < len(d):
    ln = struct.unpack('>I', d[i:i+4])[0]; typ = d[i+4:i+8]
    if typ == b'tEXt': print(d[i+8:i+8+ln])
    i += 12 + ln
```

```python
# el bug de eje, en dos lineas
r_intencion = v - 0.1*(q - 0.9*q.mean())                     # sigma = 0.004680
r_real      = v - (0.1*q - 0.09*q.mean(0)[None,:,:])         # sigma = 0.004369
```

| Fichero | Qué es |
|---|---|
| `png16.py` | Decodificador PNG de 16 bits en numpy puro (PIL no lee 16-bit RGB del todo bien) |
| `model.py` | Modelo completo verificado: ley de Hubble, residuo, bandas y comprobaciones de residuo cero |

Los dos assets del reto, `p.png` y `v.png`, van aquí al lado, así que `model.py` corre tal cual sin
descargar nada. `m.png` no hace falta buscarla: devuelve 404, que es justo el chiste.

## 9. Lo que nos llevamos

1. **Un dataset elaborado no implica que el dataset sea el puzzle.** Puede ser el decorado de una
   contraseña conceptual. La pregunta "¿y si aquí no hay nada que extraer?" hay que hacérsela
   **pronto**, no cuando ya no quedan ideas.
2. **Término en un solo eje ⇒ sospecha de bug del generador**, no de semántica oculta.
3. **La autocorrelación no contesta "¿filas o columnas?".** Para eso, ANOVA. `autocorr ≈ 0` no
   descarta nada.
4. **Alta entropía que resiste todo decode suele ser ruido**, y cada hora invertida sin sacar un bit
   estructurado es evidencia a favor de esa hipótesis, no en contra.
5. **Aprende el estilo del concurso.** Si el resto de contraseñas van en leet, tu candidato va en
   leet.

Sobre el proceso: este reto se atacó con asistencia de IA, y es el caso en el que **peor** funcionó
de toda la edición — no por falta de potencia analítica, sino por exceso. El modelo estadístico se
cerró a residuo cero, con corrección de errores propios incluida, y el candidato ganador **nunca
entró en el ranking**: no se generó ni una sola vez. La respuesta salió de leer el título y las
letras `p`, `v`, `m` como lo que eran.

La conclusión incómoda, y la que nos llevamos a la siguiente: **el análisis exhaustivo es un mal
sustituto de preguntarse qué tipo de problema tienes delante.**
