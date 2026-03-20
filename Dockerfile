FROM python:3.12-slim

WORKDIR /app

# System dependencies (ffmpeg required by pydub for audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Build-time version info
ARG BUILD_COMMIT=dev
RUN echo "$BUILD_COMMIT" > /app/BUILD_COMMIT

# Install base dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Copy builtin plugins (requirements installed at startup via entrypoint)
COPY plugins/ ./plugins/

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
