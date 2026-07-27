# Solve It EE34 — Nivel 4: "Moviplaya 2005"

> *"Esta ROM esconde un misterio que no somos capaces de resolver."*

Los assets no son una imagen: son una **ROM de Game Boy Advance de 16 MB** (`pokemon-esmeralda.gba`)
y una **partida guardada** (`pokemon-esmeralda.sav`, 131.088 bytes). El título apunta a Moviplaya
2005, el tour de playa donde Nintendo repartía eventos de Pokémon en España aquel verano.

Spoiler: **`4roM4Noc7urNo`** — leet de *"aroma nocturno"*. El reto es una cadena larga: un señuelo
que hay que descartar, una palanca que lo abre entero, una búsqueda del tesoro inyectada en el
binario, un sistema de escritura que no es el que parece, y un chiste final que ata el nombre de la
contraseña con la llave que abre la última puerta.

**Aviso de marco, por delante de todo lo demás.** El nivel está diseñado para **jugarse**: descifras
las señales de la isla, andas el recorrido que dictan, abres el pasadizo del final, ganas el combate
que hay dentro y el juego te escribe la contraseña en pantalla. Esa era la puerta principal. Nosotros
entramos por el binario, que llega antes y explica más, pero es un **atajo**. La cadena está cerrada
por las dos puntas —el recorrido se ha andado dentro del juego y la contraseña sale en pantalla—, y
las dos rutas se documentan aquí abajo, con la que seguimos marcada como tal.

---

## 1. El save es el señuelo

La reacción natural con un save de Pokémon es buscar el flag ahí: un mote, un nombre de entrenador,
un nombre de caja. Es un clásico de CTF y hay que descartarlo bien, porque los textos de Gen 3 van
en un **charset propietario** y `strings` no ve nada.

La estructura del save Gen 3 son secciones de 4 KB con su ID y su checksum; los Pokémon van
cifrados con `PID ^ TID` salvo los motes y el OT, que van en claro. Con eso se localiza el bicho
temático:

```
$ python3 deoxys.py
PID  d3c888e5  TID(vis)=19144 SID=22553
species 410 item 0 exp 132356 friendship 255
met location byte: 187 0xbb
level met: 30 game origin: 4 FireRed ball: 2
ribbons 80000000
SHINY? False
nick bytes bebfc9d2d3cdff033c21   OT bytes cdc2c3c8d3a2a5
```

Traduciendo el charset: mote **`DEOXYS`**, OT **`SHINY14`**. Y los campos que importan:

- **met location 187**, nivel 30, juego de origen **FireRed**;
- **ribbons `0x80000000`** — el bit 31 es el *fateful encounter*.

Para saber qué es el 187 no hace falta creerse una wiki: la tabla de nombres de zona
(`gRegionMapEntries`) está en la propia ROM, 8 bytes por entrada con un puntero al nombre en `+4`.
Volcándola, **187 = Birth Island** (Isla Origen). O sea, es una captura **legítima** de Isla Origen,
exactamente como la consigue cualquier jugador. Y el resto del save es un *living dex* ripeado de
internet: OTs de broma (`BRIAN`, `Miranda`), cajas con nombres por defecto, cuatro bichos en Master
Ball con TIDs distintos entre sí. Ruido de un save descargado.

Aquí conviene añadir el dato cultural, porque cierra el señuelo: **Moviplaya 2005 no repartía un
Deoxys**. Repartía el **Ori-ticket** (Aurora Ticket) vía Regalo Misterioso, que desbloquea Isla
Origen para que captures el Deoxys tú mismo. Así que el Deoxys del save es coherente con el evento
pero no *es* el evento, y no lleva nada dentro.

**El save no tiene flag.** Merecía comprobarse; no merecía más de media hora.

## 2. La palanca: la ROM está modificada, y el idioma lo delata

El dato que decide el reto está a la vista desde el primer minuto:

```
$ md5sum pokemon-esmeralda.gba
51605ffd710c397ee1c1b08f98f188e7  pokemon-esmeralda.gba
```

No coincide con el dump oficial de Emerald. Compáralo con tu propia copia limpia: el punto es que
**difiere**, no el hash concreto.

El primer intento de explotarlo fue por la vía tonta —diff byte a byte contra una referencia— y no
sirve: salen ~10 MB de 16 diferentes, porque los datos recompilados divergen en bloque aunque el
juego sea el mismo. Tampoco hay ficheros embebidos, ni bloques inyectados en el padding `0xFF`, ni
nada tras el final. Con eso se descarta la esteganografía de fichero, pero no se avanza.

La palanca buena es **diffear el texto decodificado, no los bytes**. Y funciona por una razón
concreta y muy explotable:

> La Emerald base es **inglesa**. Todo texto en **español** dentro de esta ROM es **inyectado por el
> autor**.

Ni siquiera hace falta una ROM de referencia para ver el efecto — se ve en el propio volcado, donde
el castellano inyectado convive con el inglés original:

```
El misterio de FAIL ISLAND? Ni IMOBILIS ni yo fuimos capaces de resolver esas
escrituras. Hay un viejo amigo que quizá pueda ayudarte. Hace tiempo que no le
vemos, pero debe de andar por MOSSDEEP. Pregunta por HÉCTOR.
| Este dashboard de Grafana no pinta bien, tendremos que revisar los switches...
| Hm? You don't seem to have any room for this POKeMON.
| ¡¡ received CASTFORM!
```

El decodificador son quince líneas: recorres la ROM, traduces cada byte por la tabla Gen 3, y te
quedas con las tiradas largas que parezcan frase humana.

```python
CH = {0x00:' ', 0xAD:'.', 0xB8:',', 0xAB:'!', 0xAC:'?', 0xB4:"'", 0xF0:':'}
for i,c in enumerate('0123456789'):                 CH[0xA1+i] = c
for i,c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'): CH[0xBB+i] = c
for i,c in enumerate('abcdefghijklmnopqrstuvwxyz'): CH[0xD5+i] = c

rom = open('pokemon-esmeralda.gba','rb').read()
runs, cur, start = [], '', 0
for i, b in enumerate(rom):
    if b in CH:
        if not cur: start = i
        cur += CH[b]
    else:
        if len(cur.strip()) >= 14 and sum(c.isalpha() for c in cur) >= 10:
            runs.append((start, cur.strip()))
        cur = ''
```

Restando el mismo conjunto calculado sobre una Emerald limpia (`set(chal) - set(ref)`) queda solo lo
inyectado. Con una referencia a mano es inmediato; sin ella, filtrar por acentos y palabras
castellanas te lleva al mismo sitio.

**Aviso de método, y es el error que nos costó una hora larga**: esa herramienta la habíamos escrito
mucho antes… para preguntar otra cosa. La usamos para comprobar *"¿esta ROM está en español?"*,
respondimos *"no, es inglesa"*, y seguimos buscando bloques inyectados en el padding. La pregunta
correcta —*"¿qué texto hay aquí que no esté en la original?"*— usaba exactamente el mismo código.
**Tener el instrumento adecuado no sirve de nada si le haces la pregunta pequeña.**

## 3. Lo que aparece: una búsqueda del tesoro entera

Con los diálogos inyectados a la vista, el reto se lee solo. Offsets reales de esta ROM:

| Offset | Fragmento |
|---|---|
| `0x270bcc` | *"Ni IMOBILIS ni yo fuimos capaces"* |
| `0x270c59` | *"debe de andar por MOSSDEEP."* |
| `0x1e53af` | *"CTOR, en cambio, suele estar"* |
| `0x1e53cc` | *"en el CENTRO ESPACIAL."* |
| `0x1e54c6` | *"Si quieres respuestas, busca"* |
| `0x1e54a9` | *"preguntas sobre FAIL ISLAND."* |
| `0x2246f3` | *"Claro, las escrituras dicen que..."* |
| `0x2247ac` | *"Haz sitio para el FAIL TICKET"* |
| `0x1e556f` | *"CTOR te da un ticket raro,"* |
| `0x1e55fe` | *"barcos especiales."* |
| `0x1e5660` | *"FAIL ISLAND, seg"* |
| `0x1e541e` | *"de FAIL ISLAND."* |

Los fragmentos están cortados donde están **a propósito**: el decodificador de arriba no mapea
vocales acentuadas ni `ñ`, así que cada acento **parte la tirada** y el offset que ves es el del
trozo, no el de la frase completa. Por eso *"HÉCTOR"* aparece como `CTOR` y *"señales"* no sale
entera. Se arregla ampliando `CH`, pero entonces los offsets se desplazan — así que aquí publicamos
los que produce **exactamente** el fragmento de código de la sección anterior, para que copiar y
pegar dé lo mismo que leer.

La ruta, en claro:

```
Centro Espacial de MOSSDEEP (planta alta) → HÉCTOR → FAIL TICKET
    → puerto de CALAGUA → barco → FAIL ISLAND → "llena de señales"
```

**FAIL ISLAND** y **FAIL TICKET** son la parodia de Birth Island y el Aurora Ticket, que es
exactamente el evento de Moviplaya. El chiste cierra. Y el enunciado del reto —*"un misterio que no
somos capaces de resolver"*— resulta ser una **cita literal de un NPC**: es un personaje del juego
diciéndotelo. (Y de propina, un NPC suelta *"este dashboard de Grafana no pinta bien"*, por si
quedaba duda de que el texto es inyectado.)

Aquí el reto deja de ser análisis estático: hay que **jugarlo**. Con mGBA y el save cargado, la
ruta funciona tal cual. Las señales de Fail Island están en `imagenes-isla-fail/`
(nueve capturas).

## 4. Las señales: *night writing*, y braille en el mismo cartel

Aquí es donde el reto nos ganó, y el error fue de **modelo**, no de umbral. Dos veces seguidas, y la
segunda es la interesante.

Las señales parecen Braille, y la mayor parte no lo son. Son **night writing** —la *sonografía* de
Charles Barbier, 1815—, el sistema militar del que Louis Braille partió y que luego simplificó. La
diferencia es exactamente la que decide este reto:

| | Braille | Night writing |
|---|---|---|
| Celda | **6 puntos**, 3 filas × 2 columnas | **12 puntos**, **6 filas × 2 columnas** |
| Codifica | letras | **sonidos** (fonemas) |
| Lectura | patrón de puntos → letra | **cuenta** de puntos por columna → coordenada |

En night writing cada celda es un **par de coordenadas** sobre una rejilla de 6×6 = 36 sonidos. La
columna izquierda lleva **n puntos en relieve contados desde arriba** y eso da la **fila**; la
derecha da la **columna**. No es un bitmap: es un **tally**.

La tabla de Barbier:

| | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| **1** | a | i | o | u | é | è |
| **2** | an | in | on | un | eu | ou |
| **3** | b | d | g | j | v | z |
| **4** | p | t | q | ch | f | s |
| **5** | l | m | n | r | gn | ll |
| **6** | oi | oin | ian | ien | ion | ieu |

Y la confirmación temática es del propio reto: **night writing es *escritura nocturna*** —Barbier la
diseñó para leer de noche sin luz—, y la contraseña es *"aroma **nocturno**"*. El nombre de la
técnica está dentro de la respuesta.

### Cómo se ve en los píxeles

Cada posición de punto se dibuja como una **barra horizontal de ~6 px**, en uno de dos tonos: gris
oscuro (`99`) y gris claro (`213`). Volcando una columna entera de una celda:

```python
col = [int(np.median(im[y, x-6:x+7])) for y in range(86, 190)]
print(''.join('#' if v < 150 else ('o' if v < 245 else '.') for v in col))
```

```
columna izquierda:  ...######.............######............######.......oooooo............oooooo.............oooooo........
columna derecha:    ...######.............######............oooooo.......oooooo............oooooo.............oooooo........
```

Seis barras por columna. Izquierda: `# # # o o o` → **3**. Derecha: `# # o o o o` → **2**. Un
**tally contiguo desde arriba**, que es justo lo que predice Barbier. En la señal que usamos de
banco de pruebas, **8 de sus 10 celdas** dan tallies contiguos limpios de este tipo.

### Por qué fallaron todos los intentos de OCR

El diagnóstico que dimos en su día —*"el umbral ve seis filas donde hay tres"*— estaba **del
revés**. **Hay seis filas.** Éramos nosotros los que las colapsábamos a tres para que cupieran en una
celda de Braille. Cada heurística que añadimos después —clustering de filas, dilatación por celda,
fuerza bruta sobre las convenciones oscuro/claro— era un parche para que un modelo equivocado
tragara los datos. Y funcionaban a medias, que es lo peor que puede pasarte: producían celdas de
seis puntos "imposibles" y patrones no contiguos, y nosotros leíamos eso como ruido de
umbralización en vez de como lo que era, **el modelo diciéndonos que no**.

Había además una pista explícita que nadie usó. Al mirar los carteles a ojo, la descripción fue
literalmente *"la primera celda es negrita: 1 4 / 2 5 / 3 6 - 7 - 8, son **12 elementos en total, 6
filas × 2**"*. Doce. Estaba contado y escrito, y seguimos forzando seis.

### El bug que hacía que un modelo correcto diera basura

Antes de los datos, el error de segmentación, porque es el que costó las horas.

Cada línea de texto **se ve como tres bandas horizontales**, y la tentación es tratar cada banda
como una línea. No lo son: **las tres bandas juntas son UNA línea de celdas**, con dos filas de
puntos en cada banda. 3 × 2 = las 6 filas de la celda.

Si agrupas mal, cada celda queda partida en tres trozos y el tally sale a un tercio de su valor: lees
2 y 3 donde hay 4, 5 o 6. Y lo venenoso es que **no falla de forma evidente** — produce números
plausibles, dentro de rango, que mapean a sonidos válidos de la tabla. Sale una transcripción
completa, con pinta de resultado, y es basura. El modelo de celda era correcto desde el principio;
lo que estaba mal era el agrupamiento de bandas.

Hay un segundo detalle, y aquí nos equivocamos de nuevo: en algunas señales la primera celda tiene
las barras unas tres veces más altas que las de las celdas normales, y lo despachamos como
**ornamento**. No lo es. Esas celdas llevan dato, en el otro sistema de escritura del cartel — la
sección *El segundo sistema* de más abajo. Apartarlas fue lo que dejó el decode a medias.

### Lo que dicen las señales

Con la agrupación correcta el texto se vuelve legible, y es **francés**:

```
S2   un     pas  vers …
S7   deux   pas  vers …
S4   trois  pas  vers …
S3   quatre pas  …
S8   regardez
```

Son **instrucciones de una búsqueda del tesoro**: *un / deux / trois / quatre pas vers…* y
*regardez*. Encaja con el NPC que dice que Fail Island "está llena de señales": **las señales no
llevan la contraseña, llevan el recorrido**. Son nueve indicaciones a pasos por la isla.

Que salga francés no es casualidad: la sonografía de Barbier **es** un sistema francés, y su rejilla
codifica fonemas franceses. El autor usó la tabla tal cual, en su idioma.

Y aquí está la pieza de diseño que hace bueno al reto. **Caminar un patrón concreto sobre una isla
vacía es exactamente la mecánica del evento oficial de Deoxys**: en Isla Origen, el puzzle del
triángulo consiste en moverse por un patrón preciso para que aparezca el Pokémon. El autor no
inventó un puzzle cualquiera — **replicó la mecánica del evento que da acceso a Deoxys**, que es
justo lo que repartía Moviplaya 2005. La forma del reto es una cita del evento que le da nombre.

Pero ahí se paró la primera versión del extractor (`nightwriting.py`): salían los numerales, `pas` y
`regardez`, y **la dirección no se leía nunca** — `vers` salía como `v·é·t·s`. El diagnóstico que
dimos entonces fue que el extractor mide mal las celdas de tally alto —*"cuando una columna lleva
cinco o seis marcas, las barras se funden y la cuenta baja"*—, y publicamos el decode como abierto.

**Era falso.** La sección siguiente lo cierra, y es la parte buena del reto.

### El segundo sistema: braille en el mismo cartel

El diagnóstico del "tally alto que se funde" era cómodo porque no obligaba a tocar el modelo. Lo que
pasa de verdad es que **en el mismo cartel conviven dos sistemas de escritura**, y no hay que
interpretarlos para distinguirlos: se miden.

| | barras por columna | alto de barra | sistema | cómo se lee |
|---|---|---|---|---|
| celda fina | 6 | 6–7 px | night writing | tally por columna → par `(fila, columna)` |
| celda gruesa | 3 | 18–19 px | braille de 6 puntos | bitmap `1-2-3` (izq) / `4-5-6` (der) |

Seis píxeles contra diecinueve: es una regla, no un juicio. Las celdas que habíamos apartado como
ornamento son braille y llevan dato. Y el reparto no es caprichoso — en las nueve señales, el
braille aporta exactamente lo que Barbier no da bien:

- las letras que **no están en la tabla de Barbier**: `c` `[14]`, `h` `[125]`, `x` `[1346]`, y el
  punto final `.` `[256]`;
- las de su **fila 5**: `l` `[123]`, `m` `[134]`, `n` `[1345]`, `r` `[1235]`.

Y ahí está la comprobación que lo sostiene: **ninguna celda de night writing de las nueve señales
baja de la fila 4** en su columna izquierda (los pares observados van de `11` a `46`, sin un solo
`5x` ni `6x`). El autor cortó Barbier en la fila 4 y para lo que faltaba se pasó al braille. La `r`
de *vers* nunca fue un conteo mal medido: era braille `[1235]` leído con la tabla del otro sistema.
Estábamos leyendo con una sola tabla un texto escrito en dos.

`nightwriting2.py` implementa las dos: cuenta barras por columna, decide sistema por ese número y
aplica la tabla que toca.

### Lo que dicen las señales, enteras

| | francés | castellano |
|---|---|---|
| `S1` | *sous le cristal bleu, commencé* | bajo el cristal azul, empieza |
| `S2` | *un pas vers le midi* | un paso hacia el sur |
| `S3` | *quatre pas vers l'aube* | cuatro pasos hacia el este |
| `S4` | *trois pas vers le midi* | tres pasos hacia el sur |
| `S5` | *six pas vers le couchant* | seis pasos hacia el oeste |
| `S6` | *un pas vers le nord* | un paso hacia el norte |
| `S7` | *deux pas vers l'aube* | dos pasos hacia el este |
| `S8` | *regardez en haut* | mirad arriba |
| `S9` | *libérez le doux parfum* | liberad el dulce aroma |

Dos cosas que explican por qué ninguna crib encajaba mientras leíamos con una tabla sola:

- **Las direcciones van en francés poético**, no en `nord/sud/est/ouest`: *midi* es el mediodía, el
  sur; *aube* es el alba, el este; *couchant* es el poniente, el oeste. Solo *nord* va literal.
- **La transcripción es fonética**, que es como funciona el night writing: la tabla de Barbier
  indexa sonidos, no letras. `parfun` es `p·a·r·f·[un]` con `[un]` como glifo único; `regarde an
  haut` es *regardez en haut* dicho en voz alta. No son erratas del extractor, es el sistema.

Y **S9 dice "liberad el dulce aroma"**: la instrucción que nos costó el error más caro del nivel
(§ 5) estaba escrita en el propio puzzle desde el principio. El recorrido no acaba en una pista,
acaba en una orden.

### La extracción completa

Salida de `nightwriting2.py`, tal cual. Cada celda de night writing se imprime como su par
`(n_izq, n_der)`; cada celda de braille, como su patrón de puntos entre corchetes; `/` marca
separación de palabra. Debajo de cada línea va la glosa que sale de aplicar las dos tablas:

```
=== S1
  L1 46 26 46 / [123] 15 / [14] [1235] 12 46 42 11 [123]
     sous / lé / cristal
  L2 31 [123] 25 / [14] 13 [134] [134] 15 [1345] [14] 15 [256]
     bleu / comméncé.
=== S2
  L1 24 / 41 11 46 / 35 15 [1235] 46
     un / pas / vérs
  L2 [123] 15 / [134] 12 32 12 [256]
     lé / midi.
=== S3
  L1 43 14 11 42 [1235] 15 / 41 11 46
     quatré / pas
  L2 35 15 [1235] 46 / [123] / 11 14 31 15 [256]
     vérs / l / aubé.
=== S4
  L1 42 [1235] 13 12 46 / 41 11 46
     trois / pas
  L2 35 15 [1235] 46 / [123] 15 / [134] 12 32 12 [256]
     vérs / lé / midi.
=== S5
  L1 46 12 [1346] / 41 11 46 / 35 15 [1235] 46
     six / pas / vérs
  L2 [123] 15 / [14] 26 44 21 42 [256]
     lé / couchant.
=== S6
  L1 24 / 41 11 46 / 35 15 [1235] 46
     un / pas / vérs
  L2 [123] 15 / [1345] 13 [1235] 32 [256]
     lé / nord.
=== S7
  L1 32 25 [1346] / 41 11 46 / 35 15 [1235] 46
     deux / pas / vérs
  L2 [123] / 11 14 31 15 [256]
     l / aubé.
=== S8
  L1 [1235] 15 33 11 [1235] 32 15 / 21
     régardé / an
  L2 [125] 11 14 42 [256]
     haut.
=== S9
  L1 [123] 12 31 15 [1235] 15 / [123] 15
     libéré / lé
  L2 32 26 [1346] / 41 11 [1235] 45 24 [256]
     doux / parfun.
```

La `é` de sobra en `vérs`, `libéré` o `comméncé` es el glifo `15` de Barbier —fila 1, columna 5, el
sonido `é`—, que el autor usa también donde el francés escribe `e` muda. No lo corregimos en la
salida a propósito: lo que imprime el script es lo que hay dibujado.

**Los pares se validan solos, sin necesidad de las tablas.** `41 11 46` (*pas*) aparece en **seis**
de las nueve señales y `35 15 [1235] 46` (*vers*) en **seis**, con encuadres distintos. Un extractor
con ruido no produce el mismo cuarteto en seis fotos.

### La comprobación cruzada: píxeles contra bytes

Hay una verificación mejor que las repeticiones, y no depende de los píxeles. El texto de las
señales **también está guardado en la ROM**, en nueve bloques contiguos a partir de `0x2a73c2` (seis
bytes de cabecera por bloque, luego el texto, terminador `0xFF`):

| Señal | Offset | Bytes de texto |
|---|---|---|
| `S1` | `0x2a73c2` | 28 |
| `S2` | `0x2a73e5` | 19 |
| `S3` | `0x2a73ff` | 23 |
| `S4` | `0x2a741d` | 23 |
| `S5` | `0x2a743b` | 22 |
| `S6` | `0x2a7458` | 19 |
| `S7` | `0x2a7472` | 20 |
| `S8` | `0x2a748d` | 15 |
| `S9` | `0x2a74a3` | 20 |

Sacas los glifos de los PNG por un lado y los bytes del binario por otro, y ves si se corresponden.
`crosscheck_rom.py` hace exactamente eso:

```
$ ROM=pokemon-esmeralda.gba python3 crosscheck_rom.py
biyeccion byte<->glifo: OK  (29 simbolos distintos)
```

**29 símbolos distintos, biyección perfecta, ni una colisión**, y las longitudes cuadran señal por
señal (las nueve de la tabla de arriba son también las longitudes en glifos de los nueve PNG). Es
más: probando las **362.880** formas de emparejar las nueve capturas con los nueve bloques, **solo
una es consistente** — la identidad. Cada cartel queda atado a su bloque de bytes por fuerza bruta,
no por buena voluntad.

De propina sale **cómo lo guardó el autor**. Cada byte es un **bitmap braille** de la letra latina,
con pesos `dot1=1, dot2=4, dot3=16, dot4=2, dot5=8, dot6=32`. Decodificados así, los bloques dicen:

```
S1   sys le cristal|blw commence.
S2   z pas vers|le midi.
S3   quatre pas|vers l aube.
S4   trois pas|vers le midi.
S5   six pas vers|le cykjt.
S6   z pas vers|le nord.
S7   dwx pas vers|l aube.
S8   regarde j|haut.
S9   libere le|dyx parfz.
```

(`|` es el byte `0xFE`, el salto de línea del cartel.)

Las letras raras son justo las que al francés hablado le sobran del alfabeto latino, recicladas como
dígrafos: `z`=`un`, `y`=`ou`, `w`=`eu`, `j`=`an`, `k`=`ch`. Así `sys` es *sous*, `blw` es *bleu*,
`cykjt` es *couchant* y `parfz` es *parfum*. El autor se montó un alfabeto de **29 símbolos** —26
letras, espacio, punto y salto de línea—, y luego lo pintó mezclando los dos sistemas de escritura.

Esto cierra el decode: la lectura de los carteles no descansa en cribs francesas ni en corregir
celdas a mano. Está atada byte a byte a lo que el autor escribió.

Una cautela sobre el orden, que aquí importa porque lo que se lee son instrucciones: **`S1`…`S9` es
el orden de los ficheros**, que resulta ser también el orden en que los bloques están guardados en la
ROM. Que `S1` abra —*"bajo el cristal azul, empieza"*— y que `S8` y `S9` cierren encaja con el
contenido. El orden de los seis pasos intermedios es heredado de esa numeración, no probado sobre el
mapa.

## 5. El final del recorrido, y dónde estaba de verdad la pista

El recorrido termina en un sitio concreto de Fail Island, y lo que hay que hacer allí **también está
escrito en la ROM**. Dos frases más del texto inyectado, con sus offsets, para que se pueda
verificar:

```
"El cristal azul responde al DULCE AROMA. Se abre un pasadizo."

"¡Ah sí! Yo estuve allí una vez. Pero ni idea de lo que significaba.
 Había una presencia extraña en aquella cueva, como si nos estuviera
 vigilando detrás de alguna pared."
```

Arriba va el texto tal como se lee en el juego. Y aquí, por separado, las tiradas **exactas** que el
decodificador de la sección 2 encuentra dentro de esas dos entradas, con su offset:

| Offset | Tirada literal |
|---|---|
| `0x291349` | *"El cristal azul responde"* |
| `0x291362` | *"al DULCE AROMA."* |
| `0x291372` | *"Se abre un pasadizo."* |
| `0x270341` | *"! Yo estuve all"* |
| `0x27035b` | *"Pero ni idea de lo que significaba."* |
| `0x270383` | *"a una presencia extra"* |
| `0x2703a6` | *"cueva, como si nos estuviera vigilando"* |

Las dos listas no se corresponden línea a línea **a propósito**, y el motivo es el mismo de la
sección 3: el decodificador no mapea vocales acentuadas ni `ñ`, así que cada acento **parte la
tirada**. *"Había"* se rompe en la `í` — por eso la tirada que empieza en `0x270383` es *"a una
presencia extra"* y no la frase entera. Para leerlas completas hay que ampliar `CH`, o caminar hacia
atrás hasta el `0xFF` anterior, que es el terminador de entrada.

Con eso se cierra la cadena:

1. OSINT → Moviplaya 2005 repartía el Ori-Ticket → Isla Origen → Deoxys.
2. Diff de texto de la ROM → HÉCTOR (Centro Espacial de Mossdeep) → **FAIL TICKET** → puerto de
   CALAGUA → **FAIL ISLAND**.
3. Las señales (night writing + braille) → **el recorrido a pasos** por la isla: empieza bajo el
   cristal azul, sur / este / sur / oeste / norte / este, y mira arriba.
4. Al final del recorrido, usar **Dulce Aroma** (*Sweet Scent*) → el cristal azul responde y **se
   abre un pasadizo**. Es lo que pide `S9`, la última señal: *libérez le doux parfum*.
5. Dentro de la cueva oculta hay un **entrenador**; al derrotarlo, el juego **genera** la contraseña
   —no la lleva escrita: ver abajo.

Y el remate del autor: **se entra usando Dulce Aroma y la contraseña es "aroma nocturno"**. El mismo
juego de palabras abre y cierra el reto.

### La contraseña no es un texto en la ROM: es un keygen

El punto 5 merece pararse, porque es donde el reto esconde su última vuelta de tuerca. El entrenador
de la cueva **no lleva la contraseña escrita**. Su diálogo de derrota, en `0x22e05a`, dice *"La
contraseña es"* y a continuación un **placeholder de variable** (`\n…` más un buffer que el juego
rellena en caliente), no el texto. La contraseña **no existe en el fichero** hasta que el juego la
calcula —da igual cómo la busques:

```
$ grep -abo '4roM4Noc7urNo' pokemon-esmeralda.gba          # 0 resultados (ASCII)
$ python3 -c 'ROM=open("pokemon-esmeralda.gba","rb").read()
E={" ":0}                                                  # y en el charset propietario Gen 3
for i,c in enumerate("0123456789"): E[c]=0xA1+i
for i,c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): E[c]=0xBB+i
for i,c in enumerate("abcdefghijklmnopqrstuvwxyz"): E[c]=0xD5+i
print(ROM.find(bytes(E[c] for c in "4roM4Noc7urNo")))'    # -1: tampoco está
```

Quien la produce es una **special** —una rutina que los scripts del juego invocan por número—:
`gSpecials[0x1F4] = 0x08179b3d`. Desensamblada (Thumb) es un keygen pequeño y completo:

```
seed  = (VarGet(0x404E) & 0xFFFF) | (VarGet(0x4083) << 16)
gate  : exige dos flags puestos  Y  seed == 0x3D40563B          (si no, no genera)
state = seed ^ 0xC3A5F17D
para i = 0..12:                        # 13 caracteres
    state  = xorshift32(state)         # desplazamientos 13, 17, 5
    buf[i] = (state >> 24)                          # byte alto del estado
           ^ TABLA[i & 3][ idx(i) % 19 ]            # sustitución por posición
           ^ ((29*i + 0x37) & 0xFF)                 # máscara que depende de i
buf[13] = 0xFF                         # terminador
```

`idx(i)`, según `i & 3`, es `7i+3`, `11i+5`, `13i+7` o `17i+9`, y hay **cuatro tablas de sustitución
de 19 bytes** (76 en total) en `0x5F14A0`. El `gate` es lo que ata el keygen al recorrido: sólo
produce algo cuando has hecho el camino (los dos flags) y el estado del juego vale exactamente
`0x3D40563B`. Con esa semilla el bucle escupe los trece bytes `a5 e6 e3 c7 a5 c8 e3 d7 a8 e9 e6 c8
e3`, que en Gen 3 son:

```
a5=4 e6=r e3=o c7=M a5=4 c8=N e3=o d7=c a8=7 e9=u e6=r c8=N e3=o   ->   4roM4Noc7urNo
```

**Y el entrenador es HÉCTOR otra vez.** `gTrainers[0x357]` se llama `HECTOR`, especialista de tipo
eléctrico (MAGNETON, ELECTRODE, PORYGON2, MANECTRIC, METAGROSS, niveles 55–65). El mismo nombre que
abre la ruta —el HÉCTOR del Centro Espacial que te da el FAIL TICKET— la cierra al final del
recorrido.

`keygen.py` reproduce todo esto **sin la ROM**: las 76 bytes de las tablas van embebidas (son datos
del autor, no de la Emerald comercial) y trae una función que las vuelve a extraer del binario, para
quien lo tenga, y confirma que las embebidas son las de verdad.

Aviso de método: todo lo de arriba es *reversing estático*, deducido sobre el binario. La
comprobación de que la rutina reconstruida es la misma que la compilada llegó después, jugando — la
sección siguiente.

### El reto, jugado: NIGHT CAVE

El nivel se ha jugado entero después, con calma, y cierra la cadena por la otra punta: se anda el
recorrido que dictan las señales, se responde al cristal azul con **Dulce Aroma**, se abre el
pasadizo, se gana el combate del fondo y **el juego escribe la contraseña en pantalla**. Es
exactamente la salida de `keygen.py`: la rutina reconstruida en Python y la rutina compilada dentro
de la ROM producen la misma cadena. `4roM4Noc7urNo`.

Y el combate no es un trámite narrativo. `gTrainers[0x357]` ya adelantaba el equipo —MAGNETON,
ELECTRODE, PORYGON2, MANECTRIC, METAGROSS, niveles 55–65—: es un especialista eléctrico con el
nivel al que la Emerald original remata la Liga, y cierra con un METAGROSS que no es eléctrico y
que pega fuerte. Después de todo el camino a ciegas, todavía hay que ganar.

La zona donde pasa todo esto **tiene nombre**, y está en la tabla de nombres de zona de la ROM:

```
0x5a2a4c   "NIGHT CAVE"
0x22e072   "Enhorabuena, solver."
```

Ahí está la tercera pata del chiste del autor. Las señales están en *night writing*, la escritura
nocturna de Barbier; la cueva se llama **NIGHT CAVE**; y la contraseña es *aroma **nocturno***. La
palabra que ata el reto entero está puesta hasta en el rótulo de la puerta. Y el
*"Enhorabuena, solver."* de `0x22e072` —veinticuatro bytes después del diálogo de derrota que
dispara el keygen, en `0x22e05a`—
es el autor rompiendo la cuarta pared para saludar a quien está jugando, no a quien está
desensamblando.

### La pista que buscamos donde no estaba

Esto merece decirlo con todas las letras porque es el error más caro del reto, más que el del night
writing.

*"Dulce Aroma"* como llave **no es conocimiento de Pokémon**. No sale en ninguna wiki, no es una
mecánica del juego base: **lo escribió el autor y lo inyectó en la ROM**. Nosotros lo estuvimos
buscando como si fuera lore —qué hace Sweet Scent, dónde se usa, qué esconde— cuando la frase exacta
estaba en el binario que ya teníamos volcado.

Peor: **el diff de texto que la contiene lo habíamos hecho nosotros mismos horas antes**. Era la
misma extracción que destapó HÉCTOR, FAIL TICKET y CALAGUA. La respuesta estaba en un fichero
generado por nuestra propia herramienta, y fuimos a buscarla fuera.

Se comprueba en un grep. Bajando el umbral de longitud a 8 caracteres, la ROM entera tiene **16**
tiradas de texto que contienen "aroma". Quince están **en inglés** y son del juego base:

```
0x248295   "I consider myself an AROMA LADY."
0x25d5cd   "It seems to have the distinct aroma"
0x29503e   "You weren't led astray by our aroma"
0x295063   "Aromatherapy is a form of mental"
0x29d93f   "The aroma of flowers has a magical"
0x29da88   "If you use a sweet aroma properly,"
0x5690b6   "with a sweet aroma from its head."
...
```

Y **una** está en castellano:

```
0x291362   "al DULCE AROMA."
```

Una sola aparición en 16 MB, y es la del autor. No hay ninguna otra fuente posible para esa pista
que el propio binario.

Y hay un segundo golpe, que solo se ve ahora que las señales están cerradas: **`S9` dice
"liberad el dulce aroma"**. Mientras buscábamos en wikis qué era Dulce Aroma, el último cartel de la
isla lo estaba pidiendo a la cara — en night writing y en francés, pero pidiéndolo. La pista no
estaba solo en el binario: estaba en el puzzle que teníamos a medio leer. Si el artefacto es un
puzzle, acábalo antes de salir a buscar fuera.

### Cómo se resolvió de verdad

Con honestidad, y son dos cosas distintas que conviene no mezclar:

- **Los carteles sí se transcribieron a ojo durante el concurso.** De ahí salió la geometría real
  —celdas de 6×2, doce posiciones— y la lectura de los puntos, que es justo lo que nuestro OCR no
  conseguía. Ese trabajo fue humano y fue el que puso el modelo correcto encima de la mesa.
- **Pero eso no produjo la contraseña.** La clave la sacó un compañero **inspeccionando el propio
  juego**, saltándose el recorrido: había dos vías —andar el puzzle como está diseñado, o ir directo
  al contenido inyectado— y se tomó la segunda, que era la barata. (Lo que ese compañero encontró
  inspeccionando es exactamente la special `0x1F4` de la subsección anterior; `keygen.py` la
  reproduce sin necesitar el juego.)

Lo decimos porque cambia la lectura de todo lo anterior: **el decode de las señales es lo que
*explica* el reto, no lo que lo resolvió**. Un writeup que presentara el camino largo como si
hubiera sido el nuestro estaría mintiendo sobre el proceso.

Y una tercera, que llegó al revisar esto y es la que ordena las otras dos: **el análisis del binario
fue un atajo**. El autor diseñó el nivel para jugarse —las señales se descifran mirándolas, el
recorrido se anda, HÉCTOR se gana y la contraseña sale en pantalla—, y ninguna de las dos vías que
tomamos durante el concurso pasó por ahí. Eso no rebaja el reversing: por el binario se llega antes
y se explica más —de ahí sabemos que hay un keygen, dónde vive su tabla y por qué las señales
mezclan dos escrituras—, pero es leer la partitura y no tocarla. La puerta principal era la otra.

## 6. La contraseña

```
4roM4Noc7urNo
```

*"Aroma nocturno"* en leet: `a→4`, `t→7`. No es un nombre bonito al azar: es el eco de la llave del
pasadizo —**Dulce Aroma**— más el sistema con el que están escritas las señales, el *night writing*,
que es literalmente **escritura nocturna** (Barbier lo diseñó para leer de noche sin luz). Aroma y
nocturno, las dos mitades de la contraseña, son las dos mitades del reto.

Y *nocturno* llega por tres sitios, no por dos: el *night writing* de los carteles, la zona
—**NIGHT CAVE**— y la propia contraseña. El autor puso la palabra hasta en el rótulo de la puerta.

## Reproducir

**La ROM y el save no se redistribuyen aquí**: son un juego comercial. Se bajan del nivel 4 de Solve
It en `hackit.party.eus`, y los comandos asumen que los tienes en este directorio con estos nombres.
Lo que sí va publicado es el instrumental y las nueve capturas, así que **`nightwriting.py`,
`nightwriting2.py` y `keygen.py` corren tal cual sin necesidad de la ROM**.

| Fichero | Qué hace |
|---|---|
| `pokemon-esmeralda.gba` | la ROM del reto (16 MB, gamecode `BPEE`) — *no incluida* |
| `pokemon-esmeralda.sav` | el save (128 KB + footer de 16 B de emulador) — *no incluido* |
| `parse_save.py` | estructura Gen 3: secciones, checksums, cajas |
| `deoxys.py` / `deoxys_full.py` | desencriptado y volcado del Deoxys |
| `gen3text.py` | decodificador del charset Gen 3 |
| `nightwriting.py` | extractor v1: rejilla 6×2, tallies y tabla de Barbier — el que se queda a medias |
| `nightwriting2.py` | extractor v2: distingue celda fina (night writing) de celda gruesa (braille) y lee las nueve señales enteras |
| `crosscheck_rom.py` | coteja los glifos de los PNG contra el texto de las señales en la ROM — *necesita la ROM* |
| `keygen.py` | reproduce la contraseña sin la ROM (special `0x1F4`, 76 bytes de tablas embebidas) |
| `imagenes-isla-fail/` | las nueve capturas de las señales |

Los scripts localizan sus datos junto a sí mismos, así que da igual desde dónde los lances. Los
fragmentos inline de abajo sí esperan que estés **en este directorio** (`solve-it/4/`).
Dependencias: `pillow`, `numpy` y `scipy` para `nightwriting.py`; `pillow` y `numpy` para
`nightwriting2.py`; el resto es Python de serie.

Dos rutas configurables por entorno, para no depender del sitio donde estén los ficheros:

- `nightwriting2.py` busca las capturas en `$SENALES`, y si no está, en `imagenes-isla-fail/` junto
  al script — que es donde van en este repo.
- `crosscheck_rom.py` **necesita la ROM**, que no se redistribuye: la lee de `$ROM`, y si no está,
  de `pokemon-esmeralda.gba` junto al script. Importa `nightwriting2.py`, así que los dos tienen que
  vivir en el mismo directorio.

```bash
# 1. el save no tiene flag
python3 deoxys.py                 # met location 187 = Birth Island, fateful, legítimo

# 2. el texto inyectado (la palanca)
python3 - <<'EOF'
CH={0x00:' ',0xAD:'.',0xB8:',',0xAB:'!',0xAC:'?'}
for i,c in enumerate('0123456789'): CH[0xA1+i]=c
for i,c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'): CH[0xBB+i]=c
for i,c in enumerate('abcdefghijklmnopqrstuvwxyz'): CH[0xD5+i]=c
r=open('pokemon-esmeralda.gba','rb').read()
runs,cur,st=[],'',0
for i,b in enumerate(r):
    if b in CH:
        if not cur: st=i
        cur+=CH[b]
    else:
        if len(cur.strip())>=14 and sum(c.isalpha() for c in cur)>=10: runs.append((st,cur.strip()))
        cur=''
for kw in ('FAIL ISLAND','FAIL TICKET','CALAGUA','IMOBILIS','ESPACIAL'):
    print(kw, [hex(o) for o,t in runs if kw in t][:3])
EOF

# 3. jugarlo
./jugar.sh                # mGBA con la ROM y el save cargados

# 4. extraer las señales de Fail Island
python3 nightwriting.py           # v1: solo night writing -> se queda a medias
python3 nightwriting2.py          # v2: night writing + braille -> las nueve señales enteras

# 5. verificar la extracción contra el texto de las señales en la ROM
ROM=pokemon-esmeralda.gba python3 crosscheck_rom.py   # -> biyeccion OK, 29 simbolos

# 6. la contraseña: reproducir el keygen del entrenador (special 0x1F4)
python3 keygen.py                 # sin ROM -> 4roM4Noc7urNo
python3 keygen.py pokemon-esmeralda.gba   # además comprueba las tablas contra el binario
```

## Lo que nos llevamos

1. **Un binario modificado se ataca por el diff semántico, no por el diff de bytes.** Diffear 16 MB
   da ruido; diffear el *texto decodificado* contra la versión limpia da el puzzle entero. La
   asimetría de idioma (base inglesa, inyección española) fue el filtro que lo hizo trivial.
2. **En un artefacto modificado, la pista que te falta suele estar dentro del propio artefacto.**
   Buscamos qué significaba "Dulce Aroma" en wikis de Pokémon durante un buen rato, y no significaba
   nada: **la frase la escribió el autor y estaba en la ROM**, en el mismo volcado de texto inyectado
   que ya habíamos generado nosotros horas antes. Cuando alguien ha metido contenido en un binario,
   el binario es la fuente autorizada sobre ese contenido — no internet. Antes de salir a buscar
   conocimiento externo, grepea lo que ya tienes. Y si el artefacto es un puzzle, **acábalo**: `S9`
   decía *"liberad el dulce aroma"* y llevaba horas dándonos la respuesta a medio leer.
3. **Tener la herramienta correcta no basta: hay que hacerle la pregunta correcta.** El decodificador
   Gen 3 existía una hora antes de que sirviera para algo, usado para una pregunta menor.
4. **Los assets "temáticos" son el señuelo por defecto.** El save era lo primero que todo el mundo
   iba a mirar, y por eso no tenía nada. El dato interesante era el MD5, que estaba a la vista desde
   el segundo cero.
5. **Antes de umbralizar, cuenta los puntos de una celda.** Si son 12 y no 6, no es Braille. Es la
   comprobación más barata del reto y la que no hicimos: en lugar de medir la estructura, asumimos
   el sistema por su aspecto y luego pasamos una hora ajustando parámetros para que los datos
   cupieran en él.
6. **Un modelo correcto con la segmentación mal puesta produce basura convincente.** Tres bandas
   visuales eran **una sola línea lógica** de celdas de seis filas. Al agruparlas mal, cada tally
   salía a un tercio de su valor — y seguía cayendo dentro del rango 1–6, así que mapeaba a sonidos
   válidos y producía una transcripción completa con pinta de resultado. Un decode que "sale" no
   valida tu segmentación; solo la validan las palabras reales.
7. **Un modelo equivocado no falla limpio: falla a medias, y eso lo disfraza de ruido.** Las celdas
   "imposibles" de seis puntos y los patrones no contiguos eran el modelo protestando. Los leímos
   como problemas de umbral y les pusimos parches. Cuando llevas tres heurísticas encima de una
   extracción y sigue sin generalizar, el sospechoso es la hipótesis, no el detector.
8. **Al segundo intento fallido de OCR, cambia de herramienta o de ojos.** Un artefacto visual
   pequeño es un mal objetivo para automatizar y uno trivial para una persona. Ese cambio hay que
   hacerlo pronto, no después de una hora.
9. **Resuelve los identificadores contra la fuente, no contra tu memoria.** "met location 187" se
   tradujo volcando `gRegionMapEntries` de la propia ROM. Es más rápido que buscarlo y no se
   equivoca.
10. **Cuando algo se lee a medias, desconfía del diagnóstico que no te obliga a tocar el modelo.**
   *"El extractor mide mal las celdas de tally alto porque las barras se funden"* era cómodo, encajaba
   con los síntomas y era falso. Lo que pasaba —dos sistemas de escritura en el mismo cartel— se veía
   con una regla: seis píxeles de barra contra diecinueve. Un diagnóstico que culpa al instrumento y
   deja intacta la hipótesis es sospechoso por construcción.
11. **Una verificación buena no depende del canal que estás poniendo en duda.** Las repeticiones
   entre señales validaban la extracción contra sí misma; cotejar los glifos contra los bytes de la
   ROM la valida contra el autor. Cuando el mismo artefacto existe en dos representaciones, cruzarlas
   vale más que cualquier heurística sobre una sola.

Sobre el proceso: el reto se trabajó con asistencia de IA y el reparto fue bastante nítido. La
máquina hizo todo el tramo binario y lo hizo bien —parsear el save Gen 3 con sus checksums,
desencriptar el Deoxys, escribir el decodificador de charset, volcar la tabla de zonas del ROM y,
sobre todo, el diff de texto que destapó la búsqueda del tesoro—; es trabajo que a mano son varias
horas. Donde se atascó fue en el último tramo, insistiendo en resolver por píxeles un problema de
lectura que un humano cierra en diez minutos, y anunciando varias veces que paraba sin parar. Es el
patrón más caro de trabajar así: **un asistente no tiene coste percibido de seguir intentándolo, así
que el criterio de parada lo tienes que poner tú, y conviene ponerlo por adelantado.**

El decode sí acabó cerrándose por la vía automática, pero no insistiendo: midiendo. Lo que
desatascó las celdas que se resistían no fue otra heurística encima de las tres anteriores, fue
cambiar la pregunta —de *"¿por qué cuenta mal esta celda?"* a *"¿cuántas barras
tiene y de qué alto?"*— y aceptar la respuesta, que era que ahí había otro sistema de escritura.
