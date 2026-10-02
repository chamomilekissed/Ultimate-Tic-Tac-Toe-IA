# Flujo de pruebas automáticas

`pruebas.yml` configura GitHub Actions para:

1. descargar el repositorio;
2. preparar Python 3.12;
3. instalar `pytest`;
4. verificar la sintaxis;
5. ejecutar los 100 casos finales.

Este archivo ayuda a detectar errores antes de fusionar una rama con `main`.
