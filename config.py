"""
Configuración global del proyecto Gato de Gatos
"""

# ===== CONSTANTES DEL JUEGO =====

# Símbolos de jugadores
JUGADOR_X = 'X'
JUGADOR_O = 'O'
VACIO = None

# Tamaño del tablero
TAMAÑO_MINI = 3  # Cada mini-tablero es 3x3
TAMAÑO_META = 3  # Meta-tablero es 3x3 (de mini-tableros)
TOTAL_CASILLAS = TAMAÑO_MINI * TAMAÑO_MINI * TAMAÑO_META * TAMAÑO_META  # 81

# Índices de meta-tablero
# A | B | C
# D | E | F
# G | H | I
CAMPOS = {
    'A': (0, 0), 'B': (0, 1), 'C': (0, 2),
    'D': (1, 0), 'E': (1, 1), 'F': (1, 2),
    'G': (2, 0), 'H': (2, 1), 'I': (2, 2)
}

INDICES_INVERSOS = {v: k for k, v in CAMPOS.items()}

# Índices de mini-tablero
# a | b | c
# d | e | f
# g | h | i
POSICIONES_MINI = {
    'a': (0, 0), 'b': (0, 1), 'c': (0, 2),
    'd': (1, 0), 'e': (1, 1), 'f': (1, 2),
    'g': (2, 0), 'h': (2, 1), 'i': (2, 2)
}

INDICES_MINI_INVERSOS = {v: k for k, v in POSICIONES_MINI.items()}

# ===== CONSTANTES DE MINIMAX =====

# Profundidad inicial de búsqueda
PROFUNDIDAD_INICIAL = 5

# Tiempo límite para decisión (segundos)
TIEMPO_LIMITE = 30

# Valores heurísticos extremos
VALOR_GANADOR = 10000
VALOR_PERDEDOR = -10000
VALOR_EMPATE = 0

# ===== PESOS DE LA FUNCIÓN HEURÍSTICA =====

PESO_PROGRESO_META_TABLERO = 10  # ¿Cuántos campos ha ganado?
PESO_AMENAZAS_BIFURCACIONES = 7  # ¿Tiene 2 amenazas? ¿El oponente las tiene?
PESO_DEFENSA_CRITICA = 6         # ¿El oponente va a ganar pronto?
PESO_POSICIONES_CLAVE = 7        # ¿Controla centro/esquinas del meta-tablero?
PESO_CONTROL_LOCAL = 3           # Evaluación dentro de mini-tableros
PESO_AMENAZA_DESTINO = 8         # ¿A qué mini-tablero se manda al rival: es un regalo o una trampa?

# ===== CONSTANTES DE MINIMAX (BÚSQUEDA) =====

# Presupuesto de tiempo por etapa de partida (según casillas vacías en
# mini-tableros disponibles). Siempre limitado por el tiempo_limite que
# reciba mejor_movimiento(); nunca lo excede, solo puede acortarlo.
CASILLAS_RESTANTES_APERTURA = 55
CASILLAS_RESTANTES_MEDIO = 25
TIEMPO_APERTURA = 4.0
TIEMPO_MEDIO_PARTIDA = 10.0
TIEMPO_FINAL_PARTIDA = 25.0

# Tamaño máximo de la Transposition Table (entradas) antes de dejar de guardar más
LIMITE_ESTADOS_MEMORIA = 120_000

# ===== MAPA DE POSICIONES A LÍNEAS DE VICTORIA =====
# Para cada posición, qué líneas de victoria pasan por ella

LINEAS_MINI_TABLERO = [
    # Horizontales
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    # Verticales
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    # Diagonales
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]

LINEAS_META_TABLERO = [
    # Horizontales
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    # Verticales
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    # Diagonales
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]

# Importancia relativa de cada campo en el meta-tablero
IMPORTANCIA_CAMPO = {
    (0, 0): 3,  # Esquina superior-izquierda
    (0, 1): 2,  # Borde superior
    (0, 2): 3,  # Esquina superior-derecha
    (1, 0): 2,  # Borde izquierdo
    (1, 1): 4,  # Centro (más importante)
    (1, 2): 2,  # Borde derecho
    (2, 0): 3,  # Esquina inferior-izquierda
    (2, 1): 2,  # Borde inferior
    (2, 2): 3,  # Esquina inferior-derecha
}

# ===== LOGGING Y DEBUG =====

# Nivel de verbosidad: 0=silencio, 1=básico, 2=detallado, 3=muy detallado
VERBOSIDAD = 1

# Mostrar tabla de transposiciones usado
DEBUG_CACHE = False

# Mostrar profundidad alcanzada en iterative deepening
DEBUG_PROFUNDIDAD = False
