# Cambios de la versión anterior a la versión actual

Este documento compara el archivo conservado en
`version_anterior/gato_de_gatos_anterior.py` con el código actual de `src/` y
`codigo_final_spyder/gato_de_gatos.py`.

La intención no es borrar el trabajo anterior. Se conserva para mostrar qué ya
funcionaba y qué se fortaleció durante la revisión final.

## Resumen sencillo

La versión anterior ya tenía las ideas centrales: reglas del juego, Minimax,
poda alfa-beta, profundización iterativa, tiempo máximo y una heurística
sensible al destino.

La versión actual organiza esas ideas en partes más fáciles de probar, añade
validaciones dentro del motor, pregunta directamente quién comienza, corrige el
manejo de cotas de Minimax y agrega una suite de 200 pruebas.

## Comparación general

| Tema | Versión anterior | Versión actual |
|---|---|---|
| Organización | Un archivo con funciones | Módulos en `src/` y un archivo único equivalente para Spyder |
| Estado del juego | Listas separadas para tablero y macro-tablero | Clase `Tablero` que reúne estado, historial y reglas |
| Casilla vacía | Cadena vacía `""` | `None` |
| Movimiento interno | `(mini_tablero, casilla)` | `(fila_meta, col_meta, fila_mini, col_mini)` |
| Inicio de partida | Pregunta quién comienza | Pregunta si comienza el sistema o el jugador externo y asigna X a quien inicia |
| Heurística | Una función extensa con pesos para sistema y rival | Siete componentes separados, líneas abiertas y exclusión de campos cerrados |
| Memoria de búsqueda | Guarda resultados completos | Distingue valor exacto, cota inferior y cota superior |
| Tiempo | La recursión devuelve si terminó o agotó tiempo | Excepción interna `TiempoAgotado` y restauración con `try/finally` |
| Pruebas | Pruebas básicas dentro del archivo | 200 pruebas finales más 20 históricas con `pytest` |
| Documentación | README centrado en el archivo único | README principal e índice dentro de cada carpeta |

## 1. Representación del tablero

### Antes

Se mantenían dos listas independientes:

```python
tablero[mini][casilla]
macro_tablero[mini]
```

Era una representación compacta. Sin embargo, cada función tenía que recibir
ambas listas y era posible actualizarlas de manera desigual por accidente.

### Ahora

La clase `Tablero` reúne:

```python
tablero.mini_tableros
tablero.meta_tablero
tablero.historial
```

Las operaciones que cambian el estado son métodos de la misma clase. Por
ejemplo, `aplicar_movimiento()` verifica:

- que las cuatro coordenadas estén entre 0 y 2;
- que el jugador sea X u O;
- que el mini-tablero siga abierto;
- que la casilla esté vacía.

Esto hace que las reglas no dependan solamente de que la interfaz haya validado
la entrada.

## 2. Funciones equivalentes

Los nombres cambiaron porque el código actual separa responsabilidades:

| Versión anterior | Versión actual | Función |
|---|---|---|
| `crear_tablero()` y `crear_macro_tablero()` | `Tablero.__init__()` | Crear el estado inicial. |
| `hay_tres_en_linea()` y `obtener_estado_mini()` | `Tablero.obtener_ganador_mini()` | Detectar victoria o empate local. |
| `obtener_ganador_global()` | `Tablero.detectar_ganador_meta()` | Detectar la victoria global. |
| `obtener_movimientos_legales()` | `movimientos_validos()` | Generar jugadas permitidas. |
| `aplicar_movimiento()` | `Tablero.aplicar_movimiento()` | Colocar una ficha y actualizar el campo. |
| `deshacer_movimiento()` | `Tablero.deshacer_movimiento()` | Restaurar el estado anterior. |
| `evaluar_heuristica()` | `evaluar_posicion()` | Asignar una puntuación al estado. |
| `elegir_movimiento_sistema()` | `mejor_movimiento()` | Controlar tiempo y profundidad. |
| `texto_a_movimiento()` | `convertir_texto_a_movimiento()` | Convertir una entrada como `Gc`. |
| `ejecutar_partida()` | `_ejecutar_partida()` | Coordinar turnos y final de juego. |

## 3. Pregunta de quién comienza

La versión para torneo vuelve a preguntar directamente lo que establece el
enunciado:

```text
¿A quién le toca comenzar? [S]istema / jugador [E]xterno:
```

Quien comienza recibe X internamente. Así Minimax conserva la convención de que
X realiza el primer movimiento, pero la interfaz no sustituye el resultado de
la moneda por una elección de símbolo. El archivo ejecutable entra directamente
al modo de torneo para que esta sea la primera pregunta.

## 4. Movimientos legales

La nueva función `movimientos_validos()` devuelve una lista vacía si ya existe
una victoria global o un empate. Además, `Tablero.aplicar_movimiento()` rechaza
movimientos en campos cerrados incluso si otra parte del programa intenta
aplicarlos directamente.

La regla del destino se mantiene:

- si el destino está abierto, se juega únicamente ahí;
- si el destino ya terminó, se puede escoger cualquier campo abierto;
- en el primer turno no existe un destino obligatorio.

## 5. Heurística

La versión anterior tenía una heurística jerárquica útil. La versión actual
divide la evaluación en siete funciones para poder probar y explicar cada
parte:

1. líneas abiertas con uno o dos campos en el meta-tablero;
2. bono exclusivo por amenazas adicionales de una bifurcación;
3. amenazas inmediatas en campos jugables;
4. control de centro, esquinas y bordes;
5. líneas locales en desarrollo ponderadas por su relevancia global;
6. peligro del destino inmediato;
7. campo ganado, amenaza creada y peligro del destino futuro.

La puntuación actual usa una convención fija:

- positivo favorece a X;
- negativo favorece a O;
- cero es neutral o empate.

Separar los componentes permite usar `debug=True` para observar cuánto aporta
cada uno sin cambiar el resultado final.

También se corrigieron cuatro problemas estratégicos:

- los campos ganados o empatados ya no conservan amenazas que no pueden jugarse;
- una amenaza se cuenta en defensa y una bifurcación solo añade el bono por la
  segunda amenaza, en lugar de repetir la señal completa;
- poseer uno o dos campos en una línea global recibe valores distintos y no
  lineales;
- el destino futuro distingue jugadas que ganan el mismo campo pero envían al
  rival a lugares diferentes.

Los pesos actuales son `18, 6, 5, 6, 1, 8, 4`. Se seleccionaron después de
partidas cruzadas contra la versión anterior, alternando cuál heurística usaba
X y cuál usaba O. En la comparación final a profundidad 3, la evaluación nueva
obtuvo 15 victorias, 2 derrotas y 3 empates en 20 partidas con aperturas legales
variadas. Esta medición no demuestra juego perfecto, pero sí aporta evidencia
más sólida que ajustar pesos a partir de una sola partida.

## 6. Minimax y poda alfa-beta

La idea principal no cambió. X maximiza y O minimiza. La versión actual agrega
o refuerza los siguientes puntos:

- valores terminales ajustados por la distancia desde la raíz;
- orden de movimientos para revisar primero victorias y bloqueos;
- movimiento preferido de la profundidad anterior;
- profundización iterativa;
- presupuesto adaptativo por etapa de la partida;
- límite revisado dentro de cada nodo;
- restauración del tablero con `try/finally`;
- estadísticas de nodos, profundidad, valor y tiempo.

La raíz ya no sortea todos los valores que parecen empatados. Una rama podada
puede devolver una cota igual al mejor valor conocido aunque su valor exacto
sea peor. La versión actual conserva el primer movimiento óptimo y solo lo
reemplaza ante una mejora estricta.

### Tabla de transposiciones

Una poda alfa-beta puede producir una cota en lugar de un valor exacto. La
tabla actual guarda uno de estos tipos:

```text
EXACTO
COTA_INFERIOR
COTA_SUPERIOR
```

Al recuperar una entrada, Minimax ajusta `alfa` o `beta` según corresponda. De
esta forma no trata automáticamente una cota como si fuera el resultado exacto
de toda la rama.

## 7. Manejo del tiempo

La búsqueda usa `time.monotonic()`, un reloj adecuado para medir intervalos. Si
se termina el presupuesto, se lanza internamente `TiempoAgotado`.

Cada movimiento simulado se encuentra dentro de `try/finally`, por lo que se
deshace incluso cuando el tiempo termina a mitad de la recursión. La IA devuelve
el movimiento de la última profundidad que sí terminó por completo.

Los presupuestos son 15 segundos en apertura, 20 en medio juego y 27 en el
final. Nunca exceden el límite recibido y dejan margen frente al máximo de 30
segundos del torneo.

## 8. Pruebas

Las pruebas básicas anteriores se sustituyeron como validación principal por
una suite automatizada de exactamente 200 casos:

| Grupo | Casos |
|---|---:|
| Coordenadas | 18 |
| Victorias locales | 16 |
| Victorias globales | 16 |
| Destinos | 9 |
| Aplicar y deshacer | 9 |
| Empates y libertad de destino | 9 |
| Simetría de la heurística | 8 |
| Victorias inmediatas de Minimax | 8 |
| Integración, tiempo, memoria y estilo | 7 |
| Líneas abiertas, amenazas y campos cerrados | 43 |
| Relevancia global y progreso no lineal | 25 |
| Destino libre y destino futuro | 25 |
| Regresiones finales de Minimax, inicio, tiempo y paridad | 7 |
| **Total** | **200** |

Las 20 pruebas usadas durante el desarrollo también se conservaron como una
segunda suite.

```bash
python -m pytest tests/test_gato_de_gatos.py -q
python -m pytest tests/test_regresion_historica.py -q
```

## 9. Organización de archivos

Antes había código, resultados y documentos mezclados en la raíz. Ahora cada
tipo de archivo tiene una ubicación clara:

- `src/`: código modular;
- `codigo_final_spyder/`: archivo único actual;
- `tests/`: pruebas;
- `documentacion/`: explicaciones;
- `casos_de_estudio/`: partidas y regresiones;
- `resultados/`: salidas de torneos;
- `version_anterior/`: código preservado para comparación.

Los nombres de archivos usan minúsculas y guiones bajos. Esto evita espacios en
las rutas y hace que los comandos sean más fáciles de copiar.

## 10. Qué se conservó

No se eliminó la base del proyecto. Se conservaron:

- la notación `Campo+Posición`, como `Gc`;
- la regla del tablero obligatorio;
- Minimax y la poda alfa-beta;
- la profundización iterativa;
- el límite menor a 30 segundos;
- la evaluación del destino del rival;
- las partidas utilizadas para analizar el comportamiento de la IA.

La versión actual es una continuación más organizada, validada y explicada del
trabajo anterior.
