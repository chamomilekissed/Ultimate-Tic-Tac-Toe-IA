"""
MODULO: torneo.py
DESCRIPCION: Corre un torneo de partidas IA vs IA headless (sin interfaz de
usuario, sin imprimir el tablero) para juntar estadisticas agregadas de
desempeno: tasa de victorias de X vs O, empates, duracion promedio de
partida, etc.

No modifica minimax.py ni evaluador.py -- solo ejecuta la IA tal como esta
y mide resultados sobre muchas partidas. Sirve para convertir "creo que X
domina" en un dato real, y como base para comparar variantes de pesos en el
futuro (self-play con desempate aleatorio ya no repite la misma partida).

Uso:
    python3 torneo.py                    # 20 partidas, 2s por jugada
    python3 torneo.py 30                 # 30 partidas, 2s por jugada
    python3 torneo.py 30 1.0             # 30 partidas, 1s por jugada
    python3 torneo.py 30 1.0 --seed 42   # reproducible (mismos desempates)

Nota sobre tiempo_limite: el presupuesto real por jugada sigue acotado por
la logica de mejor_movimiento() (adaptativo por etapa de partida, nunca
excede este valor). 2s por jugada con ~40-50 jugadas por partida da
partidas de un minuto o dos; para partidas mas "reales" (mas parecidas a
jugar de verdad) usa un tiempo_limite mayor, a costa de que el torneo tarde
mucho mas en total.
"""

import statistics
import sys
import time
import random
from typing import List, Optional

import tablero as tb
import minimax as mm
from config import JUGADOR_X, JUGADOR_O
from transcripciones import letra_movimiento


def jugar_partida_silenciosa(tiempo_limite: float) -> dict:
    """
    Juega una partida completa IA vs IA sin ninguna salida por pantalla.

    Returns:
        dict con: ganador ('X', 'O' o None si empate), num_jugadas,
        movimientos (lista de jugadas en notacion 'Campo+Posicion'), y
        duracion_seg (tiempo real de reloj que tomo la partida completa).
    """
    tablero = tb.Tablero()
    es_turno_x = True
    tablero_destino = None
    movimientos_jugados: List[str] = []

    inicio = time.time()
    while True:
        jugador = JUGADOR_X if es_turno_x else JUGADOR_O
        movimiento = mm.mejor_movimiento(tablero, tablero_destino, tiempo_limite=tiempo_limite)
        if movimiento is None:
            break

        movimientos_jugados.append(letra_movimiento(movimiento))
        tablero.aplicar_movimiento(*movimiento, jugador)

        if tablero.detectar_ganador_meta() is not None or tablero.verificar_empate():
            break

        es_turno_x = not es_turno_x
        tablero_destino = (movimiento[2], movimiento[3])

    return {
        "ganador": tablero.detectar_ganador_meta(),
        "num_jugadas": len(movimientos_jugados),
        "movimientos": movimientos_jugados,
        "duracion_seg": time.time() - inicio,
    }


def correr_torneo(num_partidas: int, tiempo_limite: float,
                   semilla: Optional[int] = None) -> List[dict]:
    """
    Corre `num_partidas` partidas IA vs IA headless, imprime el progreso
    con un marcador acumulado, y al final reporta estadisticas agregadas
    y guarda un log compacto de todas las partidas.

    Returns:
        La lista de resultados (uno por partida), por si se quiere seguir
        analizando en el mismo proceso (ej. desde una sesion interactiva).
    """
    if semilla is not None:
        random.seed(semilla)

    resultados: List[dict] = []
    victorias_x = victorias_o = empates = 0

    print(f"Corriendo torneo: {num_partidas} partidas, {tiempo_limite}s por jugada...\n")
    inicio_torneo = time.time()

    for i in range(1, num_partidas + 1):
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
        print(f"Partida {i:3d}/{num_partidas}: {etiqueta:6s} en {resultado['num_jugadas']:2d} jugadas "
              f"({resultado['duracion_seg']:5.1f}s)  ->  X:{victorias_x} O:{victorias_o} empate:{empates}")

    duracion_total = time.time() - inicio_torneo

    _reportar_resumen(resultados, duracion_total)
    ruta_log = f"resultados_torneo_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    _guardar_log(resultados, ruta_log, tiempo_limite)
    print(f"\nLog detallado guardado en: {ruta_log}")

    return resultados


def _reportar_resumen(resultados: List[dict], duracion_total: float) -> None:
    """Imprime el resumen agregado del torneo: tasas de victoria y duracion de partida."""
    n = len(resultados)
    victorias_x = sum(1 for r in resultados if r["ganador"] == JUGADOR_X)
    victorias_o = sum(1 for r in resultados if r["ganador"] == JUGADOR_O)
    empates = n - victorias_x - victorias_o
    jugadas_por_partida = [r["num_jugadas"] for r in resultados]

    print("\n" + "=" * 55)
    print("RESUMEN DEL TORNEO")
    print("=" * 55)
    print(f"Partidas jugadas:        {n}")
    print(f"Victorias de X:          {victorias_x:3d}  ({100 * victorias_x / n:5.1f}%)")
    print(f"Victorias de O:          {victorias_o:3d}  ({100 * victorias_o / n:5.1f}%)")
    print(f"Empates:                 {empates:3d}  ({100 * empates / n:5.1f}%)")
    print(f"Jugadas por partida:     promedio={statistics.mean(jugadas_por_partida):.1f}  "
          f"min={min(jugadas_por_partida)}  max={max(jugadas_por_partida)}"
          + (f"  desv.est.={statistics.stdev(jugadas_por_partida):.1f}" if n > 1 else ""))
    print(f"Tiempo total del torneo: {duracion_total / 60:.1f} min "
          f"({duracion_total / n:.1f}s por partida en promedio)")
    print("=" * 55)

    if n < 20:
        print(f"\nAviso: con solo {n} partidas, estos porcentajes tienen mucho margen de error.")
        print("Para conclusiones mas confiables sobre ventaja de X vs O, correr 30+ partidas.")


def _guardar_log(resultados: List[dict], ruta: str, tiempo_limite: float) -> None:
    """Guarda un log de texto plano con la secuencia de jugadas de cada partida, para poder reconstruir alguna despues si llama la atencion."""
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(f"Log de torneo -- {len(resultados)} partidas, tiempo_limite={tiempo_limite}s por jugada\n\n")
        for i, resultado in enumerate(resultados, start=1):
            ganador = resultado["ganador"] or "EMPATE"
            archivo.write(f"Partida {i}: {ganador} en {resultado['num_jugadas']} jugadas\n")
            archivo.write("  " + " ".join(resultado["movimientos"]) + "\n\n")


if __name__ == "__main__":
    _num_partidas = int(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else 20
    _tiempo_limite = float(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else 2.0
    _semilla = None
    if "--seed" in sys.argv:
        _semilla = int(sys.argv[sys.argv.index("--seed") + 1])

    correr_torneo(_num_partidas, _tiempo_limite, _semilla)
