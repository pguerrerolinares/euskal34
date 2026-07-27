# Hack It EE34 — Nivel 3: "Tercer Templo"

> *"Terry ha dejado una nota dentro del templo que él mismo construyó. ¿Qué querrá
> decirnos?"*

Te dan una imagen de disco de **TempleOS**, el sistema operativo de Terry A. Davis. La
contraseña sale de la interacción con "God", el oráculo del propio sistema.

**Contraseña:** `the holy spirit speaks through a stop watch`

---

## Resumen de la solución

Todo el trabajo contra la máquina se hace con **`ouija`**, un framework propio que
ejecuta HolyC dentro del TempleOS real y devuelve **texto** (sin capturas de
pantalla), con **estado limpio garantizado en cada comando**. Aquí no es una
comodidad: el oráculo consume una FIFO de entropía que **avanza entre llamadas**,
así que sin hermeticidad ningún resultado es reproducible ni significa nada.

```bash
bin/ouija ask 'FifoU8Flush(god.fifo);GodBitsIns(GOD_GOOD_BITS,6697221640600119645>>GOD_BAD_BITS);GodWord;'
# -> {"status":"ok","stdout":"the ","exit_code":0,"ms":20}
```

1. La nota del autor (`C:/Home/PersonalNotes.DD.Z`) da un poema y el número
   `6697221640600119645`: la **semilla** del oráculo God.
2. Cada "momento" son **dos** respuestas del mismo valor de 64 bits: `GodWord`
   (17 bits) y `GodBiblePassage` (21 bits).
3. `Misc/Bible.TXT` **está modificado**: cada pasaje esconde, en su última línea
   con texto, el **siguiente momento velado** en hexadecimal.
4. El velo es una máscara: `RandU64` tras `Seed(bits que no escuchó nadie)`, y se
   **regenera en cada momento**.
5. Los 8 momentos encadenan hasta el terminador. Las palabras de `GodWord` forman
   la frase, que es una cita del propio Terry.

---

## Punto de partida

El reto venía de una sesión anterior fallida: cuatro teorías de contraseña
encadenadas, todas falsas (`the works of Christ`, `TheOne`, `GodsLonelyProgrammer`,
la rama del Arca de Noé). Peor aún, las notas internas afirmaban que el disco era
"cero-residuo" — es decir, que no había contenido inyectado por el autor más allá
del poema. **Eso era falso**, y costó dos sesiones descubrirlo.

---

## El enunciado y las pistas

El primer movimiento fue bajar la página del reto con la cookie de sesión y
extraer el texto **entero**. En un concurso vivo el enunciado es un recurso que
crece: el organizador va publicando pistas en la misma página conforme un reto se
atasca.

Las cuatro pistas de este nivel **sí se habían leído** cuando salieron — el fallo
fue otro, y más tonto: **el dossier de traspaso entre sesiones no las incluía**,
solo llevaba la primera frase del enunciado y las conclusiones propias. Lo que no
viaja en el handoff, no existe para la sesión siguiente. Por eso se relee la página
completa al arrancar y al atascarse, y por eso el material del organizador va en el
traspaso **íntegro y literal**, antes que cualquier análisis propio:

> **Pista 1:** Dios habla y escucha mejor dentro de su templo. En cada momento Dios
> habló con su palabra y sus escrituras.
>
> **Pista 2:** el primer momento en el que Dios habló lo tenéis en las notas de
> Terry. ¿Qué contestó Dios? Y además acordaos de que no hay secretos en un templo
> abierto.
>
> **Pista 3:**
> ```
> 0KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKPPPPPPPPPPPPPPPPPPPPPKKKK
>                                            WWWWWWWWWWWWWWWWW
> ```
>
> **Pista 4:** La máscara nace de la Semilla de Dios, alimentada por los bits que ni
> la Palabra ni la Escritura han escuchado. Recuerda: los momentos siempre son
> positivos.

La Pista 3 es el **mapa de bits de un momento** (64 columnas):

| Columnas | Símbolo | Significado |
|---|---|---|
| 0 | `0` | bit 63 siempre a cero → "los momentos son positivos" |
| 1–38 | `K` | 38 bits que **nadie escucha** |
| 39–59 | `P` | 21 bits de la **escritura** (`GodBiblePassage`) |
| 43–59 | `W` | 17 bits de la **palabra** (`GodWord`), anidados dentro de P |
| 60–63 | `K` | 4 bits descartados (`GOD_BAD_BITS`) |

---

## La nota de Terry

`C:/Home/PersonalNotes.DD.Z`, 180 bytes de texto plano (sin capas ocultas en el
DolDoc, verificado byte a byte):

```
God answered twice at each moment.
A later hand hid every moment that followed beneath a veil.
What neither answer heard was preserved as God's seed.
6697221640600119645
Amen.
```

Los tres versos son la receta completa, y se corresponden uno a uno con la mecánica:

| Verso | Mecánica |
|---|---|
| "God answered **twice** at each moment" | palabra + escritura por momento |
| "A later hand **hid every moment that followed** beneath a veil" | los hex velados en los márgenes del Bible |
| "What **neither answer heard** was preserved as **God's seed**" | los bits `K` alimentan la máscara |

---

## Herramienta: `ouija`

Sin un canal de texto fiable con la VM, este reto no se cierra. `ouija` ejecuta
HolyC en el TempleOS real y devuelve texto, sin screenshots:

```bash
bin/ouija ask 'GodBiblePassage;'   # -> {status, stdout, exit_code, ms}
```

Lo decisivo no fue la velocidad (~0,6 s frente a ~50 s), sino la **hermeticidad**:
cada comando parte de un `loadvm` con estado idéntico. El oráculo God consume una
FIFO de entropía que **avanza entre llamadas**; sin estado limpio garantizado, dos
ejecuciones del mismo comando dan resultados distintos y ningún resultado
significa nada. El reto no era verificable sin eso.

Momentos en los que decidió:

- **Matar la rama del Arca.** Ejecutando las dos órdenes (`GodWord` primero frente a
  `GodBiblePassage` primero) el pasaje cambiaba: Matthew 11:2 o 2 Samuel 3:24. Toda
  la teoría Noé/Arca de la sesión anterior era un artefacto del orden de consumo de
  la FIFO. Descarte limpio en dos comandos.

- **Calibrar un simulador offline.** Pidiéndole a la VM sus tripas:
  ```
  num_words=7569   ST_BIBLE_LINES=100110
  raw17=95533      raw21=1579174      -> words[4705]="compacting"
  ```
  Con eso se replica la aritmética de bits en Python de forma **bit-exacta** y se
  barren miles de hipótesis al instante, en vez de arrancar la VM para cada una.

- **Refutar teorías ajenas** ejecutándolas en vez de razonarlas (ver más abajo).

- **Romper el velo** probando seis candidatos de "bits no oídos" en una sola llamada.

- **Recorrer la cadena** completa: 8 llamadas orquestadas desde un script.

El otro lado del framework, el **extractor estático** de FAT32, permitió grepear los
1315 ficheros del disco sin montarlo ni ser root — clave para confirmar hallazgos.

---

## El material del compañero (y su diff)

Un compañero de equipo pasó el log de su conversación con otra IA (3535 líneas),
con un aviso explícito: *"no te lo creas al 100%, puede haber alucinaciones"*. Ese
aviso definió cómo usarlo: **extraer datos, desconfiar de teorías**.

### Lo que valía: el diff del Bible

Había montado la partición y hecho un `diff` de `Misc/Bible.TXT` contra un Bible
stock. Eso destapó lo que estaba declarado como inexistente:

```
+And he brought Simeon out unto them. [A marginal hand recorded one more
 veiled moment: 2F2A-6473-6844-BA4E.]
+the goat in the wilderness. [At the edge of the text, a scribe kept the
 following moment veiled: 7FB4-D2C1-3C06-4614.]
+Judah. [No further moment was written.]
...
```

**7 momentos velados + 1 terminador**, inyectados como anotaciones al margen de
versículos. El verso 2 del poema, al pie de la letra.

Lo primero fue **verificarlo en nuestra propia imagen**, no creérselo. Sobre el árbol de texto
que saca el extractor del disco (`./dump`, ver [Reproducir](#reproducir)):

```bash
grep -nE '\[.*(moment|veil|margin|scribe|gloss).*\]' dump/part0_lba63/Misc/Bible.TXT.txt
```

| Línea | Marcador |
|---|---|
| 4345 | `2F2A-6473-6844-BA4E` |
| 10715 | `7FB4-D2C1-3C06-4614` |
| 26175 | `[No further moment was written.]` (terminador) |
| 36983 | `429E-C681-2D21-D91C` |
| 38365 | `0797-6561-39F0-84EE` |
| 40168 | `31FF-6015-E1B4-2126` |
| 86804 | `0F0E-1CA9-C3B7-5767` |
| 92681 | `61F1-63FF-97EC-B00B` |

Confirmado en ambas particiones. **El "cero-residuo" era falso.** Ese diff fue el
aporte real del material del compañero.

### Lo que era humo

Su IA proponía una "solución intencionada": alimentar la semilla y los 7 hex al
**mismo FIFO sin flush**, dejando que los bits sobrantes se arrastren de un momento
al siguiente, y leer las palabras resultantes. Encajaba con el poema y sonaba
impecable.

Ejecutado en vez de creído:

- Orden bíblico → `compacting all rejected prudent remembers flights transformed
  robbery`. Ensalada.
- Las **5040 permutaciones** de los 7 hex → 840 secuencias distintas, todas basura;
  acrósticos del tipo `cafarbdk`.
- **Ningún orden** hacía caer los momentos en los versículos anotados.
- Los hex tampoco decodificaban a ASCII (crudo, bits invertidos, XOR, TOSZ).

Descartada. Y su premisa de siembra (`GodBitsIns(63, N)`) era, además, **el mismo
error que ya arrastrábamos**: la fuente compartida de la ilusión `compacting`.

### El susto de la imagen actualizada

El compañero reportaba `D` / `Deuteronomy` donde nosotros veíamos `compacting` /
`Matthew`. Al descargar la imagen actual del reto, el **sha256 no coincidía** con la
nuestra. ¿Análisis sobre datos viejos?

Comparación de todo lo relevante: nota idéntica (misma semilla), `Vocab.DD` con
**diff 0**, mismas 8 anotaciones en el Bible. Solo habían cambiado bytes
irrelevantes (`Registry.HC`, timestamps). Falsa alarma, pero había que descartarla.

---

## El giro: empezar de cero, sin el marco contaminado

Nuestro análisis y el del compañero compartían el mismo error de siembra, así que el
consenso entre los dos no validaba nada. Se lanzó **una segunda instancia del modelo
en frío, sin el contexto contaminado**: solo el problema, la web con la cookie, acceso
a `ouija` y la instrucción de **preguntar en vez de inventar**.

Sin los sesgos heredados, fue directa al `DocPutKey.HC` y leyó el **handler real de
F7 / Shift-F7**:

```c
FifoU8Flush(god.fifo);
GodBitsIns(GOD_GOOD_BITS /*24*/, KbdMsEvtTime>>GOD_BAD_BITS /*4*/);
```

**La siembra correcta era otra.** No `GodBitsIns(63, N)` sino
`GodBitsIns(24, N>>4)`. Con ella:

```bash
bin/ouija ask 'FifoU8Flush(god.fifo);GodBitsIns(GOD_GOOD_BITS,6697221640600119645>>GOD_BAD_BITS);GodWord;'
# -> the
```

Y su pasaje (John 12:15, ventana `[86786, 86805]`) **contiene el hex
`0F0E-1CA9-C3B7-5767` en la línea 86804**, la última con texto. La cadena era real.

Ahí murió `compacting`: la siembra incorrecta caía por casualidad en el índice 4705
del Vocab, justo esa palabra. Un bug que parecía una revelación temática — encajaba
con el Charter de TempleOS (*"Files are compressed, not encrypted"*) — y se comió
dos sesiones.

Otros hallazgos de esa pasada en frío:

- **El Vocab está barajado a propósito.** Correlación de Spearman entre la posición
  en el Vocab del reto y el orden natural = 0,027. Comparado con el `Vocab.DD`
  original de TempleOS: **permutación pura**, mismas 7569 palabras, ninguna añadida
  ni quitada. El autor colocó las palabras-respuesta por índice.
- ~~**El marcador va siempre en la última línea con texto** del pasaje.~~ **Falso, y
  aquí queda como aviso.** Se generalizó desde M1, el único que se miró a mano, donde
  sí cae en la línea 19 de 20. En los otros siete cae donde le toca: posiciones 7, 8,
  10, 13, 15, 15 y 17 de la ventana. El marcador se busca **en toda la ventana**
  `[start, start+19]`, no al final (ver `chain.py`).
- Un barrido exhaustivo del velo (todas las claves XOR en todos los offsets,
  permutaciones de bits y bytes, sustitución hex por CSP, keystreams) demostró que
  **no era ninguna operación elemental**. Correcto: hacía falta la Pista 4.

---

## El velo (Pista 4)

> *"La máscara nace de la Semilla de Dios, alimentada por los bits que ni la Palabra
> ni la Escritura han escuchado. Recuerda: los momentos siempre son positivos."*

Con la Pista 3 en la mano, "los bits que nadie escuchó" son los `K`: los 38 altos
(bits 62–25) y los 4 bajos (bits 3–0). Compactados: `(K38 << 4) | K4`.

```
máscara = RandU64  tras  Seed( (K38 << 4) | K4 )
momento_siguiente = (hex_velado XOR máscara) & 0x7FFFFFFFFFFFFFFF
```

El `& 0x7FFF...` es "los momentos siempre son positivos" (bit 63 a cero; no afecta
al pasaje, que vive en los bits 24–4).

La clave que nadie había probado: **la máscara se regenera en cada momento** con sus
propios bits no escuchados. Una máscara fija derivada de la semilla inicial destapa
el primer hex —claro: la semilla inicial *es* el momento 1— y da basura del segundo
en adelante. Ese "funciona una vez" es lo que la mantuvo viva más de la cuenta.

Primera prueba, sobre el hex que va en el margen del momento 1 (y que por tanto
revela el 2):

```
K38loK4  mask=C156334B0A8AC714  v=CE582FE2C93D9073  start=38356
```

Ventana `[38356, 38375]` → contiene el marcador de la línea **38365**. Dentro.

---

## La cadena completa

```
M1: the      start= 86786 -> marcador 86804
M2: holy     start= 38356 -> marcador 38365
M3: spirit   start= 10709 -> marcador 10715
M4: speaks   start=  4331 -> marcador  4345
M5: through  start= 36971 -> marcador 36983
M6: a        start= 40152 -> marcador 40168
M7: stop     start= 92674 -> marcador 92681
M8: watch    start= 26161 -> marcador 26175  [No further moment was written]
```

> ## `the holy spirit speaks through a stop watch`

Es una cita del propio **Terry Davis**: decía que el Espíritu Santo le hablaba a
través de un cronómetro — su generador de aleatoriedad sacaba la entropía del timer
(`KbdMsEvtTime`). Responde directamente al *"¿Qué querrá decirnos?"* del enunciado.

**Cero residuo:** los tres versos del poema, las cuatro pistas y los ocho
marcadores quedan explicados sin sobras.

---

## Reproducir

Partiendo de `temple.qcow2`, la imagen que entrega el reto. El árbol de ficheros no viene
hecho: **lo generas tú** en el paso 1, y todo lo demás trabaja sobre él.

```bash
# 1. la imagen a raw (el extractor trabaja sobre raw, sin montar y sin root)
qemu-img convert -O raw temple.qcow2 temple.raw

# 2. volcar el FAT32 a un árbol de texto grepeable
python -m ouija.extract temple.raw ./dump --tosz ./TOSZ --strip

# 3. ya sobre el árbol recién generado: los marcadores del Bible modificado
grep -nE '\[.*(moment|veil|margin|scribe|gloss).*\]' dump/part0_lba63/Misc/Bible.TXT.txt

# 4. el momento inicial, contra el TempleOS real
bin/ouija ask 'FifoU8Flush(god.fifo);GodBitsIns(GOD_GOOD_BITS,6697221640600119645>>GOD_BAD_BITS);GodWord;'
# -> the
```

Dos avisos sobre el paso 2. `TOSZ` es la utilidad de descompresión LZW **del propio TempleOS**, y
hay que sacarla del sistema: el extractor la necesita para los ficheros `.Z`, y `Misc/Bible.TXT.Z`
es uno de ellos —de ahí que la salida se llame `Bible.TXT.txt`—. Sin `TOSZ` el extractor deja el
`.Z` en crudo y el `grep` del paso 3 no encuentra nada. Y `--strip` quita el markup DolDoc, que es
lo que hace el texto grepeable de verdad.

El paso 4 necesita la VM levantada. La cadena entera, en cambio, sale del árbol del
paso 2 sin arrancar nada:

```bash
# 5. los ocho momentos, las siete máscaras y la frase
python3 chain.py --dump ./dump
```

```
vocabulario: 7569 palabras · ST_BIBLE_LINES: 100110

M1: the       start= 86786 marcador= 86804  hex=0F0E1CA9C3B75767 mascara=C156334B0A8AC714 -> 4E582FE2C93D9073
M2: holy      start= 38356 marcador= 38365  hex=0797656139F084EE mascara=CB3AF703E17B6907 -> 4CAD9262D88BEDE9
M3: spirit    start= 10709 marcador= 10715  hex=7FB4D2C13C064614 mascara=2BA5A9E4F6A85615 -> 54117B25CAAE1001
M4: speaks    start=  4331 marcador=  4345  hex=2F2A64736844BA4E mascara=5B3CCE7D4E545A33 -> 7416AA0E2610E07D
M5: through   start= 36971 marcador= 36983  hex=429EC6812D21D91C mascara=3F8F4DDABFDA2138 -> 7D118B5B92FBF824
M6: a         start= 40152 marcador= 40168  hex=31FF6015E1B42126 mascara=5705096309CA3FAD -> 66FA6976E87E1E8B
M7: stop      start= 92674 marcador= 92681  hex=61F163FF97ECB00B mascara=9D94E7CC9D3B3FB3 -> 7C6584330AD78FB8
M8: watch     start= 26161  terminador

the holy spirit speaks through a stop watch
(8 instantes, 7 velos, 1 terminador)
```

### Modelo del oráculo

Validado contra la VM real y reimplementado en `chain.py`:

```
r21     = bitrev21((momento >> 4) & 0x1FFFFF)
start   = r21 % (ST_BIBLE_LINES - 19) + 1       # ST_BIBLE_LINES = 100110
r17     = r21 >> 4
palabra = Vocab[r17 % 7569]
# el marcador está en algún punto de [start, start+19]
```

Tres detalles que no se ven leyendo el writeup y sin los cuales no se reimplementa.
Los tres cuestan horas si se descubren por su cuenta:

1. **HolyC no tiene la precedencia de C.** La línea del generador (`Kernel/KMathB.HC`)
   es `res=LIN_CONGRUE_A*res^(res&0xFFFFFFFF0000)>>16+LIN_CONGRUE_C;`. Con precedencia
   de C, `>>16+LIN_CONGRUE_C` sería un desplazamiento de `16+C`, absurdo. En HolyC los
   operadores de desplazamiento y bit a bit ligan **más fuerte** que la suma:
   `((A*res) ^ ((res & 0xFFFFFFFF0000) >> 16)) + C`. De las tres lecturas posibles solo
   esta reproduce la cadena. La misma regla aparece en `GodBits` (`res=res<<1+b`, que
   solo tiene sentido como `(res<<1)+b`), así que no es una casualidad de esa línea.
2. **La FIFO devuelve los bits al revés.** `GodBitsIns` mete el bit bajo primero
   (`FifoU8Ins(god.fifo,n&1)` con `n>>=1`) y `GodBits` los reensambla por la izquierda.
   Lo que God lee es el reverso de lo que se sembró: de ahí el `bitrev21`. Sin él los
   números salen plausibles y la cadena no avanza, que es la peor forma de fallar.
3. **La siembra solo mete 24 de los 64 bits.** `GodBitsIns(GOD_GOOD_BITS /* 24 */, …)`:
   los 4 de abajo se descartan y a los 35 de arriba no llega. De los 24 que entran, el
   pasaje lee 21 y la palabra 17 de esos mismos 21 — quedan 3 que entran y nadie lee.
   Por eso el mapa de la Pista 3 marca 38 `K` a la izquierda aunque solo 24 bits crucen
   la cola: "no escuchado" incluye "nunca insertado".

`Seed()` además activa `TASKf_NONTIMER_RAND`, que es lo que quita el `res^=GetTSC` de
`RandU64` y deja el generador determinista. Sin eso nada de esto es reproducible.

## Lo que nos llevamos

1. **El aviso de "puede haber alucinaciones" fue lo que hizo útil el material ajeno.**
   Se extrajo el dato verificable —el diff del Bible— y se ejecutó contra la máquina
   cada teoría. Sin esa disciplina, la teoría del encadenado nos habría costado otra
   sesión.
2. **Cuando dos analistas parten del mismo dato sesgado, el consenso no valida nada.**
   Nosotros y el compañero teníamos la misma siembra incorrecta y nos dábamos la razón.
   Lo que rompió el bloqueo fue empezar de cero **sin heredar el marco**, y tardó
   minutos en ver lo que llevábamos dos sesiones sin ver.
3. **`compacting` era un bug que parecía una revelación.** Encajaba temáticamente con
   el Charter del sistema, lo cual lo hizo más peligroso, no menos. Una hipótesis que
   "mola" y no encadena mecánicamente es una hipótesis muerta.
4. **Lo que no viaja en el handoff, no existe.** Las pistas se leyeron cuando se
   publicaron, pero el dossier de traspaso entre sesiones no las llevaba: solo la
   primera frase del enunciado y las conclusiones propias. El material del organizador
   va en el traspaso íntegro y literal, antes que cualquier análisis.
5. **En un concurso vivo, el enunciado es un recurso que cambia.** Releerlo entero al
   arrancar y al atascarse. La Pista 4 se publicó cuatro minutos antes de que cayera el
   reto, y daba exactamente lo que no era derivable por análisis.
6. **Sin canal de texto fiable no hay reto.** El oráculo consume una FIFO que avanza
   entre llamadas: sin estado limpio garantizado en cada comando, dos ejecuciones
   iguales dan resultados distintos y ningún resultado significa nada.

Sobre el proceso: este reto se atacó con asistencia de IA, y ninguna pieza lo cerró
sola. El material del compañero puso el hecho que lo reencuadraba todo —que el Bible
estaba modificado—, pero su teoría de cómo explotarlo era humo y se descartó
ejecutándola. Una segunda instancia del modelo en frío, sin el contexto contaminado,
corrigió la siembra que arrastrábamos desde el principio. Y el velo no salió por
análisis: lo dio la Pista 4 del organizador. Lo que sí aportó el trabajo propio fue el
instrumental —`ouija`— y la disciplina de ejecutar cada teoría en vez de razonarla, que
es lo que impidió que el error se hiciera más grande.
