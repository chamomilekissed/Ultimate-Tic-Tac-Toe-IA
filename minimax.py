"""
MÓDULO: minimax.py
RESPONSABLE: Persona B
DESCRIPCIÓN: Algoritmo Minimax con optimizaciones (Alpha-Beta, Transposition Tables, etc.)

Este es el corazón de la IA. Usa búsqueda adversarial para decidir el mejor movimiento.

Optimizaciones implementadas:
1. Alpha-Beta Pruning (reduce búsqueda exponencialmente)
2. Transposition Tables (cachea posiciones ya evaluadas, con límite de tamaño)
3. Move Ordering (poda más agresivamente; incluye PV move ordering entre
   profundidades del iterative deepening)
4. Iterative Deepening (usa tiempo eficientemente, con corte duro si se agota,
   presupuesto de tiempo adaptativo por etapa de partida, y corte anticipado
   si ya se probó una victoria/derrota forzada)
5. Valores terminales ajustados por profundidad (VALOR_GANADOR - nivel): la
   IA prefiere ganar rápido y retrasar una derrota inevitable
6. Estadísticas de la última búsqueda expuestas en `ultimas_estadisticas`
   (nodos visitados, profundidad alcanzada, valor, tiempo, presupuesto)
"""

import time
from typing import Optional, Tuple, Dict, List
from config import *
import tablero as tb
import movimientos as mov
import evaluador as ev


# ===== TRANSPOSITION TABLES (CACHE GLOBAL) =====

class TranspositionTable:
    """
    Cachea evaluaciones de posiciones para no recalcularlas.

    En Ultimate Tic-Tac-Toe, distintas secuencias de movimientos pueden
    llevar al mismo estado (transposición); reutilizar su evaluación es
    CRÍTICO para la velocidad.

    Nota: guarda el valor tal cual lo retorna minimax(), incluso cuando
    proviene de una rama cortada por alpha-beta (una cota, no un valor
    exacto). Es una simplificación aceptable para este proyecto: acelera
    la búsqueda sin afectar la jugabilidad de forma perceptible.
    """

    def __init__(self):
        """Inicializa la tabla de transposición vacía."""
        self.tabla: Dict[object, int] = {}

    def guardar(self, hash_estado: object, valor: int) -> None:
        """Guarda la puntuación asociada a un estado (clave hasheable).

        No guarda más allá de LIMITE_ESTADOS_MEMORIA entradas (config.py):
        en posiciones con mucho ramaje, una sola profundidad de búsqueda
        podría generar demasiadas transposiciones distintas.
        """
        if len(self.tabla) >= LIMITE_ESTADOS_MEMORIA:
            return
        self.tabla[hash_estado] = valor

    def obtener(self, hash_estado: object) -> Optional[int]:
        """Retorna la puntuación cacheada para un estado, o None si no existe."""
        return self.tabla.get(hash_estado)

    def limpiar(self) -> None:
        """Vacía la tabla por completo."""
        self.tabla.clear()


# ===== CONTROL DE TIEMPO =====

class TiempoAgotado(Exception):
    """Señal interna para abortar minimax en curso cuando se acaba el tiempo."""
    pass


# Deadline absoluto (time.time()) vigente durante una llamada a mejor_movimiento().
# None cuando no hay una búsqueda con límite de tiempo en curso.
_tiempo_limite_absoluto: Optional[float] = None

# Nodos visitados durante la búsqueda en curso (para estadísticas).
_contador_nodos: int = 0

# Estadísticas de la última llamada a mejor_movimiento(): profundidad
# alcanzada, nodos visitados, valor encontrado, segundos usados y
# presupuesto de tiempo asignado. main.py/interfaz.py pueden leerlo para
# mostrarlo al usuario (no forma parte del valor de retorno de
# mejor_movimiento() para no romper a quienes solo esperan la jugada).
ultimas_estadisticas: Dict[str, object] = {}


# ===== MOVE ORDERING =====

def _mueve_completa_linea(tablero_3x3: List[List[Optional[str]]], fila: int, col: int, valor: str) -> bool:
    """Indica si colocar `valor` en (fila, col) completaría una línea de 3, sin modificar el mini-tablero."""
    for linea in LINEAS_MINI_TABLERO:
        if (fila, col) not in linea:
            continue
        resto = [(f, c) for f, c in linea if (f, c) != (fila, col)]
        if all(tablero_3x3[f][c] == valor for f, c in resto):
            return True
    return False


def ordenar_movimientos(tablero: "tb.Tablero", movimientos: list,
                       tablero_destino: Optional[Tuple[int, int]],
                       jugador: str,
                       movimiento_preferido: Optional[Tuple[int, int, int, int]] = None) -> list:
    """
    Ordena movimientos para mejorar la poda de Alpha-Beta.

    Orden: (0) movimiento_preferido si está en la lista (la mejor jugada
    encontrada en la profundidad anterior del iterative deepening — "PV
    move ordering": probarla primero suele podar mucho más), (1)
    movimientos que ganan un mini-tablero de inmediato, (2) movimientos
    que bloquean una victoria del oponente en ese mini-tablero, (3) el
    resto; dentro de cada grupo, prioriza campos de mayor IMPORTANCIA_CAMPO.
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


# ===== FUNCIONES PRINCIPALES =====

def minimax(tablero: "tb.Tablero", profundidad: int, alfa: float, beta: float,
            es_maximizando: bool, tablero_destino: Optional[Tuple[int, int]],
            cache: "TranspositionTable", nivel: int = 0) -> int:
    """
    Evaluación recursiva usando Minimax con Alpha-Beta Pruning.

    Args:
        tablero: Estado actual
        profundidad: Cuántos movimientos adelante buscar (0 = usar heurística)
        alfa: Mejor valor encontrado para el maximizador
        beta: Mejor valor encontrado para el minimizador
        es_maximizando: True si es turno de X (max), False si es turno de O (min)
        tablero_destino: Restricción de dónde jugar
        cache: Transposition Table para cachear posiciones repetidas
        nivel: Distancia (en jugadas) desde la raíz de esta búsqueda. Se
               resta/suma a los valores terminales para que la IA prefiera
               ganar rápido y retrasar una derrota inevitable.

    Returns:
        Puntuación heurística (o exacta, si es terminal) de la posición

    Nota sobre la cache y `nivel`: como el valor terminal ahora depende de
    `nivel` (no solo de `profundidad`), una entrada cacheada en una pasada
    de iterative deepening con profundidad_inicial=N ya NO es válida para
    una pasada con profundidad_inicial=M distinto, aunque `profundidad`
    (restante) coincida — el mismo `profundidad` restante corresponde a un
    `nivel` distinto en cada pasada. Por eso mejor_movimiento() crea una
    `cache` nueva en cada profundidad del iterative deepening en vez de
    reutilizar una sola durante todo el ciclo.
    """
    global _contador_nodos
    _contador_nodos += 1

    if _tiempo_limite_absoluto is not None and time.time() > _tiempo_limite_absoluto:
        raise TiempoAgotado()

    ganador = tablero.detectar_ganador_meta()
    if ganador == JUGADOR_X:
        return VALOR_GANADOR - nivel
    if ganador == JUGADOR_O:
        return VALOR_PERDEDOR + nivel
    if tablero.verificar_empate():
        return VALOR_EMPATE

    clave_cache = (tablero.get_estado_hash(), profundidad, tablero_destino, es_maximizando)
    valor_cacheado = cache.obtener(clave_cache)
    if valor_cacheado is not None:
        return valor_cacheado

    if profundidad == 0:
        valor = ev.evaluar_posicion(tablero, es_maximizando, tablero_destino)
        cache.guardar(clave_cache, valor)
        return valor

    jugador_actual = JUGADOR_X if es_maximizando else JUGADOR_O
    movimientos = mov.movimientos_validos(tablero, tablero_destino)
    movimientos = ordenar_movimientos(tablero, movimientos, tablero_destino, jugador_actual)

    if es_maximizando:
        valor = float('-inf')
        for movimiento in movimientos:
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
            if beta <= alfa:
                break
    else:
        valor = float('inf')
        for movimiento in movimientos:
            tablero.aplicar_movimiento(*movimiento, jugador_actual)
            siguiente_destino = (movimiento[2], movimiento[3])
            try:
                valor_hijo = minimax(tablero, profundidad - 1, alfa, beta, True, siguiente_destino, cache, nivel + 1)
            finally:
                tablero.deshacer_movimiento()
            valor = min(valor, valor_hijo)
            beta = min(beta, valor)
            if beta <= alfa:
                break

    cache.guardar(clave_cache, valor)
    return valor


def obtener_mejor_movimiento_hoja(tablero: "tb.Tablero", profundidad: int,
                                   alfa: float, beta: float, es_maximizando: bool,
                                   tablero_destino: Optional[Tuple[int, int]],
                                   cache: "TranspositionTable",
                                   movimiento_preferido: Optional[Tuple[int, int, int, int]] = None
                                   ) -> Optional[Tuple[int, int, int, int, int]]:
    """
    Versión de minimax que además retorna qué movimiento en la raíz produjo
    la mejor puntuación (minimax() solo retorna la puntuación).

    Args:
        movimiento_preferido: Mejor jugada encontrada en la profundidad
            anterior del iterative deepening, si la hay — se prueba primero
            (PV move ordering) para podar más rápido.

    Returns:
        (fila_meta, col_meta, fila_mini, col_mini, puntuacion) del mejor
        movimiento raíz, o None si no hay movimientos legales.
    """
    jugador_actual = JUGADOR_X if es_maximizando else JUGADOR_O
    movimientos = mov.movimientos_validos(tablero, tablero_destino)
    if not movimientos:
        return None
    movimientos = ordenar_movimientos(tablero, movimientos, tablero_destino, jugador_actual, movimiento_preferido)

    mejor_movimiento = movimientos[0]
    if es_maximizando:
        mejor_valor = float('-inf')
        for movimiento in movimientos:
            tablero.aplicar_movimiento(*movimiento, jugador_actual)
            siguiente_destino = (movimiento[2], movimiento[3])
            try:
                valor = minimax(tablero, profundidad - 1, alfa, beta, False, siguiente_destino, cache, nivel=1)
            finally:
                tablero.deshacer_movimiento()
            if valor > mejor_valor:
                mejor_valor = valor
                mejor_movimiento = movimiento
            alfa = max(alfa, mejor_valor)
            if beta <= alfa:
                break
    else:
        mejor_valor = float('inf')
        for movimiento in movimientos:
            tablero.aplicar_movimiento(*movimiento, jugador_actual)
            siguiente_destino = (movimiento[2], movimiento[3])
            try:
                valor = minimax(tablero, profundidad - 1, alfa, beta, True, siguiente_destino, cache, nivel=1)
            finally:
                tablero.deshacer_movimiento()
            if valor < mejor_valor:
                mejor_valor = valor
                mejor_movimiento = movimiento
            beta = min(beta, mejor_valor)
            if beta <= alfa:
                break

    return (*mejor_movimiento, mejor_valor)


def _contar_marcas(tablero: "tb.Tablero") -> Dict[str, int]:
    """Cuenta cuántas casillas tiene cada jugador, para inferir de quién es el turno."""
    conteo = {JUGADOR_X: 0, JUGADOR_O: 0}
    for mini in tablero.mini_tableros:
        for fila in mini:
            for celda in fila:
                if celda in conteo:
                    conteo[celda] += 1
    return conteo


def _contar_casillas_restantes(tablero: "tb.Tablero") -> int:
    """Cuenta casillas vacías en mini-tableros todavía disponibles (para elegir el presupuesto de tiempo)."""
    restantes = 0
    for fila_meta, col_meta in mov.mini_tableros_disponibles(tablero):
        mini = tablero.obtener_mini_tablero(fila_meta, col_meta)
        restantes += sum(fila.count(None) for fila in mini)
    return restantes


def _calcular_presupuesto(tablero: "tb.Tablero", tiempo_limite: float) -> float:
    """
    Elige cuánto tiempo dedicar a esta jugada según la etapa de la partida:
    poco en la apertura (mucho ramaje, ganar tiempo no vale la pena),
    más cuando quedan pocas casillas (las decisiones son más críticas).

    El resultado nunca excede tiempo_limite — solo puede acortarlo, así que
    llamadas con un tiempo_limite chico (como en los tests) no se alargan.
    """
    restantes = _contar_casillas_restantes(tablero)
    if restantes >= CASILLAS_RESTANTES_APERTURA:
        presupuesto = TIEMPO_APERTURA
    elif restantes >= CASILLAS_RESTANTES_MEDIO:
        presupuesto = TIEMPO_MEDIO_PARTIDA
    else:
        presupuesto = TIEMPO_FINAL_PARTIDA
    return min(presupuesto, tiempo_limite)


def mejor_movimiento(tablero: "tb.Tablero", tablero_destino: Optional[Tuple[int, int]],
                     tiempo_limite: float = TIEMPO_LIMITE) -> Optional[Tuple[int, int, int, int]]:
    """
    Encuentra el mejor movimiento usando Iterative Deepening + Minimax con
    Alpha-Beta Pruning.

    Args:
        tablero: Estado actual
        tablero_destino: Dónde debe jugar (None si puede jugar en cualquier lado)
        tiempo_limite: Segundos máximos para decidir (default TIEMPO_LIMITE);
            el presupuesto real usado puede ser menor (ver _calcular_presupuesto)
            pero nunca mayor.

    Returns:
        Tupla (fila_meta, col_meta, fila_mini, col_mini) del mejor movimiento
        encontrado, o None si no hay movimientos legales.

    El turno (X u O) se infiere del tablero: si hay tantas 'X' como 'O',
    es turno de X (primer jugador); si hay una 'X' más que 'O', es turno de O.

    Busca profundidad 1, 2, 3... hasta agotar el presupuesto, conservando
    siempre el mejor movimiento de la última profundidad completada. Si el
    tiempo se agota a mitad de una búsqueda, esa profundidad se descarta
    (podría estar incompleta) y se conserva el resultado de la anterior.
    Se detiene antes si ya se probó una victoria o derrota forzada (más
    profundidad no cambiaría la decisión). Después de llamar, las
    estadísticas de esta búsqueda quedan en `ultimas_estadisticas`.
    """
    global _tiempo_limite_absoluto, _contador_nodos, ultimas_estadisticas

    movimientos_legales = mov.movimientos_validos(tablero, tablero_destino)
    if not movimientos_legales:
        return None
    if len(movimientos_legales) == 1:
        return movimientos_legales[0]

    conteo = _contar_marcas(tablero)
    es_maximizando = conteo[JUGADOR_X] == conteo[JUGADOR_O]

    presupuesto = _calcular_presupuesto(tablero, tiempo_limite)
    tiempo_inicio = time.time()
    _tiempo_limite_absoluto = tiempo_inicio + presupuesto
    _contador_nodos = 0

    mejor_encontrado = movimientos_legales[0]
    mejor_valor = 0
    profundidad_alcanzada = 0
    movimiento_preferido = None

    try:
        for profundidad in range(1, 21):
            if time.time() - tiempo_inicio > 0.9 * presupuesto:
                break

            # Cache nueva por profundidad: ver nota sobre `nivel` en minimax().
            cache = TranspositionTable()
            resultado = obtener_mejor_movimiento_hoja(
                tablero, profundidad, float('-inf'), float('inf'),
                es_maximizando, tablero_destino, cache, movimiento_preferido
            )
            if resultado is None:
                break

            mejor_encontrado = resultado[:4]
            mejor_valor = resultado[4]
            movimiento_preferido = mejor_encontrado
            profundidad_alcanzada = profundidad

            if abs(mejor_valor) >= VALOR_GANADOR // 2:
                break  # Victoria/derrota forzada ya probada
    except TiempoAgotado:
        pass
    finally:
        _tiempo_limite_absoluto = None

    ultimas_estadisticas = {
        "profundidad": profundidad_alcanzada,
        "nodos": _contador_nodos,
        "valor": mejor_valor,
        "segundos": time.time() - tiempo_inicio,
        "presupuesto": presupuesto,
    }

    return mejor_encontrado
