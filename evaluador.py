"""
MÓDULO: evaluador.py
RESPONSABLE: Persona B
DESCRIPCIÓN: Función heurística que evalúa posiciones del juego

Esta es la "inteligencia" de la IA. Recibe un tablero y retorna una puntuación.
Minimax usa esta función para decidir qué movimientos son buenos.

Especificación:
- Retorna números positivos para posiciones ventajosas para X
- Retorna números negativos para posiciones ventajosas para O
- Retorna 0 para posiciones neutras
- Escala: -10000 a +10000 (reservados para ganadoras/perdedoras)
"""

from config import *
from typing import List, Optional, Tuple
import tablero as tb


def contar_2_en_linea(tablero_3x3: List[List[Optional[str]]], jugador: str) -> int:
    """
    Cuenta cuántas líneas tienen 2 del jugador y 1 casilla vacía (amenaza).

    Args:
        tablero_3x3: Mini-tablero 3x3 (o meta-tablero, que usa la misma
                     disposición de líneas)
        jugador: 'X' o 'O'

    Returns:
        Número de líneas con 2 del jugador y la tercera casilla vacía
    """
    conteo = 0
    for linea in LINEAS_MINI_TABLERO:
        valores = [tablero_3x3[fila][col] for fila, col in linea]
        if valores.count(jugador) == 2 and valores.count(None) == 1:
            conteo += 1
    return conteo


def evaluar_progreso_meta(tablero: "tb.Tablero") -> int:
    """
    Evalúa qué tan cerca está cada jugador de ganar el meta-tablero.

    Returns:
        VALOR_GANADOR si X ya ganó el juego, VALOR_PERDEDOR si ganó O;
        de lo contrario, la diferencia de amenazas (2-en-línea) de X menos O
        en el meta-tablero.
    """
    ganador = tablero.detectar_ganador_meta()
    if ganador == JUGADOR_X:
        return VALOR_GANADOR
    if ganador == JUGADOR_O:
        return VALOR_PERDEDOR

    amenazas_x = contar_2_en_linea(tablero.meta_tablero, JUGADOR_X)
    amenazas_o = contar_2_en_linea(tablero.meta_tablero, JUGADOR_O)
    return amenazas_x - amenazas_o


def evaluar_bifurcaciones(tablero: "tb.Tablero") -> int:
    """
    Detecta bifurcaciones: mini-tableros donde un jugador tiene 2 o más
    líneas de 2-en-línea simultáneas (múltiples amenazas de ganar ese campo).

    Returns:
        Puntuación positiva si X tiene bifurcaciones, negativa si O las tiene

    Nota: evalúa los 9 mini-tableros, incluyendo los ya decididos. Un
    mini-tablero recién ganado sigue conteniendo sus marcas reales (ganar
    no borra el contenido, solo fija meta_tablero); excluirlo aquí haría
    que la señal de dominio local desaparezca justo al completar la
    victoria, penalizando ganar en vez de premiarlo (bug real detectado
    en partida: ver evaluar_posicion).
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


def evaluar_defensa(tablero: "tb.Tablero") -> int:
    """
    Evalúa el peligro inmediato: suma de amenazas (2-en-línea) de cada
    jugador en todos los mini-tableros disponibles.

    A diferencia de evaluar_bifurcaciones (que premia la concentración de
    amenazas en un mismo mini-tablero), esta función cuenta el peligro total
    disperso en cualquier mini-tablero jugable.

    Returns:
        Puntuación positiva si X tiene más amenazas activas, negativa si O

    Nota: evalúa los 9 mini-tableros, incluyendo los ya decididos (ver
    evaluar_bifurcaciones para el motivo).
    """
    amenazas_x_total = 0
    amenazas_o_total = 0
    for fila_meta in range(TAMAÑO_META):
        for col_meta in range(TAMAÑO_META):
            mini = tablero.obtener_mini_tablero(fila_meta, col_meta)
            amenazas_x_total += contar_2_en_linea(mini, JUGADOR_X)
            amenazas_o_total += contar_2_en_linea(mini, JUGADOR_O)
    return amenazas_x_total - amenazas_o_total


def evaluar_control_posiciones(tablero: "tb.Tablero") -> int:
    """
    Evalúa quién controla posiciones estratégicas del meta-tablero.

    El centro (E) y las esquinas valen más que los bordes, según
    IMPORTANCIA_CAMPO en config.py.

    Returns:
        Puntuación positiva si X controla campos importantes, negativa si O
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


def evaluar_mini_tableros(tablero: "tb.Tablero") -> int:
    """
    Evalúa la posesión local de cada uno de los 9 mini-tableros.

    Compara casillas ocupadas por X vs O y sus amenazas (2-en-línea)
    potenciales, incluyendo mini-tableros ya decididos (ver
    evaluar_bifurcaciones para el motivo).

    Returns:
        Puntuación agregada positiva si favorece a X, negativa si favorece a O
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


def evaluar_amenaza_destino(tablero: "tb.Tablero", tablero_destino: Optional[Tuple[int, int]],
                            jugador_actual: str) -> int:
    """
    Evalúa el mini-tablero al que `jugador_actual` está obligado a jugar.

    Si ese mini-tablero ya tiene una amenaza (2-en-línea) de jugador_actual,
    es un regalo (puede ganarlo de inmediato). Si la amenaza es del rival,
    es una trampa. Si no hay restricción real (tablero_destino es None, o
    apunta a un mini-tablero ya decidido y por lo tanto movimientos.py cae
    de vuelta a "cualquier mini-tablero disponible"), se da un pequeño bono
    por la libertad de elegir.

    Args:
        tablero: Estado actual del juego
        tablero_destino: Mini-tablero obligatorio para jugador_actual, o None
        jugador_actual: 'X' o 'O' — quien debe mover en esta posición

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


def evaluar_posicion(tablero: "tb.Tablero", es_maximizando: bool,
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
                       elegir libremente. Alimenta evaluar_amenaza_destino;
                       si se omite, ese componente queda neutral.
        debug: Si True, imprime el desglose por componente (crudo y
               ponderado) antes de retornar. Usar solo para diagnóstico
               manual: minimax() lo llama sin este flag (miles de veces
               por jugada), así que activarlo dentro de la búsqueda
               inundaría la terminal y la haría mucho más lenta.

    Returns:
        Puntuación heurística (negativa para O favorable, positiva para X
        favorable). VALOR_GANADOR/VALOR_PERDEDOR si el juego ya terminó.

    Componentes de evaluación:
    1. Progreso en meta-tablero (w=PESO_PROGRESO_META_TABLERO)
    2. Bifurcaciones y amenazas (w=PESO_AMENAZAS_BIFURCACIONES)
    3. Defensa crítica (w=PESO_DEFENSA_CRITICA)
    4. Control de posiciones clave (w=PESO_POSICIONES_CLAVE)
    5. Evaluación de mini-tableros (w=PESO_CONTROL_LOCAL)
    6. Amenaza en el mini-tablero de destino forzado (w=PESO_AMENAZA_DESTINO)
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

    componentes = [
        ("progreso_meta", progreso, PESO_PROGRESO_META_TABLERO),
        ("bifurcaciones", bifurcaciones, PESO_AMENAZAS_BIFURCACIONES),
        ("defensa", defensa, PESO_DEFENSA_CRITICA),
        ("control_posiciones", control, PESO_POSICIONES_CLAVE),
        ("mini_tableros", mini, PESO_CONTROL_LOCAL),
        ("amenaza_destino", amenaza_destino, PESO_AMENAZA_DESTINO),
    ]
    puntuacion = sum(crudo * peso for _, crudo, peso in componentes)

    if debug:
        print("[evaluar_posicion] " + " | ".join(
            f"{nombre}={crudo} (x{peso}={crudo * peso})" for nombre, crudo, peso in componentes
        ))
        print(f"[evaluar_posicion] TOTAL = {puntuacion}")

    return puntuacion
