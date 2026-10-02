# Pruebas del proyecto

Esta carpeta contiene dos suites.

| Archivo | Casos | Propósito |
|---|---:|---|
| `test_gato_de_gatos.py` | 100 | Suite final: reglas, IA, integración y archivo de Spyder. |
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

## Distribución de los 100 casos finales

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
| **Total** | **100** |

## Qué errores buscan

Las pruebas comprueban, entre otras cosas, que:

- no se pueda jugar fuera del tablero, sobre una casilla ocupada o en un campo
  cerrado;
- una casilla envíe al siguiente jugador al campo correcto;
- Minimax encuentre una victoria inmediata;
- el límite de tiempo no deje movimientos simulados en el tablero;
- la tabla de transposiciones respete valores exactos y cotas;
- la versión modular y la de Spyder produzcan el mismo estado;
- ningún archivo Python use `break`, `continue` o `pass`.

GitHub Actions ejecuta automáticamente la compilación y los 100 casos finales
cuando se abre o actualiza un pull request.
