Sí, este segundo juego es **IA vs IA**: X y O son controlados por la IA. La partida empieza con **X: Ea** y **O: Aa**.  

### Transcript limpio — Juego 2

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
| 12 |    O    |   **Fa**   |                                           |
| 13 |    X    |   **Ae**   |                                           |
| 14 |    O    |   **Ec**   |                                           |
| 15 |    X    |   **Ca**   |                                           |
| 16 |    O    |   **Ah**   |                                           |
| 17 |    X    |   **Hb**   |                                           |
| 18 |    O    |   **Bh**   |                                           |
| 19 |    X    |   **Hh**   |                                           |
| 20 |    O    |   **He**   |                                           |
| 21 |    X    |   **Ei**   |                                           |
| 22 |    O    |   **If**   |                                           |
| 23 |    X    |   **Fd**   |                                           |
| 24 |    O    |   **Dg**   |                                           |
| 25 |    X    |   **Ge**   |                                           |
| 26 |    O    |   **Ed**   |                                           |
| 27 |    X    |   **Dh**   |                                           |
| 28 |    O    |   **Hi**   |                                           |
| 29 |    X    |   **Ig**   |                                           |
| 30 |    O    |   **Gi**   |                                           |
| 31 |    X    |   **Id**   |                                           |
| 32 |    O    |   **Di**   |                                           |
| 33 |    X    |   **Ic**   |                                           |
| 34 |    O    |   **Cg**   |                                           |
| 35 |    X    |   **Gg**   |                                           |
| 36 |    O    |   **Gc**   |                                           |
| 37 |    X    |   **Ce**   |                                           |
| 38 |    O    |   **Ee**   | 🏆 **O gana Campo E**                     |
| 39 |    X    |   **Ia**   | 🏆 **X gana Campo I**                     |
| 40 |    O    |   **Ag**   |                                           |
| 41 |    X    |   **Gf**   |                                           |
| 42 |    O    |   **Fb**   |                                           |
| 43 |    X    |   **Bg**   |                                           |
| 44 |    O    |   **Gb**   |                                           |
| 45 |    X    |   **Ba**   |                                           |
| 46 |    O    |   **Ad**   | 🏆 **O gana Campo A**                     |
| 47 |    X    |   **Db**   | 🏆 **X gana Campo D**                     |
| 48 |    O    |   **Be**   | 🏆 **O gana Campo B**                     |
| 49 |    X    |   **Cf**   | 🏆 **X gana Campo C**                     |
| 50 |    O    |   **Fg**   |                                           |
| 51 |    X    |   **Gd**   | 🏆 **X gana Campo G**                     |
| 52 |    O    |   **Fc**   | 🏆 **O gana Campo F**                     |
| 53 |    X    |   **Ha**   |                                           |
| 54 |    O    |   **Hc**   |                                           |
| 55 |    X    |   **Hf**   |                                           |
| 56 |    O    |   **Hg**   | 🏆 **O gana Campo H → O gana la partida** |

La primera victoria local llega bastante tarde: en el movimiento **38**, O juega **Ee** y completa la fila central `O O O` del Campo E. El meta-tablero pasa entonces a tener E para O.  Inmediatamente después, X juega **Ia** y gana el Campo I. 

El final queda muy cerrado. Antes del último movimiento, el meta-tablero es:

```text
O | O | X
---------
X | O | O
---------
X | H | X
```

O ya controla **A, B, E y F**, mientras que X controla **C, D, G e I**. Solo falta decidir **H**. 

En el movimiento **56**, O juega **Hg**. Eso completa en H la diagonal:

```text
X X O
d O X
O X O
```

por lo que **O gana H**. El meta-tablero queda:

```text
O | O | X
---------
X | O | O
---------
X | O | X
```

y O completa la columna central **B–E–H**, ganando toda la partida. El programa efectivamente termina mostrando **“O GANA”**. 

### Secuencia compacta para tus tests

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
O: Fa
X: Ae
O: Ec
X: Ca
O: Ah
X: Hb
O: Bh
X: Hh
O: He
X: Ei
O: If
X: Fd
O: Dg
X: Ge
O: Ed
X: Dh
O: Hi
X: Ig
O: Gi
X: Id
O: Di
X: Ic
O: Cg
X: Gg
O: Gc
X: Ce
O: Ee  -> O gana E
X: Ia  -> X gana I
O: Ag
X: Gf
O: Fb
X: Bg
O: Gb
X: Ba
O: Ad  -> O gana A
X: Db  -> X gana D
O: Be  -> O gana B
X: Cf  -> X gana C
O: Fg
X: Gd  -> X gana G
O: Fc  -> O gana F
X: Ha
O: Hc
X: Hf
O: Hg  -> O gana H -> O gana meta-tablero
```

Este juego es todavía más interesante que el anterior para mejorar la IA, porque **ambas IAs usan la misma lógica y aun así aparece una ventaja decisiva para O**. Además, durante los primeros **37 movimientos no se gana ni un solo campo**, y luego entre los movimientos 38 y 56 se resuelven prácticamente todos. Eso nos da un caso muy bueno para revisar si la heurística está valorando demasiado el juego local y **demasiado poco la preparación del meta-tablero**, especialmente la futura columna **B–E–H**.
