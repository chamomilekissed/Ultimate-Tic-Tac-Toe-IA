# Ultimate-Tic-Tac-Toe-IA

# Gato de Gatos con Minimax

## Descripción del proyecto

En este proyecto desarrollamos un programa capaz de jugar Gato de Gatos contra una persona.

El sistema utiliza el algoritmo minimax para analizar las posibles jugadas. Como no es posible revisar todas las partidas completas en menos de 30 segundos, también usamos una función heurística. Esta función le permite al programa estimar qué tan conveniente es una posición sin tener que llegar hasta el final de la partida.

El programa fue desarrollado en Python y se puede ejecutar directamente en Spyder. No necesita instalar ninguna biblioteca adicional.

---

## ¿Cómo se juega?

El tablero está formado por nueve mini-tableros de gato. Cada mini-tablero también tiene nueve casillas.

Los mini-tableros se identifican así:

```text
A B C
D E F
G H I
```

Las casillas de cada mini-tablero se identifican así:

```text
a b c
d e f
g h i
```

Para escribir un movimiento se usan dos letras:

- La primera indica el mini-tablero.
- La segunda indica la casilla dentro de ese mini-tablero.

Por ejemplo:

```text
Gc
```

significa que se eligió la casilla superior derecha del mini-tablero inferior izquierdo.

La casilla elegida también determina el mini-tablero donde deberá jugar el oponente. Si ese mini-tablero ya fue ganado o terminó empatado, el siguiente jugador puede elegir cualquier mini-tablero que siga abierto.

---

## ¿Cómo representamos el juego?

Representamos el tablero mediante una lista que contiene nueve listas pequeñas.

```python
tablero[mini_tablero][casilla]
```

Por ejemplo:

```python
tablero[6][2]
```

representa el movimiento `Gc`.

También usamos un macro-tablero para guardar el resultado de cada mini-tablero:

- `""` significa que todavía está abierto.
- `"X"` significa que lo ganó X.
- `"O"` significa que lo ganó O.
- `"="` significa que terminó empatado.

Finalmente, usamos la variable `destino`:

- Si contiene un número entre 0 y 8, indica el mini-tablero obligatorio.
- Si contiene `None`, el jugador puede elegir cualquier mini-tablero abierto.

---

## ¿Cómo toma decisiones el programa?

El programa utiliza minimax.

La idea es la siguiente:

1. El sistema prueba una jugada posible.
2. Después supone que el rival responderá con su mejor jugada.
3. Luego vuelve a buscar la mejor respuesta del sistema.
4. Este proceso se repite hasta alcanzar la profundidad permitida.
5. Los valores obtenidos se regresan hacia arriba para seleccionar el mejor movimiento.

El sistema es el jugador maximizador porque busca el puntaje más grande. El jugador externo es el minimizador porque intenta reducir el puntaje del sistema.

Una victoria del sistema recibe un valor muy grande y una victoria del rival recibe un valor muy negativo.

También tomamos en cuenta la profundidad:

```python
VALOR_VICTORIA - nivel
```

Esto hace que el sistema prefiera ganar lo más rápido posible.

En una derrota usamos:

```python
-VALOR_VICTORIA + nivel
```

De esta manera, si no puede evitar perder, intenta retrasar la derrota.

---

## Poda alfa-beta

La poda alfa-beta evita analizar ramas que ya no pueden cambiar la decisión final.

- `alfa` representa el mejor resultado encontrado para el sistema.
- `beta` representa el mejor resultado encontrado para el rival.
- Cuando `alfa` es mayor o igual que `beta`, ya no es necesario revisar las demás jugadas de esa rama.

La poda no cambia el resultado de minimax. Solamente permite obtenerlo más rápido.


---

## Profundización iterativa

En lugar de comenzar directamente con una búsqueda muy profunda, hacemos varias búsquedas:

```text
Profundidad 1
Profundidad 2
Profundidad 3
...
```

Cada búsqueda terminada mejora la decisión anterior.

Si se acaba el tiempo durante una profundidad, conservamos el mejor movimiento de la última búsqueda que sí terminó. Por eso el programa siempre tiene una jugada legal disponible.

El tiempo utilizado depende de la etapa de la partida:

- Apertura: máximo 4 segundos.
- Parte media: máximo 10 segundos.
- Parte final: máximo 25 segundos.

Todos los tiempos están por debajo del límite de 30 segundos.

---

## Funciones heurísticas que consideramos

### Opción 1: cantidad y posición de mini-tableros ganados

Esta opción da puntos por cada mini-tablero ganado. También puede dar más valor al centro y a las esquinas.

Ventajas:

- Es rápida.
- Es sencilla de programar.
- Es fácil de explicar.

Desventajas:

- No detecta amenazas.
- No analiza líneas incompletas.
- No considera dónde jugará el rival.

### Opción 2: líneas posibles

Esta opción cuenta las filas, columnas y diagonales que todavía puede completar cada jugador.

Una línea con dos marcas recibe más puntos que una línea con una sola marca.

Ventajas:

- Detecta amenazas y oportunidades.
- Ayuda a atacar y defender.
- Considera tanto los mini-tableros como el mega-tablero.

Desventajas:

- Puede valorar una amenaza que todavía no se puede jugar.
- No considera completamente la regla del tablero obligatorio.

### Opción 3: heurística jerárquica y sensible al destino

Combina:

1. Líneas posibles del mega-tablero.
2. Mini-tableros ganados.
3. Posición de los mini-tableros.
4. Líneas posibles dentro de cada mini-tablero.
5. Control de centros y esquinas.
6. Amenazas inmediatas.
7. Mini-tablero donde deberá jugar el siguiente jugador.
8. Libertad para jugar en cualquier tablero.

Ventajas:

- Considera las partes más importantes del juego.
- Puede atacar y defender.
- Analiza a qué tablero enviará al rival.
- Produce decisiones más completas.

Desventajas:

- Es más lenta que las otras opciones.
- Los pesos tuvieron que elegirse manualmente.
- No garantiza una partida perfecta si se alcanza el límite de profundidad.

---

## Organización del código

| Función | Propósito |
|---|---|
| `crear_tablero` | Crea los nueve mini-tableros. |
| `crear_macro_tablero` | Guarda el estado de cada mini-tablero. |
| `hay_tres_en_linea` | Comprueba filas, columnas y diagonales. |
| `obtener_estado_mini` | Decide si un mini-tablero continúa, fue ganado o empató. |
| `obtener_ganador_global` | Comprueba si alguien ganó el mega-tablero. |
| `obtener_movimientos_legales` | Genera únicamente las jugadas permitidas. |
| `aplicar_movimiento` | Coloca una marca y calcula el siguiente destino. |
| `deshacer_movimiento` | Retira una jugada después de analizarla. |
| `evaluar_heuristica` | Calcula qué tan favorable es una posición. |
| `ordenar_movimientos` | Revisa primero victorias, bloqueos y buenas posiciones. |
| `minimax` | Busca la mejor jugada mediante maximización y minimización. |
| `elegir_movimiento_sistema` | Controla la profundidad y el tiempo. |
| `texto_a_movimiento` | Convierte, por ejemplo, `Gc` en `(6, 2)`. |
| `mostrar_tablero` | Imprime el tablero completo. |
| `ejecutar_partida` | Controla los turnos y termina la partida. |


## Pruebas básicas

Desde una terminal podemos ejecutar:

```bash
python3 gato_de_gatos.py --pruebas
```

Estas pruebas comprueban:

- Conversión de coordenadas.
- Detección de tres en línea.
- Actualización del tablero.
- Cálculo del siguiente tablero.
- Empate de un mini-tablero.
- Victoria en el mega-tablero.

Si todo está correcto aparecerá:

```text
Pruebas básicas superadas correctamente.
```


## Integrantes



