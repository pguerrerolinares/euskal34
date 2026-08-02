# Hack It EE34 — Nivel 2: "Bowling Physics"

> ## ⚠️ Corrección de fondo (2026-07-27)
>
> **La primera versión de este writeup se equivocaba en lo principal.** Decía que el dataset era
> decoración, que las cuatro bandas del residuo eran ruido del generador y que la contraseña era
> solo un juego de palabras del título.
>
> **La contraseña está escrita con letras dentro de los datos**, y el reto explica cómo llegar:
> falta `m.png`, los nombres dan `p = m·v`, y despejar `m = p/v` con `p` y `v` como vectores es
> proyectar fila contra fila. Sale una matriz 256×256 —el tamaño que el HTML anunciaba para
> `m.png`— con un bitmap de cuatro líneas: `M4d` / `F0r` / `mUL` / `4`. Las "cuatro bandas de nueve
> filas" que medimos con tres decimales y llamamos ruido **son esas cuatro líneas de texto**.
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

> **Nota (2026-07-28): las trampas de §4 y §5 son de nuestro rodeo, no del reto.** Ninguna de las dos
> aparece en el camino que el nivel dicta (§6b): ahí el término `<q>_columna` no llega a existir
> porque nadie hace esa regresión —el coeficiente lo da la diagonal de la primera proyección—, y la
> pregunta que la autocorrelación contesta mal ni se plantea, porque en vez de buscar estructura
> dentro del residuo se proyecta. Se conservan porque las lecciones de método valen fuera de aquí,
> no porque haya que sortearlas para resolver el nivel.

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
es la huella que deja el mecanismo: el autor **restó** a esas 36 filas de `v` múltiplos minúsculos de
ciertas filas de `p` —coeficiente medio **−0,00519**, el **97% negativos**—, y meterle a una fila una
portadora, con el signo que sea, sube su varianza. La magnitud del múltiplo da la escala del
problema: 0,00519 contra el 0,0996 del término físico que lo tapa, **1/19 de lo que hay encima**.
Medimos la sombra del mensaje con tres decimales y le pusimos el nombre equivocado.

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

## 6b. El camino que el reto daba: reconstruir m.png

No es un conejo sacado de la chistera. El nivel lo explica entero, en cuatro pasos:

1. **Falta un fichero y te enseñan su nombre.** El HTML comenta
   `<img src="/hackit/2/static/m.png" width="256" heigth="256">`, que da 404. Retén el `256x256`.
2. **Los nombres son la fórmula.** `p`, `v` y una `m` ausente, con un título que dice *Physics*:
   `p = m·v`, el momento lineal. Y el reto no pide reconocer la fórmula, pide **despejarla**:
   `m = p/v`. El fichero que falta es el objetivo, no un guiño.
3. **Dividir vectores es proyectar.** `p/v` no es una división píxel a píxel — probada, no da nada,
   y no tiene por qué darlo: en la fórmula del momento `p` y `v` son vectores y `m` el escalar que
   los relaciona, así que se proyecta: `(v·q)/(q·q)`. Cada fila es un vector de 768 componentes; se
   proyectan todas contra todas. El `256×256` del HTML confirma que es una **tabla de todos contra
   todos** y no una división punto a punto — pero ojo, no discrimina la orientación: las cuatro
   posibles dan 256×256.
4. **ÚNICO PASO NO DEDUCIBLE: ¿la fila o la columna?** Se resuelve probando, una línea cada una.
   Con el criterio de este camino —`solve.py` entero, celdas bajo −3,5σ, z contra el fondo y sin
   contar la diagonal— salen **201 / 12 / 14 / 8** para `p` filas × `v` filas, `p` filas × `v`
   columnas, `p` columnas × `v` filas y `p` columnas × `v` columnas. Si ya has caracterizado el
   residuo, el dato orienta antes de probar: exceso de desviación por filas 0,1160 contra 0,0526 por
   columnas, y las filas con exceso están en cuatro bloques contiguos de nueve mientras que las
   columnas están dispersas.
5. **La primera proyección te escribe el modelo.** `diag(proj(v,q)) = 0,099615`, con el resto casi
   cero: cada fila de `v` es 0,1 veces **la misma** fila de `q`. Ningún ajuste, ningún barrido.
6. **Cancelas eso y vuelves a proyectar.** No es "quitar física": las filas de `q` no son ortogonales
   (se parecen ~1/√768 = 0,036), así que el término conocido `0,1·q` se derrama fuera de la diagonal
   con un ruido de **3,7e-3**, 4,4× el ruido de fondo real (8,2e-4). El mensaje vale −9,2e-3: **2,5σ**
   sobre el derrame (invisible) y **11,2σ** una vez cancelado.
7. **Renderizas la matriz entera y se lee.** Sin ventanas, sin umbrales, sin saber dónde mirar.

```python
alpha = diag(proj(v,q)).mean()                   # 0.099615, el dato escribe su modelo
m     = proj(v - alpha*q, q)                     # cancela el derrame de la portadora
```

**Esto es un atajo, y conviene decirlo:** proyectar es multiplicar por la *transpuesta*, no por la
inversa. Las dos coinciden solo si las filas de `q` son ortogonales, y no lo son —de ahí el derrame
y el paso de cancelación. El despeje canónico es una línea sin trucos, `M = P @ pinv(V)` —el orden
literal de la fórmula—, y lee el mismo texto: §8, `solve_inversa.py`.

El divisor `(q·q)` es cosmético: con el criterio del paso 4, **201** celdas con él y **202** sin él.
La ventana de filas y columnas y el umbral −3,5σ son cosa nuestra, elegidos a posteriori para
tabular controles: para leer el texto no hace falta ninguno de los dos.

**Nota de instrumento.** El paso 4 decía antes `216 / 0 / 1 y 0`, y el divisor, `212 celdas en vez
de 216`. Esas cifras son de julio y **no son reproducibles**: no salen por ninguno de los dos
caminos del repo, y el script que las produjo no se conservó. Es el fallo de §6 otra vez, en
pequeño: un número bien calculado en su día del que ya no se puede decir qué medía. Las de ahora
están medidas con el código de este directorio, y como el recuento depende del camino y del umbral,
van las tres combinaciones que tienen sentido:

| medición | p fil × v fil | p fil × v col | p col × v fil | p col × v col |
|---|---|---|---|---|
| `solve.py` (transpuesta), celdas bajo −3,5σ | **201** | 12 | 14 | 8 |
| `solve.py` (transpuesta), abs(z) > 3,5σ | **222** | 30 | 31 | 21 |
| `solve_inversa.py` (pinv), abs(z) > 3,5σ | **220** | 30 | 28 | 5 |

En las tres, z se toma contra la media y la desviación del fondo, y ni la normalización ni el
recuento incluyen la diagonal. La primera es la que usa este §6b, porque es lo que `solve.py`
ejecuta y sus letras salen en negativo; la tercera es la que cita el writeup divulgativo. Ninguna
cambia la conclusión —la orientación buena gana por un orden de magnitud en las tres—, pero son tres
instrumentos distintos y el número solo significa algo con el suyo al lado.

> **Regla**: una cifra sin el instrumento que la produjo no es un dato, es una anécdota. Si el
> script no se conserva, el número no se puede volver a citar; y si además nadie declara el
> criterio, dos medidas legítimas del mismo experimento parecen una contradicción.

**El chunk Whitespace no hace falta —si centras.** Repitiendo todo con los enteros crudos y leyendo
el coeficiente de la diagonal (allí 0,249038 = 0,1/0,4) sale **el mismo bitmap, idéntico**: 215/972
celdas en los dos casos, cero píxeles de diferencia. La razón es que la desnormalización es una
transformación afín `v = a·v_int + b`, y la proyección de aquí centra cada fila: el offset `b` se
cancela al centrar y el factor `a` es un escalar global que desaparece al leer en sigmas. Por eso
solo cambia el coeficiente de la diagonal, y por el factor exacto 1/0,4 = 2,5.

El matiz importa porque **por el camino canónico (§8, `solve_inversa.py`) sí hace algo**, aunque
tampoco sea una llave: allí no hay centrado, así que la escala no se cancela sola. Con los enteros
crudos el mensaje se lee igual (219 celdas, verificado), pero la diagonal sale **3,9410** en vez de
**10,2327**. O sea: la desnormalización completa no abre ninguna puerta, es lo que convierte esa
diagonal en el `1/H` del §3 —10,2327, o sea 1/0,0977— en vez de un escalar atado a la escala
arbitraria de los 16 bits.

Lo que el chunk sí aporta es notación — su keyword es `h` (constante de Hubble reducida) y llama `q` al
contenido de `p.png` (posición, notación hamiltoniana). Dice qué magnitud hay en cada fichero.

**Y este nivel no tuvo pistas del organizador**, al contrario que el 3, donde la Pista 4 era la
solución. Verificado contra cuatro capturas de `/hackit/2/`, dos posteriores a que el nivel cayera:
el único texto propio del reto en todas es el comentario de `m.png`. No había red, y el camino
estaba entero dentro de los dos ficheros.

Y ahí está la contraseña, escrita. El chiste cierra el nivel: `M4dF0rmUL4` = *"Mad Formula"* es el
nombre de la fórmula que has tenido que despejar para poder leerla.

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

Control, celdas bajo −3,5σ: **215 de 972** en la ventana del texto, 13 de 8.244 en esas mismas filas
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
> espacio de la imagen y legible a simple vista en el de proyección entre filas. Entre "aquí no hay
> nada" y leerlo con los ojos no hay ningún cálculo difícil: hay un cambio de base.

> **El enunciado estaba en los nombres de los ficheros.** `p`, `v` y una `m` ausente de 256×256 no
> eran un guiño temático: eran una instrucción con las dimensiones del resultado puestas. Nos
> quedamos con la mitad —vimos la fórmula, nos gustó como chiste y sacamos la contraseña de ahí— sin
> llegar a leerla como la operación que había que ejecutar sobre los datos.

## 8. Reproducir

```bash
python3 solve.py          # la contraseña, dibujada: M4d / F0r / mUL / 4 (+ deja password.png)
python3 solve_inversa.py  # lo mismo por el camino canónico: m = p·v⁻¹, en una línea
python3 model.py          # modelo completo + las 4 bandas + comprobaciones de residuo cero
python3 whitespace.py     # decodifica el chunk oculto de v.png, instruccion a instruccion
python3 png16.py p.png    # (256, 256, 3) uint16
```

### Dos caminos para el mismo despeje

`solve.py` proyecta (multiplica por la **transpuesta**) y `solve_inversa.py` despeja (multiplica por
la **inversa**, en la práctica `pinv`). El núcleo del segundo es una línea:

```python
M = P @ np.linalg.pinv(V)        # p = m·v  ->  M = P·V⁻¹.  V es 256x768, rango 256
```

Sin `alpha`, sin cancelar portadora, sin centrar, sin segunda proyección: escribes la ecuación, la
despejas y el texto está ahí. La transpuesta es una **aproximación** de la inversa que sería exacta
si las filas de `q` fueran ortogonales; como se parecen ~1/√768 = 0,036 y la diagonal vale 10 veces
el mensaje, ese 3,6% de parecido derrama por toda la tabla y lo tapa —el paso `v − alpha·q` es
justamente lo que la inversa se ahorra, porque descuenta el parecido por construcción.

Medidos con la misma vara. Ojo con los denominadores del control de fondo: no son el mismo número,
porque en el camino canónico la diagonal no se cancela en ningún paso y sus celdas valen 124-135σ —
son el `1/H` del modelo, no ruido—, así que las 9 que caen dentro del rango de columnas de la ventana (los
huecos 114-117, 127-130 y 140 entre bandas de texto) se excluyen una a una por su máscara diagonal,
5.940 − 9 = 5.931:

| | ruido σ | señal | SNR | celdas sobre umbral | fondo, mismas cols | esas filas, otras cols |
|---|---|---|---|---|---|---|
| `solve.py` (transpuesta, −3,5σ) | 0,925 | −5,63σ | 6,1 | 215/972 | **0** de 5.940 | 13 de 8.244 |
| `solve_inversa.py` (inversa, +3,5σ) | 0,919 | +14,0σ | 15,2 | 237/972 | **0** de 5.931 | 19 de 8.244 |

Los dos leen el mismo bitmap y la diferencia de celdas es de bordes del glifo. Donde no empatan es
en el margen: el orden literal pone el `1/H` en la diagonal y el mensaje en positivo, con dos veces
y media el SNR del atajo. Y los 19 del canónico no son detección de más — **18 son la propia
diagonal**: las filas 105-113 y 144-152 tienen su `M[i,i]` fuera del rango de columnas de la
ventana, así que su ~10 en sigmas se cuela en ese recuento tal cual. Ruido de verdad, 1 celda.

Lo que menos empata es la exposición: el writeup dice "despejar `m = p/v`" y el código canónico
literalmente hace eso, mientras que el atajo hace otra cosa que resulta equivalente. Esa distancia
entre lo que se dice y lo que se ejecuta es de la misma familia que el error de §6.

> **Regla**: si tu código no se parece a la frase con la que explicas el método, la frase o el código
> están de más. La forma canónica cuesta más FLOPs y menos preguntas.

**Aviso para quien reproduzca: los dos órdenes funcionan, y dan resultados espejo.** `p/v` y `v/p`
son la misma información por sus dos caras, y ninguno borra nada. Lo que cambia es dónde queda cada
cosa: si `M ≈ 0,1·I + mensaje`, entonces `M⁻¹ ≈ 10·I − 100·mensaje`, así que al invertir el orden se
invierten a la vez la diagonal y el signo del mensaje.

```
P @ pinv(V)   "p entre v", el literal : diagonal 10,2327 = 1/H, el tiempo de §3 ; mensaje ALTO
V @ pinv(P)   "v entre p"             : diagonal  0,0996 = H, la constante de §3 ; mensaje BAJO
```

De los dos, **el literal es el que la fórmula del reto dicta y el que mide mejor**: el mensaje llega
a 14,0σ, 237/972 celdas sobre +3,5σ y 0 falsos positivos de 5.931 en las filas de fondo. Es el que
hace `solve_inversa.py`. En la diagonal, en cambio, no hay nada que elegir: los dos números son el
mismo dato por sus dos caras, y ninguno de los dos es una masa (ver abajo).

Lo que sí hay que vigilar es el signo del umbral, porque todo el instrumental de este repo nació del
atajo y busca celdas **negativas**:

```
P @ pinv(V), buscando celdas bajo -3,5σ :   0 de 972    <- parece que no hay nada
P @ pinv(V), buscando celdas sobre +3,5σ: 237 de 972    <- está, y a 14,0σ
```

Ese cero no dice nada del método, dice que estás buscando manchas oscuras en un texto que salió en
claro. Es el mismo error de §6 en pequeño: la medición está bien hecha y no responde a la pregunta.

### La diagonal es un tiempo, no una masa

Corrección de una versión anterior de esta misma sección, que llamaba **masa** al 10,2327 porque el
título del reto dice `p = m·v`. No lo es, y el §3 ya tenía el nombre bueno: es el **tiempo de
Hubble**, `1/H`. `1/10,2327 = 0,097726`, que es el `0,1` de la ley `v = 0,1·(q − 0,9·<q>_col)`. El
mismo número que el §3 usa para poner el "Big Bang" en `t = −10`, y este párrafo existía diciendo lo
contrario a doce pantallas de distancia.

Tres comprobaciones, ninguna sutil:

```
M @ V ≈ Q  (M convierte velocidades en posiciones)   ->  [M] = long/(long/tiempo) = TIEMPO
v negativos: 88.368 de 196.608 (44,95%)  |  p negativos: 0
q: min 0,0000  max 1,0000  media 0,50021  skew -0,0020  kurt -1,2007  -> uniforme(0,1)
```

La segunda es la que cierra el asunto sin álgebra: si `p` fuera `m·v` con `m > 0`, los 88.368 valores
negativos de `v` tendrían que aparecer como 88.368 negativos en `p`, y `p` no tiene ni uno. La
ecuación del título **no se cumple sobre los píxeles**. Y `q` uniforme en [0,1] con el rango de 16
bits completo es una caja de partículas repartidas al azar, no un campo de momentos. Lo de 10,23 en
vez de 10,00 tiene también su explicación en casa: el bug de eje de §4 mete el término `<q>_col`, y
la diagonal carga con él.

El chiste del nivel no se toca: `p`, `v` y una `m` ausente es lo que te lleva a la operación, y de
ahí sale la contraseña. Lo que cambia es qué devuelve la operación cuando la ejecutas.

> **Regla**: que un despeje devuelva un número redondo no lo convierte en la magnitud que ibas
> buscando. Antes de ponerle nombre, mira las dimensiones y mira los signos. Aquí bastaba contar
> negativos.

### ¿Hacían falta 16 bits?

No. Recuantizando **los dos** PNG al mismo rango declarado y repitiendo el despeje canónico entero:

| bits | diagonal | celdas >3,5σ | distintas vs 16 bit | |
|---|---|---|---|---|
| 16 | 10,2327 | 237 | — | |
| 8 | 10,2303 | 234 | 3 | idéntico a ojo |
| 5 | 10,0707 | 207 | 34 | todavía legible |
| 4 | 9,6700 | 86 | 151 | roto |

El mensaje muere entre 5 y 4 bits. A 8 el bitmap sale entero y la pérdida de señal es del 0,7%.

Lo interesante es **por qué sobrevive**, porque no es obvio: una portadora perturba una muestra de
`v` en 1,4e-3, que a 8 bits son **0,88 pasos de cuantización**. Por debajo del escalón: ella sola se
redondearía a nada. Aguanta por dos motivos que se suman — cada fila lleva ~6 portadoras a la vez
(2,3 escalones, ya por encima) y la detección integra las 768 muestras de la fila. Además el ruido
propio del generador es **6,3×** el error rms de cuantizar a 8 bits, y los ruidos se suman en
cuadratura: el daño total al suelo de ruido es un **+1,25%**.

O sea que los 16 bits no sostienen la esteganografía. Son el idioma habitual de meter un dataset
físico en una textura, y punto. Lo llamativo es lo contrario de lo que parece: que el mensaje quepa
**por debajo de un escalón de 8 bits** y se lea igual.

Aviso sobre `model.py`: sus "comprobaciones de residuo cero" son las que dieron el falso negativo
de §6. Se conservan tal cual estaban, sin arreglar, porque forman parte de lo que hay que ver.

Aquí había un snippet de tres líneas que recorría los chunks y volcaba el `tEXt` crudo. Lo hace
`whitespace.py`, que además lo **interpreta**: Whitespace no es un cifrado, es un lenguaje, así que
el chunk no se descifra, se ejecuta. El script enseña el paso intermedio —caracteres invisibles
pintados, bits, decimal, carácter—, que es justo lo que faltaba para ver de dónde sale el mensaje:

```
$ python3 whitespace.py
chunk tEXt en v.png: keyword='h', 392 bytes de contenido
  espacios=215  tabuladores=120  saltos=57  (total=392)

···→→→···→     push  1110001 = 113  ->  'q'
···→·····      push  100000 =  32  ->  ' '
···→→→·→→·     push  1110110 = 118  ->  'v'
···→·→→→→→     push  1011111 =  95  ->  '_'
[... 27 pares push+output, uno por carácter ...]
↵↵↵            end   (fin de programa)

salida completa: 'q v_min = -0.2, v_max = 0.2'
```

Los tres saltos finales no son relleno: son el `END` de Whitespace, y el script los nombra en vez de
tratarlos como sobras. Y ante cualquier instrucción que no implemente **para**, diciendo cuál es y en
qué byte, en lugar de saltársela y seguir. En un writeup cuyo tema es haber sacado una conclusión de
una medición que no respondía a la pregunta, un decodificador que se niega a ignorar lo que no
entiende no es un capricho.

```python
# el bug de eje, en dos lineas
r_intencion = v - 0.1*(q - 0.9*q.mean())                     # sigma = 0.004680
r_real      = v - (0.1*q - 0.09*q.mean(0)[None,:,:])         # sigma = 0.004369
```

| Fichero | Qué es |
|---|---|
| `solve.py` | La solución por proyección (transpuesta + cancelación de la portadora) |
| `solve_inversa.py` | La misma solución por el despeje canónico y literal, `M = P @ pinv(V)` |
| `png16.py` | Decodificador PNG de 16 bits en numpy puro (PIL no lee 16-bit RGB del todo bien) |
| `model.py` | Modelo completo verificado: ley de Hubble, residuo, bandas y comprobaciones de residuo cero |
| `whitespace.py` | Extrae el chunk `tEXt` de `v.png` sin PIL y ejecuta el programa Whitespace que lleva dentro, con la traza instrucción a instrucción (bits → decimal → carácter). Implementa `push`, `output char` y `end`; ante cualquier otra para y dice cuál y en qué byte. Acepta el PNG como argumento, `v.png` por defecto |

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
