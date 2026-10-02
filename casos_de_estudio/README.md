# Casos de estudio

Esta carpeta contiene partidas reales o automáticas usadas para observar el
comportamiento de la IA. No son código necesario para ejecutar el juego; son
evidencia del proceso de prueba y análisis.

## Archivos

| Archivo | Tipo de partida o propósito |
|---|---|
| `juego_01.md` | Humano vs IA; permitió detectar un problema de evaluación en el campo E. |
| `juego_02_ia_vs_ia.md` | Primera comparación controlada IA vs IA. |
| `juego_03_post_integracion.md` | IA vs IA después de integrar optimizaciones. |
| `juego_04.md` | Humano vs IA con estadísticas de búsqueda. |
| `juego_05.md` a `juego_11.md` | Transcripciones automáticas de partidas posteriores. |
| `regresion_juego_01_campo_e.py` | Reconstruye una posición del juego 1 y comprueba que el error no reaparezca. |

## Ejecutar el caso de regresión

Desde la raíz del proyecto:

```bash
python casos_de_estudio/regresion_juego_01_campo_e.py
```

El script compara dos movimientos de una posición real. Ganar el campo E debe
recibir una evaluación igual o mejor que dejarlo sin ganar.

## Nombres de archivos

Las partidas usan `juego_NN.md`, con dos dígitos, para que GitHub las muestre en
orden. `src/transcripciones.py` usa el mismo formato al guardar una partida
nueva.
