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
3. Elegir el modo de juego.
4. Escribir movimientos con dos letras, por ejemplo `Gc`.

También se puede ejecutar desde la raíz del repositorio:

```bash
python codigo_final_spyder/gato_de_gatos.py
```

## Qué contiene

Aunque es un solo archivo, mantiene secciones separadas para:

- configuración;
- clase `Tablero`;
- movimientos legales;
- evaluación heurística;
- Minimax y poda alfa-beta;
- interfaz;
- control de la partida.

## Diferencia frente a `src/`

No son dos proyectos distintos. `src/` divide el código para facilitar su
lectura y sus pruebas; este archivo reúne la misma lógica para que pueda
ejecutarse directamente en Spyder sin configurar un paquete.

Las pruebas comparan ambas versiones durante una partida legal para comprobar
que mantengan el mismo tablero y la misma puntuación heurística.
