"""
MÓDULO: interfaz.py
RESPONSABLE: Persona C
DESCRIPCIÓN: Interfaz de entrada/salida para el juego

Gestiona:
- Lectura de movimientos del usuario
- Mostrar el tablero en terminal
- Mensajes de estado

Convención del profesor:
- Campo (meta-tablero): letras mayúsculas A-I
- Posición (mini-tablero): letras minúsculas a-i
- Formato de movimiento: "Gc" = jugar en campo G, posición c
"""

from .config import *
from typing import Optional, Tuple
from . import tablero as tb


def _simbolo_campo(tablero: "tb.Tablero", fila_meta: int, col_meta: int) -> str:
    """Retorna el símbolo a mostrar para un campo del meta-tablero: su letra (A-I) si sigue en juego, o 'X'/'O'/'=' si ya se decidió."""
    valor = tablero.meta_tablero[fila_meta][col_meta]
    if valor == 'EMPATE':
        return '='
    if valor in (JUGADOR_X, JUGADOR_O):
        return valor
    return INDICES_INVERSOS[(fila_meta, col_meta)]


def _simbolo_celda(tablero: "tb.Tablero", fila_meta: int, col_meta: int, fila_mini: int, col_mini: int) -> str:
    """Retorna el símbolo a mostrar para una casilla: su letra (a-i) si está vacía, o 'X'/'O' si está ocupada."""
    valor = tablero.obtener_casilla(fila_meta, col_meta, fila_mini, col_mini)
    if valor is not None:
        return valor
    return INDICES_MINI_INVERSOS[(fila_mini, col_mini)]


def mostrar_tablero(tablero: "tb.Tablero") -> None:
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
    """
    Imprime un mensaje de estado al usuario.
    """
    print(mensaje)


def convertir_texto_a_movimiento(entrada: str) -> Tuple[int, int, int, int]:
    """Convierte una coordenada como ``Gc`` a sus cuatro índices internos.

    Lanza ValueError cuando la entrada no tiene exactamente una letra de
    campo mayúscula (A-I) seguida por una posición minúscula (a-i).
    """
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

    Formato esperado:
    - "Ac": Campo A (0,0), mini-posición c (0,2)
    - "Ee": Campo E (1,1), mini-posición e (1,1)
    - "Ig": Campo I (2,2), mini-posición g (2,0)

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
    """
    Muestra el movimiento que hizo la IA.

    Ejemplo: "IA juega: Gc"
    """
    campo = INDICES_INVERSOS[(fila_meta, col_meta)]
    posicion = INDICES_MINI_INVERSOS[(fila_mini, col_mini)]
    mostrar_movimiento(campo, posicion, jugador="IA")


def mostrar_estadisticas_ia(estadisticas: dict) -> None:
    """
    Muestra un resumen de la búsqueda que hizo la IA para decidir su
    último movimiento (minimax.ultimas_estadisticas).

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
    """
    Pregunta con qué símbolo quiere jugar el humano (para modo humano vs IA).

    Returns:
        'X' o 'O'
    """
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


def mostrar_estado_juego(tablero: "tb.Tablero", turno: str) -> None:
    """
    Muestra información de estado del juego: turno actual, ganador o empate.
    """
    ganador = tablero.detectar_ganador_meta()
    if ganador is not None:
        mostrar_mensaje(f"¡{ganador} ha ganado el juego!")
    elif tablero.verificar_empate():
        mostrar_mensaje("El juego terminó en empate.")
    else:
        mostrar_mensaje(f"Turno de: {turno}")
