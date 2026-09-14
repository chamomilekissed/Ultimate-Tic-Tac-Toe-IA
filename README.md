# Gato de Gatos — Ultimate Tic-Tac-Toe con IA

Implementación en Python de Ultimate Tic-Tac-Toe (Gato de Gatos) con un jugador
artificial basado en Minimax + Poda Alfa-Beta. Soporta humano vs humano, humano
vs IA e IA vs IA.

---

## Estructura del proyecto

```
Gato/
├── config.py         Constantes globales: símbolos, tamaños, pesos del
│                      evaluador, presupuestos de tiempo, líneas de victoria
├── tablero.py         Clase Tablero: estado del juego y reglas básicas
├── movimientos.py     Generación de movimientos legales
├── evaluador.py        Función heurística multi-componente
├── minimax.py         Minimax + Alpha-Beta + Iterative Deepening
├── interfaz.py        Entrada/salida de terminal (formato "Gc")
├── main.py            Loop principal — los 3 modos de juego
├── tests_stub.py       Suite de pruebas (pytest)
└── Case Study/         Partidas jugadas, análisis de bugs y casos de regresión
```

Cada módulo se apoya únicamente en los de arriba en esta lista (`tablero.py`
no depende de nadie; `main.py` depende de todos). `config.py` es la única
fuente de constantes — ningún otro archivo hardcodea pesos, símbolos ni tamaños.

---

## Representación del estado (`tablero.py`)

La clase `Tablero` guarda:

- `mini_tableros`: lista de 9 mini-tableros 3×3 (`mini_tableros[fila_meta * 3 + col_meta]`),
  cada casilla es `'X'`, `'O'` o `None`.
- `meta_tablero`: matriz 3×3 con el resultado de cada mini-tablero — `'X'`,
  `'O'`, `'EMPATE'` o `None` (todavía en juego).
- `historial`: pila de movimientos aplicados, usada por `deshacer_movimiento()`
  para que minimax explore variaciones sin copiar el tablero en cada nodo.

Métodos clave: `aplicar_movimiento`, `deshacer_movimiento`, `obtener_ganador_mini`,
`detectar_ganador_meta`, `verificar_empate`, `es_mini_tablero_disponible`,
`copiar()` (copia profunda, sin historial) y `get_estado_hash()` (hash rápido
del estado completo, usado como clave de la Transposition Table).

### Convención de coordenadas

```
Meta-tablero (campos):     Dentro de cada mini-tablero (posiciones):
  A | B | C                  a | b | c
  D | E | F                  d | e | f
  G | H | I                  g | h | i
```

Un movimiento se escribe como dos letras, `Campo+Posición` — por ejemplo
`Gc` = jugar en el mini-tablero G, casilla c. La posición jugada determina el
mini-tablero **obligatorio** para el rival en su siguiente turno (si ese
mini-tablero ya está decidido, el rival puede jugar en cualquier mini-tablero
disponible).

---

## Generación de movimientos (`movimientos.py`)

`movimientos_validos(tablero, tablero_destino)` implementa la regla central
del juego:

- `tablero_destino is None` (primer turno) o apunta a un mini-tablero ya
  decidido → el jugador puede elegir cualquier mini-tablero disponible.
- En cualquier otro caso → solo puede jugar en ese mini-tablero.

---

## Función heurística (`evaluador.py`)

`evaluar_posicion(tablero, es_maximizando, tablero_destino=None, debug=False)`
retorna una puntuación en perspectiva absoluta de X (positivo = favorece a X,
negativo = favorece a O), en el rango `[VALOR_PERDEDOR, VALOR_GANADOR]`
(±10000). Primero revisa los casos terminales (`detectar_ganador_meta`,
`verificar_empate`); si el juego sigue, suma 6 componentes ponderados:

| Componente | Peso (`config.py`) | Qué mide |
|---|---|---|
| `evaluar_progreso_meta` | `PESO_PROGRESO_META_TABLERO` (10) | Amenazas de 2-en-línea a nivel **meta**-tablero |
| `evaluar_bifurcaciones` | `PESO_AMENAZAS_BIFURCACIONES` (7) | Mini-tableros con 2+ amenazas simultáneas (fork) |
| `evaluar_defensa` | `PESO_DEFENSA_CRITICA` (6) | Amenazas totales dispersas en todos los mini-tableros |
| `evaluar_control_posiciones` | `PESO_POSICIONES_CLAVE` (7) | Campos ya ganados, ponderados por `IMPORTANCIA_CAMPO` (centro > esquina > borde) |
| `evaluar_mini_tableros` | `PESO_CONTROL_LOCAL` (3) | Posesión local (casillas + amenazas) de cada mini-tablero |
| `evaluar_amenaza_destino` | `PESO_AMENAZA_DESTINO` (8) | ¿El mini-tablero al que se manda al rival es un regalo o una trampa? |

Con `debug=True` imprime el desglose completo (crudo y ponderado) de cada
componente — pensado para diagnóstico manual, **no** se usa dentro de la
búsqueda (inundaría la terminal y la haría mucho más lenta).

### Un bug real que encontramos y corregimos

Durante el análisis de una partida (ver `Case Study/Juego 1.md`), descubrimos
que `evaluar_bifurcaciones`, `evaluar_defensa` y `evaluar_mini_tableros`
excluían los mini-tableros ya decididos. Como resultado, **ganar** un
mini-tablero hacía que su señal de dominio local desapareciera de golpe, sin
compensación suficiente — la heurística literalmente puntuaba peor completar
una victoria que dejarla a medias. El fix (evaluar siempre los 9
mini-tableros) y el caso de regresión que lo verifica están documentados en
`Case Study/`.

---

## Búsqueda: Minimax + Alpha-Beta (`minimax.py`)

### Algoritmo base

`minimax(tablero, profundidad, alfa, beta, es_maximizando, tablero_destino, cache, nivel=0)`
es la búsqueda recursiva estándar: X maximiza, O minimiza, con poda
alfa-beta (`if beta <= alfa: break`). Como la búsqueda muta el tablero real
directamente (`aplicar_movimiento` / `deshacer_movimiento`) para no copiar
en cada nodo, cada llamada recursiva está envuelta en `try/finally` — así el
tablero siempre queda restaurado aunque la búsqueda se aborte a mitad de
camino (ver "Control de tiempo" abajo).

### Optimizaciones

- **Valores terminales ajustados por profundidad.** Una victoria vale
  `VALOR_GANADOR - nivel` y una derrota `VALOR_PERDEDOR + nivel`, donde
  `nivel` es la distancia (en jugadas) desde la raíz de la búsqueda. Esto
  hace que la IA prefiera ganar en el menor número de jugadas posible, y que
  retrase una derrota inevitable en vez de acelerarla.
- **Transposition Table** (`TranspositionTable`, clave = `get_estado_hash()`
  + profundidad + destino + turno): cachea posiciones repetidas para no
  recalcularlas. Tiene un límite de tamaño (`LIMITE_ESTADOS_MEMORIA`) para no
  crecer sin control. **Se reinicia en cada profundidad** del iterative
  deepening — no se reutiliza entre pasadas, porque el valor terminal ahora
  depende de `nivel`, que no es el mismo en una pasada con
  `profundidad_inicial=3` que en una con `profundidad_inicial=7` (ver
  docstring de `minimax()` para el detalle).
- **Move ordering.** `ordenar_movimientos()` prueba primero: (0) la jugada
  preferida de la profundidad anterior del iterative deepening ("PV move
  ordering" — suele podar mucho más), (1) jugadas que ganan un mini-tablero
  de inmediato, (2) jugadas que bloquean una victoria del rival, (3) el
  resto, ordenado por `IMPORTANCIA_CAMPO`.
- **Iterative Deepening con presupuesto adaptativo.** `mejor_movimiento()`
  busca profundidad 1, 2, 3... conservando el mejor movimiento de la última
  profundidad *completa*. El presupuesto de tiempo se ajusta según cuántas
  casillas quedan disponibles (`_calcular_presupuesto`): poco en la apertura
  (mucho ramaje, no vale la pena), más cerca del final (decisiones más
  críticas) — siempre acotado por el `tiempo_limite` recibido, nunca lo
  excede. Se detiene antes si ya se probó una victoria o derrota forzada.
- **Control de tiempo con corte duro.** Además del chequeo entre
  profundidades, hay un deadline absoluto revisado en cada nodo; si se
  cumple, `minimax()` lanza `TiempoAgotado` y la búsqueda se aborta
  limpiamente (gracias al `try/finally` mencionado arriba) sin dejar
  movimientos "fantasma" aplicados al tablero real.
- **Estadísticas.** Cada llamada a `mejor_movimiento()` actualiza
  `minimax.ultimas_estadisticas` (nodos visitados, profundidad alcanzada,
  valor final, segundos usados, presupuesto) — no forma parte del valor de
  retorno para no romper a quienes solo esperan la jugada; `main.py` las lee
  para mostrarlas después de cada jugada de la IA.

`mejor_movimiento(tablero, tablero_destino, tiempo_limite=TIEMPO_LIMITE)` es
el punto de entrada público — infiere de quién es el turno contando marcas
en el tablero (no recibe `jugador` como parámetro) y retorna la tupla
`(fila_meta, col_meta, fila_mini, col_mini)` del mejor movimiento encontrado.

---

## Interfaz y loop principal (`interfaz.py`, `main.py`)

`interfaz.py` centraliza toda la entrada/salida: lectura y validación de
movimientos en formato `Campo+Posición`, impresión del tablero (las casillas
vacías muestran su letra, para que el jugador sepa qué escribir), y mensajes
de estado.

`main.py` expone tres modos, todos construidos sobre el mismo loop de turnos
(`_ejecutar_partida`, que recibe cómo obtener el movimiento de X y de O):

```bash
python3 main.py
# 1. Humano vs Humano   -> jugar()
# 2. IA vs IA           -> jugar_ia_vs_ia()
# 3. Humano vs IA       -> jugar_humano_vs_ia()  (elige tu símbolo)
```

---

## Testing

```bash
python3 -m pytest tests_stub.py -v
```

20 tests cubren `Tablero`, `movimientos_validos`, `evaluar_posicion`,
`minimax` (encuentra victorias inmediatas, bloquea amenazas de un
movimiento, respeta el límite de tiempo) y una partida completa IA vs IA de
principio a fin sin errores.

### `Case Study/`

Carpeta con partidas reales jugadas contra la IA (transcritas movimiento por
movimiento), el análisis de por qué tomó ciertas decisiones, y casos de
regresión ejecutables que reconstruyen posiciones específicas de esas
partidas para verificar que un bug encontrado no vuelva a aparecer:

```bash
python3 "Case Study/regresion_juego1_campo_e.py"
```

---

## Créditos

Basado en el stub del curso de Inteligencia Artificial (ITAM, Otoño 2026).
Incorpora ideas de optimización (valores por profundidad, presupuesto de
tiempo adaptativo, PV move ordering, componente de amenaza en destino
forzado) adaptadas de una implementación de referencia compartida por el
equipo, integradas sobre la estructura modular de este proyecto.
