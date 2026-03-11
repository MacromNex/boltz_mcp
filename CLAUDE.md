# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Boltz MCP is an MCP (Model Context Protocol) server wrapping the [Boltz2](https://github.com/jwohlwend/boltz) deep learning model for protein structure prediction and protein-ligand affinity prediction. It exposes Boltz2's capabilities as MCP tools usable by Claude Code, Gemini CLI, or other MCP clients.

## Setup

### Local (conda)
```bash
bash quick_setup.sh          # creates conda env at ./env, clones Boltz2 into repo/boltz, installs deps
# Options: --skip-env, --skip-repo
```

Register with Claude Code:
```bash
claude mcp add boltz -- $(pwd)/env/bin/python $(pwd)/src/server.py
```

### Docker
```bash
docker build -t boltz_mcp:latest .

# Register with Claude Code (non-root user mode)
claude mcp add boltz -- docker run -i --rm \
  --user `id -u`:`id -g` --gpus all --ipc=host \
  -v ~/.boltz:/opt/boltz_cache:ro \
  -v `pwd`:`pwd` \
  boltz_mcp:latest
```

The Docker image does NOT include model checkpoints — mount them from the host via `-v ~/.boltz:/opt/boltz_cache:ro`. Checkpoints auto-download on first local run (~6 GB) to `~/.boltz`.

## Running

```bash
# MCP server (production)
./env/bin/python src/server.py

# MCP dev mode (with inspector)
fastmcp dev src/server.py

# CLI scripts directly
./env/bin/python scripts/structure_prediction.py --sequence "MVLSE..." --output results/out
./env/bin/python scripts/affinity_prediction.py --protein-seq "MVLSE..." --ligand-smiles "CC(=O)O" --output results/out

# With pre-computed MSA (skips slow MSA server query)
./env/bin/python scripts/affinity_prediction.py --protein-seq "MVLSE..." --ligand-smiles "CC(=O)O" --msa-path /path/to/protein.a3m --output results/out
```

## Testing

Tests are custom scripts (no pytest framework). Run from the project root with the conda env activated:
```bash
./env/bin/python tests/test_server.py          # unit tests: imports, job manager, validation tools
./env/bin/python tests/test_integration.py     # full integration: all MCP tools with real/mock data
./env/bin/python tests/test_simple.py          # quick validation of all tool types
```

## Architecture

```
src/server.py          — FastMCP server; all 13 MCP tool definitions (@mcp.tool decorators)
src/jobs/manager.py    — JobManager: async job execution via subprocess + threading
scripts/               — Standalone CLI scripts that server.py delegates to
  structure_prediction.py  — boltz predict wrapper for protein structure
  affinity_prediction.py   — boltz predict wrapper for protein-ligand affinity
examples/data/         — YAML input configs and FASTA files for testing
jobs/                  — Runtime directory for async job metadata, logs, and outputs
repo/boltz/            — Cloned Boltz2 repository (installed in editable mode)
```

### MCP Tools (13 total)

| Category | Tool | Purpose |
|----------|------|---------|
| Sync | `simple_structure_prediction` | Block & return structure prediction results |
| Sync | `simple_affinity_prediction` | Block & return affinity prediction results |
| Async | `submit_structure_prediction` | Background structure prediction, returns `job_id` |
| Async | `submit_affinity_prediction` | Background affinity prediction, returns `job_id` |
| Async | `submit_batch_structure_prediction` | Batch multiple sequences as one job |
| Jobs | `get_job_status`, `get_job_result`, `get_job_log`, `cancel_job`, `list_jobs` | Async job lifecycle management |
| Utility | `validate_protein_sequence` | Validate amino acid sequence + composition |
| Utility | `validate_ligand_smiles` | Validate SMILES + molecular properties (via RDKit) |
| Utility | `list_example_data` | List bundled example YAML/FASTA files |

All prediction tools (sync, async, batch) accept an optional `msa_path` parameter for pre-computed MSA files.

### Key Design Patterns

**Dual API surface**: Every prediction has a sync tool (`simple_*`) that blocks and returns results directly, and a submit tool (`submit_*`) that spawns a background subprocess and returns a `job_id`. Job lifecycle: pending → running → completed/failed/cancelled.

**Script delegation**: The MCP server tools import and call `run_structure_prediction()` / `run_affinity_prediction()` from `scripts/` for sync operations. For async submit operations, `JobManager` launches the same scripts as subprocesses.

**YAML config generation**: When users provide raw sequences (instead of YAML files), both scripts auto-generate temporary Boltz2-compatible YAML configs, run the prediction, then clean up the temp files. When `msa_path` is provided, it is embedded in the YAML config as `msa: <path>`.

**Pre-computed MSA reuse**: For screening multiple ligands against the same protein, compute MSA once (first run with `--use_msa_server` produces `.a3m` files in the output `msa/` directory), then pass `--msa-path` or `msa_path` to skip the MSA server on subsequent runs. This saves ~5 min per prediction.

**JobManager** (`src/jobs/manager.py`): Stores metadata/logs/results in `jobs/<job_id>/`. Each job runs in a daemon thread wrapping a subprocess. State is persisted as JSON files (`metadata.json`, `result_summary.json`).

### Adding a New MCP Tool

1. Add `@mcp.tool()` function in `src/server.py`
2. If it needs a CLI script, add to `scripts/` with the pattern: `run_*()` function + `argparse` CLI
3. For async support, use `job_manager.submit_job(script_path, args)`

## Docker Notes

- **Dockerfile**: Multi-stage build using `nvidia/cuda:12.4.1` base. Builder stage (`devel`) installs `boltz[cuda]` into a venv. Runtime stage (`runtime`) copies the venv and adds `gcc` + `python3.10-dev` for Triton JIT compilation.
- **No bundled checkpoints**: Mount host `~/.boltz` to `/opt/boltz_cache` at runtime (read-only)
- **MSA mount point**: Mount pre-computed MSA files to `/opt/msa` at runtime (read-only)
- **Non-root user support**: `HOME=/tmp`, `chmod a+rX` on app files, `a+rwx` only on runtime write dirs (`jobs/`, `tmp/`, `results/`). No `chmod 777` on sensitive paths.
- **Environment variables**: `BOLTZ_CACHE=/opt/boltz_cache`, `NUMBA_CACHE_DIR=/tmp/numba_cache`, `MPLCONFIGDIR=/tmp/matplotlib`, `TORCHINDUCTOR_CACHE_DIR=/tmp/torch_cache`
- **`.dockerignore`**: Uses `/jobs/` (with leading slash) to exclude the top-level runtime directory without excluding `src/jobs/`
- **CI/CD**: `.github/workflows/docker.yml` builds and pushes to `ghcr.io` with `latest`, `sha-*`, and semver tags

### Docker run example
```bash
docker run -i --rm \
  --user `id -u`:`id -g` \
  --gpus all --ipc=host \
  -v ~/.boltz:/opt/boltz_cache:ro \
  -v /path/to/msa:/opt/msa:ro \
  -v /path/to/workdir:/path/to/workdir \
  boltz_mcp:latest
```

## Environment Notes

- Conda env at `./env` with Python 3.10; Boltz2 installed in editable mode from `repo/boltz`
- Key deps: `boltz`, `fastmcp`, `loguru`, `torch`, `rdkit` (for SMILES validation)
- GPU (NVIDIA 8+ GB VRAM) strongly recommended; CPU fallback via `CUDA_VISIBLE_DEVICES=""`
- Models auto-download on first use (~6 GB) to `~/.boltz` (or `$BOLTZ_CACHE`)
- Both scripts set env fixes for non-root Docker: `USER`, `NUMBA_CACHE_DIR`, `MPLCONFIGDIR`, `TORCHINDUCTOR_CACHE_DIR`
