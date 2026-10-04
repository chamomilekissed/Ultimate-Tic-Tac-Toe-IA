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

from typing import List, Optional, Tuple

from . import tablero as tb
from .config import (
    BONO_GANAR_MINI_TABLERO,
    BONO_LIBERTAD_ELECCION,
    DIMENSION_META,
    DIMENSION_MINI,
    IMPORTANCIA_CAMPO,
    JUGADOR_O,
    JUGADOR_X,
    LINEAS_META_TABLERO,
    LINEAS_MINI_TABLERO,
    PESO_AMENAZA_DESTINO,
    PESO_AMENAZA_DESTINO_FUTURA,
    PESO_AMENAZAS_BIFURCACIONES,
    PESO_CONTROL_LOCAL,
    PESO_DEFENSA_CRITICA,
    PESO_POSICIONES_CLAVE,
    PESO_PROGRESO_META_TABLERO,
    VALOR_EMPATE,
    VALOR_GANADOR,
    VALOR_LINEA_META_DOS_CAMPOS,
    VALOR_LINEA_META_UN_CAMPO,
    VALOR_PERDEDOR,
)


def contar_lineas_abiertas(
    tablero_3x3: List[List[Optional[str]]], jugador: str, cantidad_marcas: int
) -> int:
    """
    Cuenta líneas que solo contienen marcas de ``jugador`` y casillas vacías.

    Parámetros:
        tablero_3x3: Mini-tablero o meta-tablero de 3 por 3.
        jugador: ``'X'`` o ``'O'``.
        cantidad_marcas: Cantidad exacta de marcas buscadas, 1 o 2.

    Retorna:
        Número de líneas abiertas con la cantidad indicada de marcas.

    Una línea con una marca rival o con ``'EMPATE'`` está cerrada para el
    jugador y no se cuenta. Separar líneas de una y dos marcas permite que el
    progreso temprano no valga lo mismo que una amenaza inmediata.
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
    """
    Cuenta cuántas líneas tienen 2 del jugador y 1 casilla vacía (amenaza).

    Parámetros:
        tablero_3x3: Mini-tablero 3x3 (o meta-tablero, que usa la misma
                     disposición de líneas)
        jugador: 'X' o 'O'

    Retorna:
        Número de líneas con 2 del jugador y la tercera casilla vacía
    """
    return contar_lineas_abiertas(tablero_3x3, jugador, 2)


def contar_1_en_linea(tablero_3x3: List[List[Optional[str]]], jugador: str) -> int:
    """Cuenta líneas abiertas con una marca del jugador y dos casillas vacías."""
    return contar_lineas_abiertas(tablero_3x3, jugador, 1)


def contar_lineas_meta_relevantes(
    tablero: "tb.Tablero", fila_meta: int, col_meta: int, jugador: str
) -> int:
    """
    Cuenta líneas del meta-tablero donde el campo indicado todavía puede
    contribuir a una victoria de ``jugador``.

    Una línea deja de ser relevante si contiene un campo del rival o un campo
    empatado. Con esto la evaluación local depende del estado real del juego:
    una casilla en un campo que participa en varias líneas abiertas vale más
    que una casilla ubicada en una zona que ya no ayuda a formar tres campos.
    """
    rival = JUGADOR_O if jugador == JUGADOR_X else JUGADOR_X
    posicion = (fila_meta, col_meta)
    relevantes = 0
    for linea in LINEAS_META_TABLERO:
        if posicion in linea:
            valores = [tablero.meta_tablero[fila][col] for fila, col in linea]
            if rival not in valores and "EMPATE" not in valores:
                relevantes += 1
    return relevantes


def evaluar_progreso_meta(tablero: "tb.Tablero") -> int:
    """
    Evalúa qué tan cerca está cada jugador de ganar el meta-tablero.

    Retorna:
        VALOR_GANADOR si X ya ganó el juego, VALOR_PERDEDOR si ganó O;
        de lo contrario, la diferencia ponderada entre líneas abiertas con
        uno o dos campos ganados.
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


def evaluar_bifurcaciones(tablero: "tb.Tablero") -> int:
    """
    Detecta bifurcaciones: mini-tableros donde un jugador tiene 2 o más
    líneas de 2-en-línea simultáneas (múltiples amenazas de ganar ese campo).

    Retorna:
        Puntuación positiva si X tiene bifurcaciones, negativa si O las tiene

    Solo se revisan campos todavía jugables. Las amenazas internas de un campo
    cerrado ya no pueden ejecutarse y, por lo tanto, no deben influir.

    Una amenaza individual se cuenta en evaluar_defensa(). Aquí solo se suma
    el exceso sobre la primera amenaza: dos amenazas producen un bono de uno,
    tres producen un bono de dos, etc. Así la bifurcación recibe un premio
    específico sin volver a sumar todas las amenazas completas.
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


def evaluar_defensa(tablero: "tb.Tablero") -> int:
    """
    Evalúa el peligro inmediato: suma amenazas de dos marcas en los
    mini-tableros que todavía se pueden jugar.

    A diferencia de evaluar_bifurcaciones(), cada amenaza aparece exactamente
    una vez aquí. La función de bifurcaciones solo añade el bono correspondiente
    a tener varias amenazas simultáneas en el mismo campo.

    Retorna:
        Puntuación positiva si X tiene más amenazas activas, negativa si O

    Los campos ganados o empatados se excluyen porque no admiten más jugadas.
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


def evaluar_control_posiciones(tablero: "tb.Tablero") -> int:
    """
    Evalúa quién controla posiciones estratégicas del meta-tablero.

    El centro (E) y las esquinas valen más que los bordes, según
    IMPORTANCIA_CAMPO en config.py.

    Retorna:
        Puntuación positiva si X controla campos importantes, negativa si O
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


def evaluar_mini_tableros(tablero: "tb.Tablero") -> int:
    """
    Evalúa líneas locales que apenas están comenzando en campos jugables.

    Solo cuenta líneas con una marca y dos espacios. Las amenazas de dos
    marcas pertenecen a evaluar_defensa(), de modo que no se duplican. Cada
    línea se multiplica por la cantidad de líneas abiertas del meta-tablero a
    las que todavía puede contribuir ese campo.

    Retorna:
        Puntuación agregada positiva si favorece a X, negativa si favorece a O
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
    tablero: "tb.Tablero",
    tablero_destino: Optional[Tuple[int, int]],
    jugador_actual: str,
) -> int:
    """
    Evalúa el mini-tablero al que `jugador_actual` está obligado a jugar.

    Si ese mini-tablero ya tiene una amenaza (2-en-línea) de jugador_actual,
    es un regalo (puede ganarlo de inmediato). Si la amenaza es del rival,
    es una trampa. Si no hay restricción real (tablero_destino es None, o
    apunta a un mini-tablero ya decidido y por lo tanto movimientos.py cae
    de vuelta a "cualquier mini-tablero disponible"), se da un pequeño bono
    por la libertad de elegir.

    Parámetros:
        tablero: Estado actual del juego
        tablero_destino: Mini-tablero obligatorio para jugador_actual, o None
        jugador_actual: 'X' o 'O' — quien debe mover en esta posición

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
    tablero: "tb.Tablero",
    tablero_destino: Optional[Tuple[int, int]],
    jugador_actual: str,
) -> int:
    """
    Extiende evaluar_amenaza_destino un nivel más: no solo "¿es peligroso
    el mini-tablero al que me mandan?", sino "de las casillas que puedo
    jugar ahí, ¿a qué campo mandaría yo al rival después, y qué tan
    peligroso es ESE campo para él?".

    Para cada casilla legal estima tres efectos: si gana el campo actual, si
    crea una amenaza nueva y qué peligro encontrará el rival en el campo de
    destino. Después conserva la mejor alternativa disponible para el jugador
    actual. Esto distingue dos movimientos ganadores que envían al rival a
    lugares distintos, algo que la versión anterior no hacía.

    Parámetros:
        tablero: Estado actual del juego
        tablero_destino: Mini-tablero obligatorio para jugador_actual, o None
        jugador_actual: 'X' o 'O' — quien debe mover en esta posición

    Retorna:
        Puntuación en perspectiva de jugador_actual (positiva = le
        conviene), o 0 si no existe un destino obligatorio jugable.
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
    tablero: "tb.Tablero",
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
                       elegir libremente. Alimenta evaluar_amenaza_destino
                       y evaluar_amenaza_destino_futura; si se omite, esos
                       componentes quedan neutrales.
        mostrar_desglose: Si es ``True``, imprime el valor sin ponderar, el
            peso y el aporte de cada componente. Se usa solo para diagnóstico
            manual, porque Minimax llama esta función miles de veces.

    Retorna:
        Puntuación heurística (negativa para O favorable, positiva para X
        favorable). VALOR_GANADOR/VALOR_PERDEDOR si el juego ya terminó.

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
