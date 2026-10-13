# ── Stage 1: builder ──────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# ── Stage 2: runtime (non-root) ───────────────────────────
FROM python:3.11-slim
WORKDIR /app
RUN groupadd -r vertex && useradd -r -g vertex vertex
COPY --from=builder /root/.local /home/vertex/.local
COPY . .
COPY ../productos.csv ./productos.csv 2>/dev/null || true
ENV PATH=/home/vertex/.local/bin:$PATH \
    PYTHONUNBUFFERED=1
USER vertex
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
