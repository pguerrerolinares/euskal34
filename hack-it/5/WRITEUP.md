# Hack It EE34 — Nivel 5: "Game Failez"

> *"Encontré el repro de un videojuego famoso en AliExpress pero no funciona como esperaba…"*

El asset es `sonic.md`: 262.144 bytes que no son markdown, sino una **ROM de Sega Mega Drive**
(SGDK, header `SEGA MEGA DRIVE` en 0x100, región `JUE`). Hay que sacar una **contraseña de 8
letras A–Z**.

Spoiler para quien solo venga a por eso: **`MYMEGAPW`**. Lo interesante es cómo se llega, y
sobre todo el rato largo que pasamos convencidos de que el reto era imposible.

---

## 1. Primer contacto: buscar el sitio donde se compara

La ROM son 256 KB de código 68000 y gráficos comprimidos, entropía alta por todas partes. Nada
de flags a simple vista. Pero un `strings` deja un literal muy claro:

```
0x779c: PASSWORD
```

Buscamos quién lo referencia:

```
0x440e: 4879 0000 779c      pea  $779c
```

Eso cae dentro de la función que arranca en `0x43f0`, que **pinta** la pantalla: empuja las
coordenadas y el puntero a `PASSWORD`, llama a la rutina de texto y luego lee los ocho slots de RAM
con `lea $e0ff0000,a4`. El buffer de la contraseña vive en **`0xFF0000`**, 8 bytes.

Quien la **valida** es otra función. En `0x5cd0`:

```
005cd0: 4bfa be2a       lea  $1afc(pc),a5      ; <- la rutina de validación
005cd4: 45f9 e0ff0000   lea  $e0ff0000.l,a2    ; <- el buffer de la password
...
005d4a: 4e95            jsr  (a5)
005d4c: 23fc ...        move.l #$c0000000,$c00004.l   ; escribe al VDP (color)
005d56: 4a00            tst.b d0
005d58: 665e            bne.b $5db8            ; d0 != 0  ->  camino de éxito
```

Ahí mismo se ve la mecánica de la pantalla: el cursor vive en `$FF059E` y se mueve con
`addq.b #1,d0; andi.b #7,d0` — módulo 8, las ocho posiciones.

Así que todo el reto está en `0x1afc`. Y ahí no hay ningún `strcmp`.

## 2. La sorpresa: dentro de la ROM hay un intérprete de Brainfuck

La rutina de `0x1afc` empieza limpiando una zona de RAM, y ese prólogo ya te da el tamaño de la
cinta sin tener que suponerlo:

```
001b02: 41f9 e0ff05a0   lea    $e0ff05a0.l,a0
001b08: 4298            clr.l  (a0)+            ; 0x50 bytes en longs...
001b0a: b1fc e0ff05f0   cmpa.l #$e0ff05f0,a0
001b10: 66f6            bne.b  $1b08
001b12: 4279 e0ff05f0   clr.w  $e0ff05f0.l      ; ...y 2 bytes más
```

`0x05a0`–`0x05f1` = **0x52 bytes**. La cinta tiene 82 celdas, ni una más.

…y luego entra en un bucle que lee bytes de `a0 = 0x79c6`, los pasa por una tabla de traducción
en `a1 = 0x78c6` y despacha sobre el valor traducido. Ocho opcodes. Punteros que suben y bajan.
Una cinta de bytes en RAM.

Es un **intérprete de Brainfuck**, y el "programa" son 206.758 bytes escondidos a plena vista
entre lo que parecía tile data.

La tabla de 256 entradas es la ofuscación: mapea cada byte del programa a un opcode canónico, y
tiene **9 valores distintos** — ocho opcodes más un NOP. Cada símbolo de BF tiene **8 codificaciones
distintas** en la ROM, así que el programa no se parece a Brainfuck ni por asomo hasta que aplicas
la tabla:

| Valor traducido | Símbolo |
|---|---|
| `0x80` | `>` |
| `0xcf` | `<` |
| `0xd9` | `+` |
| `0xcc` | `-` |
| `0xc2` | `,` |
| `0x62` | `[` |
| `0x05` | `]` |
| `0x23` | `#` |

Extraerlo es un pegote de diez líneas:

```python
rom   = open('sonic.md','rb').read()
TABLE = rom[0x78c6:0x78c6+256]
raw   = rom[0x79c6:0x79c6+0x327a6]          # 0x327a6 = 206758
M = {0x80:'>', 0xcf:'<', 0xd9:'+', 0xcc:'-', 0xc2:',', 0x62:'[', 0x05:']', 0x23:'#'}
prog = ''.join(M.get(TABLE[b], '') for b in raw)
open('prog.bf','w').write(prog)
```

Lo que sale: 206.758 comandos, **8 `,`**, **7 `#`** y **6.126 pares de corchetes**.

El opcode extra, `#`, es el que no existe en Brainfuck estándar y es el que cierra el reto. Su
handler está en `0x1b54`:

```
001b54: 0282 0000 00ff   andi.l #$ff,d2
        41f9 e0ff 05a0   lea    $e0ff05a0,a0     ; base de la cinta
        0c30 004f        cmpi.b #$4f,(a0,d2.w)   ; ¿la celda vale 'O'?
        57c0             seq    d0               ; d0 = 0xFF si sí, 0x00 si no
```

O sea: **`#` = `return celda[dp] == 0x4F`**, y retorna de la rutina inmediatamente. El primer `#`
que se ejecute decide el resultado. `'O'` de "OK".

## 3. Instrumentar antes que nada

Con esto ya se puede escribir un intérprete fiel, y es lo primero que hay que hacer: sin un
oráculo local no puedes probar ninguna hipótesis, y con 206 KB de BF ninguna hipótesis se sostiene
leyendo.

La semántica hay que sacarla del desensamblado, no suponerla. Los puntos que importan:

- **Cinta de 0x52 celdas** (índices 0..0x51) en `0xFF05A0`, bytes, inicializadas a cero.
- **`dp` acotado** al rango de la cinta: no hay wraparound ni cinta infinita. (Spoiler de la
  sección 5: da igual, el programa nunca sale de 0..0x51 y el clamp jamás dispara.)
- Aritmética de celda **mod 256**.
- **`,`** lee el i-ésimo carácter del buffer de `0xFF0000` (i = 0..7); a partir del noveno mete 0.
  Detrás de cada `,` el programa hace **65 `-`** seguidos, que normalizan `'A'`(0x41) → 0 …
  `'Z'`(0x5a) → 25.
- **`[` / `]`**: matching estándar por profundidad. Hay dos escáneres, y conviene leerlos porque un
  matching no estándar te invalidaría todo lo demás: **`0x1cf4` avanza** (`addq.l #1,d3`) y
  **`0x1c42` retrocede** (`subq.l #1,d3`). Los dos arrancan un contador a 1, recorren el programa
  traduciendo cada byte por la tabla de `0x78c6` y comparan contra `#$62` (`[`) y `#$5` (`]`).
  Profundidad clásica, sin sorpresas.
- **`#`**: lo de arriba.

Cincuenta líneas de Python y ya tienes un oráculo. Y con el oráculo, la primera medición:

```
run(b'AAAAAAAA') -> primer '#' ve 0x4e ('N')
```

`0x4e` es `'N'`. Un valor por debajo del `0x4f` que hace falta. Y cambiar un carácter cualquiera
no lo mueve.

## 4. El callejón: "esto es inganable"

Aquí es donde el reto nos ganó unas cuantas horas, y creemos que es la parte más útil del writeup.

Se ejecutaron **5.000 entradas aleatorias** A–Z. Todas dieron `0x4e`. También full-range 0..255.
Siempre `0x4e`. Instrumentando la cinta se veía que la entrada **sí** se procesaba —los estados
intermedios diferían entre `'A...'` y `'Z...'`— pero justo antes de la decisión final las celdas
relevantes valían lo mismo para todo el mundo.

De ahí salió la conclusión, escrita con todas las letras: *el check es independiente de la entrada,
ningún password puede ganar el juego*. Y encajaba **perfectamente** con el enunciado: "Game Failez",
"no funciona como esperaba". El bootleg roto que no valida nada. Una lectura preciosa.

Peor todavía: se encontró el "smoking gun" que lo explicaba. En la cola del programa aparece este
patrón repetido:

```
>*69 [-] + <*68 [ >*68 [-] <*68 [-] ] >*68 [ < [-] > [-] ] [-] + ...
```

El bucle `[ >*N [-] <*N [-] ]` pone a cero **las dos** celdas, la actual y la de N a la derecha.
Se interpretó como un "move destructivo": una comparación que en vez de restar borra los dos
operandos y, por tanto, destruye el hash de la entrada antes de compararlo. Un bug del autor. El
chiste del reto.

**Todo eso era falso.** Dos errores encadenados:

**Uno, el estadístico.** 5.000 muestras no dicen nada sobre un espacio efectivo de ~2⁶⁴. La
probabilidad de que un muestreo aleatorio acierte un check de 64 bits es indistinguible de cero;
"5.000 intentos fallidos" es exactamente el resultado que esperas tanto si el checker está roto
como si está perfecto. **El experimento no discriminaba entre las dos hipótesis**, así que no era
evidencia de ninguna. Un muestreo aleatorio nunca prueba una ausencia.

**Dos, el de lectura.** `[ >*N [-] <*N [-] ]` no es un move roto: es el **idiom compilado estándar
de `if (x) { y = 0; }`**. El bucle se entra solo si la celda actual es distinta de cero, pone a cero
la de destino y luego se pone a cero a sí misma para salir. Encadenando esos bloques con celdas
preseteadas a 1 se construyen NOT y AND lógicos, que es exactamente lo que necesita un checker que
compara 32 bits y combina los resultados. Lo que parecía un bug era el compilador de BF haciendo su
trabajo.

La corrección llegó al lanzar una **segunda instancia del modelo en frío**, sin el contexto
contaminado del análisis previo, con acceso a los mismos ficheros y al mismo dump. Sin el marco
"esto está roto" heredado, fue directa a descompilar la cola y a validar el instrumento en vez de
a confirmar la teoría. Merece la pena anotarlo tal cual: cuando dos análisis parten del mismo dato
sesgado, el consenso entre ellos no valida nada; lo que rompe el bloqueo es un análisis que **no
comparte el marco**.

## 5. La palanca: `dp` es resoluble estáticamente

En un programa de Brainfuck normal no sabes en qué celda estás sin ejecutarlo: el puntero depende
del flujo. Aquí no, y esta es la observación que convierte el problema en tratable.

Recorriendo el programa y llevando la cuenta del desplazamiento, **los 6.126 bucles tienen
desplazamiento neto cero**: el `dp` a la entrada de cada `[` es el mismo que a la salida de su `]`.
Eso es la firma de código **generado por un compilador**, que asigna variables a celdas fijas y
deja el puntero donde lo encontró.

Consecuencia: se puede calcular el `dp` de **cada uno de los 206.758 comandos** con una única
pasada lineal, sin ejecutar nada.

```python
dp, dpat, stack, bad = 0, [0]*len(bf), [], []
for i, c in enumerate(bf):
    dpat[i] = dp
    if   c == '>': dp += 1
    elif c == '<': dp -= 1
    elif c == '[': stack.append((i, dp))
    elif c == ']':
        j, d0 = stack.pop()
        if d0 != dp: bad.append((j, i))     # -> queda vacía
```

`bad` sale vacía y el rango de `dpat` es exactamente **0..0x51**. Dos regalos: el clamp de la ROM
**nunca dispara** (así que el intérprete "acotado" y el "infinito" son el mismo programa, y toda la
línea de investigación sobre si el clamp era el bug queda cerrada), y ahora se puede **descompilar
con números de celda absolutos**:

```
$ python3 bfdis.py 206325 206460
206328 c80  c80 +1
206332 c77  while c77:          <- el gate
206335 c79    c79 +1
206337 c80    c80 -1
206341 c77    while c77:
206342 c77      c77 -1
206343 c77    endw(c77)
206344 c77  endw(c77)
206347 c79  while c79:          <- camino de exito
206350 c81    while c81:
206351 c81      c81 -1
206352 c81    endw(c81)         <- c81 = 0
206353 c81    c81 +79
206432 c81    #  (c81)          <- ve 0x4f = 'O'  -> PASA
206433 c81    c81 -4
206437 c81    #  (c81)
```

De leer un río de `>>>><<<<+++` se pasa a leer un programa con variables. A partir de aquí el reto
es ingeniería inversa normal.

## 6. La estructura real del check

Con el desensamblador de celdas absolutas, la cola del programa (`198045..206347`) se lee de un
tirón: es una cadena de comparaciones sobre `c0..c31` más una condición extra sobre `c44`,
compilada como un `&&` gigante.

Extrayendo mecánicamente qué celda toca cada eslabón sale el vector de requisitos: 32 celdas que
deben valer cero o no-cero según un patrón fijo,

```
10111001001101111011101001101101   =  0xB937BA6D
```

y `c44` que debe ser distinta de cero. 33 condiciones en total.

Y el remate del programa, con celdas ya legibles:

- gate en `206332`: `if c77 { c79 = 1; c80 = 0 }`
- `block1` = `[` 206347 … `]` 206512 — si `c79 != 0`: escribe `+79` = `'O'` y el `#` **pasa**.
- `block2` = `[` 206514 … `]` 206678 — escribe `+78` = `'N'`, y su primer `#` **falla**.

Los siete `#` del programa van escribiendo los caracteres del veredicto. Dejando correr la ejecución
más allá del primero, el programa literalmente **imprime su resultado**:

```
MYMEGAPW -> b'OK\n'
AAAAAAAA -> b'NOK\n'
```

### El corazón del reto: la re-siembra

Midiendo qué caracteres influyen en esos 32 bits aparece algo desconcertante: **los caracteres 0–3
no afectan al hash**. Solo importan el 4 al 7. Parece que el autor tiró media contraseña a la basura.

No: hay una **re-siembra** escondida en la cola larga del bloque del cuarto carácter (`src
103292..103434`). El programa funciona en dos mitades independientes:

1. Estado de 32 bits, un bit por celda en `c0..c31`, sembrado con **`0x9D9EEC79`** (la constante
   embebida al principio del programa como `[-]` / `[-]+`). Se mezclan los caracteres **0–3** y se
   compara bit a bit contra **`0xD2EECDC7`**; el booleano se aparca en **`c44`**.
2. El estado se **reinicializa a `0xE6679056`**, se mezclan los caracteres **4–7** y se compara
   contra **`0xB937BA6D`**, con resultado en `c77`.
3. `c44` se pliega dentro de `c77` en el último eslabón de la cadena (`206204`).

**OK ⟺ `c44 && c77`.**

Las cuatro constantes no hay que creérselas: se leen del propio `prog.bf` parando la ejecución en el
punto adecuado y volcando `c0..c31`. Y de paso, la misma medición demuestra la separabilidad mejor
que cualquier explicación:

```
                  estado en 94736      estado en 197901
                  (mitad 1)            (mitad 2)            c44
MYMEGAPW          0xD2EECDC7           0xB937BA6D            1
MYMEAAAA          0xD2EECDC7           0x3889C54B            1
AAAAGAPW          0x8F36C537           0xB937BA6D            0
AAAAAAAA          0x8F36C537           0x3889C54B            0
```

Lee las columnas: el estado en `94736` **solo** depende de los caracteres 0–3, y el de `197901`
**solo** de los 4–7. `c44` se enciende exactamente cuando los cuatro primeros son `MYME`, pase lo que
pase con el resto. La prueba redonda es cambiar un único carácter del final:

```
MYMEGAPW -> primer # = 0x4f   c44=1
MYMEGAPX -> primer # = 0x4e   c44=1     <- la primera mitad sigue validando
AAAAAAAA -> primer # = 0x4e   c44=0
```

`MYMEGAPX` falla, pero falla **con la bandera de la primera mitad puesta**. Las dos mitades ni se
miran.

Eso explica las dos cosas raras. Los caracteres 0–3 "no influyen" porque su efecto se resume en un
único bit (`c44`) antes de que el estado se borre, y el vector de 32 bits que ves al final solo
depende de la segunda mitad. Y, sobre todo:

**el espacio de búsqueda no es 26⁸ = 208.827.064.576, son dos espacios de 26⁴ = 456.976.**

Un autor que quiere un crackme duro no parte la clave en dos mitades independientes. Esta es la
grieta del diseño, y estaba escondida detrás de una re-siembra que solo se ve descompilando.

## 7. Validar el instrumento antes de creerse su negativo

Antes de gastar cómputo, conviene comprobar que el vector de requisitos es correcto. La prueba es
directa: **inyectarlo en la cinta** en el punto justo anterior a la cadena de comparación (`src
197901`) y ver qué opina el programa.

```python
# vm2.run(inp, inject=(197901, {celda: valor, ...}))
```

- Forzando el vector completo: el primer `#` ve **`0x4f`**.
- Volteando **cualquiera** de las 33 condiciones: **`0x4e`**.

Esto vale por dos: confirma que la cadena está bien leída **y** —lo que más falta hacía después del
callejón de la sección 4— demuestra que la cadena de comparación **funciona correctamente**. El
checker nunca estuvo roto.

La regla que nos llevamos: **un instrumento que no has validado contra un positivo conocido no
produce evidencia de nada**, y menos evidencia negativa. Si no tienes un positivo, fabrícalo e
inyéctalo.

## 8. La búsqueda

Con las dos mitades separadas, la fuerza bruta es trivial. Dos detalles de implementación que la
hacen cómoda:

- **IR comprimido**: colapsar las carreras de `>`/`<` y `+`/`-` en operaciones únicas reduce el
  programa de 206.758 comandos a **35.033 ops**. Una ejecución completa baja a **~1–2 ms**.
- **VM reanudable**: el estado en el quinto `,` (`src 103443`) no depende de los caracteres 4–7, así
  que se calcula **un snapshot una sola vez** y cada candidato de la segunda mitad arranca desde
  ahí, en vez de reejecutar el programa entero.

Y el criterio de parada de cada mitad, que no necesita llegar al final:

- mitad 1: caracteres 0–3, se comprueba `c44 != 0` en el punto de la re-siembra;
- mitad 2: caracteres 4–7, se comprueban `c0..c31` contra `0xB937BA6D` justo antes de la cadena.

```
$ python3 search.py 2      # caracteres 4-7
HITS: ['GAPW']             # ~70 s, 8 procesos

$ python3 search.py 1      # caracteres 0-3
HITS: ['MYME']             # ~110 s
```

**Un único hit en cada mitad**, sobre el espacio completo. No es una heurística ni un candidato
mejor rankeado: es exhaustivo, así que la solución es **única**.

## 9. La contraseña

```
MYMEGAPW
```

"MY MEGA PW". Un chiste de Mega Drive, que es la confirmación blanda de que has dado con la
intended y no con una colisión.

Verificación final contra el intérprete, sin parchear nada:

```
MYMEGAPW -> 0x4f  ('O')  -> "OK\n"
AAAAAAAA -> 0x4e
ZZZZZZZZ -> 0x4e
MYMEGAPV -> 0x4e          # un carácter cambiado, segunda mitad
NYMEGAPW -> 0x4e          # un carácter cambiado, primera mitad
```

---

## Reproducir

Todo el instrumental está en este directorio. Solo necesita Python 3 de serie; la única dependencia
externa es `capstone`, y únicamente para `m68dis.py`.

**La ROM no se redistribuye aquí** — es una ROM comercial de Mega Drive y no es nuestra. `sonic.md`
se descarga del propio reto (Hack It EE34, nivel 5, en `hackit.party.eus`) y se deja junto a los
scripts. Para comprobar que tienes el mismo binario con el que salen todos los números de este
writeup:

```
262144 bytes
md5     de5b80bdb0d5a7db76cf471dd97c852b
sha256  8850fb05ac98ea0e3849783071b2ff0ed11273ffd6eff1bca2a8bec3c6327e44
```

**Y otros dos ficheros no vienen hechos: los generas tú**, en este orden: `prog.bf` (paso 1 de
abajo, sale de la ROM) y `dpat.pkl` (lo escribe `dpmap.py`). El resto los da por hechos: `bfdis.py`
y `chain.py` fallan si no has corrido antes `dpmap.py`.

| Fichero | Qué hace | Necesita |
|---|---|---|
| `m68dis.py` | Desensamblador m68k con capstone: `python m68dis.py sonic.md 0x1afc 0x200` | la ROM |
| `bf.py` | Intérprete BF de referencia, ingenuo y fiel al m68k | `prog.bf` |
| `dpmap.py` | Resolución estática de `dp`; comprueba que los 6.126 bucles son net-zero, y escribe `dpat.pkl` | `prog.bf` |
| `bfdis.py` | Descompilador con celdas absolutas: `python bfdis.py 206300 206700` | `dpat.pkl` |
| `chain.py` | Extrae la cadena de comparación de la cola | `dpat.pkl` |
| `vm.py` | VM con IR comprimido (35.033 ops) | `prog.bf` |
| `vm2.py` | VM con inyección en cinta, para validar el vector de requisitos | `prog.bf` |
| `probe.py` | Sondeo de influencia por posición de carácter | `prog.bf` |
| `search.py` | Fuerza bruta paralela de las dos mitades: `python search.py 1\|2` | `prog.bf` |

```bash
# 1. extraer el BF de la ROM (reproduce prog.bf byte a byte)
python3 -c "
rom=open('sonic.md','rb').read()
T=rom[0x78c6:0x78c6+256]; raw=rom[0x79c6:0x79c6+0x327a6]
M={0x80:'>',0xcf:'<',0xd9:'+',0xcc:'-',0xc2:',',0x62:'[',0x05:']',0x23:'#'}
open('prog.bf','w').write(''.join(M.get(T[b],'') for b in raw))"

# 2. resolver dp estáticamente -> escribe dpat.pkl, que necesitan bfdis.py y chain.py
python3 dpmap.py          # -> unbalanced loops: 0 / dp range 0 81

# 3. verificar la contraseña
python3 -c "import vm; print(hex(vm.run(b'MYMEGAPW')[1]))"   # -> 0x4f

# 4. derivar las cuatro constantes desde prog.bf (nada de fiarse del writeup)
python3 -c "
import vm2
h=lambda t:'0x%08X'%int(''.join('1' if t[i] else '0' for i in range(32)),2)
for src,q in [(155,'siembra'),(103443,'re-siembra'),(94736,'target mitad 1'),(197901,'target mitad 2')]:
    print('%-16s %s' % (q, h(vm2.run(b'MYMEGAPW', snap=src)[1][0])))"
# siembra          0x9D9EEC79
# re-siembra       0xE6679056
# target mitad 1   0xD2EECDC7
# target mitad 2   0xB937BA6D
```

## Lo que nos llevamos

1. **Instrumenta antes de teorizar.** El intérprete fiel, validado contra el desensamblado, es lo
   que convierte 206 KB de ruido en algo sobre lo que se puede experimentar.
2. **El muestreo aleatorio no prueba ausencia.** 5.000 entradas sobre un espacio de 2⁶⁴ dan el mismo
   resultado con un checker roto que con uno perfecto. Si tu experimento no distingue entre las dos
   hipótesis que te importan, no es evidencia: es ruido con formato de conclusión.
3. **Desconfía de la hipótesis que encaja demasiado bien con el enunciado.** "Game Failez" +
   "no funciona como esperaba" nos empujó a *querer* que el crackme estuviera roto, y una vez
   querido, apareció el bug que lo demostraba. La coincidencia temática no es evidencia mecánica.
4. **Busca la propiedad estructural que hace el problema tratable.** Aquí fue el desplazamiento neto
   cero: una pasada lineal que convierte Brainfuck en un lenguaje con variables.
5. **Valida el instrumento contra un positivo conocido**, aunque tengas que fabricarlo e inyectarlo.

Sobre el proceso: este reto se resolvió con asistencia de IA de principio a fin, y el reparto fue
desigual a propósito. El trabajo de reversing —localizar el validador, reconocer el intérprete,
extraer el programa, verificar la semántica contra el m68k— se hizo en una sesión larga que acabó
con un diagnóstico equivocado. Lo que lo desbloqueó fue lanzar una segunda instancia en frío sobre
el mismo material, sin heredar el marco "el checker está roto". Diagnosticó la cascada de errores,
descompiló la cola y cerró el reto por fuerza bruta exhaustiva. La lección no es sobre modelos, es
sobre marcos: **el sesgo viaja en el contexto, y la forma barata de romperlo es un analista que no
lo comparta.**
