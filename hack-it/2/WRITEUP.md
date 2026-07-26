# Hack It EE34 — Nivel 2: "Bowling Physics"

Este writeup es raro, y por eso merece la pena: **todo el trabajo técnico que hicimos fue
irrelevante para la solución**. Caracterizamos el dataset hasta residuo cero, encontramos un bug
del generador, corregimos un error de método propio… y la contraseña era un juego de palabras que
se leía en el título del reto.

Va entero igual, porque los dos hallazgos técnicos son transferibles y porque la lección de marco
—cuándo dejar de analizar— es más cara que cualquiera de ellos.

Contraseña: **`M4dF0rmUL4`**.

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

## 6. El callejón: el payload no era un payload

Con el modelo cerrado y las bandas aisladas, quedaba extraer el mensaje. No lo hay.

Las cuatro bandas son **exceso de varianza**, no de media: filas donde el generador metió más ruido.
El contenido es de máxima entropía y resiste todo lo que se le eche encima, porque **es exactamente
lo que parece**: ruido. No hay mensaje escondido en un canal de alta entropía continuo; hay la
firma del generador del autor, o los restos de algo que su propio pipeline destruyó.

Lo que hicimos mal no fue el análisis —el modelo es correcto y verificable— sino no haber tenido
nunca un criterio para **parar**. Un payload de alta entropía que no cede ante ningún decode es,
casi siempre, ruido; y la probabilidad de que lo sea sube con cada hora que le dedicas sin sacar un
solo bit estructurado.

## 7. La solución estaba en el título

`p`, `v`, y una `m` que el autor comentó para que la echaras de menos. Son los tres ingredientes de
**una fórmula**. El reto se llama *Bowling Physics* y el nivel entero es un chiste sobre eso.

```
M4dF0rmUL4          =  "Mad Formula"
```

Dos cosas que convierten esto en algo reproducible y no en un golpe de suerte:

**El leet es la norma de la casa.** En esta misma edición: `C4M1NOS`, `4roM4Noc7urNo`, `h0LyGr4IL`,
`t4pF1gHtINg1nINmELEEiSLAND`. Si en este concurso te sale un candidato-frase, la forma en que se
envía es **en leet**, con mayúsculas intercaladas. Generar la variante leet de cada candidato
temático debería ser automático, no una ocurrencia.

**El dataset barroco era decoración.** 65.536 partículas, un flujo de Hubble, cuatro bandas
regulares y un texto en un lenguaje esotérico: todo eso es *flavor* alrededor de un concepto. El
error de marco fue tratar el dato como algo **a decodificar** en vez de como **atrezzo de una idea**.

> **Regla**: en un reto con nombre temático fuerte y assets que resisten todos los decodes, prueba
> la hipótesis "los assets son decoración de una frase temática" **en paralelo** a la de extracción,
> no después de agotarla. Cuesta cinco minutos y compite de tú a tú con horas de estadística.

## 8. Reproducir

```bash
python3 model.py          # modelo completo + las 4 bandas + comprobaciones de residuo cero
python3 png16.py p.png    # (256, 256, 3) uint16
```

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
