# syntax=docker/dockerfile:1

FROM python:3.12-slim AS deps
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 appuser
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY src ./src
USER appuser
EXPOSE 8000
# Requires src.pipeline.api.app:create_app (pipeline domain). Redis is available via compose.
CMD ["uvicorn", "src.pipeline.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
