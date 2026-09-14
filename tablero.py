"""
MÓDULO: tablero.py
RESPONSABLE: Persona A
DESCRIPCIÓN: Representación y lógica básica del tablero Ultimate Tic-Tac-Toe

Este archivo define cómo se representa el estado del juego internamente.
CRÍTICO: Debe ser RÁPIDO - minimax lo llama miles de veces.
"""

from config import *
from typing import Optional, List, Tuple


class Tablero:
    """
    Representa el estado del juego completo.

    Estructura interna:
    - meta_tablero: Array 3x3 con ganadores de mini-tableros ('X', 'O', None, 'EMPATE')
    - mini_tableros: Array de 9 tableros 3x3 internos (índice = fila_meta * 3 + col_meta)
    - historial: Stack de movimientos previos para deshacer
    """

    def __init__(self):
        """
        Inicializa un tablero vacío.

        - meta_tablero: 3x3 lleno de None (ningún mini-tablero decidido)
        - mini_tableros: 9 mini-tableros de 3x3, todas las casillas en None
        - historial: pila vacía
        """
        self.meta_tablero: List[List[Optional[str]]] = [
            [None for _ in range(TAMAÑO_META)] for _ in range(TAMAÑO_META)
        ]
        self.mini_tableros: List[List[List[Optional[str]]]] = [
            [[None for _ in range(TAMAÑO_MINI)] for _ in range(TAMAÑO_MINI)]
            for _ in range(TAMAÑO_META * TAMAÑO_META)
        ]
        self.historial: List[Tuple[int, int, int, int, Optional[str]]] = []

    # ===== MÉTODOS AUXILIARES INTERNOS =====

    def _indice_mini(self, fila_meta: int, col_meta: int) -> int:
        """Convierte coordenadas (fila_meta, col_meta) al índice del array mini_tableros."""
        return fila_meta * TAMAÑO_META + col_meta

    # ===== MÉTODOS DE MODIFICACIÓN =====

    def aplicar_movimiento(self, fila_meta: int, col_meta: int,
                          fila_mini: int, col_mini: int, jugador: str) -> bool:
        """
        Aplica un movimiento al tablero.

        Args:
            fila_meta, col_meta: Posición del mini-tablero (0-2)
            fila_mini, col_mini: Posición dentro del mini-tablero (0-2)
            jugador: 'X' o 'O'

        Returns:
            True si el movimiento se aplicó exitosamente
            False si la casilla ya estaba ocupada
        """
        idx = self._indice_mini(fila_meta, col_meta)
        if self.mini_tableros[idx][fila_mini][col_mini] is not None:
            return False

        valor_meta_previo = self.meta_tablero[fila_meta][col_meta]
        self.historial.append((fila_meta, col_meta, fila_mini, col_mini, valor_meta_previo))

        self.mini_tableros[idx][fila_mini][col_mini] = jugador

        if valor_meta_previo is None:
            resultado_mini = self.obtener_ganador_mini(fila_meta, col_meta)
            if resultado_mini is not None:
                self.meta_tablero[fila_meta][col_meta] = resultado_mini

        return True

    def deshacer_movimiento(self) -> bool:
        """
        Deshace el último movimiento (restaura del historial).

        Returns:
            True si se deshizo algo, False si historial está vacío
        """
        if not self.historial:
            return False

        fila_meta, col_meta, fila_mini, col_mini, valor_meta_previo = self.historial.pop()
        idx = self._indice_mini(fila_meta, col_meta)
        self.mini_tableros[idx][fila_mini][col_mini] = None
        self.meta_tablero[fila_meta][col_meta] = valor_meta_previo
        return True

    # ===== MÉTODOS DE LECTURA (CRÍTICOS PARA VELOCIDAD) =====

    def obtener_mini_tablero(self, fila_meta: int, col_meta: int) -> List[List[Optional[str]]]:
        """
        Retorna el mini-tablero específico (sin copiar, para velocidad).
        """
        return self.mini_tableros[self._indice_mini(fila_meta, col_meta)]

    def obtener_casilla(self, fila_meta: int, col_meta: int,
                       fila_mini: int, col_mini: int) -> Optional[str]:
        """
        Retorna qué hay en una casilla específica ('X', 'O', o None).
        """
        return self.mini_tableros[self._indice_mini(fila_meta, col_meta)][fila_mini][col_mini]

    def obtener_ganador_mini(self, fila_meta: int, col_meta: int) -> Optional[str]:
        """
        Retorna quién ganó el mini-tablero especificado.

        Returns:
            'X' si X ganó
            'O' si O ganó
            'EMPATE' si está lleno sin ganador
            None si el juego sigue
        """
        mini = self.mini_tableros[self._indice_mini(fila_meta, col_meta)]
        ganador = self.detectar_ganador_mini(mini)
        if ganador is not None:
            return ganador
        if self.es_mini_tablero_lleno(fila_meta, col_meta):
            return 'EMPATE'
        return None

    # ===== MÉTODOS DE DETECCIÓN (CRÍTICOS PARA MINIMAX) =====

    def detectar_ganador_mini(self, tablero_3x3: List[List[Optional[str]]]) -> Optional[str]:
        """
        Detecta si alguien ganó en un mini-tablero (3-en-línea).

        Args:
            tablero_3x3: Mini-tablero a verificar

        Returns:
            'X' si X ganó
            'O' si O ganó
            None si no hay ganador
        """
        for linea in LINEAS_MINI_TABLERO:
            (f1, c1), (f2, c2), (f3, c3) = linea
            v1 = tablero_3x3[f1][c1]
            if v1 is not None and v1 == tablero_3x3[f2][c2] == tablero_3x3[f3][c3]:
                return v1
        return None

    def detectar_ganador_meta(self) -> Optional[str]:
        """
        Detecta si alguien ganó el JUEGO (3 campos en línea en meta-tablero).

        Returns:
            'X' si X ganó el juego
            'O' si O ganó el juego
            None si el juego sigue o está empatado
        """
        for linea in LINEAS_META_TABLERO:
            (f1, c1), (f2, c2), (f3, c3) = linea
            v1 = self.meta_tablero[f1][c1]
            if v1 in (JUGADOR_X, JUGADOR_O) and v1 == self.meta_tablero[f2][c2] == self.meta_tablero[f3][c3]:
                return v1
        return None

    def verificar_empate(self) -> bool:
        """
        Verifica si el juego está empatado (tablero lleno, sin ganador).

        Returns:
            True si está empatado
        """
        if self.detectar_ganador_meta() is not None:
            return False
        return all(
            self.meta_tablero[f][c] is not None
            for f in range(TAMAÑO_META)
            for c in range(TAMAÑO_META)
        )

    # ===== MÉTODOS DE ESTADO =====

    def es_mini_tablero_lleno(self, fila_meta: int, col_meta: int) -> bool:
        """
        Verifica si un mini-tablero está completamente lleno.
        """
        mini = self.mini_tableros[self._indice_mini(fila_meta, col_meta)]
        return all(celda is not None for fila in mini for celda in fila)

    def es_mini_tablero_disponible(self, fila_meta: int, col_meta: int) -> bool:
        """
        Verifica si se puede jugar en un mini-tablero.

        Returns:
            False si: ya fue ganado, está lleno, o es un empate
            True si: todavía tiene casillas vacías
        """
        return self.meta_tablero[fila_meta][col_meta] is None

    # ===== REPRESENTACIÓN Y DEBUG =====

    def __str__(self) -> str:
        """
        Retorna representación en string del tablero para mostrar en terminal.
        """
        def simbolo_celda(valor: Optional[str]) -> str:
            return valor if valor else '.'

        def simbolo_meta(valor: Optional[str]) -> str:
            if valor in (JUGADOR_X, JUGADOR_O):
                return valor
            if valor == 'EMPATE':
                return '='
            return '.'

        filas_tablero = []
        for fila_meta in range(TAMAÑO_META):
            for fila_mini in range(TAMAÑO_MINI):
                grupos = []
                for col_meta in range(TAMAÑO_META):
                    idx = self._indice_mini(fila_meta, col_meta)
                    fila_valores = self.mini_tableros[idx][fila_mini]
                    grupos.append(' '.join(simbolo_celda(c) for c in fila_valores))
                filas_tablero.append(' | '.join(grupos))
            if fila_meta < TAMAÑO_META - 1:
                filas_tablero.append('-' * 29)

        resumen_meta = '\n'.join(
            ' '.join(simbolo_meta(self.meta_tablero[f][c]) for c in range(TAMAÑO_META))
            for f in range(TAMAÑO_META)
        )

        return '\n'.join(filas_tablero) + '\n\nMETA-TABLERO:\n' + resumen_meta

    def copiar(self) -> "Tablero":
        """
        Crea una copia independiente del tablero actual.

        Usado por minimax para explorar variaciones.
        No copia el historial (se descarta para ahorrar memoria).
        """
        nuevo = Tablero()
        nuevo.mini_tableros = [
            [fila[:] for fila in mini] for mini in self.mini_tableros
        ]
        nuevo.meta_tablero = [fila[:] for fila in self.meta_tablero]
        return nuevo

    # ===== MÉTODOS PARA SERIALIZACIÓN (DEBUG) =====

    def get_estado_hash(self) -> int:
        """
        Retorna un hash único del estado actual (para Transposition Tables).

        Convierte mini_tableros y meta_tablero a tuplas inmutables y aplica
        hash() de Python. Estados distintos producen (con probabilidad
        prácticamente segura) hashes distintos, y el cálculo es O(81),
        suficientemente rápido para llamarse miles de veces en minimax.
        """
        mini_tuple = tuple(
            tuple(tuple(fila) for fila in mini) for mini in self.mini_tableros
        )
        meta_tuple = tuple(tuple(fila) for fila in self.meta_tablero)
        return hash((mini_tuple, meta_tuple))
