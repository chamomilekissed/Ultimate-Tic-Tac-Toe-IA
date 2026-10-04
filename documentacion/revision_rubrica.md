# Revisión final contra la rúbrica

Esta revisión compara el código actual con los criterios del documento de
evaluación y con las condiciones técnicas del proyecto. Su propósito es dejar
claro qué ya cubre el programa y qué debe cuidar el equipo al enviarlo.

## Cómo se asigna la calificación del código

La rúbrica parte de 10 puntos cuando no encuentra deficiencias. La calificación
baja según la cantidad de problemas detectados:

| Deficiencias detectadas | Calificación indicada por la rúbrica |
|---:|---:|
| 0 | 10 |
| 1 o 2 | 8 |
| 3 o 4 | 5 |
| Más de 4 | 2 |
| No se entrega o falla casi siempre | 0 |

El código queda preparado para evitar las deficiencias técnicas. La entrega a
tiempo y el nombre exacto del archivo dependen del equipo y no se pueden
garantizar desde el programa.

## Comprobación de cada posible deficiencia

| Criterio | Cómo se cubre en el proyecto | Evidencia |
|---|---|---|
| Entrega tardía | Es una responsabilidad del equipo. | Revisar la fecha y enviar antes del límite. |
| Medio o forma incorrectos | Existe un archivo único listo para Spyder. Para el correo se hace una copia con extensión `.txt` y el nombre solicitado. | `codigo_final_spyder/gato_de_gatos.py` y su README. |
| Código poco legible | Funciones y parámetros usan `snake_case`; constantes, `MAYÚSCULAS_CON_GUIONES_BAJOS`; clases, `PascalCase`. No se usan `break`, `continue` ni `pass`, y no hay importaciones con `*`. | Prueba estática dentro de `test_15_sin_break_continue_ni_pass()` y revisión con Ruff. |
| Documentación deficiente | Los README funcionan como manual, y las funciones no evidentes explican propósito, parámetros, restricciones y retorno. Los comentarios están en español. | README principal, README de cada carpeta y docstrings del código. |
| Funcionamiento incorrecto | Se prueban reglas, entrada, tablero, heurística, Minimax, tiempo, integración y equivalencia de las dos versiones. | 200 pruebas finales y 20 históricas aprobadas. |
| Programa incompleto | Incluye entrada manual del rival, decisión de la IA, pregunta inicial, notación del torneo, destino obligatorio, detección de fin y límite temporal. | Archivo de Spyder y pruebas de integración. |
| Falta de modularidad | Cada responsabilidad está separada en funciones y en módulos reutilizables. El archivo único conserva las mismas secciones para poder entregarse. | Carpeta `src/` y archivo final sincronizado. |

## Requisitos técnicos del proyecto

| Requisito | Estado | Implementación |
|---|:---:|---|
| Ejecutable en Python y Spyder | Cumple | El archivo final no necesita bibliotecas externas. |
| Sistema contra jugador externo | Cumple | `jugar_humano_vs_ia()` es el único modo que inicia el archivo final. |
| Movimiento externo capturado manualmente | Cumple | `obtener_movimiento_usuario()` recibe una coordenada por turno. |
| Notación campo `A-I` y posición `a-i` | Cumple | `convertir_texto_a_movimiento()` valida exactamente dos caracteres, por ejemplo `Gc`. |
| Preguntar quién comienza | Cumple | `solicitar_primer_jugador()` pregunta por sistema o jugador externo; quien comienza usa X. |
| Minimax y función heurística | Cumple | `mejor_movimiento()`, `minimax()` y `evaluar_posicion()`. |
| Decidir en menos de 30 segundos | Cumple por diseño | El presupuesto máximo interno es de 27 segundos y el corte usa `time.monotonic()`. |
| No pasar un turno | Cumple | Cada turno aplica uno de los movimientos legales disponibles. |
| Interfaz rápida y clara | Cumple | Antes de capturar, muestra el campo obligatorio y las jugadas disponibles, o los campos abiertos cuando la elección es libre. |
| Solución general y sistemática | Cumple | Las reglas se calculan desde el estado; no se codifican partidas específicas. |

La herramienta `src/torneo.py` sirve únicamente para calibración interna. No
agrega un modo de juego al archivo que se entrega.

## Ponderaciones de la función heurística

La fórmula verificada en las dos versiones es:

```text
H = 18M + 6B + 5D + 6C + 1L + 8I + 4F
```

| Componente | Símbolo | Peso |
|---|:---:|---:|
| Progreso en el meta-tablero | `M` | 18 |
| Bifurcaciones | `B` | 6 |
| Defensa y amenazas inmediatas | `D` | 5 |
| Posiciones estratégicas ganadas | `C` | 6 |
| Desarrollo local | `L` | 1 |
| Destino obligatorio inmediato | `I` | 8 |
| Consecuencia del destino futuro | `F` | 4 |

La prueba `test_29_valores_no_terminales_respetan_reserva_terminal()` comprueba
que los siete valores sean iguales en `src/config.py` y en el archivo de
Spyder. También verifica que una evaluación no terminal permanezca entre
`-10000` y `10000`, reservando esos extremos para resultados definitivos.

## Verificaciones ejecutadas

```bash
python -m ruff check src codigo_final_spyder/gato_de_gatos.py \
  casos_de_estudio/regresion_juego_01_campo_e.py \
  tests/test_gato_de_gatos.py tests/test_regresion_historica.py \
  --select E4,E7,E9,F,N

python -m pytest tests -q
```

Resultado de la revisión:

- Ruff: sin errores en las categorías revisadas;
- pruebas: **220 aprobadas**;
- suite principal: **200 casos exactos**;
- no se encontraron usos de `break`, `continue` o `pass`.

## Lista breve antes de enviar

1. Abrir y ejecutar `codigo_final_spyder/gato_de_gatos.py` en Spyder.
2. Hacer una copia y cambiarla al nombre y extensión `.txt` solicitados.
3. Abrir la copia para confirmar que contiene todo el código.
4. Adjuntar esa copia y la presentación de PowerPoint.
5. Enviar a tiempo y conservar el correo como comprobante.

