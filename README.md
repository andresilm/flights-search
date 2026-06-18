# Flights Search

Proyecto base de Python utilizando FastAPI y Uvicorn, gestionado con `uv`.

## Estructura

- `src/`: Código fuente principal de la aplicación.
- `tests/`: Pruebas unitarias y de integración.

## Instalación y Ejecución

Asegúrate de tener [uv](https://docs.astral.sh/uv/) instalado.

1. Instalar dependencias:
   ```bash
   uv sync
   ```

2. Ejecutar la aplicación en modo desarrollo:
   ```bash
   uv run uvicorn src.main:app --reload
   ```

3. Ejecutar los tests:
   ```bash
   uv run pytest
   ```
