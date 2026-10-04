"""
MÓDULO: torneo.py
DESCRIPCIÓN: Ejecuta partidas de la IA contra sí misma sin interfaz ni
impresión del tablero, para reunir estadísticas agregadas de desempeño:
tasa de victorias de X y O, empates y duración promedio de
partida, etc.

No modifica minimax.py ni evaluador.py; solo ejecuta la IA tal como está
y mide resultados de integración. Como la decisión final es determinista, dos
partidas desde el tablero vacío pueden repetir la misma secuencia. Para
comparar heurísticas deben alternarse ambas evaluaciones y usarse aperturas
legales variadas, como se hizo en la calibración final documentada.

Uso:
    python3 -m src.torneo                    # 20 partidas, 2s por jugada
    python3 -m src.torneo 30                 # 30 partidas, 2s por jugada
    python3 -m src.torneo 30 1.0             # 30 partidas, 1s por jugada

Nota sobre ``tiempo_limite``: el presupuesto real por jugada sigue acotado por
la lógica de ``mejor_movimiento()`` (adaptativo por etapa de partida, nunca
excede este valor). 2s por jugada con ~40-50 jugadas por partida da
partidas de un minuto o dos. Para simular mejor la competencia se puede usar
un ``tiempo_limite`` mayor, a costa de que el torneo tarde mucho más.
"""

import statistics
import sys
import time
from pathlib import Path
from typing import List

from . import tablero as tb
from . import minimax as mm
from .config import JUGADOR_X, JUGADOR_O
from .transcripciones import letra_movimiento


CARPETA_RESULTADOS = Path(__file__).resolve().parents[1] / "resultados"


def jugar_partida_silenciosa(tiempo_limite: float) -> dict:
    """
    Juega una partida completa IA vs IA sin ninguna salida por pantalla.

    Retorna:
        Diccionario con el ganador, la cantidad de jugadas, la secuencia en
        notación ``Campo+Posición`` y la duración total en segundos.
    """
    tablero = tb.Tablero()
    es_turno_x = True
    tablero_destino = None
    movimientos_jugados: List[str] = []

    inicio = time.monotonic()
    partida_terminada = False
    while not partida_terminada:
        jugador = JUGADOR_X if es_turno_x else JUGADOR_O
        movimiento = mm.mejor_movimiento(
            tablero, tablero_destino, tiempo_limite=tiempo_limite
        )
        if movimiento is None:
            partida_terminada = True
        else:
            movimientos_jugados.append(letra_movimiento(movimiento))
            tablero.aplicar_movimiento(*movimiento, jugador)
            partida_terminada = (
                tablero.detectar_ganador_meta() is not None
                or tablero.verificar_empate()
            )

            if not partida_terminada:
                es_turno_x = not es_turno_x
                tablero_destino = (movimiento[2], movimiento[3])

    return {
        "ganador": tablero.detectar_ganador_meta(),
        "num_jugadas": len(movimientos_jugados),
        "movimientos": movimientos_jugados,
        "duracion_segundos": time.monotonic() - inicio,
    }


def correr_torneo(cantidad_partidas: int, tiempo_limite: float) -> List[dict]:
    """
    Ejecuta ``cantidad_partidas`` partidas de la IA contra sí misma, imprime
    el progreso y guarda un registro compacto con los resultados.

    Retorna:
        La lista de resultados (uno por partida), por si se quiere seguir
        analizando en el mismo proceso, por ejemplo, desde Spyder.
    """
    resultados: List[dict] = []
    victorias_x = victorias_o = empates = 0

    print(
        f"Corriendo torneo: {cantidad_partidas} partidas, "
        f"{tiempo_limite}s por jugada...\n"
    )
    inicio_torneo = time.time()

    for numero_partida in range(1, cantidad_partidas + 1):
        resultado = jugar_partida_silenciosa(tiempo_limite)
        resultados.append(resultado)

        ganador = resultado["ganador"]
        if ganador == JUGADOR_X:
            victorias_x += 1
        elif ganador == JUGADOR_O:
            victorias_o += 1
        else:
            empates += 1

        etiqueta = ganador or "EMPATE"
        print(
            f"Partida {numero_partida:3d}/{cantidad_partidas}: "
            f"{etiqueta:6s} en {resultado['num_jugadas']:2d} jugadas "
            f"({resultado['duracion_segundos']:5.1f}s)  ->  "
            f"X:{victorias_x} O:{victorias_o} empate:{empates}"
        )

    duracion_total = time.time() - inicio_torneo

    _reportar_resumen(resultados, duracion_total)
    CARPETA_RESULTADOS.mkdir(exist_ok=True)
    ruta_registro = CARPETA_RESULTADOS / (
        f"resultado_torneo_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    )
    _guardar_registro(resultados, ruta_registro, tiempo_limite)
    print(f"\nRegistro detallado guardado en: {ruta_registro}")

    return resultados


def _reportar_resumen(resultados: List[dict], duracion_total: float) -> None:
    """Imprime tasas de victoria y duración de las partidas del torneo."""
    cantidad_resultados = len(resultados)
    victorias_x = sum(
        1 for resultado in resultados if resultado["ganador"] == JUGADOR_X
    )
    victorias_o = sum(
        1 for resultado in resultados if resultado["ganador"] == JUGADOR_O
    )
    empates = cantidad_resultados - victorias_x - victorias_o
    jugadas_por_partida = [resultado["num_jugadas"] for resultado in resultados]

    print("\n" + "=" * 55)
    print("RESUMEN DEL TORNEO")
    print("=" * 55)
    print(f"Partidas jugadas:        {cantidad_resultados}")
    print(
        f"Victorias de X:          {victorias_x:3d}  ({100 * victorias_x / cantidad_resultados:5.1f}%)"
    )
    print(
        f"Victorias de O:          {victorias_o:3d}  ({100 * victorias_o / cantidad_resultados:5.1f}%)"
    )
    print(
        f"Empates:                 {empates:3d}  ({100 * empates / cantidad_resultados:5.1f}%)"
    )
    print(
        f"Jugadas por partida:     promedio={statistics.mean(jugadas_por_partida):.1f}  "
        f"min={min(jugadas_por_partida)}  max={max(jugadas_por_partida)}"
        + (
            f"  desv.est.={statistics.stdev(jugadas_por_partida):.1f}"
            if cantidad_resultados > 1
            else ""
        )
    )
    print(
        f"Tiempo total del torneo: {duracion_total / 60:.1f} min "
        f"({duracion_total / cantidad_resultados:.1f}s por partida en promedio)"
    )
    print("=" * 55)

    if cantidad_resultados < 20:
        print(
            f"\nAviso: con solo {cantidad_resultados} partidas, estos "
            "porcentajes tienen mucho margen de error."
        )
        print("Para conclusiones más confiables, ejecutar 30 partidas o más.")


def _guardar_registro(resultados: List[dict], ruta: Path, tiempo_limite: float) -> None:
    """Guarda un registro que permite reconstruir cada partida después."""
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(
            f"Registro de torneo -- {len(resultados)} partidas, "
            f"tiempo_limite={tiempo_limite}s por jugada\n\n"
        )
        for numero_partida, resultado in enumerate(resultados, start=1):
            ganador = resultado["ganador"] or "EMPATE"
            archivo.write(
                f"Partida {numero_partida}: {ganador} en "
                f"{resultado['num_jugadas']} jugadas\n"
            )
            archivo.write("  " + " ".join(resultado["movimientos"]) + "\n\n")


if __name__ == "__main__":
    _cantidad_partidas = (
        int(sys.argv[1])
        if len(sys.argv) > 1 and not sys.argv[1].startswith("--")
        else 20
    )
    _tiempo_limite = (
        float(sys.argv[2])
        if len(sys.argv) > 2 and not sys.argv[2].startswith("--")
        else 2.0
    )
    correr_torneo(_cantidad_partidas, _tiempo_limite)
