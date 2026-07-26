# Solve It EE34 — Nivel 4: "Moviplaya 2005"

> *"Esta ROM esconde un misterio que no somos capaces de resolver."*

Los assets no son una imagen: son una **ROM de Game Boy Advance de 16 MB** (`pokemon-esmeralda.gba`)
y una **partida guardada** (`pokemon-esmeralda.sav`, 131.088 bytes). El título apunta a Moviplaya
2005, el tour de playa donde Nintendo repartía eventos de Pokémon en España aquel verano.

Spoiler: **`4roM4Noc7urNo`** — leet de *"aroma nocturno"*. El reto es una cadena larga: un señuelo
que hay que descartar, una palanca que lo abre entero, una búsqueda del tesoro inyectada en el
binario, un sistema de escritura que no es el que parece, y un chiste final que ata el nombre de la
contraseña con la llave que abre la última puerta.

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

## 4. Las señales no son Braille: son *night writing*

Aquí es donde el reto nos ganó, y el error fue de **modelo**, no de umbral.

Las señales parecen Braille y no lo son. Son **night writing** —la *sonografía* de Charles
Barbier, 1815—, el sistema militar del que Louis Braille partió y que luego simplificó. La
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

Hay un segundo detalle: en algunas señales **la primera celda es un ornamento**, no dato. Se
distingue porque sus barras son unas tres veces más altas que las de las celdas reales. No en todas:
en otras la primera celda sí lleva contenido, así que no vale descartarla por sistema.

### Lo que dicen las señales

Con la agrupación correcta el texto se vuelve legible, y es **francés**:

```
S2   un     pas  vers …
S7   deux   pas  vers …
S4   trois  pas  vers …
S3   quatre pas  …
S5   cinq   pas  vers …
S8   regardez
```

Son **instrucciones de una búsqueda del tesoro**: *un / deux / trois / quatre / cinq pas vers…* y
*regardez*. Encaja con el NPC que dice que Fail Island "está llena de señales": **las señales no
llevan la contraseña, llevan el recorrido**. Son nueve indicaciones a pasos por la isla.

**Aviso importante sobre esa lectura**: no sale letra por letra de los pares que publicamos abajo.
Es la reconstrucción de las palabras una vez sabes que el texto es francés, y descansa en corregir a
mano las celdas que nuestra extracción lee mal — que son siempre las mismas y por un motivo
identificado (§ *Donde nos quedamos*). Por ejemplo, la señal S4 da los pares `42 42 13 12 46`, que
con la tabla se leen `t·t·o·i·s`: para que diga `trois` hace falta que la segunda celda sea `54`
(=`r`) y nuestra extracción devuelve `42`. **Los pares son el dato; la glosa francesa es
interpretación.** Las dos cosas van publicadas por separado a propósito.

Que salga francés no es casualidad: la sonografía de Barbier **es** un sistema francés, y su rejilla
codifica fonemas franceses. El autor usó la tabla tal cual, en su idioma.

Y aquí está la pieza de diseño que hace bueno al reto. **Caminar un patrón concreto sobre una isla
vacía es exactamente la mecánica del evento oficial de Deoxys**: en Isla Origen, el puzzle del
triángulo consiste en moverse por un patrón preciso para que aparezca el Pokémon. El autor no
inventó un puzzle cualquiera — **replicó la mecánica del evento que da acceso a Deoxys**, que es
justo lo que repartía Moviplaya 2005. La forma del reto es una cita del evento que le da nombre.

### La extracción completa

Ésta es la salida de `nightwriting.py`, tal cual. Cada celda da un par `(n_izq, n_der)` y `/` marca
separación de palabra. Las señales van numeradas `S1`–`S9` por orden de fichero:

| Señal | Línea 1 | Línea 2 |
|---|---|---|
| `S1` | `46 26 46 / 40 15 / 11 42 12 46 42 11 40` | `31 40 25 / 11 13 21 21 15 23 11 15 23` |
| `S2` | `24 / 41 11 46 / 35 15 42 46` | `40 15 / 21 12 32 12 23` |
| `S3` | `43 14 11 42 42 15 / 41 11 46` | `35 15 42 46 / 40 / 11 14 31 15 23` |
| `S4` | `42 42 13 12 46 / 41 11 46` | `35 15 42 46 / 40 15 / 21 12 32 12 23` |
| `S5` | `46 12 22 / 41 11 46 / 35 15 42 46` | `40 15 / 11 26 44 21 42 23` |
| `S6` | `24 / 41 11 46 / 35 15 42 46` | `40 15 / 23 13 42 32 23` |
| `S7` | `32 25 22 / 41 11 46 / 35 15 42 46` | `40 / 11 14 31 15 23` |
| `S8` | `42 15 33 11 42 32 15 / 21` | `32 11 14 42 23` |
| `S9` | `40 12 31 15 42 15 / 40 15` | `32 26 22 / 41 11 42 45 24 23` |

**Estos pares se validan solos, sin necesidad de la tabla.** Fíjate en las repeticiones entre
señales distintas: `41 11 46` aparece en **seis** de las nueve, `35 15 42 46` en **seis** y `40 15`
en **seis**. Un extractor con ruido no produce el mismo cuarteto en seis fotos con encuadres
diferentes; eso es texto real con palabras repetidas. La segmentación y el conteo son consistentes.

### Donde nos quedamos

El decode **no está cerrado del todo**, y decimos exactamente dónde falla.

La extracción es **reproducible pero no del todo correcta**, y conviene separar las dos cosas: el
script devuelve siempre los mismos pares, y son los de la tabla de arriba; lo que no está garantizado
es que cada par sea el que el autor dibujó.

Las palabras que salen limpias (`pas`, `un`, `regardez`, los numerales) son cribs sólidas: son
francés real y encajan entre sí en una frase con sentido. Pero **las celdas de tally alto se leen
mal**, y el motivo es geométrico: cuando una columna tiene 5 o 6 puntos marcados, las barras quedan
**pegadas** y se funden. Eso rompe los métodos de conteo que probamos:

- contar *runs* de píxeles oscuros → **infravalora** (cinco puntos pegados cuentan como uno);
- filtrar por altura de barra para descartar el ornamento → **elimina justo esas celdas**, porque una
  columna con muchos puntos produce barras tan altas como el ornamento;
- muestrear por posición de fila (lo que hace el script publicado) → estable y reproducible, pero
  con deriva en algunas fotos, y ahí es donde se pierde la distinción entre `42` y `54`.

Ése es el motivo concreto de que `vers` salga como `v·é·t·s` en vez de `v·é·r·s`: `r` es `(5,4)`,
cinco puntos en la columna izquierda, y lo leemos como `(4,2)`. Todos los desajustes conocidos entre
la tabla de pares y la glosa francesa son de ese tipo.

Tampoco hemos reconstruido el recorrido completo paso a paso ni lo hemos andado dentro del juego.

No hemos ajustado la tabla ni la convención para que saliera "aroma nocturno". Con la respuesta
delante es facilísimo mover un parámetro hasta que "salga", y eso no es un decode: es un crib
autoconfirmado. **Publicamos el modelo, el bug de segmentación, los pares y el script; el afinado
del tally alto queda abierto.**

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
3. Las señales en night writing → **el recorrido a pasos** por la isla.
4. Al final del recorrido, usar **Dulce Aroma** (*Sweet Scent*) → el cristal azul responde y **se
   abre un pasadizo**.
5. Dentro de la cueva oculta hay un **entrenador**; al derrotarlo suelta la contraseña.

Y el remate del autor: **se entra usando Dulce Aroma y la contraseña es "aroma nocturno"**. El mismo
juego de palabras abre y cierra el reto.

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

### Cómo se resolvió de verdad

Con honestidad, y son dos cosas distintas que conviene no mezclar:

- **Los carteles sí se transcribieron a ojo durante el concurso.** De ahí salió la geometría real
  —celdas de 6×2, doce posiciones— y la lectura de los puntos, que es justo lo que nuestro OCR no
  conseguía. Ese trabajo fue humano y fue el que puso el modelo correcto encima de la mesa.
- **Pero eso no produjo la contraseña.** La clave la sacó un compañero **inspeccionando el propio
  juego**, saltándose el recorrido: había dos vías —andar el puzzle como está diseñado, o ir directo
  al contenido inyectado— y se tomó la segunda, que era la barata.

Lo decimos porque cambia la lectura de todo lo anterior: **el decode de las señales es lo que
*explica* el reto, no lo que lo resolvió**. Un writeup que presentara el camino largo como si
hubiera sido el nuestro estaría mintiendo sobre el proceso.

## 6. La contraseña

```
4roM4Noc7urNo
```

*"Aroma nocturno"* en leet: `a→4`, `t→7`. No es un nombre bonito al azar: es el eco de la llave del
pasadizo —**Dulce Aroma**— más el sistema con el que están escritas las señales, el *night writing*,
que es literalmente **escritura nocturna** (Barbier lo diseñó para leer de noche sin luz). Aroma y
nocturno, las dos mitades de la contraseña, son las dos mitades del reto.

## Reproducir

**La ROM y el save no se redistribuyen aquí**: son un juego comercial. Se bajan del nivel 4 de Solve
It en `hackit.party.eus`, y los comandos asumen que los tienes en este directorio con estos nombres.
Lo que sí va publicado es el instrumental y las nueve capturas, así que **`nightwriting.py` corre tal
cual sin necesidad de la ROM**.

| Fichero | Qué hace |
|---|---|
| `pokemon-esmeralda.gba` | la ROM del reto (16 MB, gamecode `BPEE`) — *no incluida* |
| `pokemon-esmeralda.sav` | el save (128 KB + footer de 16 B de emulador) — *no incluido* |
| `parse_save.py` | estructura Gen 3: secciones, checksums, cajas |
| `deoxys.py` / `deoxys_full.py` | desencriptado y volcado del Deoxys |
| `gen3text.py` | decodificador del charset Gen 3 |
| `nightwriting.py` | extractor de las señales: rejilla 6×2, tallies y tabla de Barbier |
| `imagenes-isla-fail/` | las nueve capturas de las señales |

Los scripts localizan sus datos junto a sí mismos, así que da igual desde dónde los lances. Los
fragmentos inline de abajo sí esperan que estés **en este directorio** (`challenges/solve4/`).
Dependencias: `pillow`, `numpy` y `scipy` para `nightwriting.py`; el resto es Python de serie.

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
./jugar.sh         # mGBA con la ROM y el save cargados

# 4. extraer las señales de Fail Island (rejilla 6x2 + tallies)
python3 nightwriting.py           # imprime los pares y su lectura con la tabla de Barbier
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
   conocimiento externo, grepea lo que ya tienes.
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

Sobre el proceso: el reto se trabajó con asistencia de IA y el reparto fue bastante nítido. La
máquina hizo todo el tramo binario y lo hizo bien —parsear el save Gen 3 con sus checksums,
desencriptar el Deoxys, escribir el decodificador de charset, volcar la tabla de zonas del ROM y,
sobre todo, el diff de texto que destapó la búsqueda del tesoro—; es trabajo que a mano son varias
horas. Donde se atascó fue en el último tramo, insistiendo en resolver por píxeles un problema de
lectura que un humano cierra en diez minutos, y anunciando varias veces que paraba sin parar. Es el
patrón más caro de trabajar así: **un asistente no tiene coste percibido de seguir intentándolo, así
que el criterio de parada lo tienes que poner tú, y conviene ponerlo por adelantado.**
