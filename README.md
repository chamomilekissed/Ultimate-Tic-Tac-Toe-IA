# Gato de Gatos — Ultimate Tic-Tac-Toe con IA

Este proyecto implementa **Gato de Gatos** en Python. Se puede jugar entre dos
personas, observar una partida IA contra IA o jugar contra una IA que usa
**Minimax con poda alfa-beta**.

La documentación está escrita para que primero se entienda la idea general y,
después, se puedan consultar los detalles técnicos necesarios para explicar el
proyecto.

## Qué archivo debo usar

| Necesidad | Archivo o comando |
|---|---|
| Abrir el proyecto en Spyder o entregar un solo archivo | `codigo_final_spyder/gato_de_gatos.py` |
| Estudiar o modificar el programa por módulos | `python -m src.main` |
| Ejecutar las 100 pruebas finales | `python -m pytest tests/test_gato_de_gatos.py -q` |
| Consultar la versión anterior | `version_anterior/gato_de_gatos_anterior.py` |

> La versión oficial actual es `codigo_final_spyder/gato_de_gatos.py`. La
> carpeta `version_anterior/` se conserva únicamente para comparar el proceso
> de mejora; no es la versión que se debe entregar.

## Cómo ejecutar el juego

Se necesita Python 3.10 o posterior. El juego no requiere bibliotecas externas.

### En Spyder

1. Abrir `codigo_final_spyder/gato_de_gatos.py`.
2. Presionar **Run** o **Ejecutar**.
3. Elegir uno de los tres modos de juego.

### Desde una terminal

Versión organizada por módulos:

```bash
python -m src.main
```

Versión de un solo archivo:

```bash
python codigo_final_spyder/gato_de_gatos.py
```

El menú ofrece:

1. Humano contra humano.
2. IA contra IA.
3. Humano contra IA.

## Regla importante sobre X y O

**X siempre hace el primer movimiento.** La pregunta del programa no decide
quién comienza por separado; pregunta qué símbolo quiere usar la persona:

- Si elige **X**, comienza la persona.
- Si elige **O**, la IA usa X y comienza la partida.

Así se respeta la regla normal del juego y se evita pedir dos decisiones que
podrían contradecirse.

## Cómo se escribe un movimiento

El tablero grande contiene nueve mini-tableros:

```text
A | B | C
D | E | F
G | H | I
```

Cada mini-tablero también tiene nueve posiciones:

```text
a | b | c
d | e | f
g | h | i
```

Un movimiento usa dos letras: primero el campo y después la posición. Por
ejemplo, `Gc` significa **campo G, posición c**.

La posición elegida determina el campo donde deberá jugar el oponente. Si ese
campo ya está ganado o empatado, el oponente puede escoger cualquier campo que
siga abierto.

## Cómo está organizado el proyecto

```text
Ultimate-Tic-Tac-Toe-IA/
├── README.md                         Guía principal
├── src/                              Código modular actual
│   ├── config.py                     Constantes y pesos
│   ├── tablero.py                    Estado y reglas del tablero
│   ├── movimientos.py                Movimientos permitidos
│   ├── evaluador.py                  Función heurística
│   ├── minimax.py                    Búsqueda de la IA
│   ├── interfaz.py                   Entrada y salida en terminal
│   ├── main.py                       Modos de juego y turnos
│   ├── transcripciones.py            Registro de partidas
│   └── torneo.py                     Partidas automáticas IA vs IA
├── codigo_final_spyder/              Versión actual en un solo archivo
├── tests/                            Pruebas finales e históricas
├── documentacion/                    Explicaciones técnicas y cambios
├── casos_de_estudio/                 Partidas analizadas y regresiones
├── resultados/                       Resultados generados por torneos
├── version_anterior/                 Código anterior conservado como referencia
└── .github/workflows/                Pruebas automáticas de GitHub
```

Cada carpeta tiene su propio `README.md` para explicar qué contiene y cómo se
usa.

## Cómo funciona el código

Una partida sigue este ciclo:

1. `main.py` identifica a quién le toca jugar.
2. `movimientos.py` obtiene únicamente las jugadas legales.
3. Si juega una persona, `interfaz.py` convierte un texto como `Gc` en
   coordenadas internas.
4. Si juega la IA, `minimax.py` analiza las respuestas posibles y pide a
   `evaluador.py` una puntuación cuando no puede buscar más profundo.
5. `tablero.py` aplica el movimiento y actualiza el resultado del
   mini-tablero correspondiente.
6. La posición jugada se convierte en el destino obligatorio del siguiente
   turno.
7. El ciclo termina cuando X u O gana tres campos en línea o cuando ya no hay
   movimientos.

### Representación interna

La clase `Tablero` guarda tres elementos principales:

- `mini_tableros`: los nueve tableros pequeños de 3 × 3.
- `meta_tablero`: el resultado de cada campo: `X`, `O`, `EMPATE` o `None`.
- `historial`: movimientos anteriores que permiten aplicar y deshacer jugadas
  durante Minimax sin copiar todo el tablero en cada nodo.

En el código modular, un movimiento se representa con cuatro números:

```python
(fila_meta, columna_meta, fila_mini, columna_mini)
```

Por ejemplo, `Gc` se convierte en `(2, 0, 0, 2)`.

## Cómo decide la IA

### Minimax

Minimax supone que ambos jugadores escogerán su mejor jugada:

- X es el jugador **maximizador** y busca el valor más alto.
- O es el jugador **minimizador** y busca el valor más bajo.

La IA simula una jugada, después la mejor respuesta del rival y continúa de
forma recursiva. Una victoria de X se acerca a `+10000`; una victoria de O se
acerca a `-10000`. También se toma en cuenta la profundidad para preferir una
victoria rápida y retrasar una derrota inevitable.

### Poda alfa-beta

`alfa` guarda la mejor opción conocida para X y `beta` la mejor opción conocida
para O. Cuando una rama ya no puede mejorar el resultado, se deja de explorar.
Esto reduce el trabajo sin cambiar la decisión que produciría Minimax.

### Profundización iterativa y tiempo

La búsqueda prueba profundidad 1, después 2, después 3 y así sucesivamente.
Si se agota el tiempo, conserva el mejor movimiento de la última profundidad
terminada. El presupuesto cambia según la etapa de la partida y nunca supera
el límite recibido.

### Tabla de transposiciones

La clase `TranspositionTable` evita recalcular posiciones repetidas. Cada
entrada indica si el valor es:

- exacto;
- una cota inferior; o
- una cota superior.

Esta distinción es necesaria porque una rama cortada por alfa-beta no siempre
produce un valor exacto.

## Función heurística

Cuando no es posible revisar la partida completa, `evaluar_posicion()` estima
qué jugador tiene ventaja. Una puntuación positiva favorece a X y una negativa
favorece a O.

| Componente | Qué observa | Peso |
|---|---|---:|
| Progreso meta | Amenazas para ganar el tablero completo | 10 |
| Bifurcaciones | Dos o más amenazas simultáneas | 7 |
| Defensa | Amenazas locales de ambos jugadores | 6 |
| Posiciones clave | Centro, esquinas y bordes ganados | 7 |
| Control local | Casillas y amenazas dentro de los campos | 3 |
| Destino inmediato | Si se manda al rival a un campo peligroso | 8 |
| Destino futuro | A qué campo podría mandar después al rival | 4 |

La explicación completa y los ejemplos numéricos están en
[`documentacion/heuristica.md`](documentacion/heuristica.md).

## Qué cambió respecto de la versión anterior

La versión anterior se conserva para documentar el avance, no porque esté
mal conservarla. La versión actual cambia principalmente lo siguiente:

| Antes | Ahora |
|---|---|
| Un archivo procedural con listas y funciones | Código modular con una clase `Tablero`, más un archivo único sincronizado |
| Se preguntaba quién comenzaba | Se pregunta si la persona quiere X u O; X siempre comienza |
| Un modo principal de humano contra sistema | Tres modos: humano vs humano, IA vs IA y humano vs IA |
| Pruebas básicas dentro del mismo archivo | 100 pruebas finales y 20 pruebas históricas con `pytest` |
| Documentos y código mezclados en la raíz | Carpetas separadas y nombres consistentes |
| Tabla de memoria limitada a resultados completos | Tabla que además identifica valores exactos y cotas de alfa-beta |
| Validaciones concentradas en la interfaz | Reglas validadas también por el propio objeto `Tablero` |

El análisis detallado, función por función, está en
[`documentacion/cambios_version_anterior_a_actual.md`](documentacion/cambios_version_anterior_a_actual.md).

## Pruebas

Instalar la única dependencia de desarrollo:

```bash
python -m pip install -r requirements-dev.txt
```

Ejecutar las 100 pruebas finales:

```bash
python -m pytest tests/test_gato_de_gatos.py -q
```

Ejecutar las 20 pruebas históricas:

```bash
python -m pytest tests/test_regresion_historica.py -q
```

Ejecutar ambas suites:

```bash
python -m pytest tests -q
```

Las pruebas revisan reglas, coordenadas, victorias, empates, destinos
obligatorios, aplicar y deshacer movimientos, heurística, Minimax, límite de
tiempo, tabla de transposiciones, una partida completa y equivalencia entre la
versión modular y el archivo de Spyder.

## Documentos relacionados

- [`src/README.md`](src/README.md): explicación de cada módulo.
- [`codigo_final_spyder/README.md`](codigo_final_spyder/README.md): cómo usar el archivo de entrega.
- [`tests/README.md`](tests/README.md): distribución de los casos de prueba.
- [`documentacion/README.md`](documentacion/README.md): índice de documentación.
- [`casos_de_estudio/README.md`](casos_de_estudio/README.md): partidas analizadas.
- [`version_anterior/README.md`](version_anterior/README.md): propósito del código conservado.

## Estado actual

- El código modular y el archivo para Spyder están sincronizados.
- Las 100 pruebas finales y las 20 históricas deben aprobar.
- GitHub Actions compila el proyecto y ejecuta la suite final en cada pull
  request.
- Los cambios de organización se preparan en una rama antes de llegar a
  `main`.
