FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS builder

RUN apt-get update && apt-get install -y \
    python3.10 python3.10-dev python3.10-venv python3-pip \
    git gcc g++ wget \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && python -m pip install --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

# Install into a venv so we can copy it cleanly to runtime
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir "boltz[cuda]" -U
RUN pip install --no-cache-dir fastmcp loguru tqdm

FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04 AS runtime

RUN apt-get update && apt-get install -y \
    python3.10 python3.10-dev python3.10-venv libgomp1 gcc \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

# Copy the venv with all dependencies
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY examples/ ./examples/
RUN chmod -R a+rX /app/src /app/scripts /app/examples

# Create runtime directories writable by any user (jobs, tmp for YAML configs, results)
RUN mkdir -p /app/jobs /app/tmp/inputs /app/tmp/outputs /app/results \
    && chmod a+rwx /app/jobs /app/tmp /app/tmp/inputs /app/tmp/outputs /app/results

# Neutral mount points for Boltz checkpoints and pre-computed MSA
# Mount host ~/.boltz to /opt/boltz_cache at runtime
# Mount pre-computed MSA files to /opt/msa at runtime
RUN mkdir -p /opt/boltz_cache /opt/msa && chmod a+rx /opt/boltz_cache /opt/msa

# Use /tmp as HOME so Python/torch/numba can write caches when running as arbitrary UID
ENV HOME=/tmp
ENV PYTHONPATH=/app
ENV BOLTZ_CACHE=/opt/boltz_cache
ENV NUMBA_CACHE_DIR=/tmp/numba_cache
ENV MPLCONFIGDIR=/tmp/matplotlib
ENV TORCHINDUCTOR_CACHE_DIR=/tmp/torch_cache
# Suppress NVIDIA banner and disable entrypoint check (banner pollutes MCP stdio)
ENV NVIDIA_PRODUCT_NAME=""
ENTRYPOINT []

CMD ["python", "src/server.py"]
