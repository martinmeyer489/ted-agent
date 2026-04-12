FROM python:3.11-slim

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy dependency files first for layer caching
COPY pyproject.toml poetry.lock* README.md ./

# Configure poetry
RUN poetry config virtualenvs.create false

# Copy project files (pyproject.toml references packages from backend/)
COPY backend/ ./backend/

# Install the project so the "app" package is on sys.path
RUN poetry install --no-interaction --no-ansi --only main

# Expose port
EXPOSE 8000

# Start the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
