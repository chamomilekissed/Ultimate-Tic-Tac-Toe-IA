# Código final para Spyder

Esta carpeta contiene la versión actual del proyecto reunida en un solo
archivo:

```text
gato_de_gatos.py
```

Es el archivo indicado para abrir en Spyder o entregar cuando se solicita un
solo programa de Python.

## Cómo usarlo

1. Abrir `gato_de_gatos.py` en Spyder.
2. Presionar **Run**.
3. Indicar si comienza el sistema (`S`) o el jugador externo (`E`).
4. Escribir movimientos con dos letras, por ejemplo `Gc`.

Antes de cada movimiento externo, el programa indica el campo obligatorio y
las opciones disponibles. Si el campo de destino está cerrado, muestra que la
elección es libre y enumera los campos abiertos.

Quien comienza usa X internamente. Esta asignación la realiza el programa y
no se pide escoger un símbolo por separado.

También se puede ejecutar desde la raíz del repositorio:

```bash
python codigo_final_spyder/gato_de_gatos.py
```

## Archivo que se envía

El documento de entrega solicita código en un solo archivo con extensión
`.txt`. Primero se prueba `gato_de_gatos.py` en Spyder. Cuando ya funciona, se
hace una copia, se le asigna el nombre solicitado para el equipo y se cambia
la extensión de esa copia a `.txt`.

Se envían únicamente esa copia y la presentación de PowerPoint. Los módulos de
`src/`, las pruebas y las herramientas de calibración permanecen en GitHub como
evidencia y apoyo técnico.

## Qué contiene

Aunque es un solo archivo, mantiene secciones separadas para:

- configuración;
- clase `Tablero`;
- movimientos legales;
- evaluación heurística;
- Minimax y poda alfa-beta;
- interfaz;
- control de la partida.

Los nombres siguen la convención de Python: `snake_case` para funciones y
variables, `MAYÚSCULAS_CON_GUIONES_BAJOS` para constantes y `PascalCase` para
clases. Los comentarios están escritos en español y explican entradas, salidas
y decisiones que no son evidentes a simple vista.

## Diferencia frente a `src/`

No son dos proyectos distintos. `src/` divide el código para facilitar su
lectura y sus pruebas; este archivo reúne la misma lógica para que pueda
ejecutarse directamente en Spyder sin configurar un paquete.

Las pruebas comparan ambas versiones durante una partida legal para comprobar
que mantengan el mismo tablero y la misma puntuación heurística.
