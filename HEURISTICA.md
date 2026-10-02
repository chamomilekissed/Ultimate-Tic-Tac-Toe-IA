# Cómo funciona la función heurística (`evaluador.py`)

Este documento explica en detalle cómo `evaluar_posicion()` decide qué tan
buena es una posición del tablero, componente por componente, con ejemplos
numéricos reales. Está pensado para quien necesite entender, defender o
seguir ajustando la heurística — incluyendo la historia de un bug real que
encontramos y cómo se corrigió.

Código fuente: [`evaluador.py`](evaluador.py). Pesos: [`config.py`](config.py).

---

## 1. Por qué existe una heurística

Minimax necesita un valor numérico para **cada posición donde deja de
buscar** (cuando `profundidad` llega a 0 en `minimax.py`), porque no puede
explorar la partida completa hasta el final en el tiempo disponible. Ahí es
donde entra `evaluar_posicion()`: en vez de "no sé quién va ganando",
calcula una estimación basada en patrones conocidos (amenazas, control de
posiciones clave, etc.) — el mismo tipo de heurísticas que usaría un
jugador humano para "sentir" que una posición es buena, sin calcular hasta
el final.

Cuando la posición **sí** es terminal (alguien ya ganó, o hay empate),
minimax nunca necesita la heurística — usa el valor exacto. Esto importa
para entender la sección 3.

---

## 2. Convención de signos: perspectiva absoluta de X

Esta es la decisión de diseño más importante de todo el módulo, y la que
más fácil se malinterpreta:

> **`evaluar_posicion()` siempre retorna el valor desde la perspectiva de
> X.** Positivo = le conviene a X. Negativo = le conviene a O. Esto es
> cierto **sin importar de quién es el turno, ni quién está "preguntando"**.

El parámetro `es_maximizando` (`True` si le toca mover a X) **no invierte
el signo**. Solo se usa para saber de quién es el turno en el componente de
`evaluar_amenaza_destino` (sección 4.6). Esto es distinto de la convención
"negamax" (donde cada nodo devuelve el valor desde la perspectiva de quien
mueve ahí, y se le cambia el signo al subir en la recursión) — aquí **no**
se le cambia el signo a nada.

**Por qué importa:** cuando la búsqueda de **O** reporta un valor cercano a
`+9990`, NO es un error de signo — significa que la propia búsqueda de O
concluyó que X tiene una victoria casi asegurada, sin importar lo que O
haga.

Rango de valores: `[VALOR_PERDEDOR, VALOR_GANADOR]` = `[-10000, +10000]`
(`config.py`).

---

## 3. Los casos terminales y su relación con `minimax.py`

Antes de calcular cualquier componente, `evaluar_posicion()` revisa si el
juego ya terminó:

```python
ganador = tablero.detectar_ganador_meta()
if ganador == JUGADOR_X:
    return VALOR_GANADOR        # +10000
if ganador == JUGADOR_O:
    return VALOR_PERDEDOR       # -10000
if tablero.verificar_empate():
    return VALOR_EMPATE         # 0
```

**Detalle importante que no es obvio leyendo solo este archivo:** cuando
`evaluar_posicion()` se llama *desde* `minimax()` (el caso normal durante
la búsqueda), este chequeo **nunca se llega a disparar**, porque
`minimax()` ya revisó exactamente lo mismo un poco antes, en su propio
código:

```python
# minimax.py
ganador = tablero.detectar_ganador_meta()
if ganador == JUGADOR_X:
    return VALOR_GANADOR - nivel   # ajustado por profundidad
if ganador == JUGADOR_O:
    return VALOR_PERDEDOR + nivel
if tablero.verificar_empate():
    return VALOR_EMPATE
...
if profundidad == 0:
    valor = ev.evaluar_posicion(tablero, es_maximizando, tablero_destino)
```

Si `minimax()` ya hubiera detectado que el juego terminó, habría retornado
ahí mismo — nunca llega a llamar a `evaluar_posicion()`. Así que el chequeo
terminal *dentro* de `evaluar_posicion()` es efectivamente una capa de
seguridad redundante para cuando la función se llama **directamente**, sin
pasar por `minimax()` — por ejemplo en los tests (`tests/test_gato_de_gatos.py`) o en
scripts de diagnóstico. Ahí sí importa, porque nadie más filtró el caso
terminal antes.

También explica por qué `evaluar_posicion()` retorna `VALOR_GANADOR` plano
(10000) mientras que `minimax()` usa `VALOR_GANADOR - nivel`: el ajuste por
`nivel` (para preferir ganar rápido) es responsabilidad de `minimax.py`, no
del evaluador — el evaluador no tiene ningún concepto de "a qué profundidad
de la búsqueda estamos".

---

## 4. Los componentes, uno por uno

Todos comparten una pieza base:

### 4.0 `contar_2_en_linea` — el bloque constructor

```python
def contar_2_en_linea(tablero_3x3, jugador):
    conteo = 0
    for linea in LINEAS_MINI_TABLERO:          # las 8 líneas de un 3x3
        valores = [tablero_3x3[f][c] for f, c in linea]
        if valores.count(jugador) == 2 and valores.count(None) == 1:
            conteo += 1
    return conteo
```

Cuenta cuántas de las 8 líneas (3 filas + 3 columnas + 2 diagonales) tienen
**exactamente** 2 marcas del jugador y la tercera casilla vacía — es decir,
amenazas de completar 3-en-línea en la próxima jugada ahí. Funciona tanto
para un mini-tablero como para el meta-tablero completo, porque ambos usan
la misma disposición de 8 líneas (`LINEAS_MINI_TABLERO` en `config.py`).

Ejemplo: mini-tablero
```
X . X
. O .
. . O
```
`contar_2_en_linea(mini, 'X')` → la fila superior tiene `X . X` (2 X, 1
vacía) → cuenta 1. La diagonal `X O O`... no, eso tiene una O, no cuenta.
Resultado: **1**.

---

### 4.1 `evaluar_progreso_meta` — peso `PESO_PROGRESO_META_TABLERO = 10`

**Pregunta que responde:** ¿quién está más cerca de ganar el meta-tablero
completo (3 campos en línea)?

```python
amenazas_x = contar_2_en_linea(tablero.meta_tablero, JUGADOR_X)
amenazas_o = contar_2_en_linea(tablero.meta_tablero, JUGADOR_O)
return amenazas_x - amenazas_o
```

Aplica `contar_2_en_linea` directamente sobre `meta_tablero` (donde cada
"casilla" es un campo A-I con valor `'X'`, `'O'`, `'EMPATE'` o `None`).
Nota que `'EMPATE'` no es `None`, así que un campo empatado **bloquea**
esa línea para ambos jugadores (no cuenta como amenaza de nadie) — es el
comportamiento correcto: una línea con un campo empatado nunca se puede
completar.

Es el peso más alto de los siete porque una amenaza a nivel meta-tablero es
lo más cerca que se puede estar de ganar el juego entero sin haberlo
ganado ya.

**Limitación conocida:** solo cuenta amenazas de "2 campos en línea, falta
el tercero" — no da ningún crédito por simplemente *poseer* campos que
todavía no forman una amenaza de línea. Ganar el primer campo del juego no
mueve este componente en absoluto (0 antes, 0 después), todo el crédito
por esa primera victoria viene de `evaluar_control_posiciones` (4.4). Es un
candidato razonable para una mejora futura (ver sección 9).

---

### 4.2 `evaluar_bifurcaciones` — peso `PESO_AMENAZAS_BIFURCACIONES = 7`

**Pregunta que responde:** ¿hay algún mini-tablero donde un jugador tenga
**2 o más** amenazas de 2-en-línea simultáneas (una bifurcación / fork)?

```python
for cada mini-tablero (los 9):
    amenazas_x = contar_2_en_linea(mini, 'X')
    amenazas_o = contar_2_en_linea(mini, 'O')
    if amenazas_x >= 2: puntuacion += amenazas_x
    if amenazas_o >= 2: puntuacion -= amenazas_o
```

Una bifurcación es especialmente peligrosa porque el rival solo puede
bloquear **una** de las dos amenazas en su turno — la otra queda libre. El
umbral `>= 2` es literalmente la definición de bifurcación: una sola
amenaza (1) no cuenta aquí (para eso está `evaluar_defensa`, 4.3).

**Recorre los 9 mini-tableros, incluyendo los ya decididos** — este detalle
tiene una historia (ver sección 8).

---

### 4.3 `evaluar_defensa` — peso `PESO_DEFENSA_CRITICA = 6`

**Pregunta que responde:** sumando TODO el peligro disperso en cualquier
mini-tablero (no solo donde se concentra en bifurcaciones), ¿quién tiene
más amenazas activas en total?

```python
amenazas_x_total += contar_2_en_linea(mini, 'X')   # para cada uno de los 9
amenazas_o_total += contar_2_en_linea(mini, 'O')
return amenazas_x_total - amenazas_o_total
```

La diferencia con `evaluar_bifurcaciones` (4.2) es el umbral: aquí **toda**
amenaza cuenta, aunque sea una sola por mini-tablero, y no hay bonus extra
por concentración. Son complementarios: bifurcaciones premia *concentrar*
amenazas en un solo tablero (fork), defensa premia *tener* amenazas en
cualquier lado (peligro disperso). Una posición con 4 mini-tableros
distintos con 1 amenaza cada uno puntúa alto en `evaluar_defensa` pero cero
en `evaluar_bifurcaciones` (ningún tablero individual llega a 2).

---

### 4.4 `evaluar_control_posiciones` — peso `PESO_POSICIONES_CLAVE = 7`

**Pregunta que responde:** de los campos del meta-tablero que ya se
decidieron, ¿quién controla los más valiosos?

```python
for cada campo del meta-tablero:
    if valor == 'X': puntuacion += IMPORTANCIA_CAMPO[campo]
    elif valor == 'O': puntuacion -= IMPORTANCIA_CAMPO[campo]
```

`IMPORTANCIA_CAMPO` (`config.py`) refleja que el centro vale más que una
esquina, y una esquina más que un borde — igual que en tic-tac-toe normal:

| Campo | A (esq.) | B (borde) | C (esq.) | D (borde) | E (centro) | F (borde) | G (esq.) | H (borde) | I (esq.) |
|---|---|---|---|---|---|---|---|---|---|
| Importancia | 3 | 2 | 3 | 2 | **4** | 2 | 3 | 2 | 3 |

A diferencia de los componentes 4.2/4.3/4.5, este **no** usa
`contar_2_en_linea` — solo mira `meta_tablero` directamente, así que es
indiferente a si el campo se ganó con una línea limpia o al filo del
alambre.

---

### 4.5 `evaluar_mini_tableros` — peso `PESO_CONTROL_LOCAL = 3`

**Pregunta que responde:** en cada uno de los 9 mini-tableros, ¿quién tiene
más material (casillas ocupadas) y más amenazas locales?

```python
for cada uno de los 9 mini-tableros:
    casillas_x = # de casillas 'X' en ese mini-tablero
    casillas_o = # de casillas 'O'
    amenazas_x = contar_2_en_linea(mini, 'X')
    amenazas_o = contar_2_en_linea(mini, 'O')
    puntuacion += (casillas_x - casillas_o) + (amenazas_x - amenazas_o)
```

Es el componente más "de grano fino": no le importa si una amenaza es
parte de una bifurcación o no, ni la importancia estratégica del campo —
solo material y amenazas locales, sumados en bruto por todo el tablero. Es
también el de menor peso, porque esta señal es más ruidosa/menos decisiva
que las demás (mucho material en un mini-tablero sin importancia
estratégica no gana la partida).

---

### 4.6 `evaluar_amenaza_destino` — peso `PESO_AMENAZA_DESTINO = 8`

**Pregunta que responde:** el mini-tablero al que el jugador en turno está
obligado a jugar (`tablero_destino`) — ¿es un regalo o una trampa?

```python
def evaluar_amenaza_destino(tablero, tablero_destino, jugador_actual):
    oponente = el otro jugador

    if tablero_destino is None or ya está decidido:
        return 1   # libertad de elegir cualquier mini-tablero: pequeño bono

    mini = ese mini-tablero
    amenazas_propias = contar_2_en_linea(mini, jugador_actual)
    amenazas_rivales = contar_2_en_linea(mini, oponente)
    return amenazas_propias - amenazas_rivales
```

Este es el componente más nuevo y el único que depende de `tablero_destino`
(el mini-tablero obligatorio para quien mueve). Es la regla táctica central
de Ultimate Tic-Tac-Toe: tu jugada determina a qué campo mandas al rival, y
mandarlo a un campo donde ya tiene una amenaza lista es regalarle una
jugada. Antes de este componente, la heurística no tenía **ninguna** señal
sobre "a dónde estoy mandando al rival" — solo evaluaba el tablero en sí.

**Detalle de implementación:** la función retorna el valor en perspectiva
de `jugador_actual` (quien debe mover), no en perspectiva de X. Por eso
`evaluar_posicion()` lo convierte antes de sumarlo:

```python
amenaza_destino_propia = evaluar_amenaza_destino(tablero, tablero_destino, jugador_actual)
amenaza_destino = amenaza_destino_propia if jugador_actual == JUGADOR_X else -amenaza_destino_propia
```

Si es a X a quien mandan a un campo peligroso, el valor ya viene negativo
(malo para X) y se usa tal cual. Si es a O a quien mandan a un campo
peligroso, la función retorna un valor *positivo* (bueno para O, en su
propia perspectiva) que hay que voltear a negativo antes de sumarlo a la
perspectiva absoluta de X.

**Nota sobre `None`:** cuando `evaluar_posicion()` se llama sin pasar
`tablero_destino` (su valor por defecto), este componente simplemente
contribuye la "libertad" de valor 1, sin ninguna información real. Esto
pasa en los tests y en llamadas directas — dentro de la búsqueda real
(`minimax.py`), siempre se pasa el `tablero_destino` correcto.

---

### 4.7 `evaluar_amenaza_destino_futura` — peso `PESO_AMENAZA_DESTINO_FUTURA = 4`

**Pregunta que responde:** un nivel más allá de 4.6 — de las casillas que
`jugador_actual` podría jugar en el mini-tablero obligatorio, ¿a dónde
mandaría cada una al rival, y qué tan peligroso es *ese* campo para él?

Esto nació directamente de una limitación que quedó documentada en la
primera versión de este archivo (sección 9): `evaluar_amenaza_destino` solo
mira el mini-tablero inmediato, sin preguntarse "si mando al rival aquí,
¿a dónde me manda él a mí después?".

```python
if tablero_destino es None o ya decidido: return 0
mini = ese mini-tablero
if contar_2_en_linea(mini, jugador_actual) > 0:
    return 0   # hay una victoria inmediata ahí — tomarla domina, no hace falta ver más allá

casillas_vacias = casillas libres de `mini`
peligros_para_rival = []
for cada (fila, col) en casillas_vacias:
    if el campo (fila, col) ya está cerrado:
        peligro = 1  # el rival obtiene libertad para elegir cualquier campo
    else:
        siguiente = tablero.obtener_mini_tablero(fila, col)   # esa es la CLAVE:
        # la posición (fila, col) DENTRO del mini-tablero actual es la
        # misma coordenada que el CAMPO al que se manda al rival — es
        # la regla del tablero obligatorio, aplicada un nivel hacia adelante
        peligro = contar_2_en_linea(siguiente, oponente) - contar_2_en_linea(siguiente, jugador_actual)
    peligros_para_rival.append(peligro)

mejor_para_jugador_actual = min(peligros_para_rival)   # jugador_actual elegiría
                                                         # la casilla que MENOS le
                                                         # convenga al rival
return -mejor_para_jugador_actual
```

**El truco de implementación** es que no hace falta simular el movimiento
con `aplicar_movimiento`/`deshacer_movimiento` para saber a qué campo manda
cada casilla candidata — la posición `(fila, col)` *dentro* del mini-tablero
actual **es literalmente** la coordenada del campo siguiente en el
meta-tablero (la misma regla que ya usan `tablero.py` y `main.py` para
calcular `tablero_destino` después de cada jugada real). Eso hace que esta
función sea barata: un tablero más por casilla candidata (hasta 9), sin
ninguna recursión de búsqueda de verdad.

**Por qué se corta si ya hay una victoria inmediata:** si `jugador_actual`
puede ganar el mini-tablero obligatorio ahora mismo, va a tomar esa jugada
casi siempre (el premio directo, vía `evaluar_control_posiciones` y
`evaluar_progreso_meta`, es mucho mayor que cualquier consideración sobre a
dónde manda al rival después) — así que este componente no intenta
"convencer" a la heurística de lo contrario.

**Peso menor que el nivel inmediato (4 contra 8):** es una señal más
especulativa — asume que `jugador_actual` jugaría exactamente la casilla
"óptima para el destino" sin considerar ningún otro factor táctico de esa
casilla en sí misma. El peso más bajo refleja esa menor certeza, siguiendo
el mismo principio que `PESO_CONTROL_LOCAL` (la señal más "de grano fino"
tiene el peso más chico).

**Ejemplo:** X debe jugar en el Campo E. O ya tiene una amenaza armada
tanto en el Campo A como en el Campo B. Si las **únicas** casillas vacías
que le quedan a X en el Campo E son `a` (manda a O al Campo A) y `b` (manda
a O al Campo B) — X está atrapado sin importar qué juegue:

```
Campo E: . . X / O O X / X O O      (solo 'a' y 'b' siguen vacías)
```

```
[evaluar_posicion] ... | amenaza_destino=-2 (x8=-16) | amenaza_destino_futura=-1 (x4=-4)
```

`amenaza_destino_futura=-1` porque, de las dos casillas disponibles,
**ambas** mandan a O a un campo donde ya tiene una amenaza (peligro=1 para
cada una) — no hay ninguna casilla "segura" entre las candidatas, así que
`mejor_para_jugador_actual = min(1, 1) = 1`, y el resultado es `-1`.

---

## 5. Cómo se combinan los componentes

```python
componentes = [
    ("progreso_meta",       progreso,        PESO_PROGRESO_META_TABLERO),   # 10
    ("bifurcaciones",       bifurcaciones,   PESO_AMENAZAS_BIFURCACIONES),  # 7
    ("defensa",             defensa,         PESO_DEFENSA_CRITICA),        # 6
    ("control_posiciones",  control,         PESO_POSICIONES_CLAVE),       # 7
    ("mini_tableros",       mini,            PESO_CONTROL_LOCAL),          # 3
    ("amenaza_destino",       amenaza_destino, PESO_AMENAZA_DESTINO),         # 8
    ("amenaza_destino_futura", amenaza_futura, PESO_AMENAZA_DESTINO_FUTURA), # 4
]
puntuacion = sum(crudo * peso for _, crudo, peso in componentes)
```

Suma ponderada simple: cada componente calcula un número "crudo" (con
signo, en perspectiva absoluta de X), se multiplica por su peso, y se
suman los siete resultados.

| # | Componente | Qué mide | Peso actual |
|---|---|---|---|
| 1 | `evaluar_progreso_meta` | Amenazas de línea a nivel **meta**-tablero | 10 |
| 2 | `evaluar_bifurcaciones` | Mini-tableros con 2+ amenazas simultáneas | 7 |
| 3 | `evaluar_defensa` | Amenazas totales dispersas en todos los mini-tableros | 6 |
| 4 | `evaluar_control_posiciones` | Campos ganados × `IMPORTANCIA_CAMPO` | 7 |
| 5 | `evaluar_mini_tableros` | Material + amenazas locales por mini-tablero | 3 |
| 6 | `evaluar_amenaza_destino` | ¿El destino forzado es un regalo o una trampa? | 8 |
| 7 | `evaluar_amenaza_destino_futura` | Un nivel más: ¿a dónde mandaría yo al rival después? | 4 |

Los pesos no salieron de una fórmula — se calibraron a mano a partir de
partidas reales (ver siguiente sección), y siguen siendo candidatos a
ajuste sistemático (ver sección 9).

---

## 6. Ejemplo completo paso a paso

Tomado de una posición real analizada en `Case Study/Juego 1.md`: X está a
punto de completar el Campo E (el centro) con la jugada `Eg`, contra la
alternativa `Ec` (que no gana nada). Con los pesos **actuales**:

**Jugada `Ec` (X no gana nada):**

| Componente | Crudo | × Peso | Subtotal |
|---|---|---|---|
| progreso_meta | 0 | ×10 | 0 |
| bifurcaciones | -2 | ×7 | -14 |
| defensa | 1 | ×6 | 6 |
| control_posiciones | 0 | ×7 | 0 |
| mini_tableros | 2 | ×3 | 6 |
| amenaza_destino | 0 | ×8 | 0 (sin `tablero_destino` en este ejemplo) |
| amenaza_destino_futura | 0 | ×4 | 0 (idem) |
| **TOTAL** | | | **-2** |

**Jugada `Eg` (X gana el Campo E, el centro):**

| Componente | Crudo | × Peso | Subtotal |
|---|---|---|---|
| progreso_meta | 0 | ×10 | 0 |
| bifurcaciones | -4 | ×7 | -28 |
| defensa | 0 | ×6 | 0 |
| control_posiciones | **4** | ×7 | **28** |
| mini_tableros | 1 | ×3 | 3 |
| amenaza_destino | 0 | ×8 | 0 |
| amenaza_destino_futura | 0 | ×4 | 0 |
| **TOTAL** | | | **3** |

`control_posiciones` sube de 0 a 4 (peso 7 = +28) porque X pasa a controlar
el campo de mayor `IMPORTANCIA_CAMPO` (el centro, vale 4). `bifurcaciones`
baja porque, al completarse la línea ganadora, esa línea ya no cuenta como
"amenaza" (tiene 3 marcas, no 2+vacía) y el mini-tablero de E deja de
aportar amenazas nuevas. El resultado neto (+3 contra -2) confirma que
`Eg` es la jugada mejor evaluada — como debe ser, dado que gana un campo.

Puedes reproducir este ejemplo exacto (y verificar que no se rompa en el
futuro) con:

```bash
python3 "Case Study/regresion_juego1_campo_e.py"
```

---

## 7. Modo debug

`evaluar_posicion(tablero, es_maximizando, tablero_destino=None, debug=True)`
imprime el desglose completo antes de retornar:

```
[evaluar_posicion] progreso_meta=0 (x10=0) | bifurcaciones=-4 (x7=-28) | defensa=0 (x6=0) | control_posiciones=4 (x7=28) | mini_tableros=1 (x3=3) | amenaza_destino=0 (x8=0) | amenaza_destino_futura=0 (x4=0)
[evaluar_posicion] TOTAL = 3
```

**Nunca se activa dentro de la búsqueda real** (`minimax()` llama a
`evaluar_posicion()` sin este flag) — con miles de llamadas por jugada,
imprimir cada una inundaría la terminal y haría la búsqueda mucho más
lenta. Es una herramienta exclusivamente para diagnóstico manual: reconstruir
una posición específica y ver exactamente qué está "pensando" el evaluador
ahí, como se hizo en `Case Study/Juego 1.md` y `Juego 2.md`.

---

## 8. Un bug real que tuvo esta heurística

Durante el análisis de `Juego 1.md`, encontramos que `evaluar_bifurcaciones`,
`evaluar_defensa` y `evaluar_mini_tableros` **excluían** los mini-tableros
ya decididos (`if not tablero.es_mini_tablero_disponible(...): continue`).
El resultado: en el instante en que un jugador **completaba** la victoria
de un mini-tablero, esos tres componentes perdían de golpe toda la señal de
dominio local que ese tablero aportaba — y la única compensación
(`evaluar_control_posiciones`) no alcanzaba a cubrir la pérdida. Con los
pesos de ese momento, `evaluar_posicion` literalmente puntuaba **ganar** un
mini-tablero peor que dejarlo a medio terminar (`Eg` daba -20 contra -2 de
`Ec`, cuando debería ser al revés).

La corrección fue simple una vez identificada: dejar de excluir los
mini-tableros decididos (ganar un tablero no borra su contenido real, solo
fija `meta_tablero`), y subir `PESO_POSICIONES_CLAVE` de 5 a 7 para que la
señal de "poseer" un campo importante pese lo suficiente. El ejemplo de la
sección 6 usa los valores **después** de este fix. Detalle completo en
`Case Study/Juego 1.md`.

---

## 9. Limitaciones conocidas / posibles mejoras futuras

- **Los pesos se calibraron a mano**, a partir de un puñado de partidas
  analizadas caso por caso, no con una búsqueda sistemática. `torneo.py`
  existe justamente para poder comparar variantes de pesos con datos de
  muchas partidas en vez de anécdotas.
- **`evaluar_progreso_meta` no premia poseer campos por sí solo** — solo
  reacciona cuando ya hay 2 campos en línea a nivel meta. Ganar el primer
  campo del juego no mueve este componente (ver sección 4.1).
- Los componentes 4.2/4.3/4.5 recorren los 9 mini-tableros con lógica
  parecida (tres bucles separados en vez de uno combinado) — funciona
  correctamente y cada uno tiene una semántica distinta, pero hay
  duplicación de iteración que se podría consolidar sin cambiar el
  resultado.
