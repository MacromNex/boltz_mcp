FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y \
    git gcc g++ wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install boltz with CUDA support and MCP dependencies
RUN pip install --no-cache-dir --prefix=/install "boltz[cuda]" -U
RUN pip install --no-cache-dir --prefix=/install --ignore-installed fastmcp loguru tqdm

# Download Boltz2 model checkpoints and CCD data into cache
ENV BOLTZ_CACHE=/root/.boltz
RUN mkdir -p ${BOLTZ_CACHE} \
    && wget -q -O ${BOLTZ_CACHE}/mols.tar \
       "https://huggingface.co/boltz-community/boltz-2/resolve/main/mols.tar" \
    && tar xf ${BOLTZ_CACHE}/mols.tar -C ${BOLTZ_CACHE} \
    && wget -q -O ${BOLTZ_CACHE}/boltz2_conf.ckpt \
       "https://huggingface.co/boltz-community/boltz-2/resolve/main/boltz2_conf.ckpt" \
    && wget -q -O ${BOLTZ_CACHE}/boltz2_aff.ckpt \
       "https://huggingface.co/boltz-community/boltz-2/resolve/main/boltz2_aff.ckpt"

FROM python:3.10-slim AS runtime

RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /install /usr/local
COPY --from=builder /root/.boltz /root/.boltz

COPY src/ ./src/
RUN chmod -R a+r /app/src/
COPY scripts/ ./scripts/
RUN chmod -R a+r /app/scripts/
COPY examples/ ./examples/
RUN chmod -R a+r /app/examples/
RUN mkdir -p jobs tmp/inputs tmp/outputs

ENV PYTHONPATH=/app
ENV BOLTZ_CACHE=/root/.boltz

CMD ["python", "src/server.py"]
