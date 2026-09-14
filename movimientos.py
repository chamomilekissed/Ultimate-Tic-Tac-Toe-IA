"""
MÓDULO: movimientos.py
RESPONSABLE: Persona A
DESCRIPCIÓN: Generación de movimientos válidos

Genera lista de movimientos legales según las reglas del juego.
"""

from config import *
from typing import List, Tuple, Optional
import tablero as tb


def movimientos_validos_mini(tablero_3x3: List[List[Optional[str]]]) -> List[Tuple[int, int]]:
    """
    Retorna casillas vacías en un mini-tablero específico.

    Args:
        tablero_3x3: Mini-tablero 3x3

    Returns:
        Lista de tuplas (fila, col) de casillas vacías
    """
    return [
        (fila, col)
        for fila in range(TAMAÑO_MINI)
        for col in range(TAMAÑO_MINI)
        if tablero_3x3[fila][col] is None
    ]


def mini_tableros_disponibles(tablero: "tb.Tablero") -> List[Tuple[int, int]]:
    """
    Retorna lista de mini-tableros donde aún se puede jugar.

    Returns:
        Lista de tuplas (fila_meta, col_meta) de mini-tableros disponibles
    """
    return [
        (fila_meta, col_meta)
        for fila_meta in range(TAMAÑO_META)
        for col_meta in range(TAMAÑO_META)
        if tablero.es_mini_tablero_disponible(fila_meta, col_meta)
    ]


def movimientos_validos(tablero: "tb.Tablero", tablero_destino: Optional[Tuple[int, int]]) -> List[Tuple[int, int, int, int]]:
    """
    Retorna lista de movimientos válidos desde la posición actual.

    Args:
        tablero: Estado actual del juego
        tablero_destino: Tupla (fila_meta, col_meta) indicando dónde DEBE jugar
                        Si None, puede jugar en cualquier lado (primer movimiento)

    Returns:
        Lista de tuplas (fila_meta, col_meta, fila_mini, col_mini)
        representando cada movimiento legal

    Reglas:
    - Si tablero_destino es None: jugador puede jugar en cualquier casilla vacía (primer turno)
    - Si tablero_destino ya fue ganado: jugador puede jugar en cualquier mini-tablero disponible
    - Si tablero_destino está lleno: jugador puede jugar en cualquier mini-tablero disponible
    - Si tablero_destino es normal: solo puede jugar en ese mini-tablero (casillas vacías)
    """
    if tablero_destino is not None and tablero.es_mini_tablero_disponible(*tablero_destino):
        tableros_a_revisar = [tablero_destino]
    else:
        tableros_a_revisar = mini_tableros_disponibles(tablero)

    movimientos = []
    for fila_meta, col_meta in tableros_a_revisar:
        mini = tablero.obtener_mini_tablero(fila_meta, col_meta)
        for fila_mini, col_mini in movimientos_validos_mini(mini):
            movimientos.append((fila_meta, col_meta, fila_mini, col_mini))
    return movimientos
