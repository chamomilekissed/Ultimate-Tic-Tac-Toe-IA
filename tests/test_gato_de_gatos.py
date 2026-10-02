"""Suite final de 100 casos para Gato de Gatos.

Prueba tanto la versión modular como el archivo único de entrega. Los casos
parametrizados cuentan por separado en pytest; la distribución está explicada
en README.md y se verifica con ``pytest --collect-only``.
"""

import ast
import importlib.util
import random
import sys
import time
from pathlib import Path

import pytest


RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import config
from src import evaluador
from src import interfaz
from src import minimax
from src import movimientos
from src import tablero


def cargar_archivo_unico():
    """Importa el archivo de entrega sin ejecutar su menú interactivo."""
    ruta = RAIZ / "codigo_final_spyder" / "gato_de_gatos.py"
    especificacion = importlib.util.spec_from_file_location("gato_final", ruta)
    assert especificacion is not None
    assert especificacion.loader is not None
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="session")
def final():
    """Módulo correspondiente al archivo único de entrega."""
    return cargar_archivo_unico()


COORDENADAS_VALIDAS = [
    (campo, posicion)
    for campo in config.CAMPOS
    for posicion in ("a", "i")
]

CASOS_LINEA = [
    (jugador, linea)
    for jugador in (config.JUGADOR_X, config.JUGADOR_O)
    for linea in config.LINEAS_MINI_TABLERO
]

DESTINOS = [
    (fila, columna)
    for fila in range(config.TAMAÑO_META)
    for columna in range(config.TAMAÑO_META)
]

PATRON_EMPATE = (
    (0, 0, "X"), (0, 1, "O"), (0, 2, "X"),
    (1, 0, "X"), (1, 1, "O"), (1, 2, "O"),
    (2, 0, "O"), (2, 1, "X"), (2, 2, "X"),
)


def crear_estado_aleatorio(semilla, cantidad_jugadas):
    """Crea una posición legal y reproducible para probar la heurística."""
    generador = random.Random(semilla)
    estado = tablero.Tablero()
    destino = None
    es_turno_x = True
    jugadas = 0
    activo = True

    while jugadas < cantidad_jugadas and activo:
        legales = movimientos.movimientos_validos(estado, destino)
        activo = len(legales) > 0
        if activo:
            movimiento = generador.choice(legales)
            jugador = config.JUGADOR_X if es_turno_x else config.JUGADOR_O
            assert estado.aplicar_movimiento(*movimiento, jugador)
            destino = (movimiento[2], movimiento[3])
            es_turno_x = not es_turno_x
            jugadas += 1

    return estado, destino, es_turno_x


def intercambiar_jugadores(estado):
    """Intercambia X y O sin alterar la geometría de una posición."""
    cambio = {None: None, "X": "O", "O": "X", "EMPATE": "EMPATE"}
    nuevo = tablero.Tablero()
    nuevo.mini_tableros = [
        [[cambio[celda] for celda in fila] for fila in mini]
        for mini in estado.mini_tableros
    ]
    nuevo.meta_tablero = [
        [cambio[celda] for celda in fila]
        for fila in estado.meta_tablero
    ]
    return nuevo


# 18 casos: dos posiciones representativas para cada campo A-I.
@pytest.mark.parametrize("campo,posicion", COORDENADAS_VALIDAS)
def test_01_coordenadas_validas(campo, posicion, final):
    texto = campo + posicion
    esperado = (*config.CAMPOS[campo], *config.POSICIONES_MINI[posicion])
    assert interfaz.convertir_texto_a_movimiento(texto) == esperado
    assert final.convertir_texto_a_movimiento(texto) == esperado


# 16 casos: ocho líneas de victoria para cada jugador.
@pytest.mark.parametrize("jugador,linea", CASOS_LINEA)
def test_02_victorias_en_mini_tablero(jugador, linea, final):
    mini = [[None for _ in range(3)] for _ in range(3)]
    for fila, columna in linea:
        mini[fila][columna] = jugador

    assert tablero.Tablero().detectar_ganador_mini(mini) == jugador
    assert final.Tablero().detectar_ganador_mini(mini) == jugador


# 16 casos: ocho líneas globales para cada jugador.
@pytest.mark.parametrize("jugador,linea", CASOS_LINEA)
def test_03_victorias_en_meta_tablero(jugador, linea, final):
    modular = tablero.Tablero()
    unico = final.Tablero()
    for fila, columna in linea:
        modular.meta_tablero[fila][columna] = jugador
        unico.meta_tablero[fila][columna] = jugador

    assert modular.detectar_ganador_meta() == jugador
    assert unico.detectar_ganador_meta() == jugador


# 9 casos: uno por cada posible mini-tablero obligatorio.
@pytest.mark.parametrize("destino", DESTINOS)
def test_04_restriccion_de_destino(destino, final):
    modular = tablero.Tablero()
    unico = final.Tablero()
    legales_modulares = movimientos.movimientos_validos(modular, destino)
    legales_unicos = final.movimientos_validos(unico, destino)

    assert len(legales_modulares) == 9
    assert legales_modulares == legales_unicos
    assert all(movimiento[:2] == destino for movimiento in legales_modulares)


# 9 casos: aplicar y deshacer en cada campo del meta-tablero.
@pytest.mark.parametrize("destino", DESTINOS)
def test_05_aplicar_y_deshacer(destino, final):
    modular = tablero.Tablero()
    unico = final.Tablero()
    movimiento = (*destino, 1, 1)
    hash_inicial_modular = modular.get_estado_hash()
    hash_inicial_unico = unico.get_estado_hash()

    assert modular.aplicar_movimiento(*movimiento, config.JUGADOR_X)
    assert unico.aplicar_movimiento(*movimiento, config.JUGADOR_X)
    assert modular.obtener_casilla(*movimiento) == config.JUGADOR_X
    assert unico.obtener_casilla(*movimiento) == config.JUGADOR_X
    assert modular.deshacer_movimiento()
    assert unico.deshacer_movimiento()
    assert modular.get_estado_hash() == hash_inicial_modular
    assert unico.get_estado_hash() == hash_inicial_unico


# 9 casos: empatar cada campo debe liberar el siguiente destino.
@pytest.mark.parametrize("destino", DESTINOS)
def test_06_empate_local_libera_destino(destino, final):
    modular = tablero.Tablero()
    unico = final.Tablero()

    for fila, columna, jugador in PATRON_EMPATE:
        assert modular.aplicar_movimiento(*destino, fila, columna, jugador)
        assert unico.aplicar_movimiento(*destino, fila, columna, jugador)

    assert modular.meta_tablero[destino[0]][destino[1]] == "EMPATE"
    assert unico.meta_tablero[destino[0]][destino[1]] == "EMPATE"
    legales_modulares = movimientos.movimientos_validos(modular, destino)
    legales_unicos = final.movimientos_validos(unico, destino)
    assert len(legales_modulares) == 72
    assert legales_modulares == legales_unicos
    assert all(movimiento[:2] != destino for movimiento in legales_modulares)


# 8 casos: la evaluación debe cambiar de signo al intercambiar X y O.
@pytest.mark.parametrize("semilla", range(8))
def test_07_simetria_de_la_heuristica(semilla):
    estado, destino, es_turno_x = crear_estado_aleatorio(semilla, 12 + semilla)
    contrario = intercambiar_jugadores(estado)
    valor = evaluador.evaluar_posicion(estado, es_turno_x, destino)
    valor_contrario = evaluador.evaluar_posicion(contrario, not es_turno_x, destino)
    assert valor == -valor_contrario


# 8 casos: Minimax debe completar cualquiera de las ocho líneas posibles.
@pytest.mark.parametrize("linea", config.LINEAS_MINI_TABLERO)
def test_08_minimax_completa_victoria_global(linea, final):
    modular = tablero.Tablero()
    unico = final.Tablero()
    for estado in (modular, unico):
        estado.meta_tablero[0][0] = config.JUGADOR_X
        estado.meta_tablero[0][1] = config.JUGADOR_X
        mini = estado.obtener_mini_tablero(0, 2)
        for fila, columna in linea[:2]:
            mini[fila][columna] = config.JUGADOR_X

    esperada = (0, 2, *linea[2])
    resultado_modular = minimax.obtener_mejor_movimiento_hoja(
        modular, 1, float("-inf"), float("inf"), True, (0, 2),
        minimax.TranspositionTable(),
    )
    resultado_unico = final.obtener_mejor_movimiento_hoja(
        unico, 1, float("-inf"), float("inf"), True, (0, 2),
        final.TranspositionTable(),
    )

    assert resultado_modular is not None
    assert resultado_unico is not None
    assert resultado_modular[:4] == esperada
    assert resultado_unico[:4] == esperada


# Los siete casos siguientes llevan el total exacto a 100.
def test_09_entradas_invalidas(final):
    invalidas = ("", "A", "Aaa", "aa", "Jb", "Az", "A1", " Gc extra ")
    for entrada in invalidas:
        with pytest.raises(ValueError):
            interfaz.convertir_texto_a_movimiento(entrada)
        with pytest.raises(ValueError):
            final.convertir_texto_a_movimiento(entrada)


def test_10_validaciones_extremas_de_reglas(final):
    for clase_tablero in (tablero.Tablero, final.Tablero):
        estado = clase_tablero()
        assert not estado.aplicar_movimiento(-1, 0, 0, 0, "X")
        assert not estado.aplicar_movimiento(0, 0, 0, 0, "Z")
        assert estado.aplicar_movimiento(0, 0, 0, 0, "X")
        assert estado.aplicar_movimiento(0, 0, 0, 1, "X")
        assert estado.aplicar_movimiento(0, 0, 0, 2, "X")
        assert not estado.aplicar_movimiento(0, 0, 1, 1, "O")

    modular = tablero.Tablero()
    unico = final.Tablero()
    modular.meta_tablero[0] = ["X", "X", "X"]
    unico.meta_tablero[0] = ["X", "X", "X"]
    assert movimientos.movimientos_validos(modular, None) == []
    assert final.movimientos_validos(unico, None) == []


def test_11_tabla_de_transposiciones_con_cotas(final):
    for modulo in (minimax, final):
        cache = modulo.TranspositionTable()
        cache.guardar("exacta", 12, modulo.TIPO_EXACTO)
        cache.guardar("inferior", 20, modulo.TIPO_COTA_INFERIOR)
        cache.guardar("superior", -5, modulo.TIPO_COTA_SUPERIOR)
        assert cache.obtener("exacta") == (12, modulo.TIPO_EXACTO)
        assert cache.obtener("inferior") == (20, modulo.TIPO_COTA_INFERIOR)
        assert cache.obtener("superior") == (-5, modulo.TIPO_COTA_SUPERIOR)
        cache.limpiar()
        assert cache.obtener("exacta") is None


def test_12_limite_de_tiempo_no_muta_el_tablero(final):
    casos = (
        (tablero.Tablero(), movimientos.movimientos_validos, minimax),
        (final.Tablero(), final.movimientos_validos, final),
    )
    for estado, obtener_legales, modulo_ia in casos:
        antes = [[fila[:] for fila in mini] for mini in estado.mini_tableros]
        legales = obtener_legales(estado, None)
        inicio = time.monotonic()
        elegido = modulo_ia.mejor_movimiento(estado, None, tiempo_limite=0.02)
        duracion = time.monotonic() - inicio
        assert elegido in legales
        assert estado.mini_tableros == antes
        assert duracion <= 0.75
        assert modulo_ia.ultimas_estadisticas["presupuesto"] <= 0.02


def test_13_paridad_entre_modulos_y_archivo_unico(final):
    modular = tablero.Tablero()
    unico = final.Tablero()
    destino = None
    es_turno_x = True
    pasos = 0
    activo = True

    while pasos < 24 and activo:
        legales_modulares = movimientos.movimientos_validos(modular, destino)
        legales_unicos = final.movimientos_validos(unico, destino)
        assert legales_modulares == legales_unicos
        activo = len(legales_modulares) > 0
        if activo:
            elegido = legales_modulares[(pasos * 7) % len(legales_modulares)]
            jugador = config.JUGADOR_X if es_turno_x else config.JUGADOR_O
            assert modular.aplicar_movimiento(*elegido, jugador)
            assert unico.aplicar_movimiento(*elegido, jugador)
            destino = (elegido[2], elegido[3])
            es_turno_x = not es_turno_x
            pasos += 1

    assert modular.mini_tableros == unico.mini_tableros
    assert modular.meta_tablero == unico.meta_tablero
    assert evaluador.evaluar_posicion(modular, es_turno_x, destino) == final.evaluar_posicion(
        unico, es_turno_x, destino
    )


def test_14_partida_completa_rapida_en_archivo_unico(final):
    random.seed(2026)
    estado = final.Tablero()
    destino = None
    es_turno_x = True
    turnos = 0
    partida_terminada = False

    while turnos < 81 and not partida_terminada:
        legales = final.movimientos_validos(estado, destino)
        assert len(legales) > 0
        antes = [[fila[:] for fila in mini] for mini in estado.mini_tableros]
        elegido = final.mejor_movimiento(estado, destino, tiempo_limite=0.003)
        assert estado.mini_tableros == antes
        assert elegido in legales
        jugador = final.JUGADOR_X if es_turno_x else final.JUGADOR_O
        assert estado.aplicar_movimiento(*elegido, jugador)
        destino = (elegido[2], elegido[3])
        es_turno_x = not es_turno_x
        turnos += 1
        partida_terminada = (
            estado.detectar_ganador_meta() is not None
            or estado.verificar_empate()
        )

    assert partida_terminada
    assert 1 <= turnos <= 81


def test_15_sin_break_continue_ni_pass():
    prohibidas = (ast.Break, ast.Continue, ast.Pass)
    hallazgos = []
    for ruta in sorted(RAIZ.rglob("*.py")):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, prohibidas):
                hallazgos.append(f"{ruta.relative_to(RAIZ)}:{nodo.lineno}")
    assert hallazgos == []
