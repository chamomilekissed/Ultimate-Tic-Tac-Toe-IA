"""
GATO DE GATOS (ULTIMATE TIC-TAC-TOE) CON MINIMAX
=================================================

Archivo único de entrega: contiene todo el motor del juego (representación
del tablero, generación de movimientos, heurística de evaluación, búsqueda
Minimax con poda Alfa-Beta, interfaz de terminal y el loop principal).

Cómo jugar
----------
Ejecutar este archivo con Python 3 (o en Spyder) y elegir un modo:
    1. Humano vs Humano
    2. IA vs IA
    3. Humano vs IA

Los movimientos se escriben con dos caracteres "Campo+Posición":
    - Campo (A-I, mayúscula): qué mini-tablero, según
          A B C
          D E F
          G H I
    - Posición (a-i, minúscula): qué casilla dentro de ese mini-tablero,
      con la misma disposición (a b c / d e f / g h i).
    Ejemplo: "Gc" = mini-tablero G (inferior izquierdo), casilla c
    (superior derecha de ese mini-tablero).

La casilla elegida determina el mini-tablero donde debe jugar el
siguiente turno. Si ese mini-tablero ya está decidido (ganado o
empatado), el siguiente jugador puede elegir cualquier mini-tablero que
siga abierto.

Algoritmo
---------
La IA usa Minimax con poda Alfa-Beta e Iterative Deepening (busca a
profundidad creciente hasta agotar un presupuesto de tiempo, que se
adapta según la etapa de la partida — apertura/medio juego/final). La
evaluación de posiciones no terminales combina 7 componentes heurísticos
(progreso en el meta-tablero, bifurcaciones, amenazas dispersas, control
de campos clave, posesión local, y dos niveles de "a qué mini-tablero se
manda al rival"); ver evaluar_posicion() más abajo para el detalle de
cada uno. evaluar_posicion() acepta un flag `debug` que imprime el
desglose completo por componente — se usó extensamente durante el
desarrollo para diagnosticar y corregir la heurística (se deja como
evidencia; no se activa durante el juego normal).
"""

import random
import time
from typing import Callable, Dict, List, Optional, Tuple


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Símbolos de jugadores
JUGADOR_X = 'X'
JUGADOR_O = 'O'
VACIO = None

# Tamaño del tablero
TAMAÑO_MINI = 3   # Cada mini-tablero es 3x3
TAMAÑO_META = 3   # Meta-tablero es 3x3 (de mini-tableros)

# Índices de meta-tablero
# A | B | C
# D | E | F
# G | H | I
CAMPOS = {
    'A': (0, 0), 'B': (0, 1), 'C': (0, 2),
    'D': (1, 0), 'E': (1, 1), 'F': (1, 2),
    'G': (2, 0), 'H': (2, 1), 'I': (2, 2)
}
INDICES_INVERSOS = {v: k for k, v in CAMPOS.items()}

# Índices de mini-tablero
# a | b | c
# d | e | f
# g | h | i
POSICIONES_MINI = {
    'a': (0, 0), 'b': (0, 1), 'c': (0, 2),
    'd': (1, 0), 'e': (1, 1), 'f': (1, 2),
    'g': (2, 0), 'h': (2, 1), 'i': (2, 2)
}
INDICES_MINI_INVERSOS = {v: k for k, v in POSICIONES_MINI.items()}

# ===== Minimax =====

TIEMPO_LIMITE = 30  # Límite de tiempo por jugada (segundos), nunca se excede

# Valores heurísticos extremos
VALOR_GANADOR = 10000
VALOR_PERDEDOR = -10000
VALOR_EMPATE = 0

# ===== Pesos de la función heurística =====

PESO_PROGRESO_META_TABLERO = 10   # ¿Cuántos campos ha ganado?
PESO_AMENAZAS_BIFURCACIONES = 7   # ¿Tiene 2 amenazas? ¿El oponente las tiene?
PESO_DEFENSA_CRITICA = 6          # ¿El oponente va a ganar pronto?
PESO_POSICIONES_CLAVE = 7         # ¿Controla centro/esquinas del meta-tablero?
PESO_CONTROL_LOCAL = 3            # Evaluación dentro de mini-tableros
PESO_AMENAZA_DESTINO = 8          # ¿A qué mini-tablero se manda al rival: es un regalo o una trampa?
PESO_AMENAZA_DESTINO_FUTURA = 4   # Un nivel más: ¿a dónde mandaría yo al rival después?

# ===== Presupuesto de tiempo por etapa de partida =====
# (según casillas vacías en mini-tableros disponibles; siempre acotado por
# el tiempo_limite que reciba mejor_movimiento(), nunca lo excede)

CASILLAS_RESTANTES_APERTURA = 55
CASILLAS_RESTANTES_MEDIO = 25
TIEMPO_APERTURA = 4.0
TIEMPO_MEDIO_PARTIDA = 10.0
TIEMPO_FINAL_PARTIDA = 25.0

# Tamaño máximo de la Transposition Table (entradas) antes de dejar de guardar más
LIMITE_ESTADOS_MEMORIA = 120_000

# ===== Líneas de victoria (filas, columnas, diagonales de un 3x3) =====

LINEAS_MINI_TABLERO = [
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]

LINEAS_META_TABLERO = [
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]

# Importancia relativa de cada campo en el meta-tablero
IMPORTANCIA_CAMPO = {
    (0, 0): 3,  # Esquina superior-izquierda
    (0, 1): 2,  # Borde superior
    (0, 2): 3,  # Esquina superior-derecha
    (1, 0): 2,  # Borde izquierdo
    (1, 1): 4,  # Centro (más importante)
    (1, 2): 2,  # Borde derecho
    (2, 0): 3,  # Esquina inferior-izquierda
    (2, 1): 2,  # Borde inferior
    (2, 2): 3,  # Esquina inferior-derecha
}


# =============================================================================
# TABLERO
# =============================================================================

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

    def _indice_mini(self, fila_meta: int, col_meta: int) -> int:
        """Convierte coordenadas (fila_meta, col_meta) al índice del array mini_tableros."""
        return fila_meta * TAMAÑO_META + col_meta

    # ----- Modificación -----

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
            False si las coordenadas o el jugador son inválidos, si el
            mini-tablero ya terminó o si la casilla está ocupada.
        """
        coordenadas = (fila_meta, col_meta, fila_mini, col_mini)
        coordenadas_validas = all(0 <= valor < TAMAÑO_MINI for valor in coordenadas)
        jugador_valido = jugador in (JUGADOR_X, JUGADOR_O)

        if not coordenadas_validas or not jugador_valido:
            return False
        if not self.es_mini_tablero_disponible(fila_meta, col_meta):
            return False

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

    # ----- Lectura (críticos para velocidad) -----

    def obtener_mini_tablero(self, fila_meta: int, col_meta: int) -> List[List[Optional[str]]]:
        """Retorna el mini-tablero específico (sin copiar, para velocidad)."""
        return self.mini_tableros[self._indice_mini(fila_meta, col_meta)]

    def obtener_casilla(self, fila_meta: int, col_meta: int,
                       fila_mini: int, col_mini: int) -> Optional[str]:
        """Retorna qué hay en una casilla específica ('X', 'O', o None)."""
        return self.mini_tableros[self._indice_mini(fila_meta, col_meta)][fila_mini][col_mini]

    def obtener_ganador_mini(self, fila_meta: int, col_meta: int) -> Optional[str]:
        """
        Retorna quién ganó el mini-tablero especificado.

        Returns:
            'X' si X ganó, 'O' si O ganó, 'EMPATE' si está lleno sin
            ganador, None si el juego sigue.
        """
        mini = self.mini_tableros[self._indice_mini(fila_meta, col_meta)]
        ganador = self.detectar_ganador_mini(mini)
        if ganador is not None:
            return ganador
        if self.es_mini_tablero_lleno(fila_meta, col_meta):
            return 'EMPATE'
        return None

    # ----- Detección (críticos para minimax) -----

    def detectar_ganador_mini(self, tablero_3x3: List[List[Optional[str]]]) -> Optional[str]:
        """Detecta si alguien ganó en un mini-tablero (3-en-línea)."""
        for linea in LINEAS_MINI_TABLERO:
            (f1, c1), (f2, c2), (f3, c3) = linea
            v1 = tablero_3x3[f1][c1]
            if v1 is not None and v1 == tablero_3x3[f2][c2] == tablero_3x3[f3][c3]:
                return v1
        return None

    def detectar_ganador_meta(self) -> Optional[str]:
        """Detecta si alguien ganó el JUEGO (3 campos en línea en meta-tablero)."""
        for linea in LINEAS_META_TABLERO:
            (f1, c1), (f2, c2), (f3, c3) = linea
            v1 = self.meta_tablero[f1][c1]
            if v1 in (JUGADOR_X, JUGADOR_O) and v1 == self.meta_tablero[f2][c2] == self.meta_tablero[f3][c3]:
                return v1
        return None

    def verificar_empate(self) -> bool:
        """Verifica si el juego está empatado (tablero lleno, sin ganador)."""
        if self.detectar_ganador_meta() is not None:
            return False
        return all(
            self.meta_tablero[f][c] is not None
            for f in range(TAMAÑO_META)
            for c in range(TAMAÑO_META)
        )

    # ----- Estado -----

    def es_mini_tablero_lleno(self, fila_meta: int, col_meta: int) -> bool:
        """Verifica si un mini-tablero está completamente lleno."""
        mini = self.mini_tableros[self._indice_mini(fila_meta, col_meta)]
        return all(celda is not None for fila in mini for celda in fila)

    def es_mini_tablero_disponible(self, fila_meta: int, col_meta: int) -> bool:
        """
        Verifica si se puede jugar en un mini-tablero.

        Returns:
            False si ya fue ganado, está lleno, o es un empate.
            True si todavía tiene casillas vacías.
        """
        return self.meta_tablero[fila_meta][col_meta] is None

    # ----- Representación y debug -----

    def __str__(self) -> str:
        """Retorna representación en string del tablero para mostrar en terminal."""
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

        Usado por minimax para explorar variaciones. No copia el
        historial (se descarta para ahorrar memoria).
        """
        nuevo = Tablero()
        nuevo.mini_tableros = [
            [fila[:] for fila in mini] for mini in self.mini_tableros
        ]
        nuevo.meta_tablero = [fila[:] for fila in self.meta_tablero]
        return nuevo

    def get_estado_hash(self) -> int:
        """
        Retorna un identificador hash del estado actual.

        Convierte mini_tableros y meta_tablero a tuplas inmutables y aplica
        hash() de Python. La probabilidad de colisión es extremadamente baja
        y el cálculo es O(81), suficientemente rápido para llamarse miles de
        veces durante minimax.
        """
        mini_tuple = tuple(
            tuple(tuple(fila) for fila in mini) for mini in self.mini_tableros
        )
        meta_tuple = tuple(tuple(fila) for fila in self.meta_tablero)
        return hash((mini_tuple, meta_tuple))


# =============================================================================
# MOVIMIENTOS VÁLIDOS
# =============================================================================

def movimientos_validos_mini(tablero_3x3: List[List[Optional[str]]]) -> List[Tuple[int, int]]:
    """
    Retorna casillas vacías en un mini-tablero específico.

    Returns:
        Lista de tuplas (fila, col) de casillas vacías
    """
    return [
        (fila, col)
        for fila in range(TAMAÑO_MINI)
        for col in range(TAMAÑO_MINI)
        if tablero_3x3[fila][col] is None
    ]


def mini_tableros_disponibles(tablero: Tablero) -> List[Tuple[int, int]]:
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


def movimientos_validos(tablero: Tablero, tablero_destino: Optional[Tuple[int, int]]) -> List[Tuple[int, int, int, int]]:
    """
    Retorna lista de movimientos válidos desde la posición actual.

    Args:
        tablero: Estado actual del juego
        tablero_destino: Tupla (fila_meta, col_meta) indicando dónde DEBE jugar.
                        Si None, puede jugar en cualquier lado (primer movimiento)

    Returns:
        Lista de tuplas (fila_meta, col_meta, fila_mini, col_mini)

    Reglas:
    - Si tablero_destino es None: jugador puede jugar en cualquier casilla vacía
    - Si tablero_destino ya fue ganado/empatado/lleno: puede jugar en
      cualquier mini-tablero disponible
    - Si tablero_destino es normal: solo puede jugar ahí
    """
    if tablero.detectar_ganador_meta() is not None or tablero.verificar_empate():
        return []

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


# =============================================================================
# EVALUADOR (FUNCIÓN HEURÍSTICA)
# =============================================================================
#
# evaluar_posicion() combina 7 componentes ponderados (pesos en la sección
# de CONFIGURACIÓN). Explicación detallada de cada uno, con ejemplos
# numéricos, en HEURISTICA.md (documento aparte del proyecto).

def contar_2_en_linea(tablero_3x3: List[List[Optional[str]]], jugador: str) -> int:
    """
    Cuenta cuántas líneas tienen 2 del jugador y 1 casilla vacía (amenaza).

    Funciona tanto para un mini-tablero como para el meta-tablero (misma
    disposición de 8 líneas: 3 filas + 3 columnas + 2 diagonales).
    """
    conteo = 0
    for linea in LINEAS_MINI_TABLERO:
        valores = [tablero_3x3[fila][col] for fila, col in linea]
        if valores.count(jugador) == 2 and valores.count(None) == 1:
            conteo += 1
    return conteo


def evaluar_progreso_meta(tablero: Tablero) -> int:
    """
    Evalúa qué tan cerca está cada jugador de ganar el meta-tablero.

    Returns:
        VALOR_GANADOR si X ya ganó el juego, VALOR_PERDEDOR si ganó O;
        si no, la diferencia de amenazas (2-en-línea) de X menos O en el
        meta-tablero.
    """
    ganador = tablero.detectar_ganador_meta()
    if ganador == JUGADOR_X:
        return VALOR_GANADOR
    if ganador == JUGADOR_O:
        return VALOR_PERDEDOR

    amenazas_x = contar_2_en_linea(tablero.meta_tablero, JUGADOR_X)
    amenazas_o = contar_2_en_linea(tablero.meta_tablero, JUGADOR_O)
    return amenazas_x - amenazas_o


def evaluar_bifurcaciones(tablero: Tablero) -> int:
    """
    Detecta bifurcaciones: mini-tableros donde un jugador tiene 2 o más
    líneas de 2-en-línea simultáneas (múltiples amenazas de ganar ese campo).

    Evalúa los 9 mini-tableros, incluyendo los ya decididos: ganar un
    mini-tablero no borra su contenido real (solo fija meta_tablero), así
    que excluirlo aquí haría que la señal de dominio local desaparezca
    justo al completar la victoria, penalizando ganar en vez de premiarlo.
    """
    puntuacion = 0
    for fila_meta in range(TAMAÑO_META):
        for col_meta in range(TAMAÑO_META):
            mini = tablero.obtener_mini_tablero(fila_meta, col_meta)
            amenazas_x = contar_2_en_linea(mini, JUGADOR_X)
            amenazas_o = contar_2_en_linea(mini, JUGADOR_O)
            if amenazas_x >= 2:
                puntuacion += amenazas_x
            if amenazas_o >= 2:
                puntuacion -= amenazas_o
    return puntuacion


def evaluar_defensa(tablero: Tablero) -> int:
    """
    Evalúa el peligro inmediato: suma de amenazas (2-en-línea) de cada
    jugador en todos los mini-tableros.

    A diferencia de evaluar_bifurcaciones (que premia la concentración de
    amenazas en un mismo mini-tablero), esta función cuenta el peligro
    total disperso en cualquier mini-tablero.
    """
    amenazas_x_total = 0
    amenazas_o_total = 0
    for fila_meta in range(TAMAÑO_META):
        for col_meta in range(TAMAÑO_META):
            mini = tablero.obtener_mini_tablero(fila_meta, col_meta)
            amenazas_x_total += contar_2_en_linea(mini, JUGADOR_X)
            amenazas_o_total += contar_2_en_linea(mini, JUGADOR_O)
    return amenazas_x_total - amenazas_o_total


def evaluar_control_posiciones(tablero: Tablero) -> int:
    """
    Evalúa quién controla posiciones estratégicas del meta-tablero.

    El centro (E) y las esquinas valen más que los bordes, según
    IMPORTANCIA_CAMPO.
    """
    puntuacion = 0
    for fila_meta in range(TAMAÑO_META):
        for col_meta in range(TAMAÑO_META):
            valor = tablero.meta_tablero[fila_meta][col_meta]
            if valor == JUGADOR_X:
                puntuacion += IMPORTANCIA_CAMPO[(fila_meta, col_meta)]
            elif valor == JUGADOR_O:
                puntuacion -= IMPORTANCIA_CAMPO[(fila_meta, col_meta)]
    return puntuacion


def evaluar_mini_tableros(tablero: Tablero) -> int:
    """
    Evalúa la posesión local de cada uno de los 9 mini-tableros: casillas
    ocupadas por X vs O y sus amenazas (2-en-línea) potenciales.
    """
    puntuacion = 0
    for fila_meta in range(TAMAÑO_META):
        for col_meta in range(TAMAÑO_META):
            mini = tablero.obtener_mini_tablero(fila_meta, col_meta)
            casillas_x = sum(fila.count(JUGADOR_X) for fila in mini)
            casillas_o = sum(fila.count(JUGADOR_O) for fila in mini)
            amenazas_x = contar_2_en_linea(mini, JUGADOR_X)
            amenazas_o = contar_2_en_linea(mini, JUGADOR_O)
            puntuacion += (casillas_x - casillas_o) + (amenazas_x - amenazas_o)
    return puntuacion


def evaluar_amenaza_destino(tablero: Tablero, tablero_destino: Optional[Tuple[int, int]],
                            jugador_actual: str) -> int:
    """
    Evalúa el mini-tablero al que `jugador_actual` está obligado a jugar.

    Si ese mini-tablero ya tiene una amenaza (2-en-línea) de jugador_actual,
    es un regalo (puede ganarlo de inmediato). Si la amenaza es del rival,
    es una trampa. Si no hay restricción real (tablero_destino es None, o
    apunta a un mini-tablero ya decidido), se da un pequeño bono por la
    libertad de elegir.

    Returns:
        Puntuación en perspectiva de jugador_actual (positiva = le
        conviene). evaluar_posicion() la convierte a perspectiva absoluta
        de X antes de sumarla.
    """
    oponente = JUGADOR_O if jugador_actual == JUGADOR_X else JUGADOR_X

    if tablero_destino is None or not tablero.es_mini_tablero_disponible(*tablero_destino):
        return 1

    mini = tablero.obtener_mini_tablero(*tablero_destino)
    amenazas_propias = contar_2_en_linea(mini, jugador_actual)
    amenazas_rivales = contar_2_en_linea(mini, oponente)
    return amenazas_propias - amenazas_rivales


def evaluar_amenaza_destino_futura(tablero: Tablero, tablero_destino: Optional[Tuple[int, int]],
                                   jugador_actual: str) -> int:
    """
    Extiende evaluar_amenaza_destino un nivel más: no solo "¿es peligroso
    el mini-tablero al que me mandan?", sino "de las casillas que puedo
    jugar ahí, ¿a qué campo mandaría yo al rival después, y qué tan
    peligroso es ESE campo para él?".

    Si jugador_actual ya tiene una victoria inmediata en el mini-tablero
    obligatorio, tomarla domina cualquier otra consideración y no tiene
    sentido asomarse más allá — se retorna 0. Si no, se asume que
    jugador_actual jugaría racionalmente la casilla que manda al rival al
    campo que MENOS le convenga a él.

    Es una aproximación barata (un tablero más por casilla candidata, sin
    simular el movimiento de verdad) — no reemplaza una búsqueda real de
    minimax, solo le da a la heurística de hoja un poco más de "olfato"
    sobre el efecto en cadena de la regla del tablero obligatorio.

    Returns:
        Puntuación en perspectiva de jugador_actual, o 0 si no aplica (sin
        destino, ya decidido, tablero lleno, o ya hay victoria inmediata).
    """
    oponente = JUGADOR_O if jugador_actual == JUGADOR_X else JUGADOR_X

    if tablero_destino is None or not tablero.es_mini_tablero_disponible(*tablero_destino):
        return 0

    mini = tablero.obtener_mini_tablero(*tablero_destino)
    if contar_2_en_linea(mini, jugador_actual) > 0:
        return 0

    casillas_vacias = [
        (fila, col)
        for fila in range(TAMAÑO_MINI)
        for col in range(TAMAÑO_MINI)
        if mini[fila][col] is None
    ]
    if not casillas_vacias:
        return 0

    peligros_para_rival = []
    for fila, col in casillas_vacias:
        if not tablero.es_mini_tablero_disponible(fila, col):
            # Mandar al rival a un campo cerrado le permite elegir cualquier
            # campo abierto. Esa libertad lo favorece, por eso representa un
            # peligro pequeño en lugar de un valor neutral.
            peligro = 1
        else:
            siguiente = tablero.obtener_mini_tablero(fila, col)
            peligro = (
                contar_2_en_linea(siguiente, oponente)
                - contar_2_en_linea(siguiente, jugador_actual)
            )
        peligros_para_rival.append(peligro)

    mejor_para_jugador_actual = min(peligros_para_rival)
    return -mejor_para_jugador_actual


def evaluar_posicion(tablero: Tablero, es_maximizando: bool,
                     tablero_destino: Optional[Tuple[int, int]] = None,
                     debug: bool = False) -> int:
    """
    Evalúa la posición actual del tablero usando heurística multi-componente.

    Args:
        tablero: Estado actual del juego
        es_maximizando: True si estamos evaluando para X (maximizador),
                       False si estamos evaluando para O (minimizador).
                       La puntuación siempre se retorna en perspectiva
                       absoluta de X (positiva=ventaja X); este parámetro
                       se conserva para la convención de llamada de minimax.
        tablero_destino: Mini-tablero al que está obligado a jugar quien
                       mueve ahora (fila_meta, col_meta), o None si puede
                       elegir libremente.
        debug: Si True, imprime el desglose por componente (crudo y
               ponderado) antes de retornar. Usar solo para diagnóstico
               manual — minimax() lo llama sin este flag (miles de veces
               por jugada), así que activarlo dentro de la búsqueda
               inundaría la terminal y la haría mucho más lenta. Se deja
               como evidencia del proceso de prueba/depuración usado
               durante el desarrollo.

    Returns:
        Puntuación heurística (negativa para O favorable, positiva para X
        favorable). VALOR_GANADOR/VALOR_PERDEDOR/VALOR_EMPATE si el juego
        ya terminó.

    Componentes de evaluación:
    1. Progreso en meta-tablero (w=PESO_PROGRESO_META_TABLERO)
    2. Bifurcaciones y amenazas (w=PESO_AMENAZAS_BIFURCACIONES)
    3. Defensa crítica (w=PESO_DEFENSA_CRITICA)
    4. Control de posiciones clave (w=PESO_POSICIONES_CLAVE)
    5. Evaluación de mini-tableros (w=PESO_CONTROL_LOCAL)
    6. Amenaza en el mini-tablero de destino forzado (w=PESO_AMENAZA_DESTINO)
    7. Amenaza en el destino forzado un nivel más adelante (w=PESO_AMENAZA_DESTINO_FUTURA)
    """
    ganador = tablero.detectar_ganador_meta()
    if ganador == JUGADOR_X:
        if debug:
            print(f"[evaluar_posicion] TERMINAL: X ya ganó el meta-tablero -> {VALOR_GANADOR}")
        return VALOR_GANADOR
    if ganador == JUGADOR_O:
        if debug:
            print(f"[evaluar_posicion] TERMINAL: O ya ganó el meta-tablero -> {VALOR_PERDEDOR}")
        return VALOR_PERDEDOR
    if tablero.verificar_empate():
        if debug:
            print(f"[evaluar_posicion] TERMINAL: empate -> {VALOR_EMPATE}")
        return VALOR_EMPATE

    jugador_actual = JUGADOR_X if es_maximizando else JUGADOR_O
    progreso = evaluar_progreso_meta(tablero)
    bifurcaciones = evaluar_bifurcaciones(tablero)
    defensa = evaluar_defensa(tablero)
    control = evaluar_control_posiciones(tablero)
    mini = evaluar_mini_tableros(tablero)
    amenaza_destino_propia = evaluar_amenaza_destino(tablero, tablero_destino, jugador_actual)
    amenaza_destino = amenaza_destino_propia if jugador_actual == JUGADOR_X else -amenaza_destino_propia
    amenaza_futura_propia = evaluar_amenaza_destino_futura(tablero, tablero_destino, jugador_actual)
    amenaza_futura = amenaza_futura_propia if jugador_actual == JUGADOR_X else -amenaza_futura_propia

    componentes = [
        ("progreso_meta", progreso, PESO_PROGRESO_META_TABLERO),
        ("bifurcaciones", bifurcaciones, PESO_AMENAZAS_BIFURCACIONES),
        ("defensa", defensa, PESO_DEFENSA_CRITICA),
        ("control_posiciones", control, PESO_POSICIONES_CLAVE),
        ("mini_tableros", mini, PESO_CONTROL_LOCAL),
        ("amenaza_destino", amenaza_destino, PESO_AMENAZA_DESTINO),
        ("amenaza_destino_futura", amenaza_futura, PESO_AMENAZA_DESTINO_FUTURA),
    ]
    puntuacion = sum(crudo * peso for _, crudo, peso in componentes)

    if debug:
        print("[evaluar_posicion] " + " | ".join(
            f"{nombre}={crudo} (x{peso}={crudo * peso})" for nombre, crudo, peso in componentes
        ))
        print(f"[evaluar_posicion] TOTAL = {puntuacion}")

    return puntuacion


# =============================================================================
# MINIMAX (BÚSQUEDA CON PODA ALFA-BETA)
# =============================================================================
#
# Optimizaciones implementadas:
# 1. Alpha-Beta Pruning
# 2. Transposition Table (con límite de tamaño)
# 3. Move Ordering (incluye PV move ordering entre profundidades)
# 4. Iterative Deepening con presupuesto de tiempo adaptativo, corte duro
#    si se agota el tiempo, y corte anticipado si ya se probó una
#    victoria/derrota forzada
# 5. Valores terminales ajustados por profundidad (VALOR_GANADOR - nivel):
#    la IA prefiere ganar rápido y retrasar una derrota inevitable
# 6. Estadísticas de la última búsqueda en `ultimas_estadisticas`
# 7. Desempate aleatorio entre movimientos raíz igualmente óptimos (evita
#    que el self-play IA vs IA sea siempre la misma partida)

TIPO_EXACTO = "EXACTO"
TIPO_COTA_INFERIOR = "COTA_INFERIOR"
TIPO_COTA_SUPERIOR = "COTA_SUPERIOR"


class TranspositionTable:
    """
    Cachea evaluaciones de posiciones para no recalcularlas.

    Cada entrada distingue entre un valor exacto, una cota inferior y una
    cota superior. Así una rama cortada por alfa-beta nunca se reutiliza
    incorrectamente como si fuera un valor exacto.
    """

    def __init__(self):
        self.tabla: Dict[object, Tuple[int, str]] = {}

    def guardar(self, hash_estado: object, valor: int,
                tipo: str = TIPO_EXACTO) -> None:
        """Guarda puntuación y tipo de cota sin exceder el límite."""
        if len(self.tabla) >= LIMITE_ESTADOS_MEMORIA:
            return
        self.tabla[hash_estado] = (valor, tipo)

    def obtener(self, hash_estado: object) -> Optional[Tuple[int, str]]:
        """Retorna ``(valor, tipo)`` o None cuando la clave no existe."""
        return self.tabla.get(hash_estado)

    def limpiar(self) -> None:
        """Vacía la tabla por completo."""
        self.tabla.clear()


class TiempoAgotado(Exception):
    """Señal interna para abortar minimax en curso cuando se acaba el tiempo."""


# Deadline absoluto (time.monotonic()) durante una llamada a mejor_movimiento().
_tiempo_limite_absoluto: Optional[float] = None

# Nodos visitados durante la búsqueda en curso (para estadísticas).
_contador_nodos: int = 0

# Estadísticas de la última llamada a mejor_movimiento(): profundidad
# alcanzada, nodos visitados, valor encontrado, segundos usados y
# presupuesto de tiempo asignado.
ultimas_estadisticas: Dict[str, object] = {}


def _mueve_completa_linea(tablero_3x3: List[List[Optional[str]]], fila: int, col: int, valor: str) -> bool:
    """Indica si colocar `valor` en (fila, col) completaría una línea de 3, sin modificar el mini-tablero."""
    return any(
        (fila, col) in linea
        and all(
            tablero_3x3[f][c] == valor
            for f, c in linea
            if (f, c) != (fila, col)
        )
        for linea in LINEAS_MINI_TABLERO
    )


def ordenar_movimientos(tablero: Tablero, movimientos: list,
                       tablero_destino: Optional[Tuple[int, int]],
                       jugador: str,
                       movimiento_preferido: Optional[Tuple[int, int, int, int]] = None) -> list:
    """
    Ordena movimientos para mejorar la poda de Alpha-Beta.

    Orden: (0) movimiento_preferido si está en la lista (PV move
    ordering), (1) movimientos que ganan un mini-tablero de inmediato,
    (2) movimientos que bloquean una victoria del oponente, (3) el resto;
    dentro de cada grupo, prioriza campos de mayor IMPORTANCIA_CAMPO.
    """
    oponente = JUGADOR_O if jugador == JUGADOR_X else JUGADOR_X

    def prioridad(movimiento):
        if movimiento == movimiento_preferido:
            return (-1, 0)

        fila_meta, col_meta, fila_mini, col_mini = movimiento
        mini = tablero.obtener_mini_tablero(fila_meta, col_meta)
        importancia = -IMPORTANCIA_CAMPO[(fila_meta, col_meta)]

        if _mueve_completa_linea(mini, fila_mini, col_mini, jugador):
            return (0, importancia)
        if _mueve_completa_linea(mini, fila_mini, col_mini, oponente):
            return (1, importancia)
        return (2, importancia)

    return sorted(movimientos, key=prioridad)


def minimax(tablero: Tablero, profundidad: int, alfa: float, beta: float,
            es_maximizando: bool, tablero_destino: Optional[Tuple[int, int]],
            cache: TranspositionTable, nivel: int = 0) -> int:
    """
    Evaluación recursiva usando Minimax con Alpha-Beta Pruning.

    Args:
        tablero: Estado actual
        profundidad: Cuántos movimientos adelante buscar (0 = usar heurística)
        alfa, beta: Ventana de poda
        es_maximizando: True si es turno de X (max), False si es turno de O (min)
        tablero_destino: Restricción de dónde jugar
        cache: Transposition Table para cachear posiciones repetidas
        nivel: Distancia (en jugadas) desde la raíz de esta búsqueda. Se
               resta/suma a los valores terminales para que la IA prefiera
               ganar rápido y retrasar una derrota inevitable.

    Nota sobre la cache y `nivel`: como el valor terminal depende de
    `nivel` (no solo de `profundidad`), una entrada cacheada en una pasada
    de iterative deepening con profundidad_inicial=N ya NO es válida para
    una pasada con profundidad_inicial=M distinto. Por eso
    mejor_movimiento() crea una `cache` nueva en cada profundidad del
    iterative deepening en vez de reutilizar una sola durante todo el ciclo.
    """
    global _contador_nodos
    _contador_nodos += 1

    if _tiempo_limite_absoluto is not None and time.monotonic() >= _tiempo_limite_absoluto:
        raise TiempoAgotado()

    ganador = tablero.detectar_ganador_meta()
    if ganador == JUGADOR_X:
        return VALOR_GANADOR - nivel
    if ganador == JUGADOR_O:
        return VALOR_PERDEDOR + nivel
    if tablero.verificar_empate():
        return VALOR_EMPATE

    alfa_original = alfa
    beta_original = beta
    clave_cache = (tablero.get_estado_hash(), profundidad, tablero_destino, es_maximizando)
    entrada_cache = cache.obtener(clave_cache)
    if entrada_cache is not None:
        valor_cacheado, tipo_cache = entrada_cache
        if tipo_cache == TIPO_EXACTO:
            return valor_cacheado
        if tipo_cache == TIPO_COTA_INFERIOR:
            alfa = max(alfa, valor_cacheado)
        elif tipo_cache == TIPO_COTA_SUPERIOR:
            beta = min(beta, valor_cacheado)
        if alfa >= beta:
            return valor_cacheado

    if profundidad == 0:
        valor = evaluar_posicion(tablero, es_maximizando, tablero_destino)
        cache.guardar(clave_cache, valor, TIPO_EXACTO)
        return valor

    jugador_actual = JUGADOR_X if es_maximizando else JUGADOR_O
    movimientos = movimientos_validos(tablero, tablero_destino)
    movimientos = ordenar_movimientos(tablero, movimientos, tablero_destino, jugador_actual)

    if not movimientos:
        valor = evaluar_posicion(tablero, es_maximizando, tablero_destino)
        cache.guardar(clave_cache, valor, TIPO_EXACTO)
        return valor

    if es_maximizando:
        valor = float('-inf')
        indice = 0
        while indice < len(movimientos) and alfa < beta:
            movimiento = movimientos[indice]
            tablero.aplicar_movimiento(*movimiento, jugador_actual)
            siguiente_destino = (movimiento[2], movimiento[3])
            try:
                valor_hijo = minimax(tablero, profundidad - 1, alfa, beta, False, siguiente_destino, cache, nivel + 1)
            finally:
                # Si minimax() lanza TiempoAgotado, este deshacer DEBE
                # ejecutarse igual: es lo único que evita dejar el
                # movimiento pegado permanentemente al tablero real
                # mientras la excepción se propaga por la recursión.
                tablero.deshacer_movimiento()
            valor = max(valor, valor_hijo)
            alfa = max(alfa, valor)
            indice += 1
    else:
        valor = float('inf')
        indice = 0
        while indice < len(movimientos) and alfa < beta:
            movimiento = movimientos[indice]
            tablero.aplicar_movimiento(*movimiento, jugador_actual)
            siguiente_destino = (movimiento[2], movimiento[3])
            try:
                valor_hijo = minimax(tablero, profundidad - 1, alfa, beta, True, siguiente_destino, cache, nivel + 1)
            finally:
                tablero.deshacer_movimiento()
            valor = min(valor, valor_hijo)
            beta = min(beta, valor)
            indice += 1

    if valor <= alfa_original:
        tipo_valor = TIPO_COTA_SUPERIOR
    elif valor >= beta_original:
        tipo_valor = TIPO_COTA_INFERIOR
    else:
        tipo_valor = TIPO_EXACTO
    cache.guardar(clave_cache, valor, tipo_valor)
    return valor


def obtener_mejor_movimiento_hoja(tablero: Tablero, profundidad: int,
                                   alfa: float, beta: float, es_maximizando: bool,
                                   tablero_destino: Optional[Tuple[int, int]],
                                   cache: TranspositionTable,
                                   movimiento_preferido: Optional[Tuple[int, int, int, int]] = None
                                   ) -> Optional[Tuple[int, int, int, int, int]]:
    """
    Versión de minimax que además retorna qué movimiento en la raíz produjo
    la mejor puntuación (minimax() solo retorna la puntuación).

    Args:
        movimiento_preferido: Mejor jugada encontrada en la profundidad
            anterior del iterative deepening, si la hay.

    Returns:
        (fila_meta, col_meta, fila_mini, col_mini, puntuacion) del mejor
        movimiento raíz, o None si no hay movimientos legales.

    Nota: cuando varios movimientos raíz empatan en la misma puntuación
    óptima, se elige uno al azar entre ellos (en vez de siempre el primero
    según el orden de exploración). Sin esto, minimax es 100% determinista
    y una partida IA vs IA desde el tablero vacío es siempre la misma. El
    desempate aleatorio no cambia la calidad de juego (todos los
    movimientos empatados son igual de óptimos por definición).
    """
    jugador_actual = JUGADOR_X if es_maximizando else JUGADOR_O
    movimientos = movimientos_validos(tablero, tablero_destino)
    if not movimientos:
        return None
    movimientos = ordenar_movimientos(tablero, movimientos, tablero_destino, jugador_actual, movimiento_preferido)

    mejores_movimientos = [movimientos[0]]
    if es_maximizando:
        mejor_valor = float('-inf')
        indice = 0
        while indice < len(movimientos) and alfa < beta:
            movimiento = movimientos[indice]
            tablero.aplicar_movimiento(*movimiento, jugador_actual)
            siguiente_destino = (movimiento[2], movimiento[3])
            try:
                valor = minimax(tablero, profundidad - 1, alfa, beta, False, siguiente_destino, cache, nivel=1)
            finally:
                tablero.deshacer_movimiento()
            if valor > mejor_valor:
                mejor_valor = valor
                mejores_movimientos = [movimiento]
            elif valor == mejor_valor:
                mejores_movimientos.append(movimiento)
            alfa = max(alfa, mejor_valor)
            indice += 1
    else:
        mejor_valor = float('inf')
        indice = 0
        while indice < len(movimientos) and alfa < beta:
            movimiento = movimientos[indice]
            tablero.aplicar_movimiento(*movimiento, jugador_actual)
            siguiente_destino = (movimiento[2], movimiento[3])
            try:
                valor = minimax(tablero, profundidad - 1, alfa, beta, True, siguiente_destino, cache, nivel=1)
            finally:
                tablero.deshacer_movimiento()
            if valor < mejor_valor:
                mejor_valor = valor
                mejores_movimientos = [movimiento]
            elif valor == mejor_valor:
                mejores_movimientos.append(movimiento)
            beta = min(beta, mejor_valor)
            indice += 1

    mejor_movimiento = random.choice(mejores_movimientos)
    return (*mejor_movimiento, mejor_valor)


def _contar_marcas(tablero: Tablero) -> Dict[str, int]:
    """Cuenta cuántas casillas tiene cada jugador, para inferir de quién es el turno."""
    conteo = {JUGADOR_X: 0, JUGADOR_O: 0}
    for mini in tablero.mini_tableros:
        for fila in mini:
            for celda in fila:
                if celda in conteo:
                    conteo[celda] += 1
    return conteo


def _contar_casillas_restantes(tablero: Tablero) -> int:
    """Cuenta casillas vacías en mini-tableros todavía disponibles (para elegir el presupuesto de tiempo)."""
    restantes = 0
    for fila_meta, col_meta in mini_tableros_disponibles(tablero):
        mini = tablero.obtener_mini_tablero(fila_meta, col_meta)
        restantes += sum(fila.count(None) for fila in mini)
    return restantes


def _calcular_presupuesto(tablero: Tablero, tiempo_limite: float) -> float:
    """
    Elige cuánto tiempo dedicar a esta jugada según la etapa de la partida:
    poco en la apertura (mucho ramaje, no vale la pena buscar más hondo),
    más cuando quedan pocas casillas (decisiones más críticas).

    El resultado nunca excede tiempo_limite — solo puede acortarlo.
    """
    restantes = _contar_casillas_restantes(tablero)
    if restantes >= CASILLAS_RESTANTES_APERTURA:
        presupuesto = TIEMPO_APERTURA
    elif restantes >= CASILLAS_RESTANTES_MEDIO:
        presupuesto = TIEMPO_MEDIO_PARTIDA
    else:
        presupuesto = TIEMPO_FINAL_PARTIDA
    return max(0.0, min(presupuesto, tiempo_limite))


def mejor_movimiento(tablero: Tablero, tablero_destino: Optional[Tuple[int, int]],
                     tiempo_limite: float = TIEMPO_LIMITE) -> Optional[Tuple[int, int, int, int]]:
    """
    Encuentra el mejor movimiento usando Iterative Deepening + Minimax con
    Alpha-Beta Pruning.

    Args:
        tablero: Estado actual
        tablero_destino: Dónde debe jugar (None si puede jugar en cualquier lado)
        tiempo_limite: Segundos máximos para decidir; el presupuesto real
            usado puede ser menor (ver _calcular_presupuesto) pero nunca mayor.

    Returns:
        Tupla (fila_meta, col_meta, fila_mini, col_mini) del mejor
        movimiento encontrado, o None si no hay movimientos legales.

    El turno (X u O) se infiere del tablero: si hay tantas 'X' como 'O',
    es turno de X (primer jugador); si hay una 'X' más que 'O', es turno de O.

    Busca profundidad 1, 2, 3... hasta agotar el presupuesto, conservando
    siempre el mejor movimiento de la última profundidad completada. Se
    detiene antes si ya se probó una victoria o derrota forzada. Después
    de llamar, las estadísticas quedan en `ultimas_estadisticas`.
    """
    global _tiempo_limite_absoluto, _contador_nodos, ultimas_estadisticas

    movimientos_legales = movimientos_validos(tablero, tablero_destino)
    if not movimientos_legales:
        ultimas_estadisticas = {
            "profundidad": 0,
            "nodos": 0,
            "valor": VALOR_EMPATE,
            "segundos": 0.0,
            "presupuesto": 0.0,
            "interrumpida": False,
        }
        return None
    if len(movimientos_legales) == 1:
        ultimas_estadisticas = {
            "profundidad": 0,
            "nodos": 0,
            "valor": 0,
            "segundos": 0.0,
            "presupuesto": 0.0,
            "interrumpida": False,
        }
        return movimientos_legales[0]

    conteo = _contar_marcas(tablero)
    es_maximizando = conteo[JUGADOR_X] == conteo[JUGADOR_O]

    presupuesto = _calcular_presupuesto(tablero, tiempo_limite)
    tiempo_inicio = time.monotonic()
    _tiempo_limite_absoluto = tiempo_inicio + presupuesto
    _contador_nodos = 0

    mejor_encontrado = movimientos_legales[0]
    mejor_valor = 0
    profundidad_alcanzada = 0
    movimiento_preferido = None
    busqueda_interrumpida = False
    seguir_buscando = presupuesto > 0
    profundidad = 1

    try:
        while profundidad <= 20 and seguir_buscando:
            tiempo_transcurrido = time.monotonic() - tiempo_inicio
            seguir_buscando = tiempo_transcurrido <= 0.9 * presupuesto

            resultado = None
            if seguir_buscando:
                cache = TranspositionTable()
                resultado = obtener_mejor_movimiento_hoja(
                    tablero, profundidad, float('-inf'), float('inf'),
                    es_maximizando, tablero_destino, cache, movimiento_preferido
                )

            if resultado is None:
                seguir_buscando = False
            else:
                mejor_encontrado = resultado[:4]
                mejor_valor = resultado[4]
                movimiento_preferido = mejor_encontrado
                profundidad_alcanzada = profundidad
                seguir_buscando = abs(mejor_valor) < VALOR_GANADOR // 2

            profundidad += 1
    except TiempoAgotado:
        busqueda_interrumpida = True
    finally:
        _tiempo_limite_absoluto = None

    ultimas_estadisticas = {
        "profundidad": profundidad_alcanzada,
        "nodos": _contador_nodos,
        "valor": mejor_valor,
        "segundos": time.monotonic() - tiempo_inicio,
        "presupuesto": presupuesto,
        "interrumpida": busqueda_interrumpida,
    }

    return mejor_encontrado


# =============================================================================
# INTERFAZ DE TERMINAL
# =============================================================================

def _simbolo_campo(tablero: Tablero, fila_meta: int, col_meta: int) -> str:
    """Retorna el símbolo a mostrar para un campo del meta-tablero: su letra (A-I) si sigue en juego, o 'X'/'O'/'=' si ya se decidió."""
    valor = tablero.meta_tablero[fila_meta][col_meta]
    if valor == 'EMPATE':
        return '='
    if valor in (JUGADOR_X, JUGADOR_O):
        return valor
    return INDICES_INVERSOS[(fila_meta, col_meta)]


def _simbolo_celda(tablero: Tablero, fila_meta: int, col_meta: int, fila_mini: int, col_mini: int) -> str:
    """Retorna el símbolo a mostrar para una casilla: su letra (a-i) si está vacía, o 'X'/'O' si está ocupada."""
    valor = tablero.obtener_casilla(fila_meta, col_meta, fila_mini, col_mini)
    if valor is not None:
        return valor
    return INDICES_MINI_INVERSOS[(fila_mini, col_mini)]


def mostrar_tablero(tablero: Tablero) -> None:
    """
    Imprime el tablero en terminal de forma legible.

    Cada casilla vacía muestra su letra de posición (a-i) y cada campo
    del meta-tablero muestra su letra (A-I) mientras sigue disponible,
    para que el jugador identifique de inmediato qué escribir.
    """
    print("TABLERO ACTUAL:\n")
    for bloque_fila in range(TAMAÑO_META):
        encabezados = []
        for col_meta in range(TAMAÑO_META):
            letra_campo = INDICES_INVERSOS[(bloque_fila, col_meta)]
            estado = tablero.meta_tablero[bloque_fila][col_meta]
            etiqueta = f"CAMPO {letra_campo}"
            if estado in (JUGADOR_X, JUGADOR_O):
                etiqueta += f" [ganador: {estado}]"
            elif estado == 'EMPATE':
                etiqueta += " [empate]"
            encabezados.append(etiqueta.ljust(20))
        print("  ".join(encabezados))

        for fila_mini in range(TAMAÑO_MINI):
            partes = []
            for col_meta in range(TAMAÑO_META):
                celdas = [
                    _simbolo_celda(tablero, bloque_fila, col_meta, fila_mini, col_mini)
                    for col_mini in range(TAMAÑO_MINI)
                ]
                partes.append('  '.join(celdas).ljust(20))
            print("  ".join(partes))
        print()

    print("META-TABLERO:")
    for fila_meta in range(TAMAÑO_META):
        print(' | '.join(_simbolo_campo(tablero, fila_meta, c) for c in range(TAMAÑO_META)))
        if fila_meta < TAMAÑO_META - 1:
            print('-' * 9)


def mostrar_mensaje(mensaje: str) -> None:
    """Imprime un mensaje de estado al usuario."""
    print(mensaje)


def convertir_texto_a_movimiento(entrada: str) -> Tuple[int, int, int, int]:
    """Convierte una coordenada como ``Gc`` a sus cuatro índices internos."""
    texto = entrada.strip()
    if len(texto) != 2:
        raise ValueError(
            f"Entrada inválida: '{texto}'. Debe tener 2 caracteres, por ejemplo 'Gc'."
        )

    campo, posicion = texto[0], texto[1]
    if campo not in CAMPOS:
        raise ValueError(
            f"Campo inválido: '{campo}'. Debe ser una letra mayúscula de A a I."
        )
    if posicion not in POSICIONES_MINI:
        raise ValueError(
            f"Posición inválida: '{posicion}'. Debe ser una letra minúscula de a a i."
        )

    fila_meta, col_meta = CAMPOS[campo]
    fila_mini, col_mini = POSICIONES_MINI[posicion]
    return (fila_meta, col_meta, fila_mini, col_mini)


def obtener_movimiento_usuario() -> Tuple[int, int, int, int]:
    """
    Lee movimiento del usuario en formato "Ac" (Campo A, mini-posición c).

    Repite la petición hasta recibir una entrada válida.

    Returns:
        Tupla (fila_meta, col_meta, fila_mini, col_mini)
    """
    movimiento = None
    while movimiento is None:
        entrada = input("Ingresa tu movimiento (Campo+Posición, ej. 'Gc'): ").strip()
        try:
            movimiento = convertir_texto_a_movimiento(entrada)
        except ValueError as error:
            mostrar_mensaje(str(error))
    return movimiento


def mostrar_movimiento(campo: str, posicion: Optional[str] = None, jugador: Optional[str] = None) -> None:
    """
    Muestra un movimiento en formato "Campo+Posición" (ej. "Gc").

    Args:
        campo: Letra del campo ('G'), o el movimiento completo ('Gc') si posicion es None
        posicion: Letra de la posición ('c'), opcional si ya viene junto en campo
        jugador: Nombre de quién juega (por defecto "Jugador")
    """
    movimiento = campo if posicion is None else f"{campo}{posicion}"
    quien = jugador if jugador else "Jugador"
    mostrar_mensaje(f"{quien} juega: {movimiento}")


def mostrar_movimiento_ia(fila_meta: int, col_meta: int, fila_mini: int, col_mini: int) -> None:
    """Muestra el movimiento que hizo la IA. Ejemplo: "IA juega: Gc"."""
    campo = INDICES_INVERSOS[(fila_meta, col_meta)]
    posicion = INDICES_MINI_INVERSOS[(fila_mini, col_mini)]
    mostrar_movimiento(campo, posicion, jugador="IA")


def mostrar_estadisticas_ia(estadisticas: dict) -> None:
    """
    Muestra un resumen de la búsqueda que hizo la IA para decidir su
    último movimiento (ultimas_estadisticas).

    Ejemplo: "Profundidad: 6 | Nodos: 12,345 | Valor: 37 | Tiempo: 3.21s / 4.0s"
    """
    if not estadisticas:
        return
    mostrar_mensaje(
        f"Profundidad: {estadisticas.get('profundidad', '?')} | "
        f"Nodos: {estadisticas.get('nodos', 0):,} | "
        f"Valor: {estadisticas.get('valor', 0)} | "
        f"Tiempo: {estadisticas.get('segundos', 0):.2f}s / {estadisticas.get('presupuesto', 0):.1f}s"
    )


def solicitar_simbolo_jugador() -> str:
    """Pregunta con qué símbolo quiere jugar el humano (para modo humano vs IA). Returns: 'X' o 'O'."""
    respuesta = ""
    while respuesta not in (JUGADOR_X, JUGADOR_O):
        respuesta = input(
            "¿Quieres ser X (empiezas tú) u O (empieza la IA)? (X/O): "
        ).strip().upper()
        if respuesta in (JUGADOR_X, JUGADOR_O):
            mostrar_mensaje(
                "Elegiste X: tú comienzas."
                if respuesta == JUGADOR_X
                else "Elegiste O: la IA comienza con X."
            )
        else:
            mostrar_mensaje(f"Respuesta inválida: '{respuesta}'. Escribe 'X' o 'O'.")
    return respuesta


def solicitar_modo_juego() -> str:
    """Solicita uno de los tres modos disponibles y valida la respuesta."""
    opcion = ""
    while opcion not in ("1", "2", "3"):
        print("1. Humano vs Humano")
        print("2. IA vs IA")
        print("3. Humano vs IA")
        opcion = input("Elige una opción (1/2/3): ").strip()
        if opcion not in ("1", "2", "3"):
            mostrar_mensaje("Opción inválida. Escribe 1, 2 o 3.")
    return opcion


def mostrar_estado_juego(tablero: Tablero, turno: str) -> None:
    """Muestra información de estado del juego: turno actual, ganador o empate."""
    ganador = tablero.detectar_ganador_meta()
    if ganador is not None:
        mostrar_mensaje(f"¡{ganador} ha ganado el juego!")
    elif tablero.verificar_empate():
        mostrar_mensaje("El juego terminó en empate.")
    else:
        mostrar_mensaje(f"Turno de: {turno}")


# =============================================================================
# LOOP PRINCIPAL DEL JUEGO
# =============================================================================

def obtener_movimiento_valido(tablero: Tablero, tablero_destino: Optional[Tuple[int, int]]) -> Tuple[int, int, int, int]:
    """
    Pide movimientos al usuario hasta obtener uno legal.

    Un movimiento es legal si aparece en movimientos_validos() para el
    tablero_destino vigente (respeta la casilla obligatoria y que esté vacía).
    """
    movimientos_legales = movimientos_validos(tablero, tablero_destino)
    while True:
        movimiento = obtener_movimiento_usuario()
        if movimiento in movimientos_legales:
            return movimiento
        mostrar_mensaje("Movimiento no permitido: la casilla está ocupada o no corresponde al campo obligatorio.")


def imprimir_resultado(tablero: Tablero) -> None:
    """Imprime el tablero final y el resultado del juego."""
    mostrar_tablero(tablero)
    ganador = tablero.detectar_ganador_meta()
    if ganador is not None:
        mostrar_mensaje(f"{ganador} GANA")
    else:
        mostrar_mensaje("EMPATE")


def _movimiento_ia(tablero: Tablero, tablero_destino: Optional[Tuple[int, int]]) -> Tuple[int, int, int, int]:
    """Obtiene el movimiento de la IA (minimax), lo anuncia y muestra estadísticas de la búsqueda."""
    movimiento = mejor_movimiento(tablero, tablero_destino)
    mostrar_movimiento_ia(*movimiento)
    mostrar_estadisticas_ia(ultimas_estadisticas)
    return movimiento


ObtenerMovimiento = Callable[[Tablero, Optional[Tuple[int, int]]], Tuple[int, int, int, int]]


def _ejecutar_partida(tablero: Tablero, obtener_movimiento_x: ObtenerMovimiento,
                     obtener_movimiento_o: ObtenerMovimiento) -> None:
    """
    Corre el loop principal de una partida, delegando en las funciones dadas
    cómo obtener el movimiento de X y de O (humano o IA) en cada turno.
    """
    es_turno_x = True
    tablero_destino = None
    partida_terminada = False

    while not partida_terminada:
        mostrar_tablero(tablero)

        if es_turno_x:
            mostrar_mensaje("Turno de X")
            jugador = JUGADOR_X
            movimiento = obtener_movimiento_x(tablero, tablero_destino)
        else:
            mostrar_mensaje("Turno de O")
            jugador = JUGADOR_O
            movimiento = obtener_movimiento_o(tablero, tablero_destino)

        tablero.aplicar_movimiento(*movimiento, jugador)

        partida_terminada = (
            tablero.detectar_ganador_meta() is not None
            or tablero.verificar_empate()
        )
        if partida_terminada:
            imprimir_resultado(tablero)
        else:
            es_turno_x = not es_turno_x
            tablero_destino = (movimiento[2], movimiento[3])


def jugar() -> None:
    """Ejecuta un juego completo de Ultimate Tic-Tac-Toe humano vs humano."""
    _ejecutar_partida(Tablero(), obtener_movimiento_valido, obtener_movimiento_valido)


def jugar_ia_vs_ia() -> None:
    """Ejecuta un juego completo IA vs IA (minimax contra sí mismo), para observar cómo juega."""
    _ejecutar_partida(Tablero(), _movimiento_ia, _movimiento_ia)


def jugar_humano_vs_ia() -> None:
    """
    Ejecuta un juego completo humano vs IA.

    Pregunta con qué símbolo quiere jugar el humano. X siempre inicia: si
    el humano elige X comienza la persona; si elige O comienza la IA.
    """
    tablero = Tablero()
    simbolo_humano = solicitar_simbolo_jugador()

    if simbolo_humano == JUGADOR_X:
        _ejecutar_partida(tablero, obtener_movimiento_valido, _movimiento_ia)
    else:
        _ejecutar_partida(tablero, _movimiento_ia, obtener_movimiento_valido)


if __name__ == "__main__":
    opcion = solicitar_modo_juego()

    if opcion == "1":
        jugar()
    elif opcion == "2":
        jugar_ia_vs_ia()
    elif opcion == "3":
        jugar_humano_vs_ia()
