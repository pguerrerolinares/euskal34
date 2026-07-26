# Solve It EE34 — Nivel 3: "Retro Shell"

Este reto no tiene fichero. Tiene un **servicio vivo**: un emulador de terminal en el navegador
que habla por WebSocket contra `hackit.party.eus:7826`.

Spoiler: **`t4pF1gHtINg1nINmELEEiSLAND`** — leet de *"tap fighting in Melee Island"*. Es un reto
corto y el error que cometimos también lo es, pero es de los que más se repiten: **descartar el
canal correcto por confundir el ruido de tu propia medición con la respuesta del servidor.**

---

## 1. El cliente oficial está capado a propósito

Antes de tocar el servicio, lee su cliente. `app.js` cabe en una pantalla y lo dice todo:

```js
function sendTap() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(' ');
    }
}

window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' || e.key === ' ') {
        e.preventDefault();
        sendTap();
    }
});
```

El único evento que existe es la **barra espaciadora**, y lo único que se manda por el socket es un
carácter: `' '`. No hay campo de texto, no hay `Enter`, no hay nada más. La página recibe y
concatena; no interpreta.

Esto es una decisión de diseño, no una limitación. **Cuando el cliente oficial de un reto está
restringido a un único tipo de input, ese canal es el mecanismo.** Anótalo y vuelve a leerlo dentro
de un rato.

Para conectarse desde Python hay un detalle: el servidor **valida `Origin`** y devuelve 403 sin él.

```python
import asyncio, websockets
async def main():
    hdrs = {"Origin": "http://hackit.party.eus:7826"}
    async with websockets.connect("ws://hackit.party.eus:7826/ws",
                                  additional_headers=hdrs) as ws:
        ...
```

## 2. Lo que emite el servidor

Nada más conectar:

```
EE34 HAL terminal

You have the manners of a beggar.
>
```

"HAL terminal" apunta a *2001*. Pero la frase no: **es un insulto de Monkey Island**. Recolectando
banners a lo largo de varias conexiones salen 24 distintos, y son el pool canónico del duelo de
insultos a espada del primer juego:

```
"If your brother is like you, better to marry a pig."
"Soon you'll be wearing my sword like a shish kebab!"
"No one will ever catch ME fighting as badly as you do."
"There are no clever moves that can help you now."
```

Dentro de una misma conexión el insulto es **fijo**. Cambia entre conexiones.

La lectura que se impone sola: *HAL te insulta, tú tienes que responder con la réplica correcta*.

## 3. El callejón: el duelo de insultos es decoy

Se atacó por ahí a fondo, y conviene contar cómo se descarta bien, porque el servidor **no te lo
pone fácil**.

Se montó el mapeo canónico de los 16 buckets insulto→réplica y se mandaron las réplicas correctas.
Respuesta: `?`. Se probó que el problema fuera de transcripción (el servidor puede tener su propia
puntuación), así que se generaron variantes de cada réplica con y sin `.`/`!`/`?` —unas ochenta
cadenas en total, `brute.py`— y se mandaron sobre el insulto fijo de una conexión. Todas: `?`. Se
probaron terminadores de línea: sin nada, `\n`, `\r\n`, `\r`. Todas: `?`.

La conclusión correcta es fuerte y hay que sacarla explícitamente: **el servidor nunca hace
string-match**. `?` no significa "réplica incorrecta"; significa *"input no reconocido"*, y lo
devuelve para cualquier texto. El tema —los insultos, el Sword Master, HAL— es la **carcasa**. No
hay nada que teclear.

Un aviso de método: el pool de 24 insultos se recolectó abriendo conexiones sucesivas, y las pruebas
de réplicas fueron unas decenas de cadenas contra un servicio de concurso. Eso es sondeo de
protocolo, no fuerza bruta: no hay diccionario, ni paralelismo, ni intento de agotar un espacio. Es
la diferencia entre caracterizar un servicio y castigarlo.

## 4. El error que costó el reto

En mitad del callejón anterior se probó lo obvio —mandar **espacios**, como hace el cliente
oficial— y el servidor **respondió distinto**: en vez de `?`, salió una `a`.

Y acto seguido lo descartamos.

Por qué: al mandar espacios en ráfaga (300 taps a 0.05 s) el servidor devolvió `?`. Al mandarlos con
pausas largas, también `?`. Como la `a` no se reproducía a voluntad, se anotó como **anomalía** y se
volvió al brute-force de texto. Se perdieron quince minutos y se estuvo a punto de perder el reto
entero.

El fallo no es de hipótesis, es de instrumentación. `?` es la respuesta del servidor a **dos** cosas
distintas —input inválido *y* ritmo incorrecto— y nosotros solo teníamos un modelo con un
significado. Cuando tu instrumento devuelve el mismo síntoma para dos causas, **un negativo no es
evidencia de nada**. Y el `?` del flood era ruido de nuestra propia sonda: éramos nosotros
rompiendo la medición, no el servidor diciendo "por aquí no".

## 5. La mecánica: el ritmo

Basta con barrer la cadencia. Dos sondas idénticas salvo por el intervalo entre taps, y sus logs
están en este directorio:

**`rawtap.py` — un tap cada 2.0 s** (`rawtap.log`):

```
  0.00 [T] 'EE34 HAL terminal\r\n'
  0.00 [T] '\r\nYou have the manners of a beggar.\r\n> '
  2.56 [T] '?'
  4.56 [T] '?'
  6.57 [T] '?'
  8.57 [T] '?'
```

**`slowtap.py` — un tap cada 1.0 s** (`slowtap.log`):

```
  0.00 'EE34 HAL terminal\r\n'
  0.00 '\r\nIf your brother is like you, better to marry a pig.\r\n> '
  2.46 'a'
  3.21 ' '
  4.47 'a'
  5.22 ' '
  6.48 'a'
  7.23 ' '
  ...
```

A **2 segundos** el servidor rechaza. A **1 segundo** acepta y responde, de forma sostenida y
estable, durante todo el minuto que dura la sonda. Y en flood, rechaza también.

O sea: hay una **ventana de cadencia**. Ni rápido ni lento: al tempo. El servidor está midiendo el
ritmo de tus pulsaciones y te dice si lo mantienes.

Y ahí encaja todo hacia atrás. El duelo de insultos de Monkey Island no era el puzzle, era la
**pista sobre el método**: esto es un *tap fight*. La contraseña lo dice literalmente —*tap
fighting in Melee Island*—: el mecanismo estaba en el **cómo** (pulsar al ritmo), no en el **qué**
(el tema de los insultos). El título tampoco mentía: "Retro Shell", una shell que solo entiende
pulsaciones.

## 6. Lo que no podemos reproducir

Aquí toca ser explícitos, porque el writeup se queda sin final limpio.

**No llegamos a extraer la contraseña del servicio.** Caracterizamos el canal, encontramos la
ventana de ritmo y llegamos a la hipótesis correcta ("esto es un watchdog de cadencia"), pero la
contraseña la cerró un humano del equipo por su cuenta, fuera de las sondas que hay en este
directorio, y el servicio ya no está en pie para volver a intentarlo.

Lo que **sí** está verificado y se puede comprobar en los logs adjuntos: el cliente solo manda
espacios, el servidor no hace string-match, `?` es el rechazo genérico, y la cadencia de ~1 s
produce respuesta sostenida mientras que 2 s y el flood no. Lo que **no** podemos documentar es la
condición exacta de victoria: cuántos taps hay que sostener, con qué tolerancia, y si la contraseña
se emite carácter a carácter por el socket o aparece de otra forma. Preferimos decirlo a inventar
un final coherente.

## Reproducir

| Fichero | Qué hace |
|---|---|
| `app.js`, `page.html`, `style.css` | el cliente oficial, tal cual se sirve |
| `tap.py` | conexión básica con lector concurrente; taps espaciados 0.4 s |
| `slowtap.py` | `python slowtap.py <n_taps> <gap>` — la sonda que encuentra la ventana |
| `rawtap.py` | igual pero fijo a 2.0 s, para contrastar |
| `synctap.py` | taps sincronizados con el eco del servidor |
| `duel.py` | el solver del duelo de insultos (el callejón) |
| `brute.py` | las ~80 variantes de réplica (el callejón) |
| `*.log`, `*_dump.txt` | las capturas de todo lo anterior |

```bash
python3 slowtap.py 60 1.0     # -> 'a' sostenida
python3 slowtap.py 60 2.0     # -> '?' siempre
```

Los comandos apuntan al servicio del concurso, que ya no está en pie. Los logs adjuntos son las
capturas originales, así que el contraste de cadencias se puede leer sin volver a tocar nada.

## Lo que nos llevamos

1. **Si el cliente oficial está capado a un solo tipo de input, ese canal es el mecanismo.** No es
   una pista sutil: es el autor cerrándote todas las puertas menos una.
2. **Un instrumento que devuelve el mismo error para dos causas distintas no produce evidencia
   negativa.** Antes de descartar una vía porque "da error", comprueba que sabes distinguir *tu*
   error del suyo.
3. **Una observación que no sabes reproducir no es una anomalía: es una hipótesis sin barrer.** La
   `a` apareció, no supimos repetirla y la archivamos. El movimiento correcto ante un resultado
   irreproducible es barrer el parámetro que no controlas —aquí, el tiempo—, no volver a lo anterior.
4. **La pista suele nombrar el método, no el tema.** "Retro Shell" + *tap* pesaban más que los
   insultos, y los insultos eran justo el señuelo que hacía costoso el camino equivocado.

Sobre el proceso: el reto se trabajó con asistencia de IA. La máquina fue rápida y buena en lo
mecánico —leer `app.js`, resolver el 403 del `Origin`, montar sondas asíncronas con lector
concurrente, recolectar el pool de banners, reconocer Monkey Island y construir el mapeo canónico— y
llegó a la hipótesis correcta del ritmo. Lo que hizo mal fue tratar un resultado irreproducible como
descartado en vez de como pendiente, y eso le costó volver al callejón dos veces. El cierre lo puso
una persona. Un patrón que se repite trabajando así: **el asistente sondea mucho más rápido de lo
que un humano puede, y precisamente por eso genera más ruido de medición del que sabe interpretar.**
