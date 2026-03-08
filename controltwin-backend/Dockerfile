# Stage 1 — builder
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt

# Stage 2 — runtime
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Créer user AVANT de copier les fichiers
RUN useradd -m -u 10001 controltwin

WORKDIR /app

# Copier les dépendances du builder
COPY --from=builder /install /usr/local

# Copier le code avec les bonnes permissions directement
COPY --chown=controltwin:controltwin . /app

RUN chmod +x /app/docker/entrypoint.sh

USER controltwin

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["/app/docker/entrypoint.sh"]