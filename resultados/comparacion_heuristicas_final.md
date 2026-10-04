# Comparación de la heurística final

Fecha de ejecución: 4 de octubre de 2026.

## Objetivo

Comparar la evaluación de `ana_correcciones_final` contra la evaluación
anterior usando el mismo algoritmo Minimax, el mismo orden de movimientos y la
misma profundidad. Las heurísticas alternaron los símbolos X y O para no
atribuir a la evaluación la ventaja de comenzar.

Cada partida comenzó después de cuatro movimientos legales generados con una
semilla distinta. Esos movimientos iniciales solo se usaron para producir
posiciones variadas durante la calibración; el programa del torneo no juega
movimientos aleatorios.

## Selección preliminar a profundidad 2

Se probaron seis combinaciones de pesos, con 20 partidas por combinación. La
combinación seleccionada fue:

```text
18, 6, 5, 6, 1, 8, 4
```

Resultado contra la heurística anterior:

| Resultado | Partidas |
|---|---:|
| Victorias | 14 |
| Derrotas | 1 |
| Empates | 5 |

## Confirmación a profundidad 3

Se ejecutaron otras 20 partidas con aperturas distintas y colores alternados:

| Resultado | Partidas |
|---|---:|
| Victorias | 15 |
| Derrotas | 2 |
| Empates | 3 |

## Interpretación

El resultado respalda el cambio de pesos y de estructura de la evaluación,
pero no demuestra que la heurística sea matemáticamente óptima. La competencia
puede incluir rivales con estrategias diferentes. Por eso también se mantienen
200 pruebas deterministas de reglas, regresión, integración y casos tácticos.
