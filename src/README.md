# Código modular

Esta carpeta contiene la versión separada por responsabilidades. Es la mejor
versión para estudiar, probar y modificar el programa, porque cada archivo se
encarga de una parte concreta.

Para jugar desde la raíz del proyecto:

```bash
python -m src.main
```

## Archivos

| Archivo | Responsabilidad |
|---|---|
| `config.py` | Símbolos, tamaños, líneas ganadoras, pesos y límites de tiempo. |
| `tablero.py` | Clase `Tablero`, estado de las 81 casillas y reglas básicas. |
| `movimientos.py` | Genera las jugadas que respetan el destino obligatorio. |
| `evaluador.py` | Calcula la puntuación heurística de una posición. |
| `minimax.py` | Elige movimientos con Minimax, alfa-beta y optimizaciones. |
| `interfaz.py` | Lee coordenadas, valida texto y muestra el tablero. |
| `main.py` | Coordina turnos y los tres modos de juego. |
| `transcripciones.py` | Guarda partidas en Markdown dentro de `casos_de_estudio/`. |
| `torneo.py` | Ejecuta varias partidas IA vs IA y guarda sus resultados. |

## Relación entre módulos

El flujo principal es:

```text
main
├── interfaz
├── tablero
├── movimientos
├── minimax
│   ├── movimientos
│   ├── evaluador
│   └── tablero
└── transcripciones
```

`config.py` es usado por casi todos los módulos para evitar repetir números o
símbolos directamente en el código.

## Explicación sencilla del flujo

1. `main.py` crea un `Tablero` vacío.
2. `movimientos.py` indica dónde se puede jugar.
3. La persona escribe una coordenada o `minimax.py` calcula una jugada.
4. `tablero.py` coloca la ficha y actualiza el campo correspondiente.
5. La casilla elegida fija el campo del siguiente turno.
6. El proceso continúa hasta una victoria global o un empate.

## Detalles técnicos principales

### `Tablero`

La clase evita mantener varias estructuras desconectadas. El método
`aplicar_movimiento()` valida las coordenadas, el jugador, el estado del campo
y la casilla. `deshacer_movimiento()` usa el historial para regresar al estado
anterior durante la búsqueda.

### `movimientos_validos()`

Recibe el estado y el destino del turno. Si el destino está abierto, solo
genera casillas de ese campo. Si está cerrado o no existe destino, genera
movimientos de todos los campos disponibles.

### `evaluar_posicion()`

Suma siete componentes. Siempre usa la perspectiva de X: los valores positivos
favorecen a X y los negativos a O. Los estados terminales usan valores exactos;
la heurística solo estima estados que todavía continúan.

### `mejor_movimiento()`

Es la entrada pública de la IA. Ejecuta profundización iterativa, respeta el
tiempo disponible y devuelve una tupla de cuatro coordenadas. El tablero queda
igual después de buscar porque cada jugada simulada se deshace en un bloque
`try/finally`.

## Torneos

Ejemplo de diez partidas con un segundo máximo por movimiento:

```bash
python -m src.torneo 10 1.0 --seed 42
```

Los archivos producidos se guardan en `resultados/`.

## Relación con el archivo de Spyder

`codigo_final_spyder/gato_de_gatos.py` contiene estas mismas piezas reunidas en
un solo archivo. La suite final prueba ambas versiones para detectar si dejan
de comportarse igual.
