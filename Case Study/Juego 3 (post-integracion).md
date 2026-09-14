Este es **Juego 3**, la primera partida jugada (IA vs IA) después de integrar las
mejoras portadas de `gato_de_gatos.py`: valores terminales ajustados por
profundidad, presupuesto de tiempo adaptativo por etapa, PV move ordering,
corte anticipado ante victoria forzada, el nuevo componente de heurística
`evaluar_amenaza_destino`, y las estadísticas de búsqueda (`ultimas_estadisticas`)
que `main.py` ahora imprime después de cada jugada de la IA.

A diferencia de los Juegos 1 y 2 (que analizaban un bug), este caso documenta
**cómo se ve la instrumentación nueva en acción**, con presupuestos de tiempo
reales (no acortados para tests): 4s en apertura, 10s en medio juego, 25s en
el final.

### Transcript — Juego 3

|  # | Jugador | Movimiento | Evento                                    |
| -: | :-----: | :--------: | ----------------------------------------- |
|  1 |    X    |   **Ea**   |                                           |
|  2 |    O    |   **Aa**   |                                           |
|  3 |    X    |   **Ab**   |                                           |
|  4 |    O    |   **Bb**   |                                           |
|  5 |    X    |   **Bc**   |                                           |
|  6 |    O    |   **Cc**   |                                           |
|  7 |    X    |   **Cd**   |                                           |
|  8 |    O    |   **Dd**   |                                           |
|  9 |    X    |   **De**   |                                           |
| 10 |    O    |   **Ef**   |                                           |
| 11 |    X    |   **Ff**   |                                           |
| 12 |    O    |   **Fg**   |                                           |
| 13 |    X    |   **Gg**   |                                           |
| 14 |    O    |   **Gc**   |                                           |
| 15 |    X    |   **Ca**   |                                           |
| 16 |    O    |   **Ai**   |                                           |
| 17 |    X    |   **Ih**   |                                           |
| 18 |    O    |   **Hh**   |                                           |
| 19 |    X    |   **Hi**   |                                           |
| 20 |    O    |   **Ib**   |                                           |
| 21 |    X    |   **Bi**   |                                           |
| 22 |    O    |   **Ii**   |                                           |
| 23 |    X    |   **Ie**   |                                           |
| 24 |    O    |   **Ei**   |                                           |
| 25 |    X    |   **Id**   |                                           |
| 26 |    O    |   **Da**   |                                           |
| 27 |    X    |   **Ae**   |                                           |
| 28 |    O    |   **Eh**   |                                           |
| 29 |    X    |   **Hf**   |                                           |
| 30 |    O    |   **Fi**   |                                           |
| 31 |    X    |   **Ic**   |                                           |
| 32 |    O    |   **Cg**   |                                           |
| 33 |    X    |   **Gd**   |                                           |
| 34 |    O    |   **Dc**   |                                           |
| 35 |    X    |   **Ce**   |                                           |
| 36 |    O    |   **Ee**   |                                           |
| 37 |    X    |   **Ed**   |                                           |
| 38 |    O    |   **Di**   |                                           |
| 39 |    X    |   **Ig**   | 🏆 **X gana Campo I**                     |
| 40 |    O    |   **Ga**   |                                           |
| 41 |    X    |   **Ah**   | 🏆 **X gana Campo A**                     |
| 42 |    O    |   **Hc**   |                                           |
| 43 |    X    |   **Ch**   |                                           |
| 44 |    O    |   **Hg**   |                                           |
| 45 |    X    |   **Gh**   |                                           |
| 46 |    O    |   **Hb**   |                                           |
| 47 |    X    |   **Bh**   |                                           |
| 48 |    O    |   **Hd**   |                                           |
| 49 |    X    |   **Dh**   |                                           |
| 50 |    O    |   **He**   | 🏆 **O gana Campo H**                     |
| 51 |    X    |   **Eg**   | 🏆 **X gana Campo E → X gana la partida** |

Meta-tablero final:

```text
X | . | .
- + - + -
. | X | .
- + - + -
. | O | X
```

X gana con la diagonal **A–E–I**, aunque solo 4 de los 9 campos llegaron a
decidirse (A, E, H, I) — el juego termina en cuanto se completa la línea,
sin importar el resto del tablero.

### Las estadísticas en acción

**Apertura** (presupuesto 4s — tablero muy abierto, no vale la pena buscar más hondo):

```text
Profundidad: 5 | Nodos: 52,738 | Valor: 3 | Tiempo: 4.00s / 4.0s
Profundidad: 6 | Nodos: 49,353 | Valor: 3 | Tiempo: 4.00s / 4.0s
```

**Medio juego** (presupuesto sube a 10s en cuanto quedan menos de 55 casillas
disponibles en mini-tableros abiertos; los valores empiezan a moverse porque
ya hay amenazas reales):

```text
Profundidad: 8  | Nodos: 119,979 | Valor: 36 | Tiempo: 10.00s / 10.0s
Profundidad: 9  | Nodos: 127,139 | Valor: 46 | Tiempo: 10.00s / 10.0s
Profundidad: 10 | Nodos: 140,356 | Valor: 51 | Tiempo: 10.00s / 10.0s
```

**Final — cascada de victoria forzada.** En la jugada 42 (`O: Hc`), la
búsqueda de O encuentra por primera vez que, jugando `O` lo mejor posible,
el resultado sigue siendo `Valor: 9990` (fuertemente favorable a X): X ya
tiene una victoria forzada sin importar lo que haga O, y el corte anticipado
(`abs(mejor_valor) >= VALOR_GANADOR // 2`) entra en acción. De ahí en
adelante, cada jugada necesita **menos** profundidad para ver el mate
completo (quedan menos jugadas hasta el final forzado), y el valor sube de 1
en 1 exactamente como predice `VALOR_GANADOR - nivel`:

```text
Profundidad: 10 | Nodos: 114,148 | Valor: 9990 | Tiempo: 7.88s / 10.0s   <- primera detección (jugada 42, O: Hc)
Profundidad: 9  | Nodos: 61,396  | Valor: 9991 | Tiempo: 4.19s / 10.0s
Profundidad: 8  | Nodos: 26,603  | Valor: 9992 | Tiempo: 1.99s / 10.0s
Profundidad: 7  | Nodos: 6,287   | Valor: 9993 | Tiempo: 0.50s / 10.0s
Profundidad: 6  | Nodos: 2,323   | Valor: 9994 | Tiempo: 0.17s / 10.0s
Profundidad: 5  | Nodos: 829     | Valor: 9995 | Tiempo: 0.06s / 10.0s
Profundidad: 4  | Nodos: 108     | Valor: 9996 | Tiempo: 0.01s / 10.0s
Profundidad: 3  | Nodos: 65      | Valor: 9997 | Tiempo: 0.01s / 10.0s
Profundidad: 2  | Nodos: 8       | Valor: 9998 | Tiempo: 0.00s / 10.0s
Profundidad: 1  | Nodos: 3       | Valor: 9999 | Tiempo: 0.00s / 25.0s   <- última jugada (51, X: Eg), resuelve al instante
```

Nodos cayendo de 114,148 a 3 y tiempo de ~8s a instantáneo en 9 jugadas:
la IA deja de "pensar" en cuanto el desenlace ya está decidido, en vez de
seguir gastando el presupuesto completo hasta el final — justo el
comportamiento que se buscaba al portar el corte anticipado y los valores
ajustados por profundidad.

### Secuencia compacta para tests

```text
X: Ea
O: Aa
X: Ab
O: Bb
X: Bc
O: Cc
X: Cd
O: Dd
X: De
O: Ef
X: Ff
O: Fg
X: Gg
O: Gc
X: Ca
O: Ai
X: Ih
O: Hh
X: Hi
O: Ib
X: Bi
O: Ii
X: Ie
O: Ei
X: Id
O: Da
X: Ae
O: Eh
X: Hf
O: Fi
X: Ic
O: Cg
X: Gd
O: Dc
X: Ce
O: Ee
X: Ed
O: Di
X: Ig  -> X gana I
O: Ga
X: Ah  -> X gana A
O: Hc
X: Ch
O: Hg
X: Gh
O: Hb
X: Bh
O: Hd
X: Dh
O: He  -> O gana H
X: Eg  -> X gana E -> X gana meta-tablero (diagonal A-E-I)
```
