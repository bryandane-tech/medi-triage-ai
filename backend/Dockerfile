# Stage 1: Build C Shared Library
FROM python:3.14-slim AS c-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    clang \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY c_engine/ /build/c_engine/
RUN clang -O3 -shared -fPIC -I c_engine/include c_engine/src/triage_engine.c -o /build/libtriage.so

# Stage 2: Final Runtime Container
FROM python:3.14-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy built C dynamic library from Stage 1
COPY --from=c-builder /build/libtriage.so /app/libtriage.so

# Copy application source
COPY backend/app /app/app

ENV C_LIB_PATH=/app/libtriage.so
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
