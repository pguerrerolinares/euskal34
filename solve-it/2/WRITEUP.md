# Solve It EE34 — Nivel 2: "Lost Fest"

> *"Curioso festi, ¿qué esconde?"* — por Owen

El asset es un JPG de 4260×2780: el cartel de un festival ficticio, **LOST FEST**, "siete noches",
del 14 al 20 de julio. Siete columnas (LUN…DOM), cada una con su lista de grupos y horarios. Abajo,
un campo **UBICACION** en rojo, **tapado con un trozo de cinta**.

Spoiler: **`C4M1NOS`**. Es el reto que más nos costó de la tanda, y casi todo el coste vino de dar
por sentada una cosa que nadie nos había dicho.

---

## 1. Lo que hay en el cartel

Lo primero es transcribir. Las 40 bandas son **reales**, y agrupadas por día son **todas del mismo
país**:

| Día | País | Grupos (en orden cronológico) |
|---|---|---|
| **LUN** 14 | México | Control Machete · Grupo Yndio · Nortec Collective · Maná · Molotov · Sak Tzevul · Acapulco Tropical |
| **MAR** 15 | China | Hiperson · Low Wormwood · SMZB · Orange Ocean · Duck Fight Goose |
| **MIE** 16 | Australia | Powderfinger · The Medics · The Pigram Brothers · Pendulum · Cold Chisel · The Avalanches · AC/DC |
| **JUE** 17 | Japón | Capsule · Coldrain · Denki Groove · Pierrot · Greenmachine |
| **VIE** 18 | Brasil | Banda Calypso · Vanguart · BaianaSystem · Aviões do Forró · Dead Fish |
| **SAB** 19 | Francia | Noir Désir · Tri Yann · Marquis de Sade · IAM · Weepers Circus |
| **DOM** 20 | España | Celtas Cortos · Platero y Tú · Mecano · Medina Azahara · Triana · M Clan |

Dos observaciones que orientan:

- **Los horarios están desordenados** dentro de cada columna. En el cartel, el lunes empieza por
  "20:20 MOLOTOV" y el "16:00 CONTROL MACHETE" aparece el tercero. Alguien ha barajado las filas a
  propósito, así que el **orden cronológico es una lectura que el reto te está pidiendo hacer**.
- El país no está escrito en ninguna parte. Lo deduces tú de las bandas.

El fichero no esconde nada: sin EXIF, sin comentario JPEG, sin datos tras el final del stream. Todo
el puzzle está en el contenido.

## 2. Callejón nº 1: los horarios

La lectura obvia de "horarios desordenados" es acróstico. Se probó a fondo y no da nada:

- primera y última letra de cada banda, por orden de hora, ascendente y descendente, por día y en
  global;
- los **minutos** son sospechosamente específicos (`19:15`, `22:45`, `16:55`) y parecen índices de
  letra dentro del nombre de la banda. Da huecos y basura;
- conversión de cada hora al huso horario de su país y reordenación global por UTC. Regulariza los
  días pero el acróstico sigue sin salir.

Los horarios son **atrezzo**: existen solo para darte un orden. No llevan mensaje.

## 3. Callejón nº 2: una mecánica preciosa y falsa

Merece la pena contarlo porque es el tipo de hipótesis contra la que hay que vacunarse.

Alguien propone: cuenta las bandas de cada día y usa ese número como **índice cíclico sobre el
nombre del país en castellano**. Con el cartel original (43 grupos):

```
LUN  MEXICO   (6 letras)  7 bandas → 7 mod 6 = 1 → M
MAR  CHINA    (5)         5 bandas → 5         → A
MIE  AUSTRALIA(9)         7 bandas → 7         → L
JUE  JAPON    (5)         8 bandas → 8 mod 5=3 → P
...
```

Sale **`MALPICA`** — que además es un topónimo real (A Coruña). Encaja con "la ubicación tapada",
usa un dato que hasta entonces no servía para nada (el número de bandas), y se puede **verificar en
código**, cosa que se hizo.

Era falsa. Y aquí está la lección: que una mecánica sea computable, reproducible y produzca una
palabra con sentido **no la valida**. Con siete grados de libertad (qué contar, qué indexar, en qué
idioma, con qué módulo) el espacio de mecánicas que escupen *algún* topónimo es enorme. Una
hipótesis solo vale si es **forzosa**: si el reto no admite razonablemente otra lectura.

## 4. La mecánica real: geoglifos

El clic viene de juntar tres piezas que ya estaban sobre la mesa: un país por día, un orden interno
que el reto se molesta en ocultar, y una **ubicación** como respuesta.

> Coge las bandas de un día. Ordénalas por hora. Pon la **ciudad natal** de cada una en el mapa de su
> país y **une los puntos en ese orden**. El recorrido dibuja un carácter.
>
> Siete días = siete caracteres.

El caso más limpio es Francia:

| Hora | Banda | Ciudad |
|---|---|---|
| 18:00 | Noir Désir | Burdeos |
| 19:10 | Tri Yann | Nantes |
| 20:20 | Marquis de Sade | Rennes |
| 21:35 | IAM | Marsella |
| 22:55 | Weepers Circus | Estrasburgo |

Burdeos → Nantes → Rennes es una subida por la costa atlántica; Rennes → Marsella es una diagonal
larga hacia el sudeste; Marsella → Estrasburgo vuelve a subir. Sube, baja en diagonal, sube: una
**N** de libro.

España, el domingo, sale igual de claro: Valladolid → Bilbao (un trazo corto hacia arriba a la
derecha), Bilbao → Madrid → Córdoba → Sevilla (una vertical larga bajando), Sevilla → Murcia (una
horizontal a la derecha). Es un **1** con su banderín y su base. O una **L**. O una **I**. Ese es el
problema del reto, y no es accidental.

### Reproducirlo

```python
import matplotlib.pyplot as plt
# ciudades = {banda: (lon, lat)}, en orden cronológico del día
xs = [lon for lon, lat in ruta]
ys = [lat for lon, lat in ruta]
plt.plot(xs, ys, '-o')
plt.gca().set_aspect(1/np.cos(np.radians(np.mean(ys))))  # corrige la proyección
plt.show()
```

Un detalle que importa: **corrige el aspecto** (`lon·cos(lat)` frente a `lat`). Sin eso, un país
alargado en latitud te deforma el glifo y lees una letra por otra. Con Australia y México la
diferencia entre una `C` y una `O` depende literalmente de eso.

Las ciudades natales las sacamos de fuentes públicas. **Aviso honesto**: no todas son inequívocas
—hay bandas que se formaron en una ciudad y se asocian a otra, y en un par de casos tuvimos que
elegir— pero el trazo global es robusto a un punto mal puesto. Lo que no es robusto es la lectura de
la letra, que es justo lo siguiente.

## 5. La ambigüedad es el reto

Con los siete glifos dibujados, cada uno admite varias lecturas:

| Día | País | Forma | Lecturas posibles |
|---|---|---|---|
| LUN | México | zigzag | **S** / 5 / Z / 2 |
| MAR | China | dos picos | **M** |
| MIE | Australia | bucle abierto por la derecha | **C** / O / D / G |
| JUE | Japón | *(ver §6)* | — |
| VIE | Brasil | un cuatro | **4** / A |
| SAB | Francia | zigzag vertical | **N** |
| DOM | España | vertical con base | **1** / I / L / J |

Solo M y N son inequívocos. El resto no. Y esto **está diseñado así**: es lo que impide resolver el
reto de un vistazo, mirando el cartel y adivinando. Hay que ganarse la desambiguación.

Como el cartel es obra del autor y no se redistribuye, los siete trazos están redibujados en una
figura nuestra — `figura_geoglifos_light.png` / `figura_geoglifos_dark.png`, generadas por
`gen_figura_geoglifos.py` en este mismo directorio: silueta de país, vértices numerados en orden
cronológico, flechas de dirección y, debajo de cada panel, la lectura. Está construida solo con
datos (ciudades, horas, países); todo lo que hay que ver del mecanismo se ve ahí sin tocar el
original.

## 6. El autor corrige el cartel a mitad de concurso

A media noche, el enunciado del reto cambió y apareció una nota: *"el jueves ha sufrido cambios de
última hora"*. El cartel se había sustituido. Los ficheros son `cartel_OLD.jpg` y `cartel_NEW.jpg`
(ver §Reproducir), y el diff de imagen localiza el cambio con precisión — no son dos regiones,
como dijimos durante el concurso, sino **tres**:

```python
from PIL import Image; import numpy as np
A = np.array(Image.open('cartel_OLD.jpg').convert('L')).astype(int)
B = np.array(Image.open('cartel_NEW.jpg').convert('L')).astype(int)
D = np.abs(A - B) > 30        # 115.379 píxeles distintos de 11.842.800
# proyectando D sobre el eje Y salen tres bandas de filas:
#   filas  651-667   cols  800-816       154 px  → un carácter: «43 GRUPOS» pasa a «40 GRUPOS»
#   filas 1034-2178  cols ~1890-2360  ~46.700 px  → la columna del JUE, entera
#   filas 2352-2451  cols  288-3994    68.370 px  → el pie del cartel, de lado a lado
```

La cabecera cuadra con el conteo real, columna a columna: 43 = 7+5+7+**8**+5+5+6 y
40 = 7+5+7+**5**+5+5+6. El jueves es el único día que cambia: −3 bandas.

El jueves (Japón) pasó de **ocho** bandas con horarios irregulares…

```
16:00 Tokyo Ska Paradise Orchestra   19:40 My Hair Is Bad
16:55 Shonen Knife                   20:35 Sakanaction
17:50 Unicorn                        21:40 Nightmare
18:45 Capsule                        22:50 One OK Rock
```

…a **cinco** con los horarios estándar del resto de días (18:00 / 19:10 / 20:20 / 21:35 / 22:55):

```
18:00 Capsule   19:10 Coldrain   20:20 Denki Groove   21:35 Pierrot   22:55 Greenmachine
```

Y aquí está el regalo: **la primera y la última banda del nuevo jueves son de la misma ciudad**
(Capsule y Greenmachine, ambas de Kanazawa). El recorrido **se cierra sobre sí mismo**. El glifo
japonés pasa de ser un polígono ambiguo a un **bucle cerrado inequívoco: una O**.

O sea, la "nota de última hora" no era sabor narrativo: era una **fe de erratas**. El autor detectó
que su jueves original se leía mal y lo rehízo para fijar una letra. Cuando en mitad de un CTF el
autor toca un reto, lo que ha tocado es exactamente donde estaba el problema.

Y queda la tercera región, la mayor en área, que no vimos hasta repasar el diff en frío después
del concurso: en el cartel corregido **el campo UBICACION y su trozo de cinta desaparecen del
pie**, y el texto de apertura queda centrado. Justo el elemento que veníamos usando como ancla de
que la respuesta era un lugar. Quien descargara el cartel después del cambio no llegó a ver nunca
esa pista; nosotros la teníamos porque habíamos guardado el original.

## 7. Callejón nº 3: anagramar

Y aquí perdimos la mayor parte del tiempo.

Con siete letras ambiguas y una respuesta que "es una ubicación" (el campo tapado del cartel),
la jugada evidente es enumerar lecturas y buscar topónimos. Se hizo, en cadena, y cada candidato
tenía una historia estupenda:

- **MADISON** — con {M,A,D,I,S,O,N}, el único lugar real que sale del multiset.
- **SALOMON** — releyendo dos glifos ambiguos (Islas Salomón).
- **SMÅLAND** — y esta convencía de verdad: en Småland (Suecia) se celebraba el **Hultsfred**, un
  festival mítico que quebró y desapareció. *"Lost Fest" = el festival perdido.* Encajaba con el
  título, con el flavor y con todo.
- **AMAZONS**, y una rama entera leyendo los glifos como **coordenadas** (cardinales + dígitos) que
  apuntaba a Boom (Bélgica), el pueblo de Tomorrowland, cuyo escenario principal ardió dos días
  antes del festival de 2025. Otra historia redonda.

Todas falsas. Y el patrón es incómodo: **si buscas una historia temática, siempre la encuentras.**
Con un espacio de lecturas ambiguo y el mundo entero como diccionario de topónimos, la convergencia
temática no es evidencia de nada. La señal de que algo iba mal no era que los candidatos fueran
malos, era que **fallaban en cadena**: cuando N lecturas plausibles producen cada una su candidato
único y todos caen, el problema no es que la búsqueda esté incompleta. **Falta una clave
estructural.**

Un dato lo dejaba claro y tardamos en escucharlo: leyendo los glifos **en orden de día** no había
ni un solo hit contra ningún corpus. Cero. Eso no dice "los glifos están mal leídos"; dice **"el
orden está mal"**.

## 8. La clave: el orden de lectura

Nadie dijo nunca que los siete caracteres se leyeran de lunes a domingo. Lo dimos por hecho porque
están dibujados así.

El país de cada día **no está impreso**: es algo que tú deduces. Y si es un dato derivado, puede ser
el criterio de ordenación. Ordena los siete países **alfabéticamente en castellano** y lee su glifo:

| # | País | Día | Glifo |
|---|---|---|---|
| 1 | **A**ustralia | MIE | **C** |
| 2 | **B**rasil | VIE | **A** (el "4") |
| 3 | **C**hina | MAR | **M** |
| 4 | **E**spaña | DOM | **I** (el "1") |
| 5 | **F**rancia | SAB | **N** |
| 6 | **J**apón | JUE | **O** (el cuadrado nuevo) |
| 7 | **M**éxico | LUN | **S** (el "5") |

**C · A · M · I · N · O · S = CAMINOS.**

Sin anagrama. Y lo que convierte esto en la solución y no en otra corazonada es que **resuelve las
tres ambigüedades a la vez y explica la corrección del autor**:

- Japón **tiene** que ser O — y es justo la letra que el autor rehízo el cartel para fijar.
- Fijada esa O, Australia **no** puede ser otra O (`CAMINOS` no tiene dos): su bucle abierto es una
  **C**. El jueves nuevo, de paso, te **calibra la fuente**: te enseña cómo dibuja este autor un
  círculo cerrado, y el de Australia no lo es.
- España es **I**, no L ni J.

Una hipótesis que desambigua todo sin elegir a dedo es de otra categoría que una que produce un
topónimo bonito. Y de paso explica por qué MADISON parecía tan sólido: con el jueves viejo la gente
leía **D** ahí, y `{M,A,D,I,S,O,N}` es precisamente el multiset que sale. El decoy estaba
construido.

En castellano, además — y esto no es una anécdota sino el control negativo más barato de toda la
cadena:

```python
glifo = {'Australia': 'C', 'Brasil': 'A', 'China': 'M', 'España': 'I',
         'Francia': 'N', 'Japón': 'O', 'México': 'S'}
en    = {'Australia': 'Australia', 'Brasil': 'Brazil', 'China': 'China', 'España': 'Spain',
         'Francia': 'France', 'Japón': 'Japan', 'México': 'Mexico'}
print(''.join(glifo[p] for p in sorted(glifo)))              # CAMINOS
print(''.join(glifo[p] for p in sorted(glifo, key=en.get)))  # CAMNOSI
```

El mismo mecanismo con los países en inglés escupe `CAMNOSI` — basura. Que un orden dé palabra y
el otro no demuestra que **el idioma del cartel es parte de la clave**, no un accidente de
presentación.

## 9. El formato

El candidato natural es `CAMINOS`, pero falta un paso que en este concurso es casi la norma: **leet**.

Los glifos que tienen forma de dígito **se escriben como dígito**. Brasil dibuja un 4 y España un 1;
no son "una A" y "una I" que casualmente parecen números, son las formas que el mapa produce, y así
es como las escribe el autor:

```
C4M1NOS
```

Ese es el motivo real de la ambigüedad del reto. No es que el autor dibujara mal las letras: es que
la contraseña **mezcla letras y dígitos**, y para leerla hay que aceptar la forma tal cual sale del
mapa en vez de "corregirla" a texto.

Precisión, ya puestos: por esa misma regla el zigzag de México es un **5**, así que la escritura
coherente sería `C4M1N05`; la contraseña oficial usa **S** en la última. Es una inconsistencia del
autor, y en la práctica no cambia nada, porque hay un matiz que no descubrimos hasta después: el
formulario **normaliza el leet**, así que la forma plana —y la todo-dígitos— también habrían
entrado. O sea que el paso del leet es cómo se *lee* el resultado, no una cerradura adicional — el
reto ya estaba resuelto al llegar a `CAMINOS`.

## Reproducir

**El cartel no se redistribuye aquí.** Son 11,3 MB y son obra del autor del reto, así que no los
publicamos: se bajan de `hackit.party.eus`, nivel 2 de Solve It. Los comandos de abajo asumen que
tienes las dos versiones en el directorio con estos nombres:

| Fichero | Qué es |
|---|---|
| `cartel.jpg` / `cartel_OLD.jpg` | el cartel original, 43 grupos |
| `cartel_NEW.jpg` | el corregido, 40 grupos, jueves rehecho |
| `figura_geoglifos_light.png` / `_dark.png` | los siete trazos redibujados por nosotros (§5) — esto sí se publica |
| `gen_figura_geoglifos.py` | el script que genera la figura; lleva dentro todas las coordenadas |
| `world.geo.json` | siluetas de país (johan/world.geo.json, dominio público). No siempre viaja con el repo: si falta, el propio script te dice cómo bajarlo |

La versión vieja solo se pudo comparar porque la habíamos descargado antes del cambio; una vez el
autor sustituyó el fichero, el original ya no está servido. Si empiezas ahora, del sitio sale la
versión corregida.

```bash
# confirmar el cambio y su alcance
python3 -c "
from PIL import Image; import numpy as np
A=np.array(Image.open('cartel_OLD.jpg').convert('L')).astype(int)
B=np.array(Image.open('cartel_NEW.jpg').convert('L')).astype(int)
print('pixeles distintos:', (np.abs(A-B)>30).sum())"
```

Para redibujar los glifos solo hacen falta las coordenadas de las ciudades natales y `matplotlib`,
con la corrección de aspecto de §4 — `python3 gen_figura_geoglifos.py` hace exactamente eso y
regenera la figura de §5 en sus dos temas. Es el paso donde conviene mirar el resultado con los
ojos: la diferencia entre C y O no la decide un algoritmo.

## Lo que nos llevamos

1. **Fallo en cadena = falta una clave estructural.** Cuando varias lecturas ambiguas producen cada
   una un candidato plausible y todos fallan, deja de generar candidatos. El siguiente movimiento no
   es buscar mejor, es preguntarse qué supuesto no has cuestionado.
2. **Enumera los órdenes.** El orden de lectura es un grado de libertad como cualquier otro, y aquí
   era *el* grado de libertad. Cuando un puzzle produce N símbolos, los órdenes derivables del
   enunciado (alfabético por cualquier atributo, por hora, por número de elementos) van **antes** de
   relajar la lectura de los símbolos.
3. **La convergencia temática no es evidencia.** Hultsfred y Tomorrowland eran historias reales,
   documentadas y perfectamente ajustadas al título. Y falsas las dos. Exige que la mecánica sea
   forzosa —que resuelva toda la ambigüedad sin cherry-picking—, no que el destino "mole".
4. **Cuando el autor toca el reto en vivo, ha señalado el sitio.** La corrección del jueves no era
   contenido nuevo: era el autor diciéndote dónde estaba la letra que rompía su puzzle.
5. **El leet es la norma, no la excepción.** Si un símbolo tiene forma de dígito, pruébalo como
   dígito antes de traducirlo a letra.

Sobre el proceso: este reto se resolvió con asistencia de IA, y el reparto es instructivo. La
máquina hizo bien el trabajo pesado —transcribir 40 bandas con sus horarios, barrer acrósticos y
esquemas de índice, geolocalizar, renderizar los glifos, enumerar lecturas contra diccionarios y
gazetteers completos— y fue también quien propuso la mecánica del geoglifo, que es la idea no obvia
del reto. Lo que no hizo fue frenar: pasó horas generando candidatos cada vez más ingeniosos dentro
de un marco equivocado, porque nada en el proceso obligaba a revisar el supuesto de partida. La
clave del orden alfabético salió al relanzar el análisis **en frío, con el problema crudo y sin el
historial de callejones**, sobre el cartel ya corregido. La lección no va de modelos: **el sesgo
viaja en el contexto acumulado, y la forma barata de romperlo es empezar de cero con los mismos
datos.**
