# Pruebas del proyecto

Esta carpeta contiene dos suites.

| Archivo | Casos | Propósito |
|---|---:|---|
| `test_gato_de_gatos.py` | 200 | Suite final: reglas, IA, heurística, integración y archivo de Spyder. |
| `test_regresion_historica.py` | 20 | Pruebas creadas durante el desarrollo y conservadas para compatibilidad. |

## Ejecutar las pruebas

Desde la raíz del proyecto:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests/test_gato_de_gatos.py -q
python -m pytest tests/test_regresion_historica.py -q
```

Para ejecutar las dos suites juntas:

```bash
python -m pytest tests -q
```

## Distribución de los 200 casos finales

| Grupo | Casos |
|---|---:|
| Conversión de coordenadas | 18 |
| Victorias en mini-tableros | 16 |
| Victorias en el meta-tablero | 16 |
| Destinos obligatorios | 9 |
| Aplicar y deshacer movimientos | 9 |
| Empates locales y destino libre | 9 |
| Simetría de la heurística | 8 |
| Victorias inmediatas de Minimax | 8 |
| Validaciones, tiempo, caché, integración y estilo | 7 |
| Líneas abiertas con una marca | 18 |
| Amenazas en todas las líneas y para ambos jugadores | 16 |
| Exclusión de amenazas en campos cerrados | 9 |
| Relevancia global del control local | 9 |
| Progreso no lineal en el meta-tablero | 16 |
| Libertad al recibir un destino cerrado | 9 |
| Victorias locales consideradas por el destino futuro | 16 |
| Regresiones finales: raíz, inicio, tiempo, paridad y rango | 7 |
| **Total** | **200** |

## Qué errores buscan

Las pruebas comprueban, entre otras cosas, que:

- no se pueda jugar fuera del tablero, sobre una casilla ocupada o en un campo
  cerrado;
- una casilla envíe al siguiente jugador al campo correcto;
- Minimax encuentre una victoria inmediata;
- Minimax no confunda una cota alfa-beta con un empate exacto;
- el límite de tiempo no deje movimientos simulados en el tablero;
- las amenazas de campos cerrados no alteren la evaluación;
- la primera pregunta distinga entre sistema y jugador externo;
- la interfaz muestre el campo obligatorio y las opciones disponibles;
- los pesos respeten la estructura de líneas abiertas del meta-tablero;
- las siete ponderaciones sean exactamente `18, 6, 5, 6, 1, 8, 4` en la
  versión modular y en el archivo de Spyder;
- la tabla de transposiciones respete valores exactos y cotas;
- la versión modular y la de Spyder produzcan el mismo estado;
- ningún archivo Python use `break`, `continue` o `pass`;
- las funciones y sus parámetros respeten `snake_case`;
- las clases y funciones del código actual tengan documentación;
- no existan importaciones globales con `*`.

En la revisión final se ejecutaron las dos suites juntas: **220 casos
aprobados**.

GitHub Actions ejecuta automáticamente la compilación y los 200 casos finales
cuando se abre o actualiza un pull request.
