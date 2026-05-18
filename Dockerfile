# Stage 1: Downloader
FROM ollama/ollama:latest AS downloader

RUN ollama serve & \
    sleep 5 && \
    ollama pull llama3

# Stage 2
FROM ollama/ollama:latest

LABEL org.opencontainers.image.authors="FNNDSC <dev@babyMRI.org>" \
      org.opencontainers.image.title="A ChRIS plugin to run an ollama server" \
      org.opencontainers.image.description="A ChRIS plugin to run an ollama server"

# Install Python
RUN apt-get update && apt-get install -y python3 python3-venv python3-pip && \
    rm -rf /var/lib/apt/lists/*

ARG SRCDIR=/usr/local/src/pl-ollama_infer
WORKDIR ${SRCDIR}

# venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ARG extras_require=none
RUN pip install ".[${extras_require}]" && \
    cd / && rm -rf ${SRCDIR}

# Create runtime user first
RUN useradd -m -u 10001 appuser

# Ollama paths
ENV OLLAMA_HOME=/opt/ollama
ENV OLLAMA_MODELS=/opt/ollama/.ollama/models
ENV OLLAMA_FLASH_ATTENTION=1

# Create directories
RUN mkdir -p /opt/ollama && \
    chown -R appuser:appuser /opt/ollama

# Copy FULL ollama cache from builder stage
COPY --from=downloader --chown=appuser:appuser \
    /root/.ollama /opt/ollama/.ollama

# Run as non-root
USER appuser


# ✅ Switch user
USER appuser

WORKDIR /
EXPOSE 11434
ENTRYPOINT []

CMD ["ollama_infer"]