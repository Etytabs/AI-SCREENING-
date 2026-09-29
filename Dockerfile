FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml .
COPY apps ./apps
COPY ml ./ml
COPY services ./services
COPY tests ./tests
COPY docs ./docs

RUN pip install --no-cache-dir ".[dev]"

EXPOSE 8000
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
