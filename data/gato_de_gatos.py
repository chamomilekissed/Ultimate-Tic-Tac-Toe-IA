"""
GATO DE GATOS CON MINIMAX
=========================

Manual de usuario
-----------------
1. Ejecute este archivo en Spyder o con Python 3.
2. Indique si comienza el sistema o el jugador externo.
3. Escriba cada movimiento externo con dos caracteres:
   - A-I: mini-tablero del mega-tablero.
   - a-i: casilla dentro de ese mini-tablero.
   Ejemplo: Gc es la casilla superior derecha del mini-tablero inferior izquierdo.
4. No se puede omitir un turno. El programa rechaza coordenadas inválidas o
   movimientos que no respeten el mini-tablero obligatorio.
5. El símbolo X siempre corresponde a quien comienza.

Representación interna
----------------------
- tablero[mini][casilla] guarda "", "X" u "O".
- macro_tablero[mini] guarda "", "X", "O" o "=". El signo "=" indica empate.
- destino guarda el índice 0-8 del mini-tablero obligatorio, o None cuando el
  jugador puede elegir cualquier mini-tablero abierto.
- Un movimiento es una tupla (mini, casilla), con ambos índices entre 0 y 8.

El programa usa minimax con poda alfa-beta, profundización iterativa, límite de
tiempo y una heurística jerárquica sensible al mini-tablero de destino.
"""

import sys
import time


# ---------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------------------------------

VACIO = ""
EMPATE = "="
CRUZ = "X"
CIRCULO = "O"

LETRAS_MACRO = "ABCDEFGHI"
LETRAS_MINI = "abcdefghi"

LINEAS = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
)

# Centro > esquina > lado.
VALOR_POSICION = (3, 2, 3, 2, 4, 2, 3, 2, 3)

VALOR_VICTORIA = 1_000_000
INFINITO = 10_000_000

# La defensa recibe un peso ligeramente mayor que el ataque.
PESOS_LINEA_MACRO_SISTEMA = (0, 180, 3_600, 0)
PESOS_LINEA_MACRO_RIVAL = (0, 220, 4_500, 0)
PESOS_LINEA_MINI_SISTEMA = (0, 3, 45, 0)
PESOS_LINEA_MINI_RIVAL = (0, 4, 55, 0)

PESO_MINI_GANADO_SISTEMA = 450
PESO_MINI_GANADO_RIVAL = 500
PESO_CONTROL_CASILLA_SISTEMA = 1
PESO_CONTROL_CASILLA_RIVAL = 2
PESO_LIBERTAD_SISTEMA = 140
PESO_LIBERTAD_RIVAL = 170
PESO_AMENAZA_FORZADA_SISTEMA = 180
PESO_AMENAZA_FORZADA_RIVAL = 200
PESO_AMENAZA_BLOQUEABLE = 120

PROFUNDIDAD_MAXIMA = 12
LIMITE_ESTADOS_MEMORIA = 120_000

# Todos los presupuestos dejan margen frente al límite de 30 segundos.
TIEMPO_APERTURA = 4.0
TIEMPO_MEDIO = 10.0
TIEMPO_FINAL = 25.0


# ---------------------------------------------------------------------------
# MÓDULO DE ESTADO Y REGLAS
# ---------------------------------------------------------------------------

def crear_tablero():
    """Crea los nueve mini-tableros vacíos.

    Retorna:
        list: Matriz 9 por 9. El primer índice identifica el mini-tablero y el
        segundo una casilla; cada valor inicial es VACIO.
    """
    return [[VACIO for _ in range(9)] for _ in range(9)]


def crear_macro_tablero():
    """Crea el estado vacío del mega-tablero.

    Retorna:
        list: Nueve valores VACIO, uno por cada mini-tablero.
    """
    return [VACIO for _ in range(9)]


def marca_contraria(marca):
    """Obtiene la marca del otro jugador.

    Parámetros:
        marca (str): Debe ser CRUZ o CIRCULO.

    Retorna:
        str: La marca contraria.

    Lanza:
        ValueError: Si la marca no pertenece al dominio permitido.
    """
    if marca == CRUZ:
        contraria = CIRCULO
    elif marca == CIRCULO:
        contraria = CRUZ
    else:
        raise ValueError("La marca debe ser X u O.")

    return contraria


def hay_tres_en_linea(marcas, jugador):
    """Determina si un jugador ocupa una línea completa.

    Parámetros:
        marcas (list): Secuencia de exactamente nueve estados.
        jugador (str): Marca CRUZ o CIRCULO.

    Retorna:
        bool: True si existe una fila, columna o diagonal del jugador.
    """
    encontrada = False
    indice = 0

    while indice < len(LINEAS) and not encontrada:
        a, b, c = LINEAS[indice]
        encontrada = (
            marcas[a] == jugador
            and marcas[b] == jugador
            and marcas[c] == jugador
        )
        indice += 1

    return encontrada


def obtener_estado_mini(mini_tablero):
    """Infiere el estado de un mini-tablero después de una jugada.

    Parámetros:
        mini_tablero (list): Nueve casillas con VACIO, CRUZ o CIRCULO.

    Retorna:
        str: CRUZ o CIRCULO si alguien ganó; EMPATE si está lleno; VACIO si
        continúa disponible.
    """
    estado = VACIO

    if hay_tres_en_linea(mini_tablero, CRUZ):
        estado = CRUZ
    elif hay_tres_en_linea(mini_tablero, CIRCULO):
        estado = CIRCULO
    elif all(casilla != VACIO for casilla in mini_tablero):
        estado = EMPATE

    return estado


def obtener_ganador_global(macro_tablero):
    """Busca al ganador del mega-tablero.

    Parámetros:
        macro_tablero (list): Nueve estados VACIO, CRUZ, CIRCULO o EMPATE.

    Retorna:
        str: CRUZ o CIRCULO si hay tres mini-tableros ganados en línea; VACIO
        cuando todavía no existe ganador.
    """
    ganador = VACIO

    if hay_tres_en_linea(macro_tablero, CRUZ):
        ganador = CRUZ
    elif hay_tres_en_linea(macro_tablero, CIRCULO):
        ganador = CIRCULO

    return ganador


def calcular_siguiente_destino(casilla, macro_tablero):
    """Aplica la regla que enlaza una casilla con el siguiente mini-tablero.

    Parámetros:
        casilla (int): Índice de 0 a 8 de la casilla recién elegida.
        macro_tablero (list): Estado actual de los nueve mini-tableros.

    Retorna:
        int o None: La casilla si ese mini-tablero sigue abierto; None si ya
        fue ganado o empatado.
    """
    if macro_tablero[casilla] == VACIO:
        destino = casilla
    else:
        destino = None

    return destino


def obtener_movimientos_legales(tablero, macro_tablero, destino):
    """Genera todos los movimientos permitidos por las reglas.

    Parámetros:
        tablero (list): Los nueve mini-tableros.
        macro_tablero (list): Estado de cada mini-tablero.
        destino (int o None): Índice obligatorio de 0 a 8, o None.

    Retorna:
        list: Tuplas (mini, casilla) que representan casillas legales.
    """
    movimientos = []
    tableros_permitidos = []

    if (
        destino is not None
        and 0 <= destino < 9
        and macro_tablero[destino] == VACIO
    ):
        tableros_permitidos.append(destino)
    else:
        for mini in range(9):
            if macro_tablero[mini] == VACIO:
                tableros_permitidos.append(mini)

    for mini in tableros_permitidos:
        for casilla in range(9):
            if tablero[mini][casilla] == VACIO:
                movimientos.append((mini, casilla))

    return movimientos


def es_movimiento_legal(movimiento, tablero, macro_tablero, destino):
    """Comprueba si un movimiento pertenece al conjunto legal actual.

    Parámetros:
        movimiento (tuple): Par (mini, casilla), ambos entre 0 y 8.
        tablero (list): Los nueve mini-tableros.
        macro_tablero (list): Estado del mega-tablero.
        destino (int o None): Mini-tablero obligatorio o None.

    Retorna:
        bool: True si el movimiento puede ejecutarse.
    """
    return movimiento in obtener_movimientos_legales(
        tablero, macro_tablero, destino
    )


def aplicar_movimiento(tablero, macro_tablero, movimiento, jugador):
    """Aplica temporal o definitivamente un movimiento legal.

    Parámetros:
        tablero (list): Estado mutable de los nueve mini-tableros.
        macro_tablero (list): Estado mutable del mega-tablero.
        movimiento (tuple): Tupla legal (mini, casilla).
        jugador (str): CRUZ o CIRCULO.

    Restricción:
        El llamador debe verificar que la casilla esté vacía y sea legal.

    Retorna:
        tuple: Estado anterior del mini-tablero y nuevo destino.

    Efecto:
        Modifica tablero y macro_tablero.
    """
    mini, casilla = movimiento
    estado_anterior = macro_tablero[mini]

    tablero[mini][casilla] = jugador
    macro_tablero[mini] = obtener_estado_mini(tablero[mini])
    nuevo_destino = calcular_siguiente_destino(
        casilla, macro_tablero
    )

    return estado_anterior, nuevo_destino


def deshacer_movimiento(
    tablero,
    macro_tablero,
    movimiento,
    estado_anterior
):
    """Restaura el estado anterior a un movimiento de minimax.

    Parámetros:
        tablero (list): Estado mutable que contiene la jugada.
        macro_tablero (list): Estado mutable del mega-tablero.
        movimiento (tuple): Movimiento que se retirará.
        estado_anterior (str): Estado previo del mini-tablero.

    Retorna:
        None. Los tableros se restauran mediante efectos laterales.
    """
    mini, casilla = movimiento
    tablero[mini][casilla] = VACIO
    macro_tablero[mini] = estado_anterior


# ---------------------------------------------------------------------------
# MÓDULO DE HEURÍSTICA E INFERENCIAS TÁCTICAS
# ---------------------------------------------------------------------------

def completaria_linea(marcas, casilla, jugador):
    """Comprueba si colocar una marca produciría tres en línea.

    Parámetros:
        marcas (list): Secuencia de nueve casillas.
        casilla (int): Posición de 0 a 8; debe estar vacía.
        jugador (str): CRUZ o CIRCULO.

    Retorna:
        bool: True si esa colocación completa alguna línea.
    """
    completa = False
    indice = 0

    if marcas[casilla] == VACIO:
        while indice < len(LINEAS) and not completa:
            linea = LINEAS[indice]

            if casilla in linea:
                cantidad = sum(
                    1
                    for posicion in linea
                    if marcas[posicion] == jugador
                )
                completa = cantidad == 2

            indice += 1

    return completa


def contar_jugadas_ganadoras(marcas, jugador):
    """Cuenta las casillas que completarían una línea inmediatamente.

    Parámetros:
        marcas (list): Secuencia de nueve casillas.
        jugador (str): CRUZ o CIRCULO.

    Retorna:
        int: Cantidad de movimientos ganadores disponibles.
    """
    cantidad = 0

    for casilla in range(9):
        if completaria_linea(marcas, casilla, jugador):
            cantidad += 1

    return cantidad


def puntuar_lineas(
    marcas,
    marca_sistema,
    marca_rival,
    pesos_sistema,
    pesos_rival
):
    """Valora las líneas todavía alcanzables por cada jugador.

    Parámetros:
        marcas (list): Estados de un mini-tablero o del mega-tablero.
        marca_sistema (str): Marca que maximiza.
        marca_rival (str): Marca que minimiza.
        pesos_sistema (tuple): Valores para 0, 1, 2 o 3 marcas.
        pesos_rival (tuple): Penalizaciones para 0, 1, 2 o 3 marcas.

    Retorna:
        int: Puntaje positivo favorable al sistema y negativo favorable al
        rival. Una línea mezclada o empatada vale cero.
    """
    puntaje = 0

    for linea in LINEAS:
        valores = [marcas[posicion] for posicion in linea]

        if EMPATE not in valores:
            cantidad_sistema = valores.count(marca_sistema)
            cantidad_rival = valores.count(marca_rival)

            if cantidad_rival == 0:
                puntaje += pesos_sistema[cantidad_sistema]

            if cantidad_sistema == 0:
                puntaje -= pesos_rival[cantidad_rival]

    return puntaje


def evaluar_heuristica(
    tablero,
    macro_tablero,
    destino,
    jugador_turno,
    marca_sistema,
    marca_rival
):
    """Estima un estado mediante una heurística jerárquica.

    Parámetros:
        tablero (list): Los nueve mini-tableros.
        macro_tablero (list): Estado del mega-tablero.
        destino (int o None): Mini-tablero del siguiente turno.
        jugador_turno (str): Marca que jugará a continuación.
        marca_sistema (str): Marca maximizada por minimax.
        marca_rival (str): Marca minimizada por minimax.

    Retorna:
        int: Valor alto si el estado favorece al sistema y bajo si favorece al
        rival.

    Inferencias:
        1. Potencial de líneas del mega-tablero.
        2. Mini-tableros ganados y su posición.
        3. Líneas y posiciones de los mini-tableros.
        4. Amenazas accesibles en el tablero obligatorio.
        5. Libertad para elegir tablero.
    """
    ganador = obtener_ganador_global(macro_tablero)

    if ganador == marca_sistema:
        puntaje = VALOR_VICTORIA
    elif ganador == marca_rival:
        puntaje = -VALOR_VICTORIA
    else:
        puntaje = puntuar_lineas(
            macro_tablero,
            marca_sistema,
            marca_rival,
            PESOS_LINEA_MACRO_SISTEMA,
            PESOS_LINEA_MACRO_RIVAL
        )

        for mini in range(9):
            factor_posicion = VALOR_POSICION[mini]
            estado_mini = macro_tablero[mini]

            if estado_mini == marca_sistema:
                puntaje += (
                    PESO_MINI_GANADO_SISTEMA
                    * factor_posicion
                )

            elif estado_mini == marca_rival:
                puntaje -= (
                    PESO_MINI_GANADO_RIVAL
                    * factor_posicion
                )

            elif estado_mini == VACIO:
                puntaje += factor_posicion * puntuar_lineas(
                    tablero[mini],
                    marca_sistema,
                    marca_rival,
                    PESOS_LINEA_MINI_SISTEMA,
                    PESOS_LINEA_MINI_RIVAL
                )

                for casilla in range(9):
                    marca = tablero[mini][casilla]
                    valor_casilla = VALOR_POSICION[casilla]

                    if marca == marca_sistema:
                        puntaje += (
                            PESO_CONTROL_CASILLA_SISTEMA
                            * factor_posicion
                            * valor_casilla
                        )

                    elif marca == marca_rival:
                        puntaje -= (
                            PESO_CONTROL_CASILLA_RIVAL
                            * factor_posicion
                            * valor_casilla
                        )

        if destino is None:
            if jugador_turno == marca_sistema:
                puntaje += PESO_LIBERTAD_SISTEMA
            else:
                puntaje -= PESO_LIBERTAD_RIVAL

        else:
            amenazas_sistema = contar_jugadas_ganadoras(
                tablero[destino],
                marca_sistema
            )
            amenazas_rival = contar_jugadas_ganadoras(
                tablero[destino],
                marca_rival
            )

            if jugador_turno == marca_sistema:
                puntaje += (
                    PESO_AMENAZA_FORZADA_SISTEMA
                    * amenazas_sistema
                )
                puntaje -= (
                    PESO_AMENAZA_BLOQUEABLE
                    * amenazas_rival
                )

            else:
                puntaje += (
                    PESO_AMENAZA_BLOQUEABLE
                    * amenazas_sistema
                )
                puntaje -= (
                    PESO_AMENAZA_FORZADA_RIVAL
                    * amenazas_rival
                )

    return puntaje


def calcular_prioridad_movimiento(
    tablero,
    macro_tablero,
    movimiento,
    jugador
):
    """Asigna prioridad de exploración sin cambiar minimax.

    Parámetros:
        tablero (list): Los nueve mini-tableros.
        macro_tablero (list): Estado del mega-tablero.
        movimiento (tuple): Movimiento legal.
        jugador (str): Marca a la que pertenece el turno.

    Retorna:
        int: Prioridad para ordenar la búsqueda.

    Nota:
        Sólo mejora la poda alfa-beta; no sustituye a la heurística.
    """
    mini, casilla = movimiento
    rival = marca_contraria(jugador)

    prioridad = (
        20 * VALOR_POSICION[mini]
        + 5 * VALOR_POSICION[casilla]
    )

    if completaria_linea(tablero[mini], casilla, rival):
        prioridad += 2_500

    estado_anterior, nuevo_destino = aplicar_movimiento(
        tablero,
        macro_tablero,
        movimiento,
        jugador
    )

    if macro_tablero[mini] == jugador:
        prioridad += 6_000

    if obtener_ganador_global(macro_tablero) == jugador:
        prioridad += 500_000

    if nuevo_destino is None:
        prioridad -= 600
    else:
        amenazas_rivales = contar_jugadas_ganadoras(
            tablero[nuevo_destino],
            rival
        )
        prioridad -= 350 * amenazas_rivales

    deshacer_movimiento(
        tablero,
        macro_tablero,
        movimiento,
        estado_anterior
    )

    return prioridad


def ordenar_movimientos(
    tablero,
    macro_tablero,
    movimientos,
    jugador,
    movimiento_preferido=None
):
    """Ordena jugadas para encontrar antes las ramas prometedoras.

    Parámetros:
        tablero (list): Los nueve mini-tableros.
        macro_tablero (list): Estado del mega-tablero.
        movimientos (list): Movimientos legales.
        jugador (str): Marca del turno.
        movimiento_preferido (tuple o None): Mejor jugada de la búsqueda
        anterior.

    Retorna:
        list: Los mismos movimientos en orden determinista.
    """
    decorados = []

    for movimiento in movimientos:
        prioridad = calcular_prioridad_movimiento(
            tablero,
            macro_tablero,
            movimiento,
            jugador
        )

        if movimiento == movimiento_preferido:
            prioridad += 900_000

        decorados.append(
            (
                -prioridad,
                movimiento[0],
                movimiento[1],
                movimiento
            )
        )

    decorados.sort()

    return [elemento[3] for elemento in decorados]


# ---------------------------------------------------------------------------
# MÓDULO DE BÚSQUEDA MINIMAX
# ---------------------------------------------------------------------------

def crear_clave_estado(
    tablero,
    macro_tablero,
    destino,
    jugador_turno,
    profundidad
):
    """Convierte un estado en una clave inmutable.

    Parámetros:
        tablero (list): Los nueve mini-tableros.
        macro_tablero (list): Estado del mega-tablero.
        destino (int o None): Restricción del turno.
        jugador_turno (str): Marca que debe jugar.
        profundidad (int): Niveles que aún explorará minimax.

    Retorna:
        tuple: Clave que distingue estados y profundidades.
    """
    casillas = tuple(
        marca
        for mini_tablero in tablero
        for marca in mini_tablero
    )

    return (
        casillas,
        tuple(macro_tablero),
        destino,
        jugador_turno,
        profundidad
    )


def minimax(
    tablero,
    macro_tablero,
    destino,
    jugador_turno,
    marca_sistema,
    marca_rival,
    profundidad,
    alfa,
    beta,
    nivel,
    limite_tiempo,
    tabla_transposicion,
    estadisticas,
    movimiento_preferido=None
):
    """Busca el valor de un estado con minimax y poda alfa-beta.

    Parámetros:
        tablero (list): Estado mutable de los mini-tableros.
        macro_tablero (list): Estado mutable del mega-tablero.
        destino (int o None): Mini-tablero obligatorio.
        jugador_turno (str): Marca que debe elegir.
        marca_sistema (str): Jugador maximizador.
        marca_rival (str): Jugador minimizador.
        profundidad (int): Niveles restantes; debe ser mayor o igual que cero.
        alfa (int): Mejor límite inferior conocido.
        beta (int): Mejor límite superior conocido.
        nivel (int): Distancia desde la raíz.
        limite_tiempo (float): Instante máximo de búsqueda.
        tabla_transposicion (dict): Memoria de valores exactos.
        estadisticas (dict): Contadores de nodos y aciertos.
        movimiento_preferido (tuple o None): Primera jugada por explorar.

    Retorna:
        tuple: Valor, mejor movimiento y estado de terminación. El tercer valor
        es False únicamente cuando se agotó el tiempo.
    """
    estadisticas["nodos"] += 1

    if time.perf_counter() >= limite_tiempo:
        return 0, None, False

    ganador = obtener_ganador_global(macro_tablero)

    if ganador == marca_sistema:
        return VALOR_VICTORIA - nivel, None, True

    if ganador == marca_rival:
        return -VALOR_VICTORIA + nivel, None, True

    movimientos = obtener_movimientos_legales(
        tablero,
        macro_tablero,
        destino
    )

    if len(movimientos) == 0:
        return 0, None, True

    if profundidad == 0:
        valor = evaluar_heuristica(
            tablero,
            macro_tablero,
            destino,
            jugador_turno,
            marca_sistema,
            marca_rival
        )
        return valor, None, True

    clave = crear_clave_estado(
        tablero,
        macro_tablero,
        destino,
        jugador_turno,
        profundidad
    )

    if clave in tabla_transposicion:
        estadisticas["aciertos_memoria"] += 1
        valor_guardado, movimiento_guardado = (
            tabla_transposicion[clave]
        )
        return valor_guardado, movimiento_guardado, True

    movimientos = ordenar_movimientos(
        tablero,
        macro_tablero,
        movimientos,
        jugador_turno,
        movimiento_preferido
    )

    maximiza = jugador_turno == marca_sistema

    if maximiza:
        mejor_valor = -INFINITO
    else:
        mejor_valor = INFINITO

    mejor_movimiento = movimientos[0]
    busqueda_completa = True
    hubo_poda = False
    indice = 0

    while (
        indice < len(movimientos)
        and busqueda_completa
        and not hubo_poda
    ):
        if time.perf_counter() >= limite_tiempo:
            busqueda_completa = False

        else:
            movimiento = movimientos[indice]

            estado_anterior, destino_hijo = aplicar_movimiento(
                tablero,
                macro_tablero,
                movimiento,
                jugador_turno
            )

            valor_hijo, _, completa_hija = minimax(
                tablero,
                macro_tablero,
                destino_hijo,
                marca_contraria(jugador_turno),
                marca_sistema,
                marca_rival,
                profundidad - 1,
                alfa,
                beta,
                nivel + 1,
                limite_tiempo,
                tabla_transposicion,
                estadisticas
            )

            deshacer_movimiento(
                tablero,
                macro_tablero,
                movimiento,
                estado_anterior
            )

            if completa_hija:
                if maximiza:
                    if valor_hijo > mejor_valor:
                        mejor_valor = valor_hijo
                        mejor_movimiento = movimiento

                    alfa = max(alfa, mejor_valor)

                else:
                    if valor_hijo < mejor_valor:
                        mejor_valor = valor_hijo
                        mejor_movimiento = movimiento

                    beta = min(beta, mejor_valor)

                hubo_poda = alfa >= beta

            else:
                busqueda_completa = False

        indice += 1

    if (
        busqueda_completa
        and not hubo_poda
        and len(tabla_transposicion) < LIMITE_ESTADOS_MEMORIA
    ):
        tabla_transposicion[clave] = (
            mejor_valor,
            mejor_movimiento
        )

    return mejor_valor, mejor_movimiento, busqueda_completa


def contar_casillas_restantes(tablero, macro_tablero):
    """Cuenta las casillas que todavía podrían jugarse.

    Parámetros:
        tablero (list): Los nueve mini-tableros.
        macro_tablero (list): Estado de cada mini-tablero.

    Retorna:
        int: Casillas vacías de mini-tableros abiertos.
    """
    cantidad = 0

    for mini in range(9):
        if macro_tablero[mini] == VACIO:
            cantidad += tablero[mini].count(VACIO)

    return cantidad


def calcular_presupuesto_tiempo(tablero, macro_tablero):
    """Selecciona un presupuesto inferior al límite reglamentario.

    Parámetros:
        tablero (list): Los nueve mini-tableros.
        macro_tablero (list): Estado de cada mini-tablero.

    Retorna:
        float: Segundos máximos de búsqueda.
    """
    restantes = contar_casillas_restantes(
        tablero,
        macro_tablero
    )

    if restantes >= 55:
        presupuesto = TIEMPO_APERTURA
    elif restantes >= 25:
        presupuesto = TIEMPO_MEDIO
    else:
        presupuesto = TIEMPO_FINAL

    return presupuesto


def elegir_movimiento_sistema(
    tablero,
    macro_tablero,
    destino,
    marca_sistema,
    marca_rival
):
    """Elige la jugada mediante profundización iterativa.

    Parámetros:
        tablero (list): Estado de los mini-tableros.
        macro_tablero (list): Estado del mega-tablero.
        destino (int o None): Mini-tablero obligatorio.
        marca_sistema (str): Marca controlada por el sistema.
        marca_rival (str): Marca del jugador externo.

    Retorna:
        tuple: Movimiento legal e informe de la búsqueda.

    Lanza:
        ValueError: Si no existe ninguna jugada legal.
    """
    inicio = time.perf_counter()

    presupuesto = calcular_presupuesto_tiempo(
        tablero,
        macro_tablero
    )
    limite_tiempo = inicio + presupuesto

    movimientos = obtener_movimientos_legales(
        tablero,
        macro_tablero,
        destino
    )

    if len(movimientos) == 0:
        raise ValueError(
            "No existe un movimiento legal disponible."
        )

    orden_inicial = ordenar_movimientos(
        tablero,
        macro_tablero,
        movimientos,
        marca_sistema
    )

    mejor_movimiento = orden_inicial[0]

    mejor_valor = evaluar_heuristica(
        tablero,
        macro_tablero,
        destino,
        marca_sistema,
        marca_sistema,
        marca_rival
    )

    estadisticas = {
        "nodos": 0,
        "aciertos_memoria": 0,
        "profundidad": 0
    }

    profundidad = 1

    casillas_restantes = contar_casillas_restantes(
        tablero,
        macro_tablero
    )

    profundidad_limite = min(
        PROFUNDIDAD_MAXIMA,
        casillas_restantes
    )

    seguir_buscando = (
        time.perf_counter() < limite_tiempo
    )

    while (
        seguir_buscando
        and profundidad <= profundidad_limite
    ):
        tabla_transposicion = {}

        valor, movimiento, completa = minimax(
            tablero,
            macro_tablero,
            destino,
            marca_sistema,
            marca_sistema,
            marca_rival,
            profundidad,
            -INFINITO,
            INFINITO,
            0,
            limite_tiempo,
            tabla_transposicion,
            estadisticas,
            mejor_movimiento
        )

        if completa and movimiento is not None:
            mejor_movimiento = movimiento
            mejor_valor = valor
            estadisticas["profundidad"] = profundidad
            profundidad += 1

            victoria_o_derrota_probada = (
                abs(mejor_valor)
                >= VALOR_VICTORIA // 2
            )

            seguir_buscando = (
                not victoria_o_derrota_probada
                and time.perf_counter() < limite_tiempo
            )

        else:
            seguir_buscando = False

    estadisticas["valor"] = mejor_valor
    estadisticas["segundos"] = (
        time.perf_counter() - inicio
    )
    estadisticas["presupuesto"] = presupuesto

    return mejor_movimiento, estadisticas


# ---------------------------------------------------------------------------
# MÓDULO DE INTERFAZ
# ---------------------------------------------------------------------------

def texto_a_movimiento(texto):
    """Convierte una coordenada humana al formato interno.

    Parámetros:
        texto (str): Dos letras. La primera pertenece a A-I y la segunda a a-i.
        Se aceptan mayúsculas o minúsculas.

    Retorna:
        tuple: Mini-tablero y casilla, ambos entre 0 y 8.

    Lanza:
        ValueError: Si la longitud o alguna letra no es válida.
    """
    limpio = texto.strip()

    if len(limpio) != 2:
        raise ValueError(
            "Use dos letras, por ejemplo Gc."
        )

    letra_macro = limpio[0].upper()
    letra_mini = limpio[1].lower()

    if letra_macro not in LETRAS_MACRO:
        raise ValueError(
            "La primera letra debe estar entre A e I."
        )

    if letra_mini not in LETRAS_MINI:
        raise ValueError(
            "La segunda letra debe estar entre a e i."
        )

    return (
        LETRAS_MACRO.index(letra_macro),
        LETRAS_MINI.index(letra_mini)
    )


def movimiento_a_texto(movimiento):
    """Convierte un movimiento interno a la notación oficial.

    Parámetros:
        movimiento (tuple): Par de índices entre 0 y 8.

    Retorna:
        str: Por ejemplo, (6, 2) se convierte en Gc.
    """
    mini, casilla = movimiento

    return (
        LETRAS_MACRO[mini]
        + LETRAS_MINI[casilla]
    )


def simbolo_visible(valor):
    """Obtiene el símbolo que se imprimirá.

    Parámetros:
        valor (str): VACIO, CRUZ, CIRCULO o EMPATE.

    Retorna:
        str: Un punto para VACIO; en otro caso, el valor recibido.
    """
    if valor == VACIO:
        simbolo = "."
    else:
        simbolo = valor

    return simbolo


def mostrar_referencia_coordenadas():
    """Muestra el mapeo de coordenadas.

    Retorna:
        None. Sólo escribe información en consola.
    """
    print("\nCoordenadas de mini-tableros y casillas:")
    print("  A B C       a b c")
    print("  D E F       d e f")
    print("  G H I       g h i")
    print("Ejemplo: Gc = mini-tablero G, casilla c.\n")


def mostrar_tablero(tablero, macro_tablero):
    """Imprime el tablero y el estado del mega-tablero.

    Parámetros:
        tablero (list): Los nueve mini-tableros.
        macro_tablero (list): Estado de los nueve mini-tableros.

    Retorna:
        None. VACIO se presenta como punto y EMPATE como signo igual.
    """
    print("\nTablero completo:")

    for fila_macro in range(3):
        for fila_mini in range(3):
            bloques = []

            for columna_macro in range(3):
                mini = (
                    3 * fila_macro
                    + columna_macro
                )
                inicio_fila = 3 * fila_mini

                fila = [
                    simbolo_visible(
                        tablero[mini][
                            inicio_fila + desplazamiento
                        ]
                    )
                    for desplazamiento in range(3)
                ]

                bloques.append(" ".join(fila))

            print("  " + " | ".join(bloques))

        if fila_macro < 2:
            print("  ------+-------+------")

    print("\nEstado del mega-tablero:")

    for fila in range(3):
        estados = [
            simbolo_visible(
                macro_tablero[
                    3 * fila + columna
                ]
            )
            for columna in range(3)
        ]

        print("  " + " ".join(estados))


def mostrar_destino(destino):
    """Explica dónde debe realizarse el siguiente movimiento.

    Parámetros:
        destino (int o None): Mini-tablero obligatorio o None.

    Retorna:
        None. Escribe la instrucción en consola.
    """
    if destino is None:
        print(
            "\nDestino: cualquier mini-tablero abierto."
        )
    else:
        print(
            "\nDestino obligatorio: mini-tablero "
            + LETRAS_MACRO[destino]
            + "."
        )


def solicitar_quien_comienza():
    """Pregunta quién realizará el primer movimiento.

    Retorna:
        bool: True si comienza el sistema; False si comienza el jugador.
    """
    respuesta_valida = False
    comienza_sistema = False

    while not respuesta_valida:
        respuesta = input(
            "¿Quién comienza? [S]istema o [J]ugador: "
        ).strip().upper()

        if respuesta in ("S", "SISTEMA"):
            comienza_sistema = True
            respuesta_valida = True

        elif respuesta in ("J", "JUGADOR"):
            comienza_sistema = False
            respuesta_valida = True

        else:
            print(
                "Respuesta inválida. Escriba S o J."
            )

    return comienza_sistema


def solicitar_movimiento_rival(
    tablero,
    macro_tablero,
    destino
):
    """Solicita y valida una jugada externa.

    Parámetros:
        tablero (list): Estado de los mini-tableros.
        macro_tablero (list): Estado del mega-tablero.
        destino (int o None): Mini-tablero obligatorio.

    Retorna:
        tuple: Primer movimiento con formato y legalidad válidos.
    """
    movimiento = None

    while movimiento is None:
        texto = input(
            "Movimiento del jugador: "
        )

        try:
            candidato = texto_a_movimiento(texto)

            if es_movimiento_legal(
                candidato,
                tablero,
                macro_tablero,
                destino
            ):
                movimiento = candidato

            else:
                print(
                    "Ese movimiento no es legal "
                    "en el estado actual."
                )
                mostrar_destino(destino)

        except ValueError as error:
            print(
                "Entrada inválida:",
                error
            )

    return movimiento


def ejecutar_partida():
    """Coordina una partida completa.

    Retorna:
        None. Alterna turnos, actualiza el estado y anuncia el resultado.
    """
    print(
        "GATO DE GATOS — "
        "MINIMAX CON HEURÍSTICA JERÁRQUICA"
    )

    mostrar_referencia_coordenadas()

    tablero = crear_tablero()
    macro_tablero = crear_macro_tablero()

    comienza_sistema = solicitar_quien_comienza()

    if comienza_sistema:
        marca_sistema = CRUZ
        marca_rival = CIRCULO
    else:
        marca_sistema = CIRCULO
        marca_rival = CRUZ

    print(
        "\nSistema:",
        marca_sistema,
        "| Jugador:",
        marca_rival
    )

    turno = CRUZ
    destino = None
    ganador = VACIO
    partida_terminada = False
    numero_turno = 1

    while not partida_terminada:
        mostrar_tablero(
            tablero,
            macro_tablero
        )
        mostrar_destino(destino)

        print(
            "\nTurno",
            numero_turno,
            "-",
            turno
        )

        if turno == marca_sistema:
            print(
                "El sistema está analizando..."
            )

            movimiento, informe = (
                elegir_movimiento_sistema(
                    tablero,
                    macro_tablero,
                    destino,
                    marca_sistema,
                    marca_rival
                )
            )

            print(
                "Movimiento del sistema:",
                movimiento_a_texto(movimiento)
            )

            print(
                "Profundidad:",
                informe["profundidad"],
                "| Nodos:",
                f'{informe["nodos"]:,}',
                "| Valor:",
                informe["valor"],
                "| Tiempo:",
                f'{informe["segundos"]:.2f} s'
            )

        else:
            movimiento = solicitar_movimiento_rival(
                tablero,
                macro_tablero,
                destino
            )

        _, destino = aplicar_movimiento(
            tablero,
            macro_tablero,
            movimiento,
            turno
        )

        ganador = obtener_ganador_global(
            macro_tablero
        )

        sin_movimientos = (
            len(
                obtener_movimientos_legales(
                    tablero,
                    macro_tablero,
                    destino
                )
            )
            == 0
        )

        partida_terminada = (
            ganador != VACIO
            or sin_movimientos
        )

        if not partida_terminada:
            turno = marca_contraria(turno)

        numero_turno += 1

    mostrar_tablero(
        tablero,
        macro_tablero
    )

    if ganador == marca_sistema:
        print(
            "\nResultado: ganó el sistema."
        )
    elif ganador == marca_rival:
        print(
            "\nResultado: ganó el jugador."
        )
    else:
        print(
            "\nResultado: empate."
        )


# ---------------------------------------------------------------------------
# PRUEBAS BÁSICAS
# ---------------------------------------------------------------------------

def ejecutar_pruebas_basicas():
    """Ejecuta comprobaciones deterministas.

    Retorna:
        None. Un error produce AssertionError; si todo funciona, muestra una
        confirmación.
    """
    tablero = crear_tablero()
    macro_tablero = crear_macro_tablero()

    assert texto_a_movimiento("Gc") == (6, 2)
    assert movimiento_a_texto((6, 2)) == "Gc"

    assert hay_tres_en_linea(
        [
            CRUZ, CRUZ, CRUZ,
            VACIO, VACIO, VACIO,
            VACIO, VACIO, VACIO
        ],
        CRUZ
    )

    estado_anterior, destino = aplicar_movimiento(
        tablero,
        macro_tablero,
        (6, 2),
        CRUZ
    )

    assert estado_anterior == VACIO
    assert destino == 2
    assert tablero[6][2] == CRUZ

    deshacer_movimiento(
        tablero,
        macro_tablero,
        (6, 2),
        estado_anterior
    )

    assert tablero[6][2] == VACIO

    macro_tablero[2] = CIRCULO

    assert (
        calcular_siguiente_destino(
            2,
            macro_tablero
        )
        is None
    )

    mini_empatado = [
        CRUZ, CIRCULO, CRUZ,
        CRUZ, CIRCULO, CIRCULO,
        CIRCULO, CRUZ, CRUZ
    ]

    assert (
        obtener_estado_mini(mini_empatado)
        == EMPATE
    )

    macro_tablero = crear_macro_tablero()
    macro_tablero[0] = CRUZ
    macro_tablero[1] = CRUZ
    macro_tablero[2] = CRUZ

    assert (
        obtener_ganador_global(macro_tablero)
        == CRUZ
    )

    print(
        "Pruebas básicas superadas correctamente."
    )


if __name__ == "__main__":
    if "--pruebas" in sys.argv:
        ejecutar_pruebas_basicas()
    else:
        ejecutar_partida()