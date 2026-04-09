FROM ollama/ollama

LABEL org.opencontainers.image.authors="FNNDSC <dev@babyMRI.org>" \
      org.opencontainers.image.title="A ChRIS plugin to run an ollama server" \
      org.opencontainers.image.description="A ChRIS plugin to run an ollama server"

# Install Python + venv support
RUN apt-get update && apt-get install -y python3 python3-venv python3-pip

ARG SRCDIR=/usr/local/src/pl-ollama_infer
WORKDIR ${SRCDIR}

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies using venv pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy rest of code
COPY . .

ARG extras_require=none

# Install your package inside venv
RUN pip install ".[${extras_require}]" \
    && cd / && rm -rf ${SRCDIR}
RUN ollama serve & \
    sleep 5 && \
    ollama pull llama3
WORKDIR /
ENTRYPOINT []
CMD ["ollama_infer"]