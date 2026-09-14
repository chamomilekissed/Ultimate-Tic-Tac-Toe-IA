"""
CASO DE REGRESIÓN: Juego 1 (Humano vs IA) — jugada 30-31, Campo E

Contexto (ver "Juego 1.md" en esta misma carpeta):
En la partida real, X (humano) construyó una victoria en el Campo E
(el centro del meta-tablero) mientras O (IA) no defendía. El análisis
encontró un bug real en evaluador.py: evaluar_bifurcaciones(),
evaluar_defensa() y evaluar_mini_tableros() excluían cualquier
mini-tablero ya decidido (`if not tablero.es_mini_tablero_disponible(...):
continue`). Como resultado, ganar un mini-tablero hacía que su señal de
dominio local (material + amenazas) desapareciera de golpe, y la única
compensación (evaluar_control_posiciones) no alcanzaba a cubrir la
pérdida. La heurística literalmente puntuaba "Eg" (X gana el Campo E)
PEOR que "Ec" (X no gana nada) en la misma posición: -20 vs -2.

Fix aplicado (2026-09-14):
1. evaluador.py: se quitó el filtro de disponibilidad en las tres
   funciones — ahora evalúan los 9 mini-tableros siempre, decididos o no.
2. config.py: PESO_POSICIONES_CLAVE subió de 5 a 7 (verificado
   empíricamente: 6 ya alcanzaba para cerrar el gap residual).

Este script reconstruye la posición exacta de la partida real, justo
antes de que O jugara "Ge" (movida 30), y verifica que el bug no
regrese: ganar el Campo E (jugada "Eg") debe evaluarse mejor o igual
que no ganarlo (jugada "Ec"), tanto en evaluación estática (profundidad
0) como en la posición previa a la jugada.

Uso:
    python3 "Case Study/regresion_juego1_campo_e.py"
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CAMPOS, POSICIONES_MINI, INDICES_INVERSOS, INDICES_MINI_INVERSOS, JUGADOR_X, JUGADOR_O
import tablero as tb
import movimientos as mov
import evaluador as ev

# Secuencia compacta de la partida real (Juego 1.md), movidas 1-29:
# todo lo jugado ANTES de que O decida la jugada 30 ("Ge").
SECUENCIA_HASTA_JUGADA_29 = """
X: Ac
O: Cb
X: Bi
O: Ic
X: Cg
O: Gd
X: Di
O: Ie
X: Ea
O: Ai
X: Ig
O: Ga
X: Ae
O: Eb
X: Bf
O: Ff
X: Fc
O: Ch
X: Hd
O: Dd
X: De
O: Ee
X: Eh
O: He
X: Ei
O: If
X: Fb
O: Bg
X: Gg
""".strip().splitlines()


def _parsear(linea: str):
    _, letras = linea.split(":")
    letras = letras.strip()
    fila_meta, col_meta = CAMPOS[letras[0]]
    fila_mini, col_mini = POSICIONES_MINI[letras[1]]
    return (fila_meta, col_meta, fila_mini, col_mini)


def _letra(movimiento) -> str:
    fila_meta, col_meta, fila_mini, col_mini = movimiento
    return INDICES_INVERSOS[(fila_meta, col_meta)] + INDICES_MINI_INVERSOS[(fila_mini, col_mini)]


def construir_posicion_jugada_30() -> "tb.Tablero":
    """Reproduce las primeras 29 jugadas reales y retorna el tablero resultante (turno de O, forzado a Campo G)."""
    t = tb.Tablero()
    for linea in SECUENCIA_HASTA_JUGADA_29:
        jugador = JUGADOR_X if linea.startswith("X") else JUGADOR_O
        ok = t.aplicar_movimiento(*_parsear(linea), jugador)
        assert ok, f"Movimiento inválido al reconstruir la partida: {linea}"
    return t


def test_ganar_campo_e_no_debe_puntuar_peor_que_no_ganarlo():
    """
    Regresión del bug encontrado el 2026-09-14: completar la victoria del
    Campo E (jugada 'Eg') debe evaluarse al menos tan bien como dejarlo sin
    ganar (jugada 'Ec'), no peor.
    """
    t = construir_posicion_jugada_30()

    # O juega "Ge" (Campo G, posición e) -> fuerza a X al Campo E.
    mov_ge = (2, 0, 1, 1)  # Campo G (2,0), posición e (1,1)
    assert _letra(mov_ge) == "Ge"
    t.aplicar_movimiento(*mov_ge, JUGADOR_O)

    mov_eg = (1, 1, 2, 0)  # Campo E, posición g -> completa g-h-i, gana el campo
    mov_ec = (1, 1, 0, 2)  # Campo E, posición c -> no gana nada

    legales = mov.movimientos_validos(t, (1, 1))
    assert mov_eg in legales and mov_ec in legales, "La posición reconstruida no coincide con la partida real"

    t.aplicar_movimiento(*mov_eg, JUGADOR_X)
    assert t.meta_tablero[1][1] == JUGADOR_X, "Eg debería ganar el Campo E"
    valor_eg = ev.evaluar_posicion(t, False)
    t.deshacer_movimiento()

    t.aplicar_movimiento(*mov_ec, JUGADOR_X)
    assert t.meta_tablero[1][1] is None, "Ec no debería decidir el Campo E"
    valor_ec = ev.evaluar_posicion(t, False)
    t.deshacer_movimiento()

    assert valor_eg >= valor_ec, (
        f"BUG DE REGRESIÓN: ganar el Campo E (Eg={valor_eg}) evalúa peor que "
        f"no ganarlo (Ec={valor_ec}). Ver evaluar_bifurcaciones/evaluar_defensa/"
        f"evaluar_mini_tableros en evaluador.py — no deben excluir mini-tableros "
        f"ya decididos."
    )


if __name__ == "__main__":
    test_ganar_campo_e_no_debe_puntuar_peor_que_no_ganarlo()
    print("OK: ganar el Campo E ya no se evalúa peor que dejarlo sin ganar (regresión del 2026-09-14 sigue arreglada).")
