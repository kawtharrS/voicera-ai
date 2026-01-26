FROM python:3.10-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ ./src/

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -e .

FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels

COPY src/ ./src/
COPY pyproject.toml .

RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from agents import aria_graph, orion_graph; print('OK')" || exit 1

EXPOSE 8000

CMD ["langgraph", "up", "--host", "0.0.0.0", "--port", "8000"]
