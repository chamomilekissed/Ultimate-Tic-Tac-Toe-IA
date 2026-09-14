"""
MÓDULO: tests.py
RESPONSABLE: Persona C
DESCRIPCIÓN: Suite de pruebas unitarias

Usar: python -m pytest tests.py -v

IMPORTANTE: Estos tests deben ejecutarse después de implementar cada módulo.
Sirven como validación de que todo funciona correctamente.

Para ejecutar solo tests de un módulo:
    pytest tests.py::test_tablero -v
    pytest tests.py::test_minimax -v
"""

import pytest
from config import *
import tablero as tb

try:
    import movimientos as mov
except ImportError:
    mov = None

try:
    import minimax as mm
except ImportError:
    mm = None

try:
    import evaluador as ev
except ImportError:
    ev = None


# ===== TESTS DEL MÓDULO TABLERO =====

class TestTablero:
    """Tests para tablero.py"""
    
    def test_crear_tablero_vacio(self):
        """Verifica que un tablero nuevo esté vacío."""
        tablero = tb.Tablero()
        for fila_meta in range(TAMAÑO_META):
            for col_meta in range(TAMAÑO_META):
                assert tablero.meta_tablero[fila_meta][col_meta] is None
                for fila_mini in range(TAMAÑO_MINI):
                    for col_mini in range(TAMAÑO_MINI):
                        assert tablero.obtener_casilla(fila_meta, col_meta, fila_mini, col_mini) is None

    def test_aplicar_movimiento_valido(self):
        """Verifica que se puede aplicar un movimiento válido."""
        tablero = tb.Tablero()
        resultado = tablero.aplicar_movimiento(0, 0, 0, 0, 'X')
        assert resultado is True
        assert tablero.obtener_casilla(0, 0, 0, 0) == 'X'

    def test_aplicar_movimiento_casilla_ocupada(self):
        """Verifica que no se puede jugar en casilla ocupada."""
        tablero = tb.Tablero()
        tablero.aplicar_movimiento(0, 0, 0, 0, 'X')
        resultado = tablero.aplicar_movimiento(0, 0, 0, 0, 'O')
        assert resultado is False
        assert tablero.obtener_casilla(0, 0, 0, 0) == 'X'

    def test_detectar_ganador_horizontal(self):
        """Verifica detección de 3-en-línea horizontal."""
        tablero = tb.Tablero()
        tablero.aplicar_movimiento(0, 0, 0, 0, 'X')
        tablero.aplicar_movimiento(0, 0, 0, 1, 'X')
        tablero.aplicar_movimiento(0, 0, 0, 2, 'X')
        assert tablero.obtener_ganador_mini(0, 0) == 'X'

    def test_detectar_ganador_vertical(self):
        """Verifica detección de 3-en-línea vertical."""
        tablero = tb.Tablero()
        tablero.aplicar_movimiento(0, 0, 0, 0, 'O')
        tablero.aplicar_movimiento(0, 0, 1, 0, 'O')
        tablero.aplicar_movimiento(0, 0, 2, 0, 'O')
        assert tablero.obtener_ganador_mini(0, 0) == 'O'

    def test_detectar_ganador_diagonal(self):
        """Verifica detección de 3-en-línea diagonal."""
        tablero = tb.Tablero()
        tablero.aplicar_movimiento(0, 0, 0, 0, 'X')
        tablero.aplicar_movimiento(0, 0, 1, 1, 'X')
        tablero.aplicar_movimiento(0, 0, 2, 2, 'X')
        assert tablero.obtener_ganador_mini(0, 0) == 'X'

    def test_detectar_ganador_meta_tablero(self):
        """Verifica detección de ganador en meta-tablero."""
        # Esta prueba es más compleja: necesita ganar 3 mini-tableros en línea
        tablero = tb.Tablero()
        # Simular ganar campos A, B, C (primera fila del meta-tablero) para X
        for col_meta in range(3):
            tablero.aplicar_movimiento(0, col_meta, 0, 0, 'X')
            tablero.aplicar_movimiento(0, col_meta, 0, 1, 'X')
            tablero.aplicar_movimiento(0, col_meta, 0, 2, 'X')
        assert tablero.detectar_ganador_meta() == 'X'

    def test_deshacer_movimiento(self):
        """Verifica que deshacer funciona."""
        tablero = tb.Tablero()
        tablero.aplicar_movimiento(0, 0, 0, 0, 'X')
        assert tablero.obtener_casilla(0, 0, 0, 0) == 'X'
        resultado = tablero.deshacer_movimiento()
        assert resultado is True
        assert tablero.obtener_casilla(0, 0, 0, 0) is None

    def test_copiar_tablero(self):
        """Verifica que copiar crea una copia independiente."""
        tablero1 = tb.Tablero()
        tablero1.aplicar_movimiento(0, 0, 0, 0, 'X')
        tablero2 = tablero1.copiar()
        assert tablero2.obtener_casilla(0, 0, 0, 0) == 'X'
        tablero2.aplicar_movimiento(0, 0, 0, 1, 'O')
        assert tablero1.obtener_casilla(0, 0, 0, 1) is None
        assert tablero2.obtener_casilla(0, 0, 0, 1) == 'O'


# ===== TESTS DEL MÓDULO MOVIMIENTOS =====

class TestMovimientos:
    """Tests para movimientos.py"""

    pytestmark = pytest.mark.skipif(mov is None, reason="movimientos.py todavía no está implementado")

    def test_movimientos_primer_turno(self):
        """En el primer turno, todos los 81 movimientos son válidos."""
        tablero = tb.Tablero()
        movs = mov.movimientos_validos(tablero, None)
        assert len(movs) == 81

    def test_movimientos_restriccion_tablero(self):
        """Si hay restricción, solo se pueden jugar movimientos en ese tablero."""
        tablero = tb.Tablero()
        tablero_destino = (0, 0)  # Mini-tablero A
        movs = mov.movimientos_validos(tablero, tablero_destino)
        assert all(fila_meta == 0 and col_meta == 0 for fila_meta, col_meta, _, _ in movs)
        assert len(movs) <= 9

    def test_movimientos_tablero_lleno_permite_libre(self):
        """Si destino está lleno, permite jugar en cualquier otro."""
        tablero = tb.Tablero()
        # Llenar mini-tablero (0, 0) sin que nadie gane (empate local)
        grilla_empate = [
            (0, 0, 'X'), (0, 1, 'O'), (0, 2, 'X'),
            (1, 0, 'X'), (1, 1, 'O'), (1, 2, 'O'),
            (2, 0, 'O'), (2, 1, 'X'), (2, 2, 'X'),
        ]
        for fila_mini, col_mini, jugador in grilla_empate:
            tablero.aplicar_movimiento(0, 0, fila_mini, col_mini, jugador)
        assert tablero.obtener_ganador_mini(0, 0) == 'EMPATE'

        tablero_destino = (0, 0)
        movs = mov.movimientos_validos(tablero, tablero_destino)
        assert len(movs) > 9
        assert all(not (fila_meta == 0 and col_meta == 0) for fila_meta, col_meta, _, _ in movs)


# ===== TESTS DEL MÓDULO EVALUADOR =====

class TestEvaluador:
    """Tests para evaluador.py"""

    pytestmark = pytest.mark.skipif(ev is None, reason="evaluador.py todavía no está implementado")

    def test_evaluar_tablero_vacio(self):
        """Tablero vacío debería tener puntuación cercana a 0."""
        tablero = tb.Tablero()
        puntuacion = ev.evaluar_posicion(tablero, True)
        assert abs(puntuacion) < 100

    def test_evaluar_ganador_inmediato(self):
        """Posición ganadora debe retornar puntuación muy alta."""
        tablero = tb.Tablero()
        # Crear posición donde X ganó: gana los campos A, B, C (primera fila)
        for col_meta in range(3):
            tablero.aplicar_movimiento(0, col_meta, 0, 0, 'X')
            tablero.aplicar_movimiento(0, col_meta, 0, 1, 'X')
            tablero.aplicar_movimiento(0, col_meta, 0, 2, 'X')
        puntuacion = ev.evaluar_posicion(tablero, True)
        assert puntuacion > 5000

    def test_evaluar_posicion_perdedora(self):
        """Posición perdedora debe retornar puntuación muy baja."""
        tablero = tb.Tablero()
        # Crear posición donde O ganó: gana los campos A, B, C (primera fila)
        for col_meta in range(3):
            tablero.aplicar_movimiento(0, col_meta, 0, 0, 'O')
            tablero.aplicar_movimiento(0, col_meta, 0, 1, 'O')
            tablero.aplicar_movimiento(0, col_meta, 0, 2, 'O')
        puntuacion = ev.evaluar_posicion(tablero, True)
        assert puntuacion < -5000


# ===== TESTS DEL MÓDULO MINIMAX =====

def _llenar_mini_empate(tablero, fila_meta, col_meta, invertir=False):
    """Llena un mini-tablero con un patrón sin ganador (empate 5-4 o 4-5)."""
    patron = [
        (0, 0, 'X'), (0, 1, 'O'), (0, 2, 'X'),
        (1, 0, 'X'), (1, 1, 'O'), (1, 2, 'O'),
        (2, 0, 'O'), (2, 1, 'X'), (2, 2, 'X'),
    ]
    for fila_mini, col_mini, jugador in patron:
        if invertir:
            jugador = 'O' if jugador == 'X' else 'X'
        tablero.aplicar_movimiento(fila_meta, col_meta, fila_mini, col_mini, jugador)


class TestMinimax:
    """Tests para minimax.py"""

    pytestmark = pytest.mark.skipif(mm is None, reason="minimax.py todavía no está implementado")

    def test_minimax_encuentra_ganadora(self):
        """Minimax debería encontrar y ejecutar ganadora inmediata."""
        tablero = tb.Tablero()
        # X ya ganó los campos A y B; en C tiene 2-en-línea a punto de
        # completar la fila A-B-C y ganar TODO el juego. El resto de
        # campos quedan empatados (decididos) para acotar la búsqueda a
        # las únicas casillas relevantes: las vacías de C.
        for col_mini in range(3):
            tablero.aplicar_movimiento(0, 0, 0, col_mini, 'X')
            tablero.aplicar_movimiento(0, 1, 0, col_mini, 'X')
        tablero.aplicar_movimiento(0, 2, 0, 0, 'X')
        tablero.aplicar_movimiento(0, 2, 0, 1, 'X')
        tablero.aplicar_movimiento(0, 2, 1, 0, 'O')
        tablero.aplicar_movimiento(0, 2, 2, 1, 'O')
        for fila_meta, col_meta in [(1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]:
            _llenar_mini_empate(tablero, fila_meta, col_meta, invertir=True)

        movimiento = mm.mejor_movimiento(tablero, None, tiempo_limite=5)
        assert movimiento == (0, 2, 0, 2)

        tablero.aplicar_movimiento(*movimiento, 'X')
        assert tablero.detectar_ganador_meta() == 'X'

    def test_minimax_bloquea_amenaza(self):
        """Minimax debería bloquear amenaza de oponente."""
        tablero = tb.Tablero()
        # O ya ganó los campos D y E; en F tiene 2-en-línea a punto de
        # completar la fila D-E-F y ganar TODO el juego. X debe bloquear
        # la única casilla que evita esa victoria. El resto de campos
        # quedan empatados (decididos) para acotar la búsqueda.
        tablero.aplicar_movimiento(1, 0, 0, 0, 'O')
        tablero.aplicar_movimiento(1, 0, 0, 1, 'O')
        tablero.aplicar_movimiento(1, 0, 0, 2, 'O')
        tablero.aplicar_movimiento(1, 1, 0, 0, 'O')
        tablero.aplicar_movimiento(1, 1, 0, 1, 'O')
        tablero.aplicar_movimiento(1, 1, 0, 2, 'O')
        tablero.aplicar_movimiento(1, 2, 0, 0, 'O')
        tablero.aplicar_movimiento(1, 2, 0, 1, 'O')
        tablero.aplicar_movimiento(1, 2, 1, 0, 'X')
        tablero.aplicar_movimiento(1, 2, 2, 1, 'X')
        for fila_meta, col_meta in [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)]:
            _llenar_mini_empate(tablero, fila_meta, col_meta, invertir=False)

        movimiento = mm.mejor_movimiento(tablero, (1, 1), tiempo_limite=5)
        assert movimiento == (1, 2, 0, 2)

    def test_minimax_respeta_tiempo_limite(self):
        """Minimax no debe exceder tiempo límite."""
        import time
        tablero = tb.Tablero()
        tiempo_inicio = time.time()
        movimiento = mm.mejor_movimiento(tablero, None, tiempo_limite=1)
        tiempo_transcurrido = time.time() - tiempo_inicio
        assert tiempo_transcurrido <= 1.5


# ===== TESTS DE INTEGRACIÓN =====

class TestIntegracion:
    """Tests que verifican que todo funciona junto."""

    pytestmark = pytest.mark.skipif(
        mov is None or mm is None,
        reason="movimientos.py y/o minimax.py todavía no están implementados",
    )

    def test_juego_ai_vs_ai(self):
        """Simula un juego IA vs IA sin crashes."""
        tablero = tb.Tablero()
        es_turno_x = True
        tablero_destino = None
        pasos = 0
        max_pasos = 200  # Máximo para evitar loops infinitos
        
        while pasos < max_pasos:
            # Obtener movimiento
            movimiento = mm.mejor_movimiento(
                tablero, 
                tablero_destino, 
                tiempo_limite=2
            )
            
            if movimiento is None:
                # No hay movimientos válidos
                break
            
            fila_meta, col_meta, fila_mini, col_mini = movimiento
            jugador = 'X' if es_turno_x else 'O'
            
            # Aplicar movimiento
            tablero.aplicar_movimiento(fila_meta, col_meta, fila_mini, col_mini, jugador)
            
            # Verificar fin de juego
            ganador = tablero.detectar_ganador_meta()
            if ganador:
                assert ganador in (JUGADOR_X, JUGADOR_O)
                break
            
            if tablero.verificar_empate():
                break
            
            # Siguiente turno
            es_turno_x = not es_turno_x
            tablero_destino = (fila_mini, col_mini)
            pasos += 1
        
        # TODO: Verificar que el juego terminó sin crashes
        assert pasos > 0  # Se jugó al menos 1 movimiento
    
    def test_movimientos_siempre_validos(self):
        """En cualquier momento, hay al menos un movimiento válido."""
        tablero = tb.Tablero()
        tablero_destino = None
        pasos = 0
        
        while pasos < 100:
            movimientos = mov.movimientos_validos(tablero, tablero_destino)
            
            # TODO: Verificar que hay al menos un movimiento
            assert len(movimientos) > 0, "No hay movimientos disponibles"
            
            if len(movimientos) == 0:
                break
            
            # Jugar movimiento aleatorio
            import random
            movimiento = random.choice(movimientos)
            fila_meta, col_meta, fila_mini, col_mini = movimiento
            jugador = 'X' if pasos % 2 == 0 else 'O'
            
            tablero.aplicar_movimiento(fila_meta, col_meta, fila_mini, col_mini, jugador)

            # El invariante ("siempre hay movimiento válido") solo aplica
            # mientras el juego sigue: una vez que gana alguien o empata,
            # movimientos_validos() retorna [] correctamente.
            if tablero.detectar_ganador_meta() is not None or tablero.verificar_empate():
                break

            # Siguiente restricción
            tablero_destino = (fila_mini, col_mini)
            pasos += 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
