# Hack It EE34 — Nivel 4: "Embedded secret"

> *"Un secreto incrustado."*

El nivel no trae fichero: trae un servicio. En la página, una propiedad CSS inválida
metida a mano en un `<dd>` —`port: 55432;`— y un usuario que se llama `vecwarden`. Eso es
todo lo que hay que ver para empezar: hay un **PostgreSQL** escuchando en el puerto 55432, y
el nombre de usuario es un guiño a Vaultwarden (una bóveda de contraseñas). Hay que sacar una
contraseña que se escribe en el formulario del reto.

Spoiler: **`TheEagleSeesTheForest`**. Y como en casi todos los buenos retos, lo que más
enseña es el rato largo que pasamos **declarando que la respuesta no existía** — teniéndola ya
generada en el disco.

---

## 1. Entrar: pageinspect sobre tablas con las filas borradas

Conectando con las credenciales dadas hay una tabla `candidates`: **65.908 filas**, cada una
un string tipo contraseña (`shadow`, `matrix`, `letmein`, gibberish `ojudekixaw`…) y un
**embedding** de 128 dimensiones (`pgvector`). 65.908 agujas idénticas: es el pajar. Volveremos
a él en la sección 3 para enterrarlo.

La puerta real aparece mirando el catálogo. El autor **redefinió `get_raw_page`** (la función
de la extensión `pageinspect`) como un wrapper que solo deja leer dos relaciones:

```sql
-- get_raw_page redefinida por el autor
IF relname NOT IN ('maintenance.idx_rebuild_log', 'maintenance.meta') THEN
    RAISE EXCEPTION 'permission denied';
```

`SELECT` directo sobre el esquema `maintenance` da *permission denied*, pero el wrapper deja
leer sus **páginas en crudo**. Y ahí está el truco: las dos tablas tienen las filas **borradas**
(tuplas muertas), invisibles a `SELECT` pero recuperables de la página física.

`heap_page_item_attrs`/`tuple_data_split` exigen superusuario (bloqueado), pero `heap_page_items`
—que el wrapper sí expone— devuelve el `t_data` crudo. Se parsea a mano:

- `maintenance.meta` → **una** tupla muerta: `(w=400, h=90)`.
- `maintenance.idx_rebuild_log` → **400** tuplas muertas, cada una dos `int16` little-endian
  `(idx, valor)`. Los `idx` son 0..399 y los `valor` son una **permutación exacta de 0..399**.

Los nombres de columna (los da `pg_attribute`, legible aunque el esquema esté bloqueado)
rematan la lectura: `meta(w, h)` y `idx_rebuild_log(disp_c, orig_c)`. Es decir: **una imagen de
400×90 con las columnas barajadas**, y el log es el mapeo columna-mostrada → columna-original
para desbarajarla. `disp_c`/`orig_c` = "display column / original column".

**Corolario reusable**: un canal o una tabla **capados a propósito** (whitelist, filas
borradas, función redefinida) son el mecanismo, no un obstáculo. El pajar decorativo nunca se
protege así.

## 2. De dónde salen los píxeles

`meta` dice 400×90 = 36.000 píxeles. La fuente natural son los 65.908 embeddings. Proyectados a
2D por PCA, dos componentes dominan (PC1 std ≈ 116, PC2 ≈ 22.5) y el resto es suelo de ruido
isótropo: cada candidato aporta esencialmente **un punto (x, y)** y 126 dimensiones de ruido.

Y los rangos cuadran a la primera:

```
PC1 span ≈ 400   (-198.9 .. 201.1)      -> el eje x, 400 columnas
PC2 span ≈  90   ( -59.1 ..  31.4)      -> el eje y,  90 filas
```

La imagen es el **scatter PC1×PC2 binado a 400×90**, y las 400 columnas están barajadas por la
permutación de `idx_rebuild_log`. El brillo de cada píxel es la **densidad** de puntos que caen
en esa celda: los píxeles del texto tienen más puntos que el ruido de fondo.

El pipeline de reconstrucción, entonces:

1. binar los 65.908 puntos (PC1→columna, PC2→fila) → mapa de densidad 400×90;
2. **aplanar el marginal vertical** (restar el perfil medio por fila) — quitar la "hierba" del
   pajar, que es una rampa de densidad que crece hacia abajo y tapa el texto;
3. **desbarajar las columnas** con la permutación;
4. suavizar.

Suena limpio. No lo fue.

## 3. El callejón: matar la imagen que teníamos generada

Esto es lo que hay que contar entero, porque es el error caro y es reproducible en cualquier
reto.

El scatter, mirado en crudo, parece **hierba creciendo desde abajo** — un pajar temático, sin
texto a la vista. Probamos densidad a varios umbrales, ocupancia binaria, residual de Pearson,
bit de signo de los embeddings, `binary_quantize`, orden por id, orden físico (`ctid`)… todo
ruido. Se midió que PC1 es esencialmente `Uniform[0,400]` (std 115.9 = 400/√12) y PC2
`Uniform[0,90]` (std 22.5 = 90/√12): puntos uniformes en el lienzo, sin imagen en la densidad
global.

Se buscó también una segunda opinión: **una instancia del modelo en frío**, con contexto
limpio, atacó lo mismo por su cuenta. Y **convergió en el mismo veredicto**: la densidad es
**rank-1 separable** —`densidad(x,y) = f(x)·g(y)`, un gradiente puro— con un χ² de interacción
a 400×90 de **0.62** (por debajo de 1: indistinguible de ruido). De ahí salió la frase, escrita
con todas las letras: *matemáticamente imposible que haya texto en esa densidad*.

Dos errores, encadenados.

**Uno.** Para atacar la orientación correcta se generó un **set combinatorio de 8 variantes** de
la reconstrucción: signo de PC1 ∈ {+,−} × signo de PC2 ∈ {+,−} × dirección del desbarajado ∈
{A, B}. Ocho imágenes escritas a disco de una tirada. Y se **abrió una sola** —la del signo
(+,+)—, salió ruido, y se generalizó a "no hay texto". El texto estaba nítido en la variante de
signo **(−,−)**, una de las siete que nadie llegó a mirar.

**Dos.** El "proof of absence" estadístico era de baja potencia. El rank-1 mide la densidad
**global**; el texto era una **modulación débil** que solo emergía en una orientación y un
desbarajado concretos —justo los que no se abrieron—. Un test que no distingue "no hay señal"
de "hay señal débil fuera del eje que miro" no prueba una negativa. **`densidad(x,y) = f(x)·g(y)`
a nivel agregado es compatible con que haya texto local**; el promedio lo borra.

Las dos lecciones, en una frase cada una:

- **Si generas N variantes de una reconstrucción, míralas TODAS antes de concluir ausencia.**
  Muestrear una y generalizar el negativo es catastrófico, y aquí costó el reto durante horas.
- **Un test estadístico de baja potencia no prueba una negativa.** "Imposible que haya texto"
  fue exceso de confianza; la señal existía, en una orientación que el test agregado no veía.

Lo que rompió el bloqueo fue mirar la imagen que ya teníamos y no habíamos abierto. El pipeline
—aplanar la hierba, desbarajar columnas, suavizar— **era el correcto desde el principio**.

## 4. Un red herring que además estaba prohibido

Merece mención, sin dramatizar. Buscando "la aguja en el pajar" apareció en la base de datos un
rol **`bootstrap`** con `rolsuper = true` y `rolcanlogin = true`: un superusuario que acepta
login. La lectura tentadora: la aguja es la contraseña de ese superusuario, escondida entre los
65.908 candidatos, y se encuentra probándolos contra el login.

Se descartó por una razón que no es técnica: **las bases del concurso prohíben la fuerza bruta
de credenciales** (el servidor loguea cada intento y es baneable). No es una vía legítima aunque
funcionara. Y no funcionaba: el `bootstrap` era ruido, el mecanismo real (la imagen) no
necesita ningún login. La regla operativa: si una vía te lleva a martillear un oráculo, párate
y relee las bases antes que el teclado.

## 5. La contraseña

Con la variante correcta (signo (−,−), desbarajado A), aplanada y suavizada, el texto se lee sin
esfuerzo:

```
TheEagleSeesTheForest
```

"El águila ve el bosque" — el que mira desde arriba distingue la figura entre los árboles, que
es exactamente lo que había que hacer con el scatter. La confirmación blanda de que es la
intended y no una casualidad.

## Reproducir

Se necesita acceso al Postgres del reto (o un dump de `candidates` + la permutación). El esquema
del ataque, sin credenciales:

```sql
-- 1. las dos tablas 'maintenance' con filas borradas, vía el wrapper de pageinspect
SELECT * FROM heap_page_items(get_raw_page('maintenance.meta', 0));         -- -> (400, 90)
SELECT * FROM heap_page_items(get_raw_page('maintenance.idx_rebuild_log', 0));  -- -> 400 pares
-- parsear t_data a mano: dos int16 LE por tupla muerta
```

```python
# 2. reconstruir la imagen desde los embeddings (pseudocódigo)
X = emb - emb.mean(0)
U, S, Vt = np.linalg.svd(X, full_matrices=False)
pc1, pc2 = (X @ Vt.T)[:, 0], (X @ Vt.T)[:, 1]

# binar a 400x90, PROBAR LOS 4 SIGNOS y ambas direcciones de desbarajado (8 variantes)
for sx in (1, -1):
    for sy in (1, -1):
        img = densidad_2d(sx*pc1, sy*pc2, W=400, H=90)   # conteo por celda
        img = img - img.mean(0)                          # aplanar el marginal-y (la hierba)
        for direccion in ('A', 'B'):
            out = desbarajar_columnas(img, perm, direccion)
            guardar(blur(out), f'BH_{sx}{sy}_{direccion}.png')   # y MIRARLAS TODAS
# el texto está en BH_-1-1_A
```

## Lo que nos llevamos

1. **Un canal capado a propósito es el mecanismo.** Función redefinida, whitelist de dos tablas,
   filas borradas: el autor te está señalando la puerta, no cerrándola. El pajar decorativo
   (65.908 embeddings) nunca se protege así.
2. **Si generas N variantes, míralas todas antes de concluir ausencia.** Abrir una de ocho y
   generalizar el negativo es el fallo más caro del reto.
3. **Un test estadístico de baja potencia no prueba una negativa.** Rank-1 en la densidad global
   es compatible con texto local; el promedio lo borra. "Matemáticamente imposible" fue una
   conclusión que el instrumento no podía sostener.
4. **Si una vía te lleva a fuerza bruta contra un oráculo, relee las bases.** Aquí era baneable,
   y además era un señuelo.

Sobre el proceso: este reto se resolvió con asistencia de IA. El reversing de la base de datos
—descubrir el wrapper de `pageinspect`, recuperar las tuplas muertas, deducir que `meta`+
permutación son una imagen 400×90 barajada, y montar el pipeline de reconstrucción— lo hizo la
máquina, y bien. Lo que la máquina hizo mal fue **declarar la imagen muerta** con un test de
baja potencia y una sola de las ocho variantes abiertas; una segunda instancia en frío convergió
en el mismo veredicto equivocado, porque compartía el marco "rank-1 = sin texto". Lo que rompió
el bloqueo fue un humano insistiendo en mirar la imagen y abriendo la variante que faltaba. La
lección no es sobre modelos: **el consenso de dos análisis que parten del mismo marco no valida
nada**, y una negativa estadística sin potencia es solo una opinión con formato de teorema.
