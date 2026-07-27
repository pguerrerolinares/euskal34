# Solve It EE34 — Nivel 5: "Drawings in the wall"

> *"En uno de mis viajes, dentro de una cueva encontré los siguientes símbolos. ¿Me ayudas a
> descifrarlos?"*

Un PNG con tres líneas de glifos geométricos. Nada más.

La contraseña es **`MENEGROTH`**, y el título del reto la contenía desde el primer minuto — pero
eso no lo vimos hasta el final, así que lo dejamos para el final.

Dos avisos por delante, porque este writeup es distinto de los otros. El primero: el cierre no
salió del mismo método que el resto del análisis — lo remató **un compañero de equipo durante el
propio concurso**, por una vía que en su momento no supimos reproducir. Esta revisión documenta esa
vía, la reproduce y la deja verificada (sección 7). El segundo: el camino largo que sí recorrimos en
directo tiene el hallazgo más transferible de los trece niveles, y no es criptográfico, es de
**método**. Si trabajas con agentes, la sección 3 es la única parte que importa.

---

## 1. La transcripción

Lo primero es mecánico y salió bien: segmentar la imagen, recortar cada glifo, clusterizarlos
por similitud visual y sacar la secuencia. El resultado:

- **71 signos** en total, **25 distintos**.
- `|` = separador de palabra, `||` / `|||` = fin de frase.
- **22 palabras** repartidas en **tres líneas**.

Etiquetando los 25 signos como `S01`..`S25`, el criptograma es este:

```
L1  S01-S02 | S03-S04 | S01-S05 | S06-S07-S08-S01 | S09-S03-S01-S06-S10-S01-S05 |
    S11 | S01-S02 | S12-S08-S13-S06-S07 | S14-S07-S02 | S15-S14-S16-S02

L2  S17 | S18-S14-S01-S05 | S16-S19 | S12-S08-S13-S05 | S12-S06-S20-S08-S15-S11-S05 |
    S16-S19 | S01-S13-S04-S07-S04 | S17-S04 | S21-S05-S07-S05 | S22-S23

L3  S15-S24-S05 | S09-S25-S04
```

> **Nota sobre el corte de línea**: la transcripción se contó mal una vez, con `S22-S23` como
> arranque de la línea 3 en vez de cierre de la línea 2. Lo zanja mirar directamente
> `row3.png`: son **seis glifos agrupados 3 + 3**, con un separador simple entre los dos grupos y
> la doble barra de fin de frase al final. No hay ninguna palabra de cinco signos en esa imagen.
> `S22-S23` (`og`) es la última palabra de la línea 2; la línea 3 son `S15-S24-S05` (`tusen`) y
> `S09-S25-S04` (`huler`), sección 7.

La transcripción se verificó a fondo: distancias de píxel entre clusters para descartar que dos
formas parecidas fueran el mismo signo partido en dos (las cuatro variantes de rombo son
realmente distintas; las barras con dos y tres travesaños también). **La transcripción no era el
problema.** Merece la pena decirlo porque durante horas se sospechó de ella, y esa sospecha
—volveremos— era el síntoma de otra cosa.

## 2. El callejón largo: atacar el cifrado sin saber qué sistema es

Con 25 símbolos y 22 palabras, la lectura obvia es "sustitución monoalfabética, texto en
castellano" (concurso vasco, enunciado en castellano). Y ahí se fueron decenas de scripts:
análisis de frecuencias, solver de criptograma por patrones contra diccionario, hill-climbing con
quadgramas, beam search, simulated annealing, constraint solving, cifrado de Hill en varias
variantes, pruebas en castellano, inglés y euskera.

**Nada convergió nunca.** Ni una sola vez salió una frase limpia.

Ese "nada converge nunca" era el dato, y no se leyó como tal. Cuando media docena de métodos
independientes y bien implementados fallan sobre un criptograma de 71 signos, la conclusión no
es "necesito un séptimo método": es que **el modelo del problema está mal**. Se estaba atacando
el cifrado sin haber respondido antes la pregunta previa: *¿qué sistema de escritura es esto?*

### El modo de fallo peor: cribs que se autoconfirman

Hay una parte de esto que hay que contar con todas las letras, porque es más peligrosa que
perder tiempo.

Ante la falta de convergencia, se pasó a fijar **cribs** a mano: adivinar una palabra y propagar
las letras. Se fijó que una palabra de siete signos era `mientes`, otra `pues`, y más adelante
—cuando apareció la idea de que el texto pudiera estar en leet— `cu4l` y `v0c3s`. Sobre esas
anclas se construyó una lectura parcial de las 22 palabras que **parecía sólida**: cada crib
nueva se validaba contra las anteriores (¿es compatible con la biyección? ¿respeta las letras ya
asignadas?), y como eran compatibles entre sí, el sistema se reforzaba solo.

El problema: **el texto no era castellano**. Todo el edificio era coherente internamente y falso
por completo. Y lo que hace esto tan traicionero es que el criterio de validación —"la crib nueva
encaja con las anteriores"— **es un criterio real y estaba bien aplicado**. Un conjunto de cribs
mutuamente compatibles no es evidencia de que el idioma sea el correcto; solo lo es de que las
cribs no se contradicen. Con 25 símbolos y 22 palabras hay libertad de sobra para construir
decenas de sistemas mutuamente compatibles y todos equivocados.

La señal de alarma estaba a la vista y se racionalizó: **ninguna lectura cerraba del todo**.
Siempre quedaban palabras en basura, siempre había huecos. En vez de leerlo como refutación, se
explicó — "el autor ofuscó parte del texto a propósito", "es leet mixto", "hay jerga". Cada
excusa salvaba el marco un rato más. La regla, dicha en corto: **si tu hipótesis necesita una
excepción nueva cada vez que la contrastas, la hipótesis es la excepción.**

Y un corolario incómodo: los descartes hechos bajo un marco equivocado **hay que reabrirlos
cuando el marco cae**. Varias lecturas alternativas se rechazaron por violar la biyección
estricta de una sustitución monoalfabética; cuando más tarde se adoptó el modelo leet —que rompe
esa biyección por diseño— nadie volvió a mirarlas.

## 3. El giro de método: cambiar el formato del problema, no el esfuerzo

Esta es la parte por la que este writeup existe.

Durante todo el callejón anterior había un ruido de fondo constante: la desconfianza en la
propia percepción. El análisis volvía una y otra vez a *"quizá no he recortado bien los glifos"*,
*"quizá dos clusters son el mismo signo"*, *"déjame verificar la segmentación otra vez"*. Se
verificó, en efecto, varias veces, y siempre salía correcta. Pero la duda regresaba en cuanto el
siguiente solver fallaba.

Ese bucle tiene un diagnóstico, y no es "el analista es malo": **el canal era el equivocado**.
Razonar sobre una imagen significa re-percibir los glifos en cada pasada, y una percepción que
hay que rehacer continuamente nunca se convierte en un hecho estable sobre el que construir. El
resultado es que cada fallo aguas abajo se reinterpreta como un posible fallo de lectura aguas
arriba, y el análisis nunca avanza.

La salida no fue insistir ni verificar por séptima vez. Fue **cambiar la representación**:
convertir cada glifo a **SVG**, un fichero por símbolo, geometría explícita —trazos,
coordenadas, primitivas— en lugar de píxeles. Con eso los 25 signos dejan de ser algo que hay que
*mirar* y pasan a ser algo que se puede *citar*: `S07` es una entidad con identidad estable, y la
discusión pasa de "¿es esto un rombo o un rombo con un pie?" a razonar sobre la secuencia.

Formulado en general, que es como vale fuera de este reto:

> **Si un agente desconfía repetidamente de su propia percepción, el problema no es el agente:
> es el canal.** La solución no es pedirle que mire con más cuidado, ni verificar la extracción
> una vez más — es convertir la percepción en un artefacto simbólico, estable y citable, y
> razonar sobre él.

Aplica a mucho más que a glifos: leer un tablero desde una foto, extraer una tabla de un PDF,
sacar el estado de una captura de pantalla. Mientras el dato viva como píxeles, cada conclusión
arrastra la duda de la extracción. En cuanto vive como estructura, el razonamiento se despega
del reconocimiento y puedes atacar el problema real.

## 4. La identificación: un buscador visual, no un solver

Con los símbolos ya en formato limpio seguía faltando lo esencial: **qué son**. Y eso no lo
resolvió ningún solver ni ningún modelo razonando: se resolvió **pasando la imagen por un
buscador visual** (Google Lens), que devolvió una identificación inmediata — **elamita lineal**,
la escritura de la Elam de la Edad del Bronce, descifrada en gran parte en 2022 por el equipo de
François Desset.

La regla, que es la que el reto enseña y la que nos saltamos:

> **Ante símbolos no identificados, identifica el sistema de escritura ANTES de atacar el
> cifrado.** Y el instrumento para eso no es un criptoanalizador: es un buscador —textual o
> visual— sobre las formas.

Todo el trabajo de la sección 2 estaba condenado desde antes de empezar, no por mala ejecución
sino por orden de operaciones.

## 5. Cuánto casa realmente con el elamita lineal

Aquí toca ser sobrio, porque la identificación es sugerente pero no es una llave.

Comparando nuestros 25 signos contra la lámina de signos elamitas conocidos (64 entradas):

| Nivel de correspondencia | Cuántos | Ejemplos |
|---|---|---|
| **Fuerte** (la forma está esencialmente en el repertorio) | **10** | `S02`/`S19` línea vertical con punto arriba y abajo · `S16` rombo liso · `S10` rombo con barra vertical · `S04` hexágono alargado con barras horizontales · `S03` zigzag de picos triangulares · `S01` peine/rayado bajo barra · `S14` chevron con puntos · `S07` rombo sobre tallo · `S21` cuadro reticulado |
| **Moderada** (existe la familia, no la forma exacta) | **13** | `S05`, `S08`, `S09`, `S11`, `S12`, `S13`, `S15`, `S17`, `S18`, `S20`, `S23`, `S24`, `S25` |
| **Ninguna** | **2** | `S06` (círculo atravesado por una diagonal) y `S22` (caja escalonada con puntos) |

**Y ahora el caveat, que es tan importante como la tabla**: el repertorio elamita lineal es
grande y **geométricamente genérico** — rombos, líneas con puntos, triángulos, rayados,
aspas. Cualquier alfabeto inventado con estética lapidaria casa por azar con buena parte de él.
Que 23 de 25 "rimen" es **mucho más débil de lo que parece**, y el juicio de parecido es visual,
que es justo el tipo de juicio que produce falsos positivos con formas abstractas.

Conclusión que sostenemos: **el autor se inspiró en la estética del elamita lineal**. Lo que
*no* se sigue de ahí es que los valores silábicos publicados descifren el texto. Nuestro intento
de transliteración silábica no produjo nada legible, y el paso crítico —decidir qué signo nuestro
*es* qué signo elamita— no lo pudimos cerrar por encima del "se parece".

## 6. Lo que dice la estructura sobre la línea 3 (y dónde se equivocó)

Esta sección se escribió **antes** de conocer la respuesta. Es medible y no depende de ninguna
identificación. Contando la frecuencia de cada signo, con el corte de línea correcto (`row3.png`:
seis glifos, 3+3):

- **8 signos aparecen una sola vez** en todo el texto (`S10`, `S18`, `S20`, `S21`, `S22`, `S23`,
  `S24`, `S25`).
- La **línea 3 son dos palabras**, `S15-S24-S05` (`tusen`, 3 signos) y `S09-S25-S04` (`huler`, 3
  signos), y entre las dos **concentran 2 de esos 8** (`S24`, `S25`).
- Los otros dos hapax que en algún momento se creyeron de la línea 3 (`S22`, `S23`) son, en
  realidad, la **última palabra de la línea 2** (`og`) — no hay ninguna palabra de cinco signos en
  la línea 3, la que tiene más signos únicos es de tres, con **1 único de 3**.

Un bloque final construido con sílabas que no aparecen en ninguna otra parte del texto sigue
siendo, en general, la firma típica de un nombre propio. Pero contrastado con el texto completo
(sección 7), esa lectura falla en dos frentes: la concentración de hapax en la línea 3 es la
mitad de lo que se llegó a creer, y lo que señala no es un nombre — es «tusen huler», **"mil
cuevas"**, dos sustantivos comunes. Los dos nombres propios reales del criptograma son **Doriath**
(última palabra de la línea 1) y **Esgalduin** (línea 2), donde nadie los buscó.

Un detalle que sí se sostiene: **`S01` y `S05` empatan como signos más frecuentes** (8 apariciones
cada uno), y `S05` aparece casi siempre en posición final de palabra —7 de sus 8 apariciones—,
incluida la última palabra de la línea 3.

### Qué acotó esto, y qué no

Conviene separar bien los dos pasos, porque es fácil venderlos como uno solo, y uno de los dos no
sobrevive a la corrección del corte de línea.

**Paso 1, semántico**: partiendo del enunciado (*"dentro de una cueva"*) se preselecciona a mano
una lista corta de topónimos de *El Silmarillion* asociados a cuevas y salas subterráneas —
**Menegroth**, **Belegost**, **Nogrod**, **Nargothrond**, **Utumno**, **Androth**. Esto es
lectura temática, no análisis, y no depende de la transcripción: sigue en pie.

**Paso 2, estructural, y este cae**: la restricción que se usó en su momento —"la primera palabra
de la línea 3 tiene 5 signos, todos distintos"— partía del corte de línea mal contado. Con el
corte correcto esa palabra tiene **3 signos**, no 5, y además ahora sabemos (sección 7) que la
línea 3 no codifica ningún nombre. El filtro de sílabas que en su día redujo los seis candidatos a
tres —*Menegroth*, *Belegost* y *Androth*—, y dentro del cual estaba la respuesta correcta, se
apoyaba en un conteo que no era el real. Fue un acierto por motivos equivocados, y no lo
sostenemos como método: se deja constancia de que ocurrió, no como ruta válida al resultado.

Y encima, **el filtro no redujo el corpus de El Silmarillion a tres, redujo a tres los seis
nombres que ya estábamos barajando**. Aplicando la misma regla a medio centenar de topónimos de la
obra sobreviven **dieciocho** — Almaren, Avallone, Dorlomin, Eldamar, Estolad, Formenos,
**Gondolin**, Himring, Ilmarin, **Neldoreth**, Nevrast, Taniquetil, Tolfalas, Tumladen, Vinyamar y
compañía. Y varios son tan temáticamente plausibles como los nuestros: Gondolin es la ciudad
oculta, Neldoreth el bosque de Doriath, Himring una fortaleza.

O sea: **el único recorte defendible es el semántico**, no el estructural. El encuadre honesto es
este:

> **La estructura te dice dónde mirar; no te dice qué es.** Y aquí ni siquiera acertó el "dónde":
> la mayor concentración real de hapax está repartida entre el final de la línea 2 y la línea 3, y
> ninguna de las dos lleva un nombre — la línea 3 es «tusen huler», dos sustantivos comunes.
> Elegir *Menegroth* fue, de principio a fin, trabajo de lectura temática.

El análisis estructural **no acotó lo que creíamos que acotaba**. Sigue mereciendo la pena
contarlo — no como método que funcionó, sino como ejemplo de cómo un corte de línea mal contado
puede disfrazarse de hallazgo durante horas.

## 7. El final: el título llevaba la respuesta

El reto lo cerró **un compañero de equipo**, durante el propio concurso. Esta sección documenta,
reproduce y verifica esa vía: el texto plano es **noruego**, escrito con los valores fonéticos que
el equipo de François Desset publicó en 2022 para el elamita lineal (sección 4) — pero no como
sustitución letra a letra. Es un **abjad**: cada signo aporta la **consonante** de su celda en la
lámina de Desset, y las vocales se escriben solo a veces, con los cuatro signos vocálicos (`a`,
`e`, `i`, `u`). Ese es el motivo de fondo por el que ningún ataque de la sección 2 cerraba nunca:
todos asumían "un signo = una letra", y aquí un mismo signo consonántico reaparece con vocales
distintas alrededor que simplemente no están escritas.

La prueba más clara es la palabra de siete signos que ningún crib logró leer durante el concurso:
`h·v·d·s·t·d·n`. Como consonantes sueltas no dice nada; como esqueleto de una palabra noruega de
11 letras, es inmediata: **hovedstaden**.

### La tabla abjad

25 signos, 25 celdas de la lámina de Desset, cada una con la consonante que aporta:

```
S01: te   clase T  (d/t)              S14: ri2  clase R  (r)
S02: ta   clase T  (t/d)              S15: tu2  clase T  (d/t)
S03: wi   clase W  (v)                S16: a    clase A  (a)
S04: ra   clase R  (r)                S17: pu2  clase P  (p/f)
S05: na   clase N  (n)                S18: pe   clase P  (b)
S06: sa   clase S  (s)                S19: u2   clase U  (v)
S07: ki   clase K  (k/g)              S20: ka   clase K  (g)
S08: la   clase L  (l)                S21: ku2  clase K  (k)
S09: hu   clase H  (h)                S22: u    clase U  (o)
S10: ti   clase T  (t)                S23: ka2  clase K  (g)
S11: i    clase I  (i)                S24: si   clase S  (s)
S12: e    clase E  (e, y la a de "alviske")   S25: li   clase L  (l)
S13: wi2  clase W  (v)
```

Tres celdas las fijan directamente las palabras ancla, no al revés: **`S10` = t** (la t de
hoved**s**t**aden**), **`S13` = v** (fijada a la vez por d**v**erger, el**v**en y al**v**iske) y
**`S20` = g** (la g de Es**g**alduin).

### Las anclas duras

Dos palabras del texto no dejan margen de interpretación: **`hovedstaden`** y **`Esgalduin`** dan
**match único** contra las 605.000 formas del Norsk Ordbank. Con 25 signos y un abjad de
consonantes hay margen de sobra para que un esqueleto corto encaje con varias palabras — pero
ninguna de estas dos (7 signos cada una) tiene una alternativa real en el diccionario noruego. Ese
es el argumento que cierra la discusión de si el parecido es azar: fijadas esas dos palabras, el
resto de la frase se resuelve sin margen de maniobra.

### El texto

```
Det var den skjulte hovedstaden i det alviske riket Doriath.
På bredden av elven Esgalduin, av dverger for kongen, og
tusen huler.
```

*(«Era la capital escondida del reino élfico de Doriath. A orillas del río Esgalduin, por enanos
para el rey, y mil cuevas.»)*

*(Nota: la palabra es **`alviske`**, no `elviske`. Quedó mal en una revisión anterior de este
mismo writeup.)*

### Los puntos que no cierran perfectos

El descifrado no es una sustitución mecánica sin fisuras, y se declara así en vez de maquillarlo.
Quedan dos puntos donde el autor del reto tomó un atajo al codificar, no donde falle el
descifrado:

- La **`a`** de **`alviske`** se escribe con el signo de `e` (`S12`) — la misma celda que cubre la
  `e` normal en el resto del texto.
- La **`dd`** de **`bredden`** se colapsa en un solo signo (`S01`): la escritura no representa
  consonantes dobles.

*(Una revisión anterior de este writeup daba un tercer punto — `og` y `tusen` fundidas en un
token sin separador. No es así: `row3.png` muestra separador simple entre ambas, son dos palabras
limpias. Ver la nota de la sección 1.)*

### Sobre el Silmarillion, un matiz

No hay ninguna cita literal de *El Silmarillion* en el texto — eso sigue siendo cierto. Pero es más
preciso decir que el autor del reto **usa el léxico exacto de su traducción al noruego**, no que
inventó el noruego desde cero: la traducción de Nils Ivar Agøy contiene, en un pasaje que no
teníamos localizado, «På Esgalduins søndre bredd… lå Menegroths huler; og hele Doriath lå øst for
Sirion» — «en la orilla sur del Esgalduin... yacían las cuevas de Menegroth; y todo Doriath se
extendía al este del Sirion». Y **`alviske`** (la forma que usa Agøy para "élfico") aparece 13
veces en el libro. El autor no citó una frase: escribió la suya propia con el vocabulario exacto de
esa traducción — Doriath, Esgalduin, *alviske*, *huler* — que es un vínculo más fuerte con el
original que una cita suelta, y explica por qué ninguna búsqueda de frase textual daba con nada.

### Por qué describe Menegroth sin nombrarla

`MENEGROTH` no aparece en el texto: es la respuesta a lo que el texto describe, no una palabra
del propio texto. **Menegroth** son *"las Mil Cavernas"*: el reino subterráneo de Thingol en
Doriath, a orillas del Esgalduin, excavado en la roca por los enanos de Belegost. Frase a frase,
el noruego reconstruido **es** la ficha de Menegroth sin decir su nombre: la capital escondida
(*hovedstaden*) del reino élfico de Doriath, a orillas del Esgalduin, obra de enanos para el rey,
de mil cuevas. Y verificado contra el texto de Tolkien:

> *"Carven figures of beasts and birds there ran upon the walls, or climbed upon the pillars, or
> peered among the branches entwined with many flowers."*
> — *El Silmarillion*, «De los Sindar»

En los salones de Menegroth había **figuras talladas de bestias y aves recorriendo los muros**,
trepando por los pilares y asomando entre ramas de piedra entrelazadas con flores. Es decir:
**"Drawings in the wall"**, el título del reto, es una descripción literal de Menegroth. Y el enunciado —*"dentro de una cueva encontré los siguientes símbolos"*—
dice exactamente lo mismo otra vez.

**El nombre del reto contenía la respuesta desde el primer minuto**, mientras nosotros estábamos
dentro del criptograma haciendo análisis de frecuencias. No es que la pista fuera sutil: es que
no la miramos, porque habíamos decidido que el problema era criptográfico y el título era
decoración. Es el mismo error de la sección 2 —modelo equivocado del problema— cometido un nivel
más arriba.

### Reproducir el descifrado

Verificador sin dependencias (`decipher_norwegian.py`, en este directorio): no aplica el diccionario
en un solo sentido, **cifra la frase noruega reconstruida** y comprueba letra a letra que reproduce
los 71 signos exactos del criptograma.

```python
#!/usr/bin/env python3
"""
Verificador final solve5: elamita lineal -> noruego (modelo abjad).

Tabla cerrada: signo -> (celda Desset, clase fonetica).
Frase objetivo: se comprueba signo a signo que el cifrado de la frase
noruega reconstruida reproduce exactamente los 71 signos del criptograma.
"""

CRYPTO = [[1,2],[3,4],[1,5],[6,7,8,1],[9,3,1,6,10,1,5],[11],[1,2],[12,8,13,6,7],[14,7,2],[15,14,16,2],
     [17],[18,14,1,5],[16,19],[12,8,13,5],[12,6,20,8,15,11,5],[16,19],[1,13,4,7,4],[17,4],[21,5,7,5],
     [22,23],[15,24,5],[9,25,4]]
# La segmentacion de palabra la fija row3.png: 6 glifos en dos grupos de 3, con
# separador simple entre ambos y doble barra de fin de frase al cierre. S22-S23
# ("og") es la ultima palabra de L2; L3 son S15-S24-S05 ("tusen") y S09-S25-S04
# ("huler"). El verificador reproduce los 71 signos igual con cualquier
# agrupacion -- comprueba la lectura, no la segmentacion -- pero la imagen manda.

TABLE = {  # signo: (celda elamita Desset, clase, letras noruegas que cubre)
    1:  ('te',  'T', 'd/t'),
    2:  ('ta',  'T', 't/d'),
    3:  ('wi',  'W', 'v'),
    4:  ('ra',  'R', 'r'),
    5:  ('na',  'N', 'n'),
    6:  ('sa',  'S', 's'),
    7:  ('ki',  'K', 'k/g'),
    8:  ('la',  'L', 'l'),
    9:  ('hu',  'H', 'h'),
    10: ('ti',  'T', 't'),
    11: ('i',   'I', 'i'),
    12: ('e',   'E', 'e (y la a de alviske)'),
    13: ('wi2', 'W', 'v'),
    14: ('ri2', 'R', 'r'),
    15: ('tu2', 'T', 'd/t'),
    16: ('a',   'A', 'a'),
    17: ('pu2', 'P', 'p/f (sila "pa" completa en "paa")'),
    18: ('pe',  'P', 'b'),
    19: ('u2',  'U', 'v (grafia latina u~v)'),
    20: ('ka',  'K', 'g'),
    21: ('ku2', 'K', 'k'),
    22: ('u',   'U', 'o'),
    23: ('ka2', 'K', 'g'),
    24: ('si',  'S', 's'),
    25: ('li',  'L', 'l'),
}

# Frase noruega reconstruida, palabra a palabra, con el cifrado esperado:
# cada palabra -> lista de (letra(s) del noruego, signo que las representa)
PHRASE = [
    ("det",         [('d',1),('e',None),('t',2)]),
    ("var",         [('v',3),('a',None),('r',4)]),
    ("den",         [('d',1),('e',None),('n',5)]),
    ("skjulte",     [('s',6),('k',7),('j',None),('u',None),('l',8),('t',1),('e',None)]),
    ("hovedstaden", [('h',9),('o',None),('v',3),('e',None),('d',1),('s',6),('t',10),('a',None),('d',1),('e',None),('n',5)]),
    ("i",           [('i',11)]),
    ("det",         [('d',1),('e',None),('t',2)]),
    ("alviske",     [('a',12),('l',8),('v',13),('i',None),('s',6),('k',7),('e',None)]),
    ("riket",       [('r',14),('i',None),('k',7),('e',None),('t',2)]),
    ("Doriath",     [('d',15),('o',None),('r',14),('i',None),('a',16),('t',2),('h',None)]),
    ("på",          [('på',17)]),
    ("bredden",     [('b',18),('r',14),('e',None),('dd',1),('e',None),('n',5)]),
    ("av",          [('a',16),('v',19)]),
    ("elven",       [('e',12),('l',8),('v',13),('e',None),('n',5)]),
    ("Esgalduin",   [('e',12),('s',6),('g',20),('a',None),('l',8),('d',15),('u',None),('i',11),('n',5)]),
    ("av",          [('a',16),('v',19)]),
    ("dverger",     [('d',1),('v',13),('e',None),('r',4),('g',7),('e',None),('r',4)]),
    ("for",         [('f',17),('o',None),('r',4)]),
    ("kongen",      [('k',21),('o',None),('n',5),('g',7),('e',None),('n',5)]),
    ("og",          [('o',22),('g',23)]),
    ("tusen",       [('t',15),('u',None),('s',24),('e',None),('n',5)]),
    ("huler",       [('h',9),('u',None),('l',25),('e',None),('r',4)]),
]

print(f"{'#':>3} {'criptograma':<28} {'palabra':<14} cifrado letra a letra")
ok_all = True
for wi, (signs, (word, enc)) in enumerate(zip(CRYPTO, PHRASE)):
    produced = [s for _, s in enc if s is not None]
    match = "OK " if produced == signs else "FAIL"
    if produced != signs: ok_all = False
    sig_str = '-'.join(f"S{s:02d}" for s in signs)
    det = ' '.join(f"{l}»S{s:02d}" if s else f"({l})" for l, s in enc)
    print(f"w{wi+1:>2} {sig_str:<28} {word:<14} {det}   [{match}]")

print()
print("TOTAL:", "los 71 signos reproducen el criptograma EXACTAMENTE" if ok_all else "HAY DISCREPANCIAS")
```

Salida real (ejecutado tal cual, sin editar):

```
  # criptograma                  palabra        cifrado letra a letra
w 1 S01-S02                      det            d»S01 (e) t»S02   [OK ]
w 2 S03-S04                      var            v»S03 (a) r»S04   [OK ]
w 3 S01-S05                      den            d»S01 (e) n»S05   [OK ]
w 4 S06-S07-S08-S01              skjulte        s»S06 k»S07 (j) (u) l»S08 t»S01 (e)   [OK ]
w 5 S09-S03-S01-S06-S10-S01-S05  hovedstaden    h»S09 (o) v»S03 (e) d»S01 s»S06 t»S10 (a) d»S01 (e) n»S05   [OK ]
w 6 S11                          i              i»S11   [OK ]
w 7 S01-S02                      det            d»S01 (e) t»S02   [OK ]
w 8 S12-S08-S13-S06-S07          alviske        a»S12 l»S08 v»S13 (i) s»S06 k»S07 (e)   [OK ]
w 9 S14-S07-S02                  riket          r»S14 (i) k»S07 (e) t»S02   [OK ]
w10 S15-S14-S16-S02              Doriath        d»S15 (o) r»S14 (i) a»S16 t»S02 (h)   [OK ]
w11 S17                          på             på»S17   [OK ]
w12 S18-S14-S01-S05              bredden        b»S18 r»S14 (e) dd»S01 (e) n»S05   [OK ]
w13 S16-S19                      av             a»S16 v»S19   [OK ]
w14 S12-S08-S13-S05              elven          e»S12 l»S08 v»S13 (e) n»S05   [OK ]
w15 S12-S06-S20-S08-S15-S11-S05  Esgalduin      e»S12 s»S06 g»S20 (a) l»S08 d»S15 (u) i»S11 n»S05   [OK ]
w16 S16-S19                      av             a»S16 v»S19   [OK ]
w17 S01-S13-S04-S07-S04          dverger        d»S01 v»S13 (e) r»S04 g»S07 (e) r»S04   [OK ]
w18 S17-S04                      for            f»S17 (o) r»S04   [OK ]
w19 S21-S05-S07-S05              kongen         k»S21 (o) n»S05 g»S07 (e) n»S05   [OK ]
w20 S22-S23                      og             o»S22 g»S23   [OK ]
w21 S15-S24-S05                  tusen          t»S15 (u) s»S24 (e) n»S05   [OK ]
w22 S09-S25-S04                  huler          h»S09 (u) l»S25 (e) r»S04   [OK ]

TOTAL: los 71 signos reproducen el criptograma EXACTAMENTE
```

Los 71 signos, sin excepción, salen de cifrar la frase reconstruida — no al revés. Es la prueba
más fuerte que tenemos de que la lectura es correcta y no un ajuste post-hoc.

---

## Reproducir

En este directorio están la imagen original (`level.png`), las tres líneas sueltas
(`row1.png`, `row2.png`, `row3.png`), los 25 símbolos limpios en SVG y PNG
(`symbols_clean/S01..S25`) y la lámina de contacto (`symbols_clean/contact_clean.png`). La
lámina de signos elamitas con la que se hizo el contraste no la redistribuimos porque no es
nuestra: es [*List of known Linear Elamite characters*](https://commons.wikimedia.org/wiki/File:List_of_known_Linear_Elamite_characters.jpg)
de Wikimedia Commons. La transcripción está en la sección 1 y el análisis de frecuencias es
inmediato:

```python
from collections import Counter
L1 = [[1,2],[3,4],[1,5],[6,7,8,1],[9,3,1,6,10,1,5],[11],[1,2],[12,8,13,6,7],[14,7,2],[15,14,16,2]]
L2 = [[17],[18,14,1,5],[16,19],[12,8,13,5],[12,6,20,8,15,11,5],[16,19],[1,13,4,7,4],[17,4],[21,5,7,5],[22,23]]
L3 = [[15,24,5],[9,25,4]]

W = L1 + L2 + L3
c = Counter(s for w in W for s in w)
hapax = {s for s, n in c.items() if n == 1}
print(len(W), 'palabras,', sum(c.values()), 'signos,', len(c), 'distintos')
print('hapax:', sorted(hapax))                                  # 8 signos
print('hapax en L3:', [s for w in L3 for s in w if s in hapax])  # 2 de los 8; S22,S23 estan en L2
```

## Lo que nos llevamos

1. **El título y el enunciado son input, no decoración.** "Drawings in the wall" + "dentro de una
   cueva" es una descripción literal de Menegroth, las Mil Cavernas de paredes talladas. La
   respuesta estaba en la cabecera de la página desde el primer minuto y la tratamos como
   ambientación. Antes de abrir un solver: **lee el título como si fuera una pista, porque lo es.**
2. **Identifica el sistema de escritura antes de atacar el cifrado.** Un buscador visual sobre
   las formas resuelve en segundos lo que ningún criptoanalizador va a resolver nunca. El orden
   de operaciones era todo el reto.
3. **Si un agente desconfía repetidamente de su propia percepción, cambia el canal, no el
   esfuerzo.** Convertir píxeles en SVG —geometría explícita y citable— es lo que despegó el
   razonamiento del reconocimiento. Es el hallazgo más reutilizable de este reto.
4. **Un conjunto de cribs mutuamente compatibles no valida el idioma.** Solo demuestra que no se
   contradicen entre sí. Es un sistema que se autoconfirma mientras se aleja de la solución.
5. **"Nunca cierra del todo" es una refutación, no un detalle a explicar.** Cada excepción que
   inventas para salvar la hipótesis (ofuscación, jerga, leet) es una medida de lo mal que va.
6. **Cuando cae el marco, reabre los descartes que hiciste bajo él.** Las lecturas rechazadas por
   violar una regla que después abandonas siguen en el tablero, y nadie vuelve a mirarlas.
7. **La estadística de símbolos vale aunque no tengas la clave — para localizar, no para
   elegir.** Y hay que recontarla cuando el dato de entrada estaba mal: aquí el corte de línea se
   contó una vez con un signo de más, y eso infló la concentración de hapax en la línea 3 al
   doble de la real. Corregido el corte, lo que queda tampoco era un nombre propio, era una
   conjunción (en la línea 2) y dos sustantivos comunes (en la 3). Quedarse con tres candidatos y
   acertar entre ellos no fue mérito de la aritmética de sílabas, sino de la lectura temática — la
   aritmética partía, además, de un conteo equivocado. No confundas los dos pasos ni le atribuyas
   a un cálculo un recorte que hizo la semántica.

Sobre el proceso: este reto se atacó con asistencia de IA de forma intensiva, y es el ejemplo
más claro de la serie de que **más cómputo no arregla un modelo equivocado del problema**. Toda
la potencia se fue en criptoanálisis cada vez más sofisticado sobre una premisa falsa; lo que
movió la aguja fueron dos intervenciones humanas baratísimas: convertir los glifos a SVG (arreglar
el canal) y arrastrar la imagen a un buscador visual (identificar el sistema). Una segunda
instancia en frío, con contexto limpio, tampoco desbloqueó: siguió una lectura silábica elamita
literal que no cerraba, porque compartía la premisa de que la solución era descifrable desde el
propio texto. Y el cierre real lo puso un compañero, durante el propio concurso, leyendo el
elamita lineal como un abjad —consonantes, vocales casi siempre mudas— aplicado al noruego
(sección 7) — algo que ni el cómputo barato ni el caro llegaron a probar en su momento.

El reto acabó cayendo, así que sí es un writeup de victoria — pero de una victoria repartida y
con la lección al revés de lo que uno esperaría: **el trabajo caro no sirvió y las dos cosas que
funcionaron fueron gratis** (cambiar el formato del dato, y leer el título).
