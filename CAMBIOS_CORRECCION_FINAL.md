# Corrección final del proyecto

Esta rama corrige y sincroniza el archivo único de entrega con los módulos del
proyecto. `main` no se modificó directamente: los cambios se prepararon en la
rama `correccion-final-100-pruebas` para poder revisarlos antes de fusionar.

## Cambio visible para quien juega

X siempre realiza el primer movimiento. Por eso ya no existe una pregunta
separada de "quién comienza". En Humano vs IA, la pregunta ahora explica la
consecuencia de cada elección:

- X: comienza la persona.
- O: comienza la IA usando X.

También se valida el menú principal para que una opción distinta de 1, 2 o 3
no cierre el programa silenciosamente.

## Correcciones de reglas

- Se rechazan coordenadas fuera del tablero y símbolos diferentes de X/O.
- No se permite colocar una ficha dentro de un mini-tablero ya ganado o
  empatado.
- Después de una victoria global o un empate, la lista de movimientos legales
  queda vacía.
- En la heurística futura, mandar al rival a un campo cerrado ya no se evalúa
  como neutral: se reconoce que el rival obtiene libertad para elegir.

## Correcciones de Minimax

- La tabla de transposiciones distingue valores exactos, cotas inferiores y
  cotas superiores. Un valor obtenido mediante una poda alfa-beta ya no se
  reutiliza incorrectamente como si fuera exacto.
- El control de tiempo usa `time.monotonic()`, que no cambia si el reloj del
  sistema se ajusta durante una búsqueda.
- Las estadísticas se reinician incluso cuando no existe movimiento o solo
  queda uno.
- Se conserva el tablero mediante `try/finally` cuando expira el tiempo.

## Restricciones de estilo

Se eliminaron `break`, `continue` y `pass` de todos los archivos Python. La
suite incluye una prueba basada en el árbol sintáctico de Python para impedir
que vuelvan a introducirse por accidente.

## Pruebas

La suite nueva contiene exactamente 100 casos:

| Grupo | Casos |
|---|---:|
| Conversión de coordenadas | 18 |
| Victorias en mini-tableros | 16 |
| Victorias en el meta-tablero | 16 |
| Restricción de destino | 9 |
| Aplicar y deshacer movimientos | 9 |
| Empates locales y liberación del destino | 9 |
| Simetría de la heurística | 8 |
| Victorias inmediatas encontradas por Minimax | 8 |
| Validaciones, tiempo, cache, integración y estilo | 7 |
| **Total** | **100** |

Comandos de verificación:

```bash
python3 -m pytest tests/test_gato_de_gatos.py -q
python3 -m pytest tests_stub.py -q
python3 -m compileall -q .
```

Resultados obtenidos en esta rama:

- `100 passed` en la suite final.
- `20 passed` en la suite histórica.
- Todos los archivos Python compilan correctamente.

Además, `.github/workflows/pruebas.yml` ejecuta automáticamente la compilación
y los 100 casos cada vez que se actualiza la rama o se abre un Pull Request.

## Archivo para Spyder

El archivo que se debe abrir en Spyder o convertir a `.txt` para la entrega es:

`CODIGO_FINAL_ENTREGA/gato_de_gatos.py`

Los módulos (`tablero.py`, `movimientos.py`, `evaluador.py`, `minimax.py`,
`interfaz.py` y `main.py`) se conservaron porque permiten probar y explicar por
separado cada parte del proyecto.
