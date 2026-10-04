# Función heurística final

Este documento explica cómo `evaluar_posicion()` estima quién tiene ventaja
cuando Minimax alcanza su límite de profundidad. La explicación corresponde a
la rama `ana_correcciones_final` y al archivo de entrega para Spyder.

## Idea principal

La heurística siempre usa la perspectiva de X:

- un resultado positivo favorece a X;
- un resultado negativo favorece a O;
- cero representa equilibrio;
- una victoria usa `+10000` o `-10000` y no una estimación.

La fórmula es:

```text
H = 18M + 6B + 5D + 6C + 1L + 8I + 4F
```

| Letra | Componente | Peso |
|---|---|---:|
| `M` | Progreso en líneas del meta-tablero | 18 |
| `B` | Bono por bifurcaciones | 6 |
| `D` | Amenazas inmediatas activas | 5 |
| `C` | Campos ganados y posición estratégica | 6 |
| `L` | Desarrollo local con relevancia global | 1 |
| `I` | Situación del destino inmediato | 8 |
| `F` | Consecuencia del destino futuro | 4 |

Los pesos no representan probabilidades. Indican qué señales deben influir más
al comparar dos posiciones no terminales.

## Bloque básico: líneas abiertas

`contar_lineas_abiertas()` revisa las ocho líneas de un tablero de 3 por 3.
Una línea está abierta para X si contiene únicamente X y espacios vacíos. Una O
o un campo marcado como `EMPATE` la cierra para X.

Se distinguen dos casos:

- una marca y dos espacios: desarrollo temprano;
- dos marcas y un espacio: amenaza inmediata.

Esta separación evita tratar una jugada inicial como si ya estuviera a punto de
ganar el campo.

## 1. Progreso del meta-tablero: `M`

`evaluar_progreso_meta()` analiza líneas completas del tablero grande.

- una casilla global ganada dentro de una línea abierta aporta 1;
- dos casillas globales ganadas dentro de una línea abierta aportan 8;
- tres casillas producen una victoria terminal de 10000.

El crecimiento es no lineal porque estar a un campo de ganar la partida es
mucho más importante que poseer un campo aislado.

Además, una posición participa automáticamente en distintas cantidades de
líneas:

- centro: cuatro líneas;
- esquina: tres líneas;
- borde: dos líneas.

Por eso una victoria en el centro puede contribuir a más planes globales.

## 2. Bifurcaciones: `B`

Una bifurcación ocurre cuando un jugador mantiene dos o más amenazas en el
mismo mini-tablero. El oponente normalmente solo puede bloquear una.

La primera amenaza se contabiliza en `D`. Este componente suma únicamente las
amenazas adicionales:

```text
bono = máximo(0, cantidad_de_amenazas - 1)
```

Así una amenaza no se suma otra vez completa y se elimina el conteo repetido de
la versión anterior.

## 3. Defensa y amenazas inmediatas: `D`

`evaluar_defensa()` cuenta las líneas de dos marcas y un espacio de ambos
jugadores, pero solamente dentro de campos que todavía se pueden jugar.

Una figura dentro de un campo ya ganado o empatado no se considera amenaza,
porque nadie puede colocar otra ficha ahí. La versión anterior conservaba esas
figuras como si siguieran activas y podía alterar la decisión con información
que ya no tenía efecto en la partida.

## 4. Posiciones controladas: `C`

`evaluar_control_posiciones()` premia campos que ya fueron ganados:

| Posición | Valor base |
|---|---:|
| Centro | 4 |
| Esquina | 3 |
| Borde | 2 |

Este componente representa posesión consolidada. Es diferente del progreso
meta: `C` pregunta qué campos pertenecen a cada jugador y `M` pregunta si esos
campos forman líneas que todavía pueden completarse.

## 5. Desarrollo local: `L`

`evaluar_mini_tableros()` observa líneas con una marca y dos espacios. No
vuelve a contar amenazas de dos marcas.

Cada campo se pondera dinámicamente con
`contar_lineas_meta_relevantes()`. Una línea global deja de ser relevante para
X si contiene un campo ganado por O o un empate, y lo mismo ocurre al invertir
los jugadores.

Esto evita valorar igual:

- una marca que ayuda a completar varias líneas globales;
- una marca situada en un campo que ya no puede contribuir a ninguna victoria
  global del jugador.

## 6. Destino inmediato: `I`

Cada movimiento determina el campo del siguiente turno. Por eso
`evaluar_amenaza_destino()` revisa el mini-tablero donde está obligado a jugar
el jugador actual.

- si ahí tiene una amenaza propia, el destino lo favorece;
- si la amenaza pertenece al rival, probablemente tendrá que defenderse;
- si el destino está cerrado, obtiene un bono de libertad igual a 2 porque
  puede escoger cualquier campo abierto.

El valor se calcula primero desde la perspectiva del jugador que mueve y luego
se convierte a la perspectiva fija de X.

## 7. Destino futuro: `F`

`evaluar_amenaza_destino_futura()` revisa cada casilla legal del campo
obligatorio y estima tres consecuencias:

1. si la jugada gana el mini-tablero actual;
2. cuántas amenazas nuevas crea;
3. qué peligro encontrará el rival en el campo al que será enviado.

Una victoria local recibe un bono base de 3. Mandar al rival a un campo cerrado
se considera peligroso porque le entrega libertad de elección.

La versión anterior devolvía cero en cuanto detectaba cualquier victoria local.
Eso hacía indistinguibles dos jugadas ganadoras aunque una enviara al rival a
un campo seguro y la otra le regalara una oportunidad. La versión final compara
esas consecuencias antes de escoger.

## Por qué se excluyen los campos cerrados

Al ganar un campo desaparecen sus señales locales, pero aparecen señales más
importantes:

- el campo controlado se suma en `C`;
- su participación en líneas globales se suma en `M`;
- si completa tres campos, Minimax devuelve el valor terminal.

Por eso ya no es necesario conservar amenazas internas que no pueden jugarse.
La desaparición del detalle local es reemplazada por información global real.

## Selección de pesos

Los pesos se probaron mediante partidas cruzadas contra la evaluación anterior.
Las dos heurísticas usaron el mismo Minimax y se alternó cuál controlaba X y
cuál controlaba O.

Se compararon seis combinaciones iniciales a profundidad 2. La combinación
`18, 6, 5, 6, 1, 8, 4` obtuvo 14 victorias, 1 derrota y 5 empates frente a la
versión anterior. Después se repitió la comparación a profundidad 3 con
aperturas legales distintas:

| Resultado de la heurística final | Partidas |
|---|---:|
| Victorias | 15 |
| Derrotas | 2 |
| Empates | 3 |
| Total | 20 |

Esta muestra no demuestra que la función sea matemáticamente óptima. Sí muestra
que los pesos no se eligieron únicamente por intuición y que la versión final
superó a la anterior bajo las mismas condiciones de búsqueda.

## Relación con Minimax

La heurística solo se utiliza al alcanzar profundidad cero. Antes de eso,
Minimax revisa:

1. victoria global de X;
2. victoria global de O;
3. empate;
4. límite de profundidad.

Una victoria detectada durante la búsqueda usa `10000 - nivel`; una derrota usa
`-10000 + nivel`. Así se prefiere ganar pronto y retrasar una derrota inevitable.

## Diagnóstico

Para revisar una posición manualmente se puede usar:

```python
evaluar_posicion(tablero, es_maximizando, tablero_destino, debug=True)
```

El programa imprime el valor crudo, el peso y la aportación final de cada uno
de los siete componentes. Esta opción no debe activarse dentro de una partida
normal porque Minimax llama al evaluador miles de veces.

## Limitaciones que permanecen

- Una heurística estima: no reemplaza una búsqueda completa hasta el final.
- Las pruebas contra otra evaluación no representan todos los sistemas que
  podrían aparecer en el torneo.
- Los pesos pueden volver a calibrarse con más rivales y más partidas.
- El destino futuro analiza una aproximación de una jugada; Minimax continúa
  siendo responsable de explorar secuencias completas.

Estas limitaciones están documentadas para no afirmar que el sistema juega de
manera perfecta. La mejora consiste en que ahora cada componente tiene una
responsabilidad clara, se basa en jugadas todavía posibles y cuenta con pruebas
de regresión específicas.
