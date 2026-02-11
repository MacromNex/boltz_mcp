# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Boltz MCP is an MCP (Model Context Protocol) server wrapping the [Boltz2](https://github.com/jwohlwend/boltz) deep learning model for protein structure prediction and protein-ligand affinity prediction. It exposes Boltz2's capabilities as MCP tools usable by Claude Code, Gemini CLI, or other MCP clients.

## Setup

```bash
bash quick_setup.sh          # creates conda env at ./env, clones Boltz2 into repo/boltz, installs deps
# Options: --skip-env, --skip-repo
```

Register with Claude Code:
```bash
claude mcp add boltz -- $(pwd)/env/bin/python $(pwd)/src/server.py
```

## Running

```bash
# MCP server (production)
./env/bin/python src/server.py

# MCP dev mode (with inspector)
fastmcp dev src/server.py

# CLI scripts directly
./env/bin/python scripts/structure_prediction.py --sequence "MVLSE..." --output results/out
./env/bin/python scripts/affinity_prediction.py --protein-seq "MVLSE..." --ligand-smiles "CC(=O)O" --output results/out
```

## Testing

Tests are custom scripts (no pytest framework). Run from the project root with the conda env activated:
```bash
./env/bin/python tests/test_server.py          # unit tests: imports, job manager, validation tools
./env/bin/python tests/test_integration.py     # full integration: all MCP tools with real/mock data
```

## Architecture

```
src/server.py          — FastMCP server; all MCP tool definitions (@mcp.tool decorators)
src/jobs/manager.py    — JobManager: async job execution via subprocess + threading
scripts/               — Standalone CLI scripts that server.py delegates to
  structure_prediction.py  — boltz predict wrapper for protein structure
  affinity_prediction.py   — boltz predict wrapper for protein-ligand affinity
examples/data/         — YAML input configs and FASTA files for testing
jobs/                  — Runtime directory for async job metadata, logs, and outputs
repo/boltz/            — Cloned Boltz2 repository (installed in editable mode)
```

### Key Design Patterns

**Dual API surface**: Every prediction has a sync tool (`simple_*`) that blocks and returns results directly, and a submit tool (`submit_*`) that spawns a background subprocess and returns a `job_id`. Job lifecycle: pending → running → completed/failed/cancelled.

**Script delegation**: The MCP server tools import and call `run_structure_prediction()` / `run_affinity_prediction()` from `scripts/` for sync operations. For async submit operations, `JobManager` launches the same scripts as subprocesses via `mamba run -p ./env python <script>`.

**YAML config generation**: When users provide raw sequences (instead of YAML files), both scripts auto-generate temporary Boltz2-compatible YAML configs, run the prediction, then clean up the temp files.

**JobManager** (`src/jobs/manager.py`): Stores metadata/logs/results in `jobs/<job_id>/`. Each job runs in a daemon thread wrapping a subprocess. State is persisted as JSON files (`metadata.json`, `result_summary.json`).

### Adding a New MCP Tool

1. Add `@mcp.tool()` function in `src/server.py`
2. If it needs a CLI script, add to `scripts/` with the pattern: `run_*()` function + `argparse` CLI
3. For async support, use `job_manager.submit_job(script_path, args)` which builds `mamba run` commands

## Environment Notes

- Conda env at `./env` with Python 3.10; Boltz2 installed in editable mode from `repo/boltz`
- Key deps: `boltz`, `fastmcp`, `loguru`, `torch`, `rdkit` (for SMILES validation)
- GPU (NVIDIA 8+ GB VRAM) strongly recommended; CPU fallback via `CUDA_VISIBLE_DEVICES=""`
- Models auto-download on first use (~2-4 GB)
