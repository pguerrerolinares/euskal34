# Solve It EE34 — Nivel 5: "Drawings in the wall"

> *"En uno de mis viajes, dentro de una cueva encontré los siguientes símbolos. ¿Me ayudas a
> descifrarlos?"*

Un PNG con tres líneas de glifos geométricos. Nada más.

La contraseña es **`MENEGROTH`**, y el título del reto la contenía desde el primer minuto — pero
eso no lo vimos hasta el final, así que lo dejamos para el final.

Dos avisos por delante, porque este writeup es distinto de los otros. El primero: **no lo cerramos
nosotros**; lo remató un compañero de equipo por una vía que aún **no hemos podido reproducir**. El
segundo: el camino que sí recorrimos tiene el hallazgo más transferible de los trece niveles, y no
es criptográfico, es de **método**. Si trabajas con agentes, la sección 3 es la única parte que
importa.

---

## 1. La transcripción

Lo primero es mecánico y salió bien: segmentar la imagen, recortar cada glifo, clusterizarlos
por similitud visual y sacar la secuencia. El resultado:

- **71 signos** en total, **25 distintos**.
- `|` = separador de palabra, `||` / `|||` = fin de frase.
- **21 palabras** repartidas en **tres líneas**.

Etiquetando los 25 signos como `S01`..`S25`, el criptograma es este:

```
L1  S01-S02 | S03-S04 | S01-S05 | S06-S07-S08-S01 | S09-S03-S01-S06-S10-S01-S05 |
    S11 | S01-S02 | S12-S08-S13-S06-S07 | S14-S07-S02 | S15-S14-S16-S02

L2  S17 | S18-S14-S01-S05 | S16-S19 | S12-S08-S13-S05 | S12-S06-S20-S08-S15-S11-S05 |
    S16-S19 | S01-S13-S04-S07-S04 | S17-S04 | S21-S05-S07-S05

L3  S22-S23-S15-S24-S05 | S09-S25-S04
```

La transcripción se verificó a fondo: distancias de píxel entre clusters para descartar que dos
formas parecidas fueran el mismo signo partido en dos (las cuatro variantes de rombo son
realmente distintas; las barras con dos y tres travesaños también). **La transcripción no era el
problema.** Merece la pena decirlo porque durante horas se sospechó de ella, y esa sospecha
—volveremos— era el síntoma de otra cosa.

## 2. El callejón largo: atacar el cifrado sin saber qué sistema es

Con 25 símbolos y 21 palabras, la lectura obvia es "sustitución monoalfabética, texto en
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
anclas se construyó una lectura parcial de las 21 palabras que **parecía sólida**: cada crib
nueva se validaba contra las anteriores (¿es compatible con la biyección? ¿respeta las letras ya
asignadas?), y como eran compatibles entre sí, el sistema se reforzaba solo.

El problema: **el texto no era castellano**. Todo el edificio era coherente internamente y falso
por completo. Y lo que hace esto tan traicionero es que el criterio de validación —"la crib nueva
encaja con las anteriores"— **es un criterio real y estaba bien aplicado**. Un conjunto de cribs
mutuamente compatibles no es evidencia de que el idioma sea el correcto; solo lo es de que las
cribs no se contradicen. Con 25 símbolos y 21 palabras hay libertad de sobra para construir
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

## 6. Lo que sí dice la estructura: la línea 3 lleva un nombre propio

Esta sección se escribió **antes** de conocer la respuesta, y es la parte del análisis que
resistió. Es medible y no depende de ninguna identificación. Contando la frecuencia de cada signo:

- **8 signos aparecen una sola vez** en todo el texto (`S10`, `S18`, `S20`, `S21`, `S22`, `S23`,
  `S24`, `S25`).
- La **línea 3 son dos palabras**, `S22-S23-S15-S24-S05` (5 signos) y `S09-S25-S04` (3 signos),
  y entre las dos **concentran 4 de esos 8**.
- La primera tiene **3 signos únicos de sus 5** — la mayor concentración de todo el criptograma,
  con diferencia.

Un bloque final construido con sílabas que no aparecen en ninguna otra parte del texto es la
firma de un **nombre propio**: usa fonemas que el resto del mensaje no necesita. Encaja con la
forma del reto — un texto que termina señalando algo, y ese algo es la respuesta.

Un detalle más: **`S05` es el signo más frecuente (8 apariciones) y aparece casi siempre en
posición final de palabra**, incluida la última palabra de la línea 3. Sea cual sea su valor, el
nombre termina en la misma sílaba que media docena de palabras del texto.

### Qué acotó esto, y qué no

Conviene separar bien los dos pasos, porque es fácil venderlos como uno solo y no lo son.

**Paso 1, semántico**: partiendo del enunciado (*"dentro de una cueva"*) se preselecciona a mano
una lista corta de topónimos de *El Silmarillion* asociados a cuevas y salas subterráneas —
**Menegroth**, **Belegost**, **Nogrod**, **Nargothrond**, **Utumno**, **Androth**. Esto es
lectura temática, no análisis.

**Paso 2, estructural**: sobre esos seis se aplica la restricción de la línea 3 —primera palabra
= **5 signos todos distintos**, es decir 5 sílabas distintas en un silabario CV—. Sobreviven
**tres**: *Menegroth* (me-ne-go-ro-th), *Belegost* y *Androth*. Se caen *Nargothrond* (pide unas
siete sílabas) y *Utumno* y *Nogrod* (cuatro o menos).

La respuesta era **Menegroth**, y estaba entre los tres.

Ahora la parte que hay que decir sin maquillar: **el filtro no redujo el corpus de El
Silmarillion a tres, redujo a tres los seis nombres que ya estábamos barajando**. Aplicando la
misma regla a medio centenar de topónimos de la obra sobreviven **dieciocho** — Almaren, Avallone,
Dorlomin, Eldamar, Estolad, Formenos, **Gondolin**, Himring, Ilmarin, **Neldoreth**, Nevrast,
Taniquetil, Tolfalas, Tumladen, Vinyamar y compañía. Y varios son tan temáticamente plausibles
como los nuestros: Gondolin es la ciudad oculta, Neldoreth el bosque de Doriath, Himring una
fortaleza.

O sea: **el recorte de verdad lo hizo la preselección semántica, no la aritmética de sílabas**, y
conviene no disfrazar lo uno de lo otro. El encuadre honesto es este:

> **La estructura te dice dónde mirar; no te dice qué es.** La distribución de hapax localizó el
> nombre propio al final del texto —eso sí es un resultado del análisis, y es barato y sólido—
> pero elegir *cuál* nombre fue trabajo de lectura temática, y ni siquiera llegó a uno.

El análisis estructural **acotó, no acertó**. Sigue mereciendo la pena por lo que cuesta: contar
frecuencias de símbolos es gratis y te dice en qué parte del criptograma está la respuesta,
aunque no tengas la clave.

## 7. El final: el título llevaba la respuesta

El reto lo cerró **un compañero de equipo**, no nosotros, y por una vía que no hemos conseguido
reproducir. Según su relato: los signos se mapean **parcialmente a algo cercano al noruego**;
como varios no tienen correspondencia uno a uno, se sustituyeron ciertas letras, y con eso el
texto encajaba. La traducción daba **una frase de *El Silmarillion* referida a una cueva**, y el
nombre de esa cueva era la contraseña:

```
MENEGROTH
```

**Menegroth** son *"las Mil Cavernas"*: el reino subterráneo de Thingol en Doriath, excavado en
la roca por los enanos de Belegost. Y ahora la parte que duele, verificada contra el texto de
Tolkien:

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

### Lo que sigue sin cerrar

Sabemos el destino, no el camino. **Seguimos sin poder reproducir el paso signos → noruego →
frase de *El Silmarillion***, y esa parte continúa siendo testimonio de segunda mano sin
evidencia en nuestro material. En particular, no sabemos si esa vía era la intended o un atajo
afortunado, ni cómo encajan con ella los valores silábicos del elamita lineal (sección 5).

El organizador publica writeups oficiales al cabo de unos días. Cuando salga el de este nivel,
cerrará ese hueco.

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
L2 = [[17],[18,14,1,5],[16,19],[12,8,13,5],[12,6,20,8,15,11,5],[16,19],[1,13,4,7,4],[17,4],[21,5,7,5]]
L3 = [[22,23,15,24,5],[9,25,4]]

W = L1 + L2 + L3
c = Counter(s for w in W for s in w)
hapax = {s for s, n in c.items() if n == 1}
print(len(W), 'palabras,', sum(c.values()), 'signos,', len(c), 'distintos')
print('hapax:', sorted(hapax))                                  # 8 signos
print('hapax en L3:', [s for w in L3 for s in w if s in hapax])  # 4 de los 8
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
   elegir.** Contar hapax señaló dónde estaba el nombre propio sin descifrar una sola palabra.
   Quedarse con tres candidatos ya no fue mérito suyo, sino de la lectura temática; no confundas
   los dos pasos ni le atribuyas a la aritmética un recorte que hizo la semántica.

Sobre el proceso: este reto se atacó con asistencia de IA de forma intensiva, y es el ejemplo
más claro de la serie de que **más cómputo no arregla un modelo equivocado del problema**. Toda
la potencia se fue en criptoanálisis cada vez más sofisticado sobre una premisa falsa; lo que
movió la aguja fueron dos intervenciones humanas baratísimas: convertir los glifos a SVG (arreglar
el canal) y arrastrar la imagen a un buscador visual (identificar el sistema). Una segunda
instancia en frío, con contexto limpio, tampoco desbloqueó: siguió una lectura silábica elamita
literal que no cerraba, porque compartía la premisa de que la solución era descifrable desde el
propio texto. Y el cierre real lo puso un compañero, por un camino que aún no sabemos reproducir.

El reto acabó cayendo, así que sí es un writeup de victoria — pero de una victoria repartida y
con la lección al revés de lo que uno esperaría: **el trabajo caro no sirvió y las dos cosas que
funcionaron fueron gratis** (cambiar el formato del dato, y leer el título).
