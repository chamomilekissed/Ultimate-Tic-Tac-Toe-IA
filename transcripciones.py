"""
MODULO: transcripciones.py
DESCRIPCION: Genera automaticamente la transcripcion de una partida en el
mismo formato Markdown usado en "Case Study/" (tabla de jugadas +
estadisticas de la IA + evento por jugada + meta-tablero final + secuencia
compacta), para no tener que armarla a mano despues de cada partida.

Uso (ver main.py): se crea un RegistradorPartida al inicio de la partida,
se llama registrar() despues de cada jugada, y al terminar se llama
guardar() para escribir el archivo .md.
"""

import os
import re
from typing import Dict, List, Optional, Tuple

from config import INDICES_INVERSOS, INDICES_MINI_INVERSOS, JUGADOR_X, JUGADOR_O, VALOR_GANADOR
import tablero as tb

Movimiento = Tuple[int, int, int, int]


def letra_movimiento(movimiento: Movimiento) -> str:
    """Convierte un movimiento (fila_meta, col_meta, fila_mini, col_mini) a notacion 'Campo+Posicion' (ej. 'Gc')."""
    fila_meta, col_meta, fila_mini, col_mini = movimiento
    return INDICES_INVERSOS[(fila_meta, col_meta)] + INDICES_MINI_INVERSOS[(fila_mini, col_mini)]


def _formato_valor(valor: int) -> str:
    """Formatea el valor de la evaluacion con signo explicito; lo resalta en negritas si ya es casi terminal."""
    texto = "0" if valor == 0 else f"{valor:+d}"
    if abs(valor) >= VALOR_GANADOR // 2:
        texto = f"**{texto}**"
    return texto


def _formato_estadisticas(estadisticas: Optional[dict]) -> str:
    """Formatea 'profundidad / nodos / valor' para una jugada de la IA, o '-' si la jugo un humano."""
    if not estadisticas:
        return "—"
    return (
        f"{estadisticas.get('profundidad', '?')} / "
        f"{estadisticas.get('nodos', 0):,} / "
        f"{_formato_valor(estadisticas.get('valor', 0))}"
    )


def _siguiente_numero_juego(carpeta: str) -> int:
    """Encuentra el siguiente numero de 'Juego N' disponible, revisando los archivos ya existentes en la carpeta."""
    maximo = 0
    if os.path.isdir(carpeta):
        for nombre in os.listdir(carpeta):
            coincidencia = re.match(r'Juego (\d+)', nombre)
            if coincidencia:
                maximo = max(maximo, int(coincidencia.group(1)))
    return maximo + 1


class RegistradorPartida:
    """
    Acumula cada jugada de una partida (con las estadisticas de la IA, si
    aplica) para poder generar y guardar su transcripcion en Markdown al
    terminar, sin tener que copiarla a mano desde la consola.
    """

    def __init__(self, modo: str, origen_x: str = "Jugador", origen_o: str = "Jugador"):
        """
        Args:
            modo: Descripcion corta del modo de juego (ej. "Humano vs IA")
            origen_x, origen_o: Quien controla a X y a O (ej. "Humano", "IA")
        """
        self.modo = modo
        self.origenes = {JUGADOR_X: origen_x, JUGADOR_O: origen_o}
        self.jugadas: List[dict] = []

    def registrar(self, jugador: str, movimiento: Movimiento, estadisticas: Optional[dict] = None) -> None:
        """Registra una jugada ya aplicada. `estadisticas` es minimax.ultimas_estadisticas si la jugo la IA, o None si fue humana."""
        self.jugadas.append({
            "jugador": jugador,
            "movimiento": movimiento,
            "estadisticas": dict(estadisticas) if estadisticas else None,
        })

    def _reproducir(self) -> Tuple[List[dict], "tb.Tablero"]:
        """
        Reproduce las jugadas registradas sobre un tablero nuevo para
        detectar automaticamente que campos se ganaron/empataron y quien
        gano la partida, en vez de tener que anotarlo a mano.
        """
        tablero = tb.Tablero()
        filas = []
        for numero, jugada in enumerate(self.jugadas, start=1):
            jugador = jugada["jugador"]
            movimiento = jugada["movimiento"]
            fila_meta, col_meta, fila_mini, col_mini = movimiento

            antes = tablero.meta_tablero[fila_meta][col_meta]
            tablero.aplicar_movimiento(fila_meta, col_meta, fila_mini, col_mini, jugador)
            despues = tablero.meta_tablero[fila_meta][col_meta]
            campo = INDICES_INVERSOS[(fila_meta, col_meta)]

            evento = ""
            if antes is None and despues is not None:
                if despues == 'EMPATE':
                    evento = f"🤝 **Campo {campo} empata**"
                else:
                    evento = f"🏆 **{despues} gana {campo}**"

            ganador_meta = tablero.detectar_ganador_meta()
            if ganador_meta is not None:
                remate = f"**{ganador_meta} gana la partida**"
                evento = f"{evento} → {remate}" if evento else f"🏆 {remate}"

            filas.append({
                "numero": numero,
                "jugador": jugador,
                "letra": letra_movimiento(movimiento),
                "evento": evento,
                "estadisticas": jugada["estadisticas"],
            })
        return filas, tablero

    def generar_markdown(self, titulo: str) -> str:
        """Arma el documento Markdown completo: contexto, tabla, meta-tablero final y secuencia compacta."""
        filas, tablero_final = self._reproducir()

        lineas = [
            f"Transcripción generada automáticamente. Modo: **{self.modo}** "
            f"(X = {self.origenes[JUGADOR_X]}, O = {self.origenes[JUGADOR_O]}).",
            "",
            f"## Transcript — {titulo}",
            "",
            "|  # | Jugador | Movimiento | IA: prof. / nodos / valor | Evento |",
            "| -: | :-----: | :--------: | -------------------------- | ------ |",
        ]
        for fila in filas:
            lineas.append(
                f"| {fila['numero']:2d} | {fila['jugador']:^7s} | **{fila['letra']}** | "
                f"{_formato_estadisticas(fila['estadisticas'])} | {fila['evento']} |"
            )
        lineas.append("")

        lineas.append("Meta-tablero final:")
        lineas.append("")
        lineas.append("```text")
        for f in range(3):
            simbolos = [tablero_final.meta_tablero[f][c] for c in range(3)]
            fila_texto = [('=' if s == 'EMPATE' else s) or '.' for s in simbolos]
            lineas.append(" | ".join(fila_texto))
            if f < 2:
                lineas.append("- + - + -")
        lineas.append("```")
        lineas.append("")

        lineas.append("### Secuencia compacta")
        lineas.append("")
        lineas.append("```text")
        for fila in filas:
            sufijo = ""
            if fila["evento"]:
                texto_evento = re.sub(r'[🏆🤝*]', '', fila["evento"]).strip()
                texto_evento = texto_evento.replace('→', '->')
                sufijo = f"  -> {texto_evento}"
            lineas.append(f"{fila['jugador']}: {fila['letra']}{sufijo}")
        lineas.append("```")

        return "\n".join(lineas) + "\n"

    def guardar(self, carpeta: str = "Case Study") -> str:
        """
        Genera el markdown y lo guarda con el siguiente numero disponible
        ("Juego N.md", sin tildes ni tipografia especial en el nombre del
        archivo). Retorna la ruta donde se guardo.
        """
        os.makedirs(carpeta, exist_ok=True)
        siguiente = _siguiente_numero_juego(carpeta)
        titulo = f"Juego {siguiente}"
        ruta = os.path.join(carpeta, f"{titulo}.md")
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(self.generar_markdown(titulo))
        return ruta
