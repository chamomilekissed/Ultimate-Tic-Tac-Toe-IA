# Resultados de torneos

Esta carpeta guarda las salidas producidas por `src/torneo.py`.

Cada archivo registra:

- ganador de cada partida;
- cantidad de jugadas;
- secuencia completa de movimientos;
- tiempo máximo configurado por jugada.

El archivo `resultado_torneo_20260915_190440.txt` es un resultado histórico que
se conserva como evidencia.

Para generar otro torneo desde la raíz:

```bash
python -m src.torneo 10 1.0 --seed 42
```

Esto ejecuta diez partidas IA vs IA, permite hasta un segundo por movimiento y
usa una semilla para que los desempates sean reproducibles. El nuevo archivo se
guardará automáticamente en esta carpeta.
