# Hack It / Solve It — Euskal Encounter 34

Writeups de doce de los trece niveles del concurso de la EE34 (julio de 2026).

## Qué es esto

La **Euskal Encounter** es la party informática que se celebra cada verano en Bilbao. Uno de sus
concursos clásicos es el **Hack It**, organizado por *Ontza*, *Owen* y su equipo sobre el Hack It
Framework, y jugado en `hackit.party.eus`. Se divide en dos tracks:

- **Solve It** — siete niveles de lógica, criptografía, encodings, acertijos visuales y puzzles.
- **Hack It** — seis niveles de reversing y hacking propiamente dicho.

La respuesta de cada nivel es siempre una **contraseña** que se escribe en un formulario. Y el
formato tiene dos reglas que condicionan cómo se juega:

- **Los niveles se desbloquean en cadena.** No puedes ni ver el enunciado del siguiente hasta
  resolver el anterior. No hay forma de elegir por dónde empezar ni de trabajar en paralelo.
- Existe un **"saltar nivel"** como válvula anti-atasco: te desbloquea el siguiente sin darte el
  punto, pero el nivel saltado **sigue puntuando si lo resuelves después**. Eso convierte cada
  atasco en una decisión: seguir picando o saltar y volver.

Esa mecánica explica el ritmo de la edición. Un reto que no cae no solo te cuesta su punto: te
bloquea la cola entera hasta que decides saltarlo.

## Resultado

Equipo **PeruEsClave**: **primeros del global con 12 puntos** — **7/7 en Solve It** y **5/6 en Hack
It**. El único que no cayó fue **Hack It 6 "Classical Music"**, que solo resolvieron dos equipos.

El primer puesto se decidió **por tiempo**: w0pr terminó también con 12 puntos y el desempate fue
la velocidad de resolución. Conviene tenerlo presente al leer los writeups, porque varios cuentan
horas gastadas en callejones sin salida — y ese era, literalmente, el margen.

Los writeups cuentan también lo que no salió, y lo dejan marcado en vez de maquillarlo. **Tres de
los doce tienen algo abierto**: un reto que no cayó (Hack It 6), una contraseña que nunca llegamos a
extraer del servicio (Solve It 3) y un cabo del enunciado que nadie ha conseguido explicar ni
siquiera después de resolver el nivel (Solve It 6). Cada uno dice cuál es su hueco y hasta dónde
llega lo verificado.

Otros dos lo tuvieron y ya no. El cierre de **Solve It 5** lo dio un compañero durante el concurso
por una vía que en su momento no reprodujimos: ahora está documentada y verificada. Y el decode de
las señales de **Solve It 4** se publicó a medias con un diagnóstico que resultó ser falso; ahora
las nueve señales se leen enteras y la extracción está cotejada contra los bytes de la ROM. Un
writeup que solo enseña la línea recta miente sobre cómo se resuelve esto de verdad — pero uno que
deja un "abierto" cuando ya no lo está, también.

## Los trece niveles

| # | Reto | Contraseña | Writeup |
|---|---|---|---|
| **Solve It 1** | Singular Calculus | `ODDMATHS` | [→](solve-it/1/WRITEUP.md) |
| **Solve It 2** | Lost Fest | `C4M1NOS` | [→](solve-it/2/WRITEUP.md) |
| **Solve It 3** | Retro Shell | `t4pF1gHtINg1nINmELEEiSLAND` | [→](solve-it/3/WRITEUP.md) |
| **Solve It 4** | Moviplaya 2005 | `4roM4Noc7urNo` | [→](solve-it/4/WRITEUP.md) |
| **Solve It 5** | Drawings in the wall | `MENEGROTH` | [→](solve-it/5/WRITEUP.md) |
| **Solve It 6** | The Last Crusade | `h0LyGr4IL` | [→](solve-it/6/WRITEUP.md) |
| **Solve It 7** | One Thousand and One Nights | `Allah` | [→](solve-it/7/WRITEUP.md) |
| **Hack It 1** | Easy Peasy | *no registrada* | [→](hack-it/1/README.md) |
| **Hack It 2** | Bowling Physics | `M4dF0rmUL4` | [→](hack-it/2/WRITEUP.md) |
| **Hack It 3** | Tercer Templo | `the holy spirit speaks through a stop watch` | [→](hack-it/3/WRITEUP.md) |
| **Hack It 4** | Embedded secret | `TheEagleSeesTheForest` | [→](hack-it/4/WRITEUP.md) |
| **Hack It 5** | Game Failez | `MYMEGAPW` | [→](hack-it/5/WRITEUP.md) |
| **Hack It 6** | Classical Music | *sin resolver* (parte 1/3: `v1nTag3`) | [→](hack-it/6/WRITEUP.md) |

Un hueco, y conviene decir por qué: **Hack It 1** lo resolvió un compañero por su cuenta, fuera de
las sesiones que documentamos. No tenemos material de primera mano ni registro de la contraseña, y
la única descripción que nos llegó del mecanismo —algo escondido en el HTML de la página— es de
segunda mano y no la hemos podido verificar, así que no la damos por buena.

**Solve It 5** sí tiene writeup; el cierre también lo dio un compañero, durante el propio concurso,
y por una vía que en su momento no reprodujimos. Esta revisión ya la deja documentada y verificada.
El camino largo que sí recorrimos en directo va publicado entero, porque lo que se aprendió por él
es de lo más aprovechable de la serie.

## Los retos, uno a uno

**Solve It 1 — Singular Calculus.** Nueve sumas, la primera mal resuelta, el resto con
interrogantes. Todo el reto cabe en dos líneas de Python; lo difícil fue dejar de buscarle tres
pies al gato.

**Solve It 2 — Lost Fest.** El cartel de un festival de siete noches con la ubicación tapada con
cinta. Cuarenta bandas reales, horarios desordenados, y a mitad de concurso el autor cambió el
cartel.

**Solve It 3 — Retro Shell.** Un terminal en el que el cliente oficial solo sabe enviar espacios.
El servidor te insulta en cada conexión, pero nunca lee lo que escribes.

**Solve It 4 — Moviplaya 2005.** Una ROM de Pokémon Esmeralda con una partida guardada. El save es
lo primero que mira todo el mundo, y por eso no lleva nada dentro. Lo bueno va inyectado en el
binario, y las señales de la isla que se inventó el autor están escritas en dos sistemas a la vez.

**Solve It 5 — Drawings in the wall.** Tres líneas de símbolos geométricos encontrados en una cueva,
y nada más. La respuesta estaba en el título del reto desde el primer minuto y tardamos catorce
horas en verla.

**Solve It 6 — The Last Crusade.** No se juega desde el teclado: hay que pasear por el recinto de
la party cazando balizas Bluetooth. Cada una entrega una imagen de estática de televisión con un
rótulo que apunta a la siguiente — y el rótulo no era lo único que llevaban dentro.

**Solve It 7 — One Thousand and One Nights.** Una sola frase, sin ficheros. El nivel más corto de
la edición y el que con más elegancia te manda a hacer aritmética que no hace ninguna falta.

**Hack It 2 — Bowling Physics.** Dos PNG de 16 bits con la posición y la velocidad de 65.536
partículas, y ni una línea de enunciado. Caracterizamos el dataset hasta el último decimal, y todo
ese trabajo resultó ser irrelevante para la respuesta.

**Hack It 3 — Tercer Templo.** Una imagen de disco de TempleOS, y hay que sacarle la contraseña
hablando con el oráculo "God" de Terry Davis. Cada pregunta consume entropía que no vuelve, así que
sin ejecución hermética ningún resultado significa nada.

**Hack It 4 — Embedded secret.** Una propiedad CSS inválida colada en el HTML delata un PostgreSQL,
y dentro hay 65.908 candidatos a contraseña con sus embeddings. Pasamos un buen rato declarando que
la respuesta no existía, teniéndola ya generada en el disco.

**Hack It 5 — Game Failez.** Una ROM de Mega Drive comprada en AliExpress que "no funciona como
esperaba". Dentro hay un intérprete de Brainfuck, y unas cuantas horas convencidos de que el reto
era imposible de ganar.

**Hack It 6 — Classical Music.** Un fichero de audio de 413 MB que en realidad es una cinta VHS. El
único punto que se nos escapó: sacamos la primera de sus tres partes y ahí nos quedamos.

## Sobre el método

Esta serie se resolvió **con asistencia de IA de principio a fin**, y los writeups cuentan el
reparto real: qué hizo bien la máquina, dónde se equivocó, y qué desbloqueó una persona. Aparecen
los callejones sin salida con nombre y apellidos, porque son la parte que normalmente no se publica
y es donde está casi todo el aprendizaje.

Dos patrones se repitieron lo bastante como para merecer un apartado propio. Sirven para cualquiera
que trabaje con agentes, no solo para CTFs:

**1. Reformatear el artefacto al medio donde el agente es fiable.** Un modelo que desconfía de su
propia percepción deja de razonar y se dedica a re-extraer los mismos datos una y otra vez. Se ve
clarísimo cuando el input son capturas de pantalla o glifos: el bucle no es "pensar mal", es "no
fiarse de lo que ve". La solución no fue insistir, fue **cambiar el canal**. En el criptograma de
[Solve It 5](solve-it/5/WRITEUP.md) los glifos se convirtieron a **SVG** —geometría
explícita en vez de píxeles— y el razonamiento se desatascó solo. En el TempleOS de
[Hack It 3](hack-it/3/WRITEUP.md) se construyó `ouija`, una interfaz que ejecuta HolyC dentro
de la VM real y devuelve **texto**, con estado limpio garantizado en cada llamada, en lugar de leer
capturas del emulador. El problema casi nunca es el agente: es el canal por el que le llega el mundo.

**2. El sesgo viaja en el contexto.** Varias veces, lo que rompió un bloqueo no fue una idea nueva
sino **empezar de cero con los mismos datos**: lanzar un análisis en frío, sin heredar el marco del
anterior. En Hack It 5 llevábamos horas con un diagnóstico equivocado —"este crackme está roto"— que
un análisis limpio deshizo en una pasada. En Solve It 2 pasó lo mismo con un supuesto que nadie
había cuestionado. El corolario incómodo es que **dos análisis que parten del mismo contexto sesgado
no se validan entre sí**: su acuerdo no añade información. Lo que rompe el bloqueo es un analista
que no comparta el marco.

## Créditos

Los retos los montan **Ontza**, que lleva años en esto, y **Owen**, que estrenaba puesto — y que
además es colega nuestro: en otras ediciones nos peleábamos los Hack It juntos, y este año estaba al
otro lado, poniéndolos. Trece niveles, trece ideas distintas, y varios con una vuelta de tuerca que
da gusto encontrar. Gracias por el curro.

**PeruEsClave** fuimos cuatro: **t3ndo**, **servida**, **garridinsi** y el que firma estos writeups.
La edición se ganó entre los cuatro, y los writeups van escritos en «nosotros» porque así se
trabajó.

Los writeups son nuestros y los errores también.

## Licencia

Este repositorio se publica bajo licencia **MIT** (ver [LICENSE](LICENSE)). Esa licencia cubre
**nuestros writeups y scripts** — el análisis, el código de resolución, las herramientas propias.
**No cubre los retos en sí ni sus materiales**, que son de la organización del Hack It —**Ontza**,
**Owen** y su equipo—, o de terceros cuando el reto los cita.

Algunos writeups incluyen la imagen del propio nivel porque sin ella no se entienden: la
inscripción de Solve It 5, las capturas de ruido de Solve It 6, los PNG de datos de Hack It 2. Son
de *Ontza* y se reproducen solo para explicar su reto.

Lo que **no** se redistribuye es lo que no nos corresponde repartir: las ROMs comerciales de Solve
It 4 y Hack It 5, el cartel de Solve It 2, la lámina de signos elamitas de Wikimedia Commons y el
audio de 395 MB de Hack It 6. Cada writeup dice dónde conseguirlo o cómo regenerarlo.
