# Ultimate-Tic-Tac-Toe-IA

HEURÍSTICAS QUE PODEMOS USAR

| Heurística                          | Qué evalúa                                                                                 | Ventajas                                       | Desventajas                                                      |
| ----------------------------------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------- | ---------------------------------------------------------------- |
| 1. Material posicional              | Mini-tableros ganados, centros y esquinas.                                                 | Muy rápida y fácil de explicar.                | No detecta amenazas ni considera el tablero de destino.          |
| 2. Potencial de líneas              | Líneas con una o dos marcas, tanto locales como globales.                                  | Detecta ataques y bloqueos.                    | Puede valorar amenazas que todavía no son accesibles.            |
| 3. Jerárquica y sensible al destino | Líneas globales, líneas locales, posiciones, amenazas inmediatas y libertad de movimiento. | Representa mejor la estrategia real del juego. | Requiere justificar y ajustar sus pesos; es un poco más costosa. |



MIN-MAX

