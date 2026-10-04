"""
CASO DE REGRESIÓN: Juego 1 (Humano vs IA) — jugada 30-31, Campo E

Contexto (ver ``juego_01.md`` en esta misma carpeta):
En la partida real, X (humano) construyó una victoria en el Campo E
(el centro del meta-tablero) mientras O (IA) no defendía. El análisis
encontró un error real: la evaluación de una versión anterior podía asignar
un valor menor a "Eg" (X gana el Campo E) que a "Ec" (X no gana el campo)
en la misma posición.

La versión final separa las responsabilidades. Los patrones tácticos de un
campo cerrado ya no se cuentan porque no se pueden jugar. En su lugar, la
victoria obtenida aparece como progreso del meta-tablero y como control de una
posición estratégica. Así se reconoce el beneficio real sin conservar
amenazas internas que ya dejaron de existir.

Este programa reconstruye la posición exacta de la partida real, justo
antes de que O jugara "Ge" (movimiento 30), y verifica que el error no
regrese: ganar el Campo E (jugada "Eg") debe evaluarse mejor o igual
que no ganarlo (jugada "Ec"), tanto en evaluación estática (profundidad
0) como en la posición previa a la jugada.

Uso:
    python3 casos_de_estudio/regresion_juego_01_campo_e.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    CAMPOS,
    POSICIONES_MINI,
    INDICES_INVERSOS,
    INDICES_MINI_INVERSOS,
    JUGADOR_X,
    JUGADOR_O,
)
from src import tablero as tb
from src import movimientos as mov
from src import evaluador as ev

# Secuencia compacta de la partida real (juego_01.md), movidas 1-29:
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


def _parsear_movimiento(linea: str):
    """Convierte una línea como ``X: Ac`` a sus cuatro índices internos."""
    _, letras = linea.split(":")
    letras = letras.strip()
    fila_meta, col_meta = CAMPOS[letras[0]]
    fila_mini, col_mini = POSICIONES_MINI[letras[1]]
    return (fila_meta, col_meta, fila_mini, col_mini)


def _convertir_a_texto(movimiento) -> str:
    """Convierte cuatro índices internos a la notación de dos letras."""
    fila_meta, col_meta, fila_mini, col_mini = movimiento
    return (
        INDICES_INVERSOS[(fila_meta, col_meta)]
        + INDICES_MINI_INVERSOS[(fila_mini, col_mini)]
    )


def construir_posicion_jugada_30() -> "tb.Tablero":
    """Reproduce 29 jugadas y retorna el turno de O, obligado al campo G."""
    tablero_partida = tb.Tablero()
    for linea in SECUENCIA_HASTA_JUGADA_29:
        jugador = JUGADOR_X if linea.startswith("X") else JUGADOR_O
        movimiento_aplicado = tablero_partida.aplicar_movimiento(
            *_parsear_movimiento(linea), jugador
        )
        assert movimiento_aplicado, (
            f"Movimiento inválido al reconstruir la partida: {linea}"
        )
    return tablero_partida


def test_ganar_campo_e_no_debe_puntuar_peor_que_no_ganarlo():
    """
    Regresión del error encontrado el 2026-09-14: completar la victoria del
    Campo E (jugada 'Eg') debe evaluarse al menos tan bien como dejarlo sin
    ganar (jugada 'Ec'), no peor.
    """
    tablero_partida = construir_posicion_jugada_30()

    # O juega "Ge" (Campo G, posición e) -> fuerza a X al Campo E.
    movimiento_ge = (2, 0, 1, 1)  # Campo G (2,0), posición e (1,1)
    assert _convertir_a_texto(movimiento_ge) == "Ge"
    tablero_partida.aplicar_movimiento(*movimiento_ge, JUGADOR_O)

    movimiento_eg = (1, 1, 2, 0)  # Completa g-h-i y gana el campo E.
    movimiento_ec = (1, 1, 0, 2)  # Juega en E-c, pero no gana el campo.

    movimientos_legales = mov.movimientos_validos(tablero_partida, (1, 1))
    assert (
        movimiento_eg in movimientos_legales and movimiento_ec in movimientos_legales
    ), "La posición reconstruida no coincide con la partida real"

    tablero_partida.aplicar_movimiento(*movimiento_eg, JUGADOR_X)
    assert tablero_partida.meta_tablero[1][1] == JUGADOR_X, (
        "Eg debería ganar el Campo E"
    )
    valor_eg = ev.evaluar_posicion(tablero_partida, False)
    tablero_partida.deshacer_movimiento()

    tablero_partida.aplicar_movimiento(*movimiento_ec, JUGADOR_X)
    assert tablero_partida.meta_tablero[1][1] is None, (
        "Ec no debería decidir el Campo E"
    )
    valor_ec = ev.evaluar_posicion(tablero_partida, False)
    tablero_partida.deshacer_movimiento()

    assert valor_eg >= valor_ec, (
        f"ERROR DE REGRESIÓN: ganar el Campo E (Eg={valor_eg}) evalúa peor que "
        f"no ganarlo (Ec={valor_ec}). Ver evaluar_bifurcaciones/evaluar_defensa/"
        f"evaluar_progreso_meta/evaluar_control_posiciones en evaluador.py."
    )


if __name__ == "__main__":
    test_ganar_campo_e_no_debe_puntuar_peor_que_no_ganarlo()
    print(
        "OK: ganar el Campo E ya no se evalúa peor que dejarlo sin ganar (regresión del 2026-09-14 sigue arreglada)."
    )
