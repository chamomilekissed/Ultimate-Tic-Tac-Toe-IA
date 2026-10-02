"""
MÓDULO: main.py
RESPONSABLE: Persona C
DESCRIPCIÓN: Loop principal del juego

Coordina la lógica del juego: inicialización, turnos, detección de fin
de juego y entrada/salida a través de interfaz.py. Soporta tres modos:
humano vs humano, IA vs IA, y humano vs IA.
"""

from config import *
import tablero as tb
import movimientos as mov
import minimax as mm
import interfaz as ui
from transcripciones import RegistradorPartida
from typing import Callable, Optional, Tuple


def obtener_movimiento_valido(tablero: "tb.Tablero", tablero_destino: Optional[Tuple[int, int]]) -> Tuple[Tuple[int, int, int, int], None]:
    """
    Pide movimientos al usuario hasta obtener uno legal.

    Un movimiento es legal si aparece en movimientos.movimientos_validos()
    para el tablero_destino vigente (respeta la casilla obligatoria y que
    esté vacía).

    Returns:
        (movimiento, None) — el segundo elemento va en None porque no hay
        estadísticas de búsqueda que registrar para una jugada humana (ver
        ObtenerMovimiento / RegistradorPartida).
    """
    movimientos_legales = mov.movimientos_validos(tablero, tablero_destino)
    while True:
        movimiento = ui.obtener_movimiento_usuario()
        if movimiento in movimientos_legales:
            return movimiento, None
        ui.mostrar_mensaje("Movimiento no permitido: la casilla está ocupada o no corresponde al campo obligatorio.")


def imprimir_resultado(tablero: "tb.Tablero") -> None:
    """
    Imprime el tablero final y el resultado del juego.
    """
    ui.mostrar_tablero(tablero)
    ganador = tablero.detectar_ganador_meta()
    if ganador is not None:
        ui.mostrar_mensaje(f"{ganador} GANA")
    else:
        ui.mostrar_mensaje("EMPATE")


def _movimiento_ia(tablero: "tb.Tablero", tablero_destino: Optional[Tuple[int, int]]) -> Tuple[Tuple[int, int, int, int], dict]:
    """Obtiene el movimiento de la IA (minimax), lo anuncia y muestra estadísticas de la búsqueda.

    Returns:
        (movimiento, estadisticas) — estadisticas es una copia de
        minimax.ultimas_estadisticas en el momento de esta jugada, para que
        RegistradorPartida pueda incluirla en la transcripción.
    """
    movimiento = mm.mejor_movimiento(tablero, tablero_destino)
    ui.mostrar_movimiento_ia(*movimiento)
    ui.mostrar_estadisticas_ia(mm.ultimas_estadisticas)
    return movimiento, dict(mm.ultimas_estadisticas)


ObtenerMovimiento = Callable[["tb.Tablero", Optional[Tuple[int, int]]], Tuple[Tuple[int, int, int, int], Optional[dict]]]


def _ejecutar_partida(tablero: "tb.Tablero", obtener_movimiento_x: ObtenerMovimiento,
                     obtener_movimiento_o: ObtenerMovimiento,
                     registrador: Optional[RegistradorPartida] = None) -> None:
    """
    Corre el loop principal de una partida, delegando en las funciones dadas
    cómo obtener el movimiento de X y de O (humano o IA) en cada turno.

    Si se da un `registrador`, cada jugada se le registra y, al terminar la
    partida, se guarda automáticamente su transcripción en Case Study/.
    """
    es_turno_x = True
    tablero_destino = None
    partida_terminada = False

    while not partida_terminada:
        ui.mostrar_tablero(tablero)

        if es_turno_x:
            ui.mostrar_mensaje("Turno de X")
            jugador = JUGADOR_X
            movimiento, estadisticas = obtener_movimiento_x(tablero, tablero_destino)
        else:
            ui.mostrar_mensaje("Turno de O")
            jugador = JUGADOR_O
            movimiento, estadisticas = obtener_movimiento_o(tablero, tablero_destino)

        tablero.aplicar_movimiento(*movimiento, jugador)
        if registrador is not None:
            registrador.registrar(jugador, movimiento, estadisticas)

        partida_terminada = (
            tablero.detectar_ganador_meta() is not None
            or tablero.verificar_empate()
        )
        if partida_terminada:
            imprimir_resultado(tablero)
            if registrador is not None:
                ruta = registrador.guardar()
                ui.mostrar_mensaje(f"Transcripción guardada en: {ruta}")
        else:
            es_turno_x = not es_turno_x
            tablero_destino = (movimiento[2], movimiento[3])


def jugar() -> None:
    """
    Ejecuta un juego completo de Ultimate Tic-Tac-Toe humano vs humano.
    """
    registrador = RegistradorPartida("Humano vs Humano", origen_x="Humano", origen_o="Humano")
    _ejecutar_partida(tb.Tablero(), obtener_movimiento_valido, obtener_movimiento_valido, registrador)


def jugar_ia_vs_ia() -> None:
    """
    Ejecuta un juego completo de Ultimate Tic-Tac-Toe IA vs IA (minimax
    contra sí mismo), para observar cómo juega.
    """
    registrador = RegistradorPartida("IA vs IA", origen_x="IA", origen_o="IA")
    _ejecutar_partida(tb.Tablero(), _movimiento_ia, _movimiento_ia, registrador)


def jugar_humano_vs_ia() -> None:
    """
    Ejecuta un juego completo de Ultimate Tic-Tac-Toe humano vs IA.

    Pregunta con qué símbolo quiere jugar el humano. X siempre inicia: si
    el humano elige X comienza la persona; si elige O comienza la IA.
    """
    tablero = tb.Tablero()
    simbolo_humano = ui.solicitar_simbolo_jugador()

    if simbolo_humano == JUGADOR_X:
        registrador = RegistradorPartida("Humano vs IA", origen_x="Humano", origen_o="IA")
        _ejecutar_partida(tablero, obtener_movimiento_valido, _movimiento_ia, registrador)
    else:
        registrador = RegistradorPartida("Humano vs IA", origen_x="IA", origen_o="Humano")
        _ejecutar_partida(tablero, _movimiento_ia, obtener_movimiento_valido, registrador)


if __name__ == "__main__":
    opcion = ui.solicitar_modo_juego()

    if opcion == "1":
        jugar()
    elif opcion == "2":
        jugar_ia_vs_ia()
    elif opcion == "3":
        jugar_humano_vs_ia()
