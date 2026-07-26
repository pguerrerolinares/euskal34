# Solve It EE34 — Nivel 1: "Singular Calculus"

> *"Las mates no parece que se le den muy bien a Begitxo, ¿o sí?"* — por ontza

El asset es un único PNG de 800×1200. Se ve una lista de nueve sumas:

```
1 + 1 = 3
1 + 2 = ?
1 + 3 = ?
...
1 + 9 = ?
```

Solo la primera muestra resultado, y está mal. El resto son interrogantes. Hay que sacar una
contraseña.

Spoiler: **`ODDMATHS`**. Lo interesante es que el reto entero cabe en dos líneas de Python, y aun
así nos costó veinte minutos de más por empeñarnos en que tenía que ser complicado.

---

## 1. El PNG no es lo que aparenta

Lo primero, siempre, es mirar el fichero y no la imagen:

```python
from PIL import Image
import numpy as np
im = Image.open('level.png')
print(im.mode, im.size)          # LA (800, 1200)
arr = np.array(im)
print(sorted(set(arr[:,:,0].flatten())))      # [0, 1, 2, 3, 4, 5, 255]
print(len(set(arr[:,:,1].flatten())))         # 26
```

Modo **`LA`**: escala de grises **más canal alpha**. Y ahí está la anomalía que decide el reto:

- el canal **L** (el gris) toma solo **7 valores**: 0–5 y 255 (el fondo);
- el canal **alpha** toma **26 valores distintos**.

Que un canal tenga exactamente 26 niveles en un puzzle de contraseñas es demasiada coincidencia.
Descontando el 255 del fondo quedan **25 opacidades distintas** repartidas entre los glifos.

Lo que ves en pantalla es el resultado de componer ambos: como `L ≤ 5`, el gris aporta casi nada y
el aspecto de cada dígito lo fija la opacidad. Unos números se ven casi negros y otros casi
invisibles. **Esa diferencia visual es el mensaje**, no un efecto estético.

## 2. Extraer un valor por glifo

Hay que pasar de píxeles a una tabla. Cada dígito es una componente conexa de la máscara
`alpha < 255`, así que se segmenta y se toma la mediana de alpha dentro de cada una:

```python
from scipy import ndimage
arr = np.array(Image.open('level.png'))
L, A = arr[:,:,0].astype(int), arr[:,:,1].astype(int)
lab, n = ndimage.label(A < 255)
comps = []
for i, sl in enumerate(ndimage.find_objects(lab), 1):
    sel = (lab[sl] == i)
    ys, xs = sl
    comps.append(((ys.start+ys.stop)//2, (xs.start+xs.stop)//2,
                  int(np.median(A[sl][sel]))))
comps.sort()                     # ordena por fila, luego por columna
```

Dos detalles prácticos que ahorran confusión:

- El `+` y el `=` salen con **alpha = 255**, así que la máscara `A < 255` los descarta sola. Los
  únicos glifos con opacidad variable son los dígitos. Eso ya te dice dónde mirar.
- Los `?` se parten en **dos** componentes (el gancho y el punto), ambas con el mismo alpha. Hay que
  deduplicar por valor dentro de cada fila o contarás nueve operandos donde hay tres.

La tabla que sale:

| fila | izquierda | derecha | resultado |
|---|---|---|---|
| `1 + 1 = 3` | 1 | 2 | **3** |
| `1 + 2 = ?` | 210 | 61 | **15** |
| `1 + 3 = ?` | 44 | 216 | **4** |
| `1 + 4 = ?` | 41 | 219 | **4** |
| `1 + 5 = ?` | 63 | 206 | **13** |
| `1 + 6 = ?` | 67 | 190 | **1** |
| `1 + 7 = ?` | 158 | 118 | **20** |
| `1 + 8 = ?` | 162 | 102 | **8** |
| `1 + 9 = ?` | 136 | 139 | **19** |

## 3. El callejón: tratar la opacidad como un ranking

Aquí es donde perdimos el tiempo, y creemos que es la parte útil de este writeup.

Con 25 opacidades distintas y una fila de ejemplo cuyos tres glifos son justo los tres más tenues
(1, 2, 3), la lectura que se impone sola es: **ordena las 25 opacidades y numéralas A=1 … Y=25**.
Es elegante, la fila-ejemplo parece confirmarla (`A + B = C`), y produce estructura inmediatamente:

- ordenados por rango, en **cada** fila `rango(izq) + rango(der) = 35` exacto;
- los 16 operandos son **exactamente** las letras J–Y, emparejadas en espejo tipo Atbash
  (W+L, K+X, J+Y, M+V, N+U, S+P, T+O, Q+R).

Eso es una regularidad real y muy vistosa, y nos convenció de que los operandos eran relleno
estructural y el mensaje vivía solo en la columna resultado. De ahí salieron varias horas-persona
de nada:

- barridos de anagramas y órdenes de lectura contra diccionarios es/en/eu, sin un solo hit;
- el título, *"Singular"*, empujando a álgebra lineal: montar matrices 3×3 con los valores y buscar
  una **singular** (determinante cero). Nada;
- el canal L, con sus seis niveles casi invisibles, tratado como canal esteganográfico
  independiente. Se renderizó coloreado por L y no hay nada;
- metadatos del PNG (`tEXt`, cola tras `IEND`, CRCs): limpio.

Y una tentación peor, que es la que conviene señalar: con el ranking, los resultados salen
`3,7,4,4,6,1,9,5,8`, que **debería** ser una permutación de 1–9 pero le falta el 2 y le sobra un 4.
Es facilísimo contarse la historia de que ese defecto es *el punto singular* del reto. No lo era: era
un artefacto de haber elegido mal la transformación. **Una hipótesis equivocada también produce
patrones**, y cuanto más bonita es la anomalía que genera, más sospechosa debería ser.

Lo que nos sacó fue un dato de contexto, no una idea: el reto ya lo habían resuelto varios equipos,
o sea que la solución no podía ser rebuscada. Con esa cota, la respuesta aparece en dos minutos.

## 4. La lectura correcta: no hay que rankear nada

Vuelve a la tabla de la sección 2 y mira los valores crudos. En las filas 2–9:

- los operandos tienen alpha **entre 41 y 219**, todos **> 26**;
- los resultados valen **15, 4, 4, 13, 1, 20, 8, 19**, todos **≤ 26**.

Los resultados son los únicos valores del canal que caben en el alfabeto. **A1Z26 directo sobre el
alpha crudo**, sin ordenar, sin rangos:

```
15 → O    4 → D    4 → D    13 → M
 1 → A   20 → T    8 → H    19 → S
```

**`ODDMATHS`** — *odd maths*, las mates raras de Begitxo. El *"¿o sí?"* del enunciado es el remate
del chiste.

Y la fila de ejemplo encaja como leyenda: su resultado tiene **alpha 3** y el dígito dibujado es un
**3**. Te está enseñando la regla —*el alpha del resultado es el dato*— con un caso donde alpha y
dígito coinciden.

## 5. La verificación: por qué los operandos no eran decoración

Nuestra primera explicación fue "los operandos son relleno". Es falsa, y verla es lo que cierra el
reto sin residuo. Suma los alphas crudos de cada fila:

```
fila 2: 210 + 61  = 271 = 256 + 15  → O
fila 3:  44 + 216 = 260 = 256 +  4  → D
fila 4:  41 + 219 = 260 = 256 +  4  → D
fila 5:  63 + 206 = 269 = 256 + 13  → M
fila 6:  67 + 190 = 257 = 256 +  1  → A
fila 7: 158 + 118 = 276 = 256 + 20  → T
fila 8: 162 + 102 = 264 = 256 +  8  → H
fila 9: 136 + 139 = 275 = 256 + 19  → S
```

**`alpha(izq) + alpha(der) ≡ alpha(res) (mod 256)`**, exacto en las nueve filas. Y la primera fila es
el caso base sin overflow: `1 + 2 = 3`.

Ahí está el chiste completo. En pantalla las cuentas de Begitxo están mal (`1+1=3`), pero **en el
canal alpha la aritmética es perfecta**: lo que falla es que un byte se desborda. Título, flavor y
mecanismo cuadran los tres, y cada valor de la imagen tiene función: los operandos no son relleno,
son los sumandos que producen el resultado por overflow.

## 6. Reproducir

Todo el reto, de PNG a contraseña:

```python
from PIL import Image
import numpy as np
from scipy import ndimage

arr = np.array(Image.open('level.png'))
A = arr[:,:,1].astype(int)
lab, _ = ndimage.label(A < 255)
comps = []
for i, sl in enumerate(ndimage.find_objects(lab), 1):
    sel = (lab[sl] == i); ys, xs = sl
    comps.append(((ys.start+ys.stop)//2, (xs.start+xs.stop)//2, int(np.median(A[sl][sel]))))
comps.sort()

rows = []
for c in comps:                                   # agrupa en filas
    if rows and abs(c[0] - rows[-1][0][0]) < 40: rows[-1].append(c)
    else: rows.append([c])

for r in rows:
    r.sort(key=lambda t: t[1])
    vals = [c[2] for i, c in enumerate(r) if i == 0 or c[2] != r[i-1][2]]  # dedup del '?'
    l, d, s = vals
    assert (l + d) % 256 == s                     # el invariante, en las 9 filas
print(''.join(chr(64 + v) for v in [15,4,4,13,1,20,8,19]))   # ODDMATHS
```

Sobre el canal L: tiene seis niveles (0–5) y no encontramos nada en él. Los valores no son
constantes por fila ni por columna ni siguen el mensaje; es tinta casi negra con ruido de
cuantización. Lo decimos porque nos comió un rato: **que un canal tenga poca varianza no lo
convierte en un canal oculto.**

## Lo que nos llevamos

1. **Cuando descartas seis hipótesis complejas, vuelve a la simple que descartaste primero.** La
   observación buena —"el alpha tiene 26 niveles, eso es un alfabeto"— la escribimos en el minuto
   dos y la enterramos acto seguido bajo una interpretación más sofisticada. No fue un fallo de
   generación: fue un fallo de no volver.
2. **Prueba la transformación identidad antes que cualquier otra.** Ante N valores distintos ≤26 en
   un canal, A1Z26 sobre el valor **crudo** va primero; rangos, percentiles y normalizaciones
   después. Lo caro fue añadir un paso que el reto no pedía.
3. **Una hipótesis falsa también genera estructura.** El invariante suma-35 y los pares Atbash son
   reales *dentro* del ranking, y son preciosos, y no significan nada. Un patrón bonito confirma que
   tu transformación es consistente, no que sea la correcta.
4. **Cero residuo es el criterio de parada.** "Los operandos son relleno" debió sonar mal en cuanto
   lo escribimos: dieciséis valores sin función es demasiado residuo. Forzar su explicación es lo
   que destapa el `mod 256`.

Sobre el proceso: el reto se resolvió con asistencia de IA. La parte mecánica —abrir el PNG, ver el
`LA`, segmentar glifos, tabular opacidades, barrer diccionarios y descartar stego— la hizo la
máquina bien y rápido, y es trabajo que a mano lleva su rato. El desbloqueo, en cambio, fue humano y
no fue técnico: fue la observación de que otros equipos ya lo habían resuelto, luego no podía ser
complicado. Esa cota de complejidad es información real sobre el espacio de búsqueda, y vale más que
otra hora de análisis. Merece la pena tenerlo presente cuando se trabaja así: **el asistente explora
mucho más rápido, pero no sabe cuándo dejar de explorar; eso lo tienes que poner tú.**
