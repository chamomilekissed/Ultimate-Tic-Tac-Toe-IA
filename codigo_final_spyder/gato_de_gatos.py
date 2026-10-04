"""
GATO DE GATOS (ULTIMATE TIC-TAC-TOE) CON MINIMAX
=================================================

Archivo único de entrega: contiene todo el motor del juego (representación
del tablero, generación de movimientos, heurística de evaluación, búsqueda
Minimax con poda alfa-beta, interfaz de terminal y el ciclo principal).

Cómo jugar
----------
Ejecutar este archivo con Python 3 o en Spyder. La primera pregunta solicita
si le toca comenzar a nuestro sistema o al jugador externo, como requiere el
formato del torneo. Quien comienza usa X internamente.

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
siga abierto."""

import time
from typing import Callable, Dict, List, Optional, Sequence, Tuple


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Símbolos de jugadores
JUGADOR_X = "X"
JUGADOR_O = "O"

# Dimensiones del tablero. Las constantes usan MAYÚSCULAS_CON_GUIONES_BAJOS.
DIMENSION_MINI = 3  # Cada mini-tablero tiene 3 filas y 3 columnas.
DIMENSION_META = 3  # El meta-tablero contiene 3 por 3 mini-tableros.

# Índices de meta-tablero
# A | B | C
# D | E | F
# G | H | I
CAMPOS = {
    "A": (0, 0),
    "B": (0, 1),
    "C": (0, 2),
    "D": (1, 0),
    "E": (1, 1),
    "F": (1, 2),
    "G": (2, 0),
    "H": (2, 1),
    "I": (2, 2),
}
INDICES_INVERSOS = {v: k for k, v in CAMPOS.items()}

# Índices de mini-tablero
# a | b | c
# d | e | f
# g | h | i
POSICIONES_MINI = {
    "a": (0, 0),
    "b": (0, 1),
    "c": (0, 2),
    "d": (1, 0),
    "e": (1, 1),
    "f": (1, 2),
    "g": (2, 0),
    "h": (2, 1),
    "i": (2, 2),
}
INDICES_MINI_INVERSOS = {v: k for k, v in POSICIONES_MINI.items()}

# ===== Minimax =====

TIEMPO_LIMITE = 30  # Límite de tiempo por jugada (segundos), nunca se excede

# Valores heurísticos extremos
VALOR_GANADOR = 10000
VALOR_PERDEDOR = -10000
VALOR_EMPATE = 0

# ===== Pesos de la función heurística =====

# Líneas abiertas de uno o dos campos en el meta-tablero.
PESO_PROGRESO_META_TABLERO = 18
# Bono por cada amenaza adicional de una bifurcación.
PESO_AMENAZAS_BIFURCACIONES = 6
# Amenazas inmediatas en campos todavía jugables.
PESO_DEFENSA_CRITICA = 5
# Centro, esquinas y bordes ya ganados.
PESO_POSICIONES_CLAVE = 6
# Líneas locales en desarrollo, sin duplicar amenazas.
PESO_CONTROL_LOCAL = 1
# Situación táctica del campo obligatorio.
PESO_AMENAZA_DESTINO = 8
# Consecuencia del campo al que se enviará al rival.
PESO_AMENAZA_DESTINO_FUTURA = 4

VALOR_LINEA_META_UN_CAMPO = 1
VALOR_LINEA_META_DOS_CAMPOS = 8
BONO_LIBERTAD_ELECCION = 2
BONO_GANAR_MINI_TABLERO = 3

# ===== Presupuesto de tiempo por etapa de partida =====
# (según casillas vacías en mini-tableros disponibles; siempre acotado por
# el tiempo_limite que reciba mejor_movimiento())
CASILLAS_RESTANTES_APERTURA = 55
CASILLAS_RESTANTES_MEDIO = 25
TIEMPO_APERTURA = 15.0
TIEMPO_MEDIO_PARTIDA = 20.0
TIEMPO_FINAL_PARTIDA = 27.0

# Cantidad máxima de posiciones guardadas en la tabla de transposiciones.
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
    Representa el estado completo del juego.

    Estructura interna:
    - meta_tablero: arreglo 3x3 con ganadores de mini-tableros ('X', 'O', None, 'EMPATE')
    - mini_tableros: arreglo de 9 tableros 3x3 internos (índice = fila_meta * 3 + col_meta)
    - historial: pila de movimientos previos para deshacer
    """

    def __init__(self):
        """
        Inicializa un tablero vacío.

        - meta_tablero: 3x3 lleno de None (ningún mini-tablero decidido)
        - mini_tableros: 9 mini-tableros de 3x3, todas las casillas en None
        - historial: pila vacía
        """
        self.meta_tablero: List[List[Optional[str]]] = [
            [None for _ in range(DIMENSION_META)] for _ in range(DIMENSION_META)
        ]
        self.mini_tableros: List[List[List[Optional[str]]]] = [
            [[None for _ in range(DIMENSION_MINI)] for _ in range(DIMENSION_MINI)]
            for _ in range(DIMENSION_META * DIMENSION_META)
        ]
        self.historial: List[Tuple[int, int, int, int, Optional[str]]] = []

    def _indice_mini(self, fila_meta: int, col_meta: int) -> int:
        """Convierte coordenadas del meta-tablero al índice de ``mini_tableros``."""
        return fila_meta * DIMENSION_META + col_meta

    # ----- Modificación -----

    def aplicar_movimiento(
        self, fila_meta: int, col_meta: int, fila_mini: int, col_mini: int, jugador: str
    ) -> bool:
        """
        Aplica un movimiento al tablero.

        Parámetros:
            fila_meta, col_meta: Posición del mini-tablero; enteros de 0 a 2.
            fila_mini, col_mini: Posición interna; enteros de 0 a 2.
            jugador: Símbolo ``'X'`` o ``'O'``.

        Retorna:
            ``True`` si se aplicó el movimiento; ``False`` si algún dato es
            inválido, el mini-tablero terminó o la casilla está ocupada.
        """
        coordenadas = (fila_meta, col_meta, fila_mini, col_mini)
        coordenadas_validas = all(0 <= valor < DIMENSION_MINI for valor in coordenadas)
        jugador_valido = jugador in (JUGADOR_X, JUGADOR_O)

        if not coordenadas_validas or not jugador_valido:
            return False
        if not self.es_mini_tablero_disponible(fila_meta, col_meta):
            return False

        indice_mini = self._indice_mini(fila_meta, col_meta)
        if self.mini_tableros[indice_mini][fila_mini][col_mini] is not None:
            return False

        valor_meta_previo = self.meta_tablero[fila_meta][col_meta]
        self.historial.append(
            (fila_meta, col_meta, fila_mini, col_mini, valor_meta_previo)
        )

        self.mini_tableros[indice_mini][fila_mini][col_mini] = jugador

        if valor_meta_previo is None:
            resultado_mini = self.obtener_ganador_mini(fila_meta, col_meta)
            if resultado_mini is not None:
                self.meta_tablero[fila_meta][col_meta] = resultado_mini

        return True

    def deshacer_movimiento(self) -> bool:
        """
        Deshace el último movimiento (restaura del historial).

        Retorna:
            ``True`` si se deshizo una jugada; ``False`` si no había ninguna.
        """
        if not self.historial:
            return False

        fila_meta, col_meta, fila_mini, col_mini, valor_meta_previo = (
            self.historial.pop()
        )
        indice_mini = self._indice_mini(fila_meta, col_meta)
        self.mini_tableros[indice_mini][fila_mini][col_mini] = None
        self.meta_tablero[fila_meta][col_meta] = valor_meta_previo
        return True

    # ----- Lectura (críticos para velocidad) -----

    def obtener_mini_tablero(
        self, fila_meta: int, col_meta: int
    ) -> List[List[Optional[str]]]:
        """Retorna el mini-tablero específico (sin copiar, para velocidad)."""
        return self.mini_tableros[self._indice_mini(fila_meta, col_meta)]

    def obtener_casilla(
        self, fila_meta: int, col_meta: int, fila_mini: int, col_mini: int
    ) -> Optional[str]:
        """Retorna qué hay en una casilla específica ('X', 'O', o None)."""
        return self.mini_tableros[self._indice_mini(fila_meta, col_meta)][fila_mini][
            col_mini
        ]

    def obtener_ganador_mini(self, fila_meta: int, col_meta: int) -> Optional[str]:
        """
        Retorna quién ganó el mini-tablero especificado.

        Retorna:
            'X' si X ganó, 'O' si O ganó, 'EMPATE' si está lleno sin
            ganador, None si el juego sigue.
        """
        mini = self.mini_tableros[self._indice_mini(fila_meta, col_meta)]
        ganador = self.detectar_ganador_mini(mini)
        if ganador is not None:
            return ganador
        if self.es_mini_tablero_lleno(fila_meta, col_meta):
            return "EMPATE"
        return None

    # ----- Detección (críticos para minimax) -----

    def detectar_ganador_mini(
        self, tablero_3x3: List[List[Optional[str]]]
    ) -> Optional[str]:
        """Detecta si alguien ganó en un mini-tablero (3-en-línea)."""
        for linea in LINEAS_MINI_TABLERO:
            (f1, c1), (f2, c2), (f3, c3) = linea
            v1 = tablero_3x3[f1][c1]
            if v1 is not None and v1 == tablero_3x3[f2][c2] == tablero_3x3[f3][c3]:
                return v1
        return None

    def detectar_ganador_meta(self) -> Optional[str]:
        """Detecta si alguien ganó el juego (3 campos en línea en meta-tablero)."""
        for linea in LINEAS_META_TABLERO:
            (f1, c1), (f2, c2), (f3, c3) = linea
            v1 = self.meta_tablero[f1][c1]
            if (
                v1 in (JUGADOR_X, JUGADOR_O)
                and v1 == self.meta_tablero[f2][c2] == self.meta_tablero[f3][c3]
            ):
                return v1
        return None

    def verificar_empate(self) -> bool:
        """Verifica si el juego está empatado (tablero lleno, sin ganador)."""
        if self.detectar_ganador_meta() is not None:
            return False
        return all(
            self.meta_tablero[f][c] is not None
            for f in range(DIMENSION_META)
            for c in range(DIMENSION_META)
        )

    # ----- Estado -----

    def es_mini_tablero_lleno(self, fila_meta: int, col_meta: int) -> bool:
        """Verifica si un mini-tablero está completamente lleno."""
        mini = self.mini_tableros[self._indice_mini(fila_meta, col_meta)]
        return all(celda is not None for fila in mini for celda in fila)

    def es_mini_tablero_disponible(self, fila_meta: int, col_meta: int) -> bool:
        """
        Verifica si se puede jugar en un mini-tablero.

        Retorna:
            False si ya fue ganado por X o O, está lleno, o es un empate.
            True si todavía tiene casillas vacías para jugar.
        """
        return self.meta_tablero[fila_meta][col_meta] is None

    # ----- Representación para la terminal -----

    def __str__(self) -> str:
        """Retorna una cadena con el tablero listo para mostrar en la terminal."""

        def simbolo_celda(valor: Optional[str]) -> str:
            """Convierte una casilla vacía en un punto para mostrarla."""
            return valor if valor else "."

        def simbolo_meta(valor: Optional[str]) -> str:
            """Convierte el resultado de un campo en un símbolo visible."""
            if valor in (JUGADOR_X, JUGADOR_O):
                return valor
            if valor == "EMPATE":
                return "="
            return "."

        filas_tablero = []
        for fila_meta in range(DIMENSION_META):
            for fila_mini in range(DIMENSION_MINI):
                grupos = []
                for col_meta in range(DIMENSION_META):
                    indice_mini = self._indice_mini(fila_meta, col_meta)
                    fila_valores = self.mini_tableros[indice_mini][fila_mini]
                    grupos.append(" ".join(simbolo_celda(c) for c in fila_valores))
                filas_tablero.append(" | ".join(grupos))
            if fila_meta < DIMENSION_META - 1:
                filas_tablero.append("-" * 29)

        resumen_meta = "\n".join(
            " ".join(
                simbolo_meta(self.meta_tablero[f][c]) for c in range(DIMENSION_META)
            )
            for f in range(DIMENSION_META)
        )

        return "\n".join(filas_tablero) + "\n\nMETA-TABLERO:\n" + resumen_meta

    def copiar(self) -> "Tablero":
        """
        Crea una copia del tablero actual

        Usado por minimax para ver variaciones. No copia el
        historial.
        """
        nuevo = Tablero()
        nuevo.mini_tableros = [
            [fila[:] for fila in mini] for mini in self.mini_tableros
        ]
        nuevo.meta_tablero = [fila[:] for fila in self.meta_tablero]
        return nuevo

    def obtener_hash_estado(self) -> int:
        """
        Regresa un identificador hash del estado actual.

        Convierte mini_tableros y meta_tablero a tuplas  y aplica
        hash() de Python.
        """
        mini_tuple = tuple(
            tuple(tuple(fila) for fila in mini) for mini in self.mini_tableros
        )
        meta_tuple = tuple(tuple(fila) for fila in self.meta_tablero)
        return hash((mini_tuple, meta_tuple))


# =============================================================================
# MOVIMIENTOS VÁLIDOS
# =============================================================================


def movimientos_validos_mini(
    tablero_3x3: List[List[Optional[str]]],
) -> List[Tuple[int, int]]:
    """
    Regresa casillas vacías en un mini-tablero específico.

    Retorna:
        Lista de tuplas (fila, col) de casillas vacías
    """
    return [
        (fila, col)
        for fila in range(DIMENSION_MINI)
        for col in range(DIMENSION_MINI)
        if tablero_3x3[fila][col] is None
    ]


def mini_tableros_disponibles(tablero: Tablero) -> List[Tuple[int, int]]:
    """
    Regresa lista de mini-tableros donde aún se puede jugar.

    Retorna:
        Lista de tuplas (fila_meta, col_meta) de mini-tableros disponibles
    """
    return [
        (fila_meta, col_meta)
        for fila_meta in range(DIMENSION_META)
        for col_meta in range(DIMENSION_META)
        if tablero.es_mini_tablero_disponible(fila_meta, col_meta)
    ]


def movimientos_validos(
    tablero: Tablero, tablero_destino: Optional[Tuple[int, int]]
) -> List[Tuple[int, int, int, int]]:
    """
    Regresa lista de movimientos válidos desde la posición actual.

    Parámetros:
        tablero: Estado actual del juego
        tablero_destino: Tupla (fila_meta, col_meta) indicando dónde DEBE jugar.
                        Si None, puede jugar en cualquier lado (primer movimiento)

    Retorna:
        Lista de tuplas (fila_meta, col_meta, fila_mini, col_mini)

    Reglas:
    - Si tablero_destino es None: jugador puede jugar en cualquier casilla vacía
    - Si tablero_destino ya fue ganado/empatado/lleno: puede jugar en
      cualquier mini-tablero disponible
    - Si tablero_destino es normal: solo puede jugar ahí
    """
    if tablero.detectar_ganador_meta() is not None or tablero.verificar_empate():
        return []

    if tablero_destino is not None and tablero.es_mini_tablero_disponible(
        *tablero_destino
    ):
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
# de CONFIGURACIÓN).


def contar_lineas_abiertas(
    tablero_3x3: List[List[Optional[str]]], jugador: str, cantidad_marcas: int
) -> int:
    """
    Cuenta líneas con una cantidad exacta de marcas y el resto vacío.

    Una marca rival o un campo ``EMPATE`` cierra la línea. Separar líneas de
    una y dos marcas evita asignar el mismo valor al progreso temprano y a
    una amenaza inmediata.
    """
    conteo = 0
    if cantidad_marcas in (1, 2):
        for linea in LINEAS_MINI_TABLERO:
            valores = [tablero_3x3[fila][col] for fila, col in linea]
            marcas_correctas = valores.count(jugador) == cantidad_marcas
            vacias_correctas = valores.count(None) == 3 - cantidad_marcas
            if marcas_correctas and vacias_correctas:
                conteo += 1
    return conteo


def contar_2_en_linea(tablero_3x3: List[List[Optional[str]]], jugador: str) -> int:
    """Cuenta líneas abiertas con dos marcas y una casilla vacía."""
    return contar_lineas_abiertas(tablero_3x3, jugador, 2)


def contar_1_en_linea(tablero_3x3: List[List[Optional[str]]], jugador: str) -> int:
    """Cuenta líneas abiertas con una marca y dos casillas vacías."""
    return contar_lineas_abiertas(tablero_3x3, jugador, 1)


def contar_lineas_meta_relevantes(
    tablero: Tablero, fila_meta: int, col_meta: int, jugador: str
) -> int:
    """Cuenta líneas globales donde el campo aún puede ayudar a ``jugador``."""
    rival = JUGADOR_O if jugador == JUGADOR_X else JUGADOR_X
    posicion = (fila_meta, col_meta)
    relevantes = 0
    for linea in LINEAS_META_TABLERO:
        if posicion in linea:
            valores = [tablero.meta_tablero[fila][col] for fila, col in linea]
            if rival not in valores and "EMPATE" not in valores:
                relevantes += 1
    return relevantes


def evaluar_progreso_meta(tablero: Tablero) -> int:
    """
    Evalúa qué tan cerca está cada jugador de ganar el meta-tablero.

    Retorna:
        VALOR_GANADOR si X ya ganó el juego, VALOR_PERDEDOR si ganó O;
        si no, la diferencia de progreso en todas las líneas abiertas.
    """
    ganador = tablero.detectar_ganador_meta()
    if ganador == JUGADOR_X:
        return VALOR_GANADOR
    if ganador == JUGADOR_O:
        return VALOR_PERDEDOR

    progreso_x = (
        contar_1_en_linea(tablero.meta_tablero, JUGADOR_X) * VALOR_LINEA_META_UN_CAMPO
        + contar_2_en_linea(tablero.meta_tablero, JUGADOR_X)
        * VALOR_LINEA_META_DOS_CAMPOS
    )
    progreso_o = (
        contar_1_en_linea(tablero.meta_tablero, JUGADOR_O) * VALOR_LINEA_META_UN_CAMPO
        + contar_2_en_linea(tablero.meta_tablero, JUGADOR_O)
        * VALOR_LINEA_META_DOS_CAMPOS
    )
    return progreso_x - progreso_o


def evaluar_bifurcaciones(tablero: Tablero) -> int:
    """
    Detecta bifurcaciones: mini-tableros donde un jugador tiene 2 o más
    líneas de 2-en-línea simultáneas (múltiples amenazas de ganar ese campo).

    Solo revisa campos jugables. Cada amenaza individual se cuenta en
    evaluar_defensa(); aquí únicamente se suma el exceso sobre la primera.
    """
    puntuacion = 0
    for fila_meta in range(DIMENSION_META):
        for col_meta in range(DIMENSION_META):
            if tablero.es_mini_tablero_disponible(fila_meta, col_meta):
                mini = tablero.obtener_mini_tablero(fila_meta, col_meta)
                amenazas_x = contar_2_en_linea(mini, JUGADOR_X)
                amenazas_o = contar_2_en_linea(mini, JUGADOR_O)
                puntuacion += max(0, amenazas_x - 1)
                puntuacion -= max(0, amenazas_o - 1)
    return puntuacion


def evaluar_defensa(tablero: Tablero) -> int:
    """
    Evalúa amenazas inmediatas solamente en campos todavía jugables.

    Cada amenaza se cuenta una vez; evaluar_bifurcaciones agrega únicamente
    el bono por mantener varias amenazas simultáneas.
    """
    amenazas_x_total = 0
    amenazas_o_total = 0
    for fila_meta in range(DIMENSION_META):
        for col_meta in range(DIMENSION_META):
            if tablero.es_mini_tablero_disponible(fila_meta, col_meta):
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
    for fila_meta in range(DIMENSION_META):
        for col_meta in range(DIMENSION_META):
            valor = tablero.meta_tablero[fila_meta][col_meta]
            if valor == JUGADOR_X:
                puntuacion += IMPORTANCIA_CAMPO[(fila_meta, col_meta)]
            elif valor == JUGADOR_O:
                puntuacion -= IMPORTANCIA_CAMPO[(fila_meta, col_meta)]
    return puntuacion


def evaluar_mini_tableros(tablero: Tablero) -> int:
    """
    Evalúa líneas de una marca en campos jugables, sin volver a contar las
    amenazas de dos marcas. Su valor depende de cuántas líneas abiertas del
    meta-tablero todavía puede completar cada jugador mediante ese campo.
    """
    puntuacion = 0
    for fila_meta in range(DIMENSION_META):
        for col_meta in range(DIMENSION_META):
            if tablero.es_mini_tablero_disponible(fila_meta, col_meta):
                mini = tablero.obtener_mini_tablero(fila_meta, col_meta)
                desarrollo_x = contar_1_en_linea(mini, JUGADOR_X)
                desarrollo_o = contar_1_en_linea(mini, JUGADOR_O)
                relevancia_x = contar_lineas_meta_relevantes(
                    tablero, fila_meta, col_meta, JUGADOR_X
                )
                relevancia_o = contar_lineas_meta_relevantes(
                    tablero, fila_meta, col_meta, JUGADOR_O
                )
                puntuacion += desarrollo_x * relevancia_x
                puntuacion -= desarrollo_o * relevancia_o
    return puntuacion


def evaluar_amenaza_destino(
    tablero: Tablero, tablero_destino: Optional[Tuple[int, int]], jugador_actual: str
) -> int:
    """
    Evalúa el mini-tablero al que `jugador_actual` está obligado a jugar.

    Si ese mini-tablero ya tiene una amenaza (2-en-línea) de jugador_actual,
    puede ganarlo de inmediato. Si la amenaza es del rival,
    es una trampa. Si no hay restricción real (tablero_destino es None, o
    apunta a un mini-tablero ya decidido), se da un pequeño bono por la
    libertad de elegir.

    Retorna:
        Puntuación en perspectiva de jugador_actual (positiva = le
        conviene). evaluar_posicion() la convierte a perspectiva absoluta
        de X antes de sumarla.
    """
    oponente = JUGADOR_O if jugador_actual == JUGADOR_X else JUGADOR_X

    if tablero_destino is None or not tablero.es_mini_tablero_disponible(
        *tablero_destino
    ):
        return BONO_LIBERTAD_ELECCION

    mini = tablero.obtener_mini_tablero(*tablero_destino)
    amenazas_propias = contar_2_en_linea(mini, jugador_actual)
    amenazas_rivales = contar_2_en_linea(mini, oponente)
    return amenazas_propias - amenazas_rivales


def movimiento_completa_linea(
    tablero_3x3: List[List[Optional[str]]], fila: int, col: int, jugador: str
) -> bool:
    """Indica si colocar una marca en una casilla vacía completa una línea."""
    return any(
        (fila, col) in linea
        and all(tablero_3x3[f][c] == jugador for f, c in linea if (f, c) != (fila, col))
        for linea in LINEAS_MINI_TABLERO
    )


def contar_amenazas_creadas(
    tablero_3x3: List[List[Optional[str]]], fila: int, col: int, jugador: str
) -> int:
    """Cuenta amenazas nuevas que aparecerían al jugar en ``(fila, col)``."""
    creadas = 0
    for linea in LINEAS_MINI_TABLERO:
        if (fila, col) in linea:
            otros = [tablero_3x3[f][c] for f, c in linea if (f, c) != (fila, col)]
            if otros.count(jugador) == 1 and otros.count(None) == 1:
                creadas += 1
    return creadas


def evaluar_amenaza_destino_futura(
    tablero: Tablero, tablero_destino: Optional[Tuple[int, int]], jugador_actual: str
) -> int:
    """
    Extiende evaluar_amenaza_destino un nivel más: no solo "¿es peligroso
    el mini-tablero al que me mandan?", sino "de las casillas que puedo
    jugar ahí, ¿a qué campo mandaría yo al rival después, y qué tan
    peligroso es ESE campo para él?".

    Para cada casilla legal considera si gana el campo actual, si crea una
    amenaza y qué peligro encontrará el rival en el siguiente destino. Esto
    permite distinguir dos victorias locales que envían al rival a campos
    diferentes.

    Retorna:
        Puntuación en perspectiva de jugador_actual, o 0 si no existe un
        campo obligatorio jugable.
    """
    oponente = JUGADOR_O if jugador_actual == JUGADOR_X else JUGADOR_X

    if tablero_destino is None or not tablero.es_mini_tablero_disponible(
        *tablero_destino
    ):
        return 0

    mini = tablero.obtener_mini_tablero(*tablero_destino)
    casillas_vacias = [
        (fila, col)
        for fila in range(DIMENSION_MINI)
        for col in range(DIMENSION_MINI)
        if mini[fila][col] is None
    ]
    if not casillas_vacias:
        return 0

    valores_movimientos = []
    for fila, col in casillas_vacias:
        gana_campo = movimiento_completa_linea(mini, fila, col, jugador_actual)
        amenazas_creadas = contar_amenazas_creadas(mini, fila, col, jugador_actual)
        cierra_el_destino_elegido = gana_campo and (fila, col) == tablero_destino
        destino_libre = (
            not tablero.es_mini_tablero_disponible(fila, col)
            or cierra_el_destino_elegido
        )
        if destino_libre:
            peligro = BONO_LIBERTAD_ELECCION
        else:
            siguiente = tablero.obtener_mini_tablero(fila, col)
            peligro = contar_2_en_linea(siguiente, oponente) - contar_2_en_linea(
                siguiente, jugador_actual
            )
        beneficio = BONO_GANAR_MINI_TABLERO * int(gana_campo) + amenazas_creadas
        valores_movimientos.append(beneficio - peligro)

    return max(valores_movimientos)


def evaluar_posicion(
    tablero: Tablero,
    es_maximizando: bool,
    tablero_destino: Optional[Tuple[int, int]] = None,
    mostrar_desglose: bool = False,
) -> int:
    """
    Evalúa la posición actual del tablero usando heurística multi-componente.

    Parámetros:
        tablero: Estado actual del juego
        es_maximizando: True si estamos evaluando para X (maximizador),
                       False si estamos evaluando para O (minimizador).
                       La puntuación siempre se retorna en perspectiva
                       absoluta de X (positiva=ventaja X); este parámetro
                       se conserva para la convención de llamada de minimax.
        tablero_destino: Mini-tablero al que está obligado a jugar quien
                       mueve ahora (fila_meta, col_meta), o None si puede
                       elegir libremente.
        mostrar_desglose: Si es ``True``, imprime el valor sin ponderar, el
            peso y el aporte de cada componente. Se usa solo para diagnóstico
            manual, porque Minimax llama esta función miles de veces.

    Retorna:
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
        if mostrar_desglose:
            print(
                f"[evaluar_posicion] TERMINAL: X ya ganó el meta-tablero -> {VALOR_GANADOR}"
            )
        return VALOR_GANADOR
    if ganador == JUGADOR_O:
        if mostrar_desglose:
            print(
                f"[evaluar_posicion] TERMINAL: O ya ganó el meta-tablero -> {VALOR_PERDEDOR}"
            )
        return VALOR_PERDEDOR
    if tablero.verificar_empate():
        if mostrar_desglose:
            print(f"[evaluar_posicion] TERMINAL: empate -> {VALOR_EMPATE}")
        return VALOR_EMPATE

    jugador_actual = JUGADOR_X if es_maximizando else JUGADOR_O
    progreso = evaluar_progreso_meta(tablero)
    bifurcaciones = evaluar_bifurcaciones(tablero)
    defensa = evaluar_defensa(tablero)
    control = evaluar_control_posiciones(tablero)
    mini = evaluar_mini_tableros(tablero)
    amenaza_destino_propia = evaluar_amenaza_destino(
        tablero, tablero_destino, jugador_actual
    )
    amenaza_destino = (
        amenaza_destino_propia
        if jugador_actual == JUGADOR_X
        else -amenaza_destino_propia
    )
    amenaza_futura_propia = evaluar_amenaza_destino_futura(
        tablero, tablero_destino, jugador_actual
    )
    amenaza_futura = (
        amenaza_futura_propia if jugador_actual == JUGADOR_X else -amenaza_futura_propia
    )

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

    if mostrar_desglose:
        print(
            "[evaluar_posicion] "
            + " | ".join(
                f"{nombre}={crudo} (x{peso}={crudo * peso})"
                for nombre, crudo, peso in componentes
            )
        )
        print(f"[evaluar_posicion] TOTAL = {puntuacion}")

    return puntuacion


# =============================================================================
# MINIMAX (BÚSQUEDA CON PODA ALFA-BETA)
# =============================================================================
#
# Optimizaciones implementadas:
# 1. Poda alfa-beta.
# 2. Tabla de transposiciones con límite de tamaño.
# 3. Ordenamiento de movimientos: prueba primero las jugadas prometedoras.
# 4. Profundización iterativa con presupuesto adaptativo y corte
#    si se agota el tiempo, y corte anticipado si ya se probó una
#    victoria/derrota forzada
# 5. Valores terminales ajustados por profundidad (VALOR_GANADOR - nivel):
#    la IA prefiere ganar rápido y retrasar una derrota inevitable
# 6. Estadísticas de la última búsqueda en `ultimas_estadisticas`
# 7. Selección segura del primer valor óptimo exacto en la raíz: no confunde
#    con un empate las cotas generadas por la poda alfa-beta.

TIPO_EXACTO = "EXACTO"
TIPO_COTA_INFERIOR = "COTA_INFERIOR"
TIPO_COTA_SUPERIOR = "COTA_SUPERIOR"


class TablaTransposiciones:
    """
    Guarda evaluaciones de posiciones para no calcularlas de nuevo.

    Cada entrada distingue entre un valor exacto, una cota inferior y una
    cota superior. Así una rama cortada por alfa-beta nunca se reutiliza
    incorrectamente como si fuera un valor exacto.
    """

    def __init__(self):
        """Inicializa una tabla de transposiciones vacía."""
        self.tabla: Dict[object, Tuple[int, str]] = {}

    def guardar(self, hash_estado: object, valor: int, tipo: str = TIPO_EXACTO) -> None:
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


class TiempoAgotadoError(Exception):
    """Señal interna para abortar minimax en curso cuando se acaba el tiempo."""


# Instante límite absoluto de ``time.monotonic()`` durante la búsqueda.
_tiempo_limite_absoluto: Optional[float] = None

# Nodos visitados durante la búsqueda en curso (para estadísticas).
_contador_nodos: int = 0

# Estadísticas de la última llamada a mejor_movimiento(): profundidad
# alcanzada, nodos visitados, valor encontrado, segundos usados y presupuesto de tiempo asignado.
ultimas_estadisticas: Dict[str, object] = {}


def _mueve_completa_linea(
    tablero_3x3: List[List[Optional[str]]], fila: int, col: int, valor: str
) -> bool:
    """Indica si colocar `valor` en (fila, col) completaría una línea de 3, sin modificar el mini-tablero."""
    return any(
        (fila, col) in linea
        and all(tablero_3x3[f][c] == valor for f, c in linea if (f, c) != (fila, col))
        for linea in LINEAS_MINI_TABLERO
    )


def ordenar_movimientos(
    tablero: Tablero,
    movimientos: list,
    tablero_destino: Optional[Tuple[int, int]],
    jugador: str,
    movimiento_preferido: Optional[Tuple[int, int, int, int]] = None,
) -> list:
    """
    Ordena movimientos para mejorar la poda alfa-beta.

    Orden: (0) movimiento_preferido si está en la lista, (1) movimientos
    que ganan un mini-tablero de inmediato,
    (2) movimientos que bloquean una victoria del oponente, (3) el resto;
    dentro de cada grupo, prioriza campos de mayor IMPORTANCIA_CAMPO.
    """
    oponente = JUGADOR_O if jugador == JUGADOR_X else JUGADOR_X

    def prioridad(movimiento):
        """Asigna un grupo táctico y una prioridad posicional a la jugada."""
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


def minimax(
    tablero: Tablero,
    profundidad: int,
    alfa: float,
    beta: float,
    es_maximizando: bool,
    tablero_destino: Optional[Tuple[int, int]],
    tabla_transposiciones: TablaTransposiciones,
    nivel: int = 0,
) -> int:
    """
    Evalúa recursivamente una posición con Minimax y poda alfa-beta.

    Parámetros:
        tablero: Estado actual
        profundidad: Cuántos movimientos adelante buscar (0 = usar heurística)
        alfa, beta: Ventana de poda
        es_maximizando: True si es turno de X (max), False si es turno de O (min)
        tablero_destino: Restricción de dónde jugar
        tabla_transposiciones: Memoria de posiciones evaluadas durante esta
            profundidad de búsqueda.
        nivel: Distancia (en jugadas) desde la raíz de esta búsqueda. Se
               resta/suma a los valores terminales para que la IA prefiera
               ganar rápido y retrasar una derrota inevitable.

    Como el valor terminal depende de ``nivel``, una entrada guardada en una
    pasada de profundización no es válida para otra profundidad inicial. Por
    eso ``mejor_movimiento()`` crea una tabla nueva en cada pasada.
    """
    global _contador_nodos
    _contador_nodos += 1

    if (
        _tiempo_limite_absoluto is not None
        and time.monotonic() >= _tiempo_limite_absoluto
    ):
        raise TiempoAgotadoError()

    ganador = tablero.detectar_ganador_meta()
    if ganador == JUGADOR_X:
        return VALOR_GANADOR - nivel
    if ganador == JUGADOR_O:
        return VALOR_PERDEDOR + nivel
    if tablero.verificar_empate():
        return VALOR_EMPATE

    alfa_original = alfa
    beta_original = beta
    clave_tabla = (
        tablero.obtener_hash_estado(),
        profundidad,
        tablero_destino,
        es_maximizando,
    )
    entrada_guardada = tabla_transposiciones.obtener(clave_tabla)
    if entrada_guardada is not None:
        valor_guardado, tipo_guardado = entrada_guardada
        if tipo_guardado == TIPO_EXACTO:
            return valor_guardado
        if tipo_guardado == TIPO_COTA_INFERIOR:
            alfa = max(alfa, valor_guardado)
        elif tipo_guardado == TIPO_COTA_SUPERIOR:
            beta = min(beta, valor_guardado)
        if alfa >= beta:
            return valor_guardado

    if profundidad == 0:
        valor = evaluar_posicion(tablero, es_maximizando, tablero_destino)
        tabla_transposiciones.guardar(clave_tabla, valor, TIPO_EXACTO)
        return valor

    jugador_actual = JUGADOR_X if es_maximizando else JUGADOR_O
    movimientos = movimientos_validos(tablero, tablero_destino)
    movimientos = ordenar_movimientos(
        tablero, movimientos, tablero_destino, jugador_actual
    )

    if not movimientos:
        valor = evaluar_posicion(tablero, es_maximizando, tablero_destino)
        tabla_transposiciones.guardar(clave_tabla, valor, TIPO_EXACTO)
        return valor

    if es_maximizando:
        valor = float("-inf")
        indice = 0
        while indice < len(movimientos) and alfa < beta:
            movimiento = movimientos[indice]
            tablero.aplicar_movimiento(*movimiento, jugador_actual)
            siguiente_destino = (movimiento[2], movimiento[3])
            try:
                valor_hijo = minimax(
                    tablero,
                    profundidad - 1,
                    alfa,
                    beta,
                    False,
                    siguiente_destino,
                    tabla_transposiciones,
                    nivel + 1,
                )
            finally:
                # Si minimax() lanza TiempoAgotadoError, este deshacer DEBE
                # ejecutarse igual: es lo único que evita dejar el
                # movimiento pegado permanentemente al tablero real
                # mientras la excepción se propaga por la recursión.
                tablero.deshacer_movimiento()
            valor = max(valor, valor_hijo)
            alfa = max(alfa, valor)
            indice += 1
    else:
        valor = float("inf")
        indice = 0
        while indice < len(movimientos) and alfa < beta:
            movimiento = movimientos[indice]
            tablero.aplicar_movimiento(*movimiento, jugador_actual)
            siguiente_destino = (movimiento[2], movimiento[3])
            try:
                valor_hijo = minimax(
                    tablero,
                    profundidad - 1,
                    alfa,
                    beta,
                    True,
                    siguiente_destino,
                    tabla_transposiciones,
                    nivel + 1,
                )
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
    tabla_transposiciones.guardar(clave_tabla, valor, tipo_valor)
    return valor


def obtener_mejor_movimiento_hoja(
    tablero: Tablero,
    profundidad: int,
    alfa: float,
    beta: float,
    es_maximizando: bool,
    tablero_destino: Optional[Tuple[int, int]],
    tabla_transposiciones: TablaTransposiciones,
    movimiento_preferido: Optional[Tuple[int, int, int, int]] = None,
) -> Optional[Tuple[int, int, int, int, int]]:
    """
    Versión de minimax que además retorna qué movimiento en la raíz produjo
    la mejor puntuación (minimax() solo retorna la puntuación).

    Parámetros:
        movimiento_preferido: Mejor jugada encontrada en la profundidad
            anterior de la profundización iterativa, si la hay.

    Retorna:
        (fila_meta, col_meta, fila_mini, col_mini, puntuacion) del mejor
        movimiento raíz, o None si no hay movimientos legales.

    Una búsqueda con ventana alfa-beta estrecha puede devolver una cota igual
    al mejor valor conocido aunque la jugada sea realmente peor. Por eso se
    conserva el primer movimiento óptimo y solo se reemplaza cuando aparece
    una mejora estricta; no se sortean igualdades que podrían ser cotas.
    """
    jugador_actual = JUGADOR_X if es_maximizando else JUGADOR_O
    movimientos = movimientos_validos(tablero, tablero_destino)
    if not movimientos:
        return None
    movimientos = ordenar_movimientos(
        tablero, movimientos, tablero_destino, jugador_actual, movimiento_preferido
    )

    mejor_movimiento = movimientos[0]
    if es_maximizando:
        mejor_valor = float("-inf")
        indice = 0
        while indice < len(movimientos) and alfa < beta:
            movimiento = movimientos[indice]
            tablero.aplicar_movimiento(*movimiento, jugador_actual)
            siguiente_destino = (movimiento[2], movimiento[3])
            try:
                valor = minimax(
                    tablero,
                    profundidad - 1,
                    alfa,
                    beta,
                    False,
                    siguiente_destino,
                    tabla_transposiciones,
                    nivel=1,
                )
            finally:
                tablero.deshacer_movimiento()
            if valor > mejor_valor:
                mejor_valor = valor
                mejor_movimiento = movimiento
            alfa = max(alfa, mejor_valor)
            indice += 1
    else:
        mejor_valor = float("inf")
        indice = 0
        while indice < len(movimientos) and alfa < beta:
            movimiento = movimientos[indice]
            tablero.aplicar_movimiento(*movimiento, jugador_actual)
            siguiente_destino = (movimiento[2], movimiento[3])
            try:
                valor = minimax(
                    tablero,
                    profundidad - 1,
                    alfa,
                    beta,
                    True,
                    siguiente_destino,
                    tabla_transposiciones,
                    nivel=1,
                )
            finally:
                tablero.deshacer_movimiento()
            if valor < mejor_valor:
                mejor_valor = valor
                mejor_movimiento = movimiento
            beta = min(beta, mejor_valor)
            indice += 1

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


def mejor_movimiento(
    tablero: Tablero,
    tablero_destino: Optional[Tuple[int, int]],
    tiempo_limite: float = TIEMPO_LIMITE,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Encuentra el mejor movimiento con profundización iterativa, Minimax y
    poda alfa-beta.

    Parámetros:
        tablero: Estado actual
        tablero_destino: Dónde debe jugar (None si puede jugar en cualquier lado)
        tiempo_limite: Segundos máximos para decidir; el presupuesto real
            usado puede ser menor (ver _calcular_presupuesto) pero nunca mayor.

    Retorna:
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
                tabla_transposiciones = TablaTransposiciones()
                resultado = obtener_mejor_movimiento_hoja(
                    tablero,
                    profundidad,
                    float("-inf"),
                    float("inf"),
                    es_maximizando,
                    tablero_destino,
                    tabla_transposiciones,
                    movimiento_preferido,
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
    except TiempoAgotadoError:
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
    """Regresa el símbolo a mostrar para un campo del meta-tablero: su letra (A-I) si sigue en juego, o 'X'/'O'/'=' si ya se decidió."""
    valor = tablero.meta_tablero[fila_meta][col_meta]
    if valor == "EMPATE":
        return "="
    if valor in (JUGADOR_X, JUGADOR_O):
        return valor
    return INDICES_INVERSOS[(fila_meta, col_meta)]


def _simbolo_celda(
    tablero: Tablero, fila_meta: int, col_meta: int, fila_mini: int, col_mini: int
) -> str:
    """Retorna el símbolo a mostrar para una casilla: su letra (a-i) si está vacía, o 'X'/'O' si está ocupada."""
    valor = tablero.obtener_casilla(fila_meta, col_meta, fila_mini, col_mini)
    if valor is not None:
        return valor
    return INDICES_MINI_INVERSOS[(fila_mini, col_mini)]


def mostrar_tablero(tablero: Tablero) -> None:
    """
    Imprime el tablero en la terminal de forma legible.

    Cada casilla vacía muestra su letra de posición (a-i) y cada campo
    del meta-tablero muestra su letra (A-I) mientras sigue disponible,
    para que el jugador identifique de inmediato qué escribir.
    """
    print("TABLERO ACTUAL:\n")
    for bloque_fila in range(DIMENSION_META):
        encabezados = []
        for col_meta in range(DIMENSION_META):
            letra_campo = INDICES_INVERSOS[(bloque_fila, col_meta)]
            estado = tablero.meta_tablero[bloque_fila][col_meta]
            etiqueta = f"CAMPO {letra_campo}"
            if estado in (JUGADOR_X, JUGADOR_O):
                etiqueta += f" [ganador: {estado}]"
            elif estado == "EMPATE":
                etiqueta += " [empate]"
            encabezados.append(etiqueta.ljust(20))
        print("  ".join(encabezados))

        for fila_mini in range(DIMENSION_MINI):
            partes = []
            for col_meta in range(DIMENSION_META):
                celdas = [
                    _simbolo_celda(tablero, bloque_fila, col_meta, fila_mini, col_mini)
                    for col_mini in range(DIMENSION_MINI)
                ]
                partes.append("  ".join(celdas).ljust(20))
            print("  ".join(partes))
        print()

    print("META-TABLERO:")
    for fila_meta in range(DIMENSION_META):
        print(
            " | ".join(
                _simbolo_campo(tablero, fila_meta, c) for c in range(DIMENSION_META)
            )
        )
        if fila_meta < DIMENSION_META - 1:
            print("-" * 9)


def mostrar_mensaje(mensaje: str) -> None:
    """Imprime un mensaje de estado al usuario."""
    print(mensaje)


def convertir_movimiento_a_texto(movimiento: Tuple[int, int, int, int]) -> str:
    """Convierte cuatro índices internos a la notación del torneo, como ``Gc``.

    Parámetros:
        movimiento: Tupla ``(fila_meta, columna_meta, fila_mini,
            columna_mini)``; cada índice debe estar entre 0 y 2.

    Retorna:
        Dos caracteres: campo en mayúscula y posición en minúscula.
    """
    fila_meta, col_meta, fila_mini, col_mini = movimiento
    campo = INDICES_INVERSOS[(fila_meta, col_meta)]
    posicion = INDICES_MINI_INVERSOS[(fila_mini, col_mini)]
    return campo + posicion


def mostrar_opciones_movimiento(
    movimientos_legales: Sequence[Tuple[int, int, int, int]],
) -> None:
    """Explica el campo permitido antes de pedir la jugada del oponente.

    Si todos los movimientos pertenecen al mismo campo, muestra ese campo y
    las posiciones disponibles. Si la regla permite elección libre, muestra
    los campos abiertos. La lista recibida debe venir de
    ``movimientos_validos()``.
    """
    campos = sorted(
        {
            INDICES_INVERSOS[(movimiento[0], movimiento[1])]
            for movimiento in movimientos_legales
        }
    )
    if len(campos) == 1:
        opciones = ", ".join(
            convertir_movimiento_a_texto(movimiento)
            for movimiento in movimientos_legales
        )
        mostrar_mensaje(
            f"Campo obligatorio: {campos[0]}. Movimientos disponibles: {opciones}."
        )
    elif campos:
        mostrar_mensaje(
            "Elección libre. Campos disponibles: " + ", ".join(campos) + "."
        )


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

    Retorna:
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


def mostrar_movimiento(
    campo: str, posicion: Optional[str] = None, jugador: Optional[str] = None
) -> None:
    """
    Muestra un movimiento en formato "Campo+Posición" (ej. "Gc").

    Parámetros:
        campo: Letra del campo ('G'), o el movimiento completo ('Gc') si posicion es None
        posicion: Letra de la posición ('c'), opcional si ya viene junto en campo
        jugador: Nombre de quién juega (por defecto "Jugador")
    """
    movimiento = campo if posicion is None else f"{campo}{posicion}"
    quien = jugador if jugador else "Jugador"
    mostrar_mensaje(f"{quien} juega: {movimiento}")


def mostrar_movimiento_ia(
    fila_meta: int, col_meta: int, fila_mini: int, col_mini: int
) -> None:
    """Muestra el movimiento que hizo la IA. Ejemplo: "IA juega: Gc"."""
    campo = INDICES_INVERSOS[(fila_meta, col_meta)]
    posicion = INDICES_MINI_INVERSOS[(fila_mini, col_mini)]
    mostrar_movimiento(campo, posicion, jugador="IA")


def mostrar_estadisticas_ia(estadisticas: dict) -> None:
    """
    Muestra un resumen de la búsqueda que hizo la IA para decidir su
    último movimiento (ultimas_estadisticas).

    Ejemplo: "Profundidad: 6 | Nodos: 12,345 | Valor: 37 | Tiempo: 12.4s / 15.0s"
    """
    if not estadisticas:
        return
    mostrar_mensaje(
        f"Profundidad: {estadisticas.get('profundidad', '?')} | "
        f"Nodos: {estadisticas.get('nodos', 0):,} | "
        f"Valor: {estadisticas.get('valor', 0)} | "
        f"Tiempo: {estadisticas.get('segundos', 0):.2f}s / {estadisticas.get('presupuesto', 0):.1f}s"
    )


def solicitar_primer_jugador() -> str:
    """Pregunta si comienza nuestro sistema o el jugador externo."""
    respuesta = ""
    while respuesta not in ("S", "E"):
        respuesta = (
            input("¿A quién le toca comenzar? [S]istema / jugador [E]xterno: ")
            .strip()
            .upper()
        )
        if respuesta in ("S", "E"):
            mostrar_mensaje(
                "Comienza nuestro sistema y jugará como X."
                if respuesta == "S"
                else "Comienza el jugador externo y jugará como X."
            )
        else:
            mostrar_mensaje(f"Respuesta inválida: '{respuesta}'. Escribe 'S' o 'E'.")
    return "SISTEMA" if respuesta == "S" else "EXTERNO"


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
# CICLO PRINCIPAL DEL JUEGO
# =============================================================================


def obtener_movimiento_valido(
    tablero: Tablero, tablero_destino: Optional[Tuple[int, int]]
) -> Tuple[int, int, int, int]:
    """
    Pide movimientos al usuario hasta obtener uno legal.

    Un movimiento es legal si aparece en movimientos_validos() para el
    tablero_destino vigente (respeta la casilla obligatoria y que esté vacía).
    """
    movimientos_legales = movimientos_validos(tablero, tablero_destino)
    mostrar_opciones_movimiento(movimientos_legales)
    while True:
        movimiento = obtener_movimiento_usuario()
        if movimiento in movimientos_legales:
            return movimiento
        mostrar_mensaje(
            "Movimiento no permitido: la casilla está ocupada o no corresponde al campo obligatorio."
        )


def imprimir_resultado(tablero: Tablero) -> None:
    """Imprime el tablero final y el resultado del juego."""
    mostrar_tablero(tablero)
    ganador = tablero.detectar_ganador_meta()
    if ganador is not None:
        mostrar_mensaje(f"{ganador} GANA")
    else:
        mostrar_mensaje("EMPATE")


def _movimiento_ia(
    tablero: Tablero, tablero_destino: Optional[Tuple[int, int]]
) -> Tuple[int, int, int, int]:
    """Obtiene el movimiento de la IA (minimax), lo anuncia y muestra estadísticas de la búsqueda."""
    movimiento = mejor_movimiento(tablero, tablero_destino)
    if movimiento is None:
        raise RuntimeError("La IA no encontró movimientos en una posición activa.")
    mostrar_movimiento_ia(*movimiento)
    mostrar_estadisticas_ia(ultimas_estadisticas)
    return movimiento


TipoObtenerMovimiento = Callable[
    [Tablero, Optional[Tuple[int, int]]], Tuple[int, int, int, int]
]


def _ejecutar_partida(
    tablero: Tablero,
    obtener_movimiento_x: TipoObtenerMovimiento,
    obtener_movimiento_o: TipoObtenerMovimiento,
) -> None:
    """
    Ejecuta el ciclo principal de una partida y delega en las funciones dadas
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
            tablero.detectar_ganador_meta() is not None or tablero.verificar_empate()
        )
        if partida_terminada:
            imprimir_resultado(tablero)
        else:
            es_turno_x = not es_turno_x
            tablero_destino = (movimiento[2], movimiento[3])


def jugar_humano_vs_ia() -> None:
    """
    Ejecuta la partida de torneo entre el sistema y el jugador externo.

    Pregunta quién comienza y asigna X a esa parte; la otra parte usa O.
    """
    tablero = Tablero()
    primer_jugador = solicitar_primer_jugador()

    if primer_jugador == "EXTERNO":
        _ejecutar_partida(tablero, obtener_movimiento_valido, _movimiento_ia)
    else:
        _ejecutar_partida(tablero, _movimiento_ia, obtener_movimiento_valido)


if __name__ == "__main__":
    jugar_humano_vs_ia()
