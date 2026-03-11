# Boltz MCP Server

**Structure and affinity prediction using Boltz2 via Docker**

An MCP (Model Context Protocol) server for Boltz2 protein modeling with 13 tools:
- Predict protein 3D structures from sequences or YAML configs
- Predict protein-ligand binding affinity
- Submit long-running jobs with async monitoring
- Track and retrieve job results
- Validate protein sequences and ligand SMILES
- Batch process multiple sequences
- Pre-computed MSA support for fast ligand screening

## Quick Start with Docker

### Approach 1: Pull Pre-built Image from GitHub

```bash
# Pull the latest image
docker pull ghcr.io/macromnex/boltz_mcp:latest

# Register with Claude Code
claude mcp add boltz -- docker run -i --rm \
  --user `id -u`:`id -g` --gpus all --ipc=host \
  -v ~/.boltz:/opt/boltz_cache:ro \
  -v `pwd`:`pwd` \
  ghcr.io/macromnex/boltz_mcp:latest
```

### Approach 2: Build Docker Image Locally

```bash
git clone https://github.com/MacromNex/boltz_mcp.git
cd boltz_mcp
docker build -t boltz_mcp:latest .

claude mcp add boltz -- docker run -i --rm \
  --user `id -u`:`id -g` --gpus all --ipc=host \
  -v ~/.boltz:/opt/boltz_cache:ro \
  -v `pwd`:`pwd` \
  boltz_mcp:latest
```

**Requirements:**
- Docker with GPU support (`nvidia-docker` or Docker with NVIDIA runtime)
- Boltz2 model checkpoints at `~/.boltz` (auto-downloaded on first local run)
- Claude Code installed

### Docker Flags Explained

| Flag | Purpose |
|------|---------|
| `-i` | Interactive mode for MCP stdio |
| `--rm` | Remove container after exit |
| `` --user `id -u`:`id -g` `` | Run as current user (output files owned by you) |
| `--gpus all` | Access all GPUs |
| `--ipc=host` | Host IPC namespace for PyTorch performance |
| `-v ~/.boltz:/opt/boltz_cache:ro` | Mount cached model checkpoints (read-only) |
| `-v path:path` | Mount working directory for input/output access |

### Pre-computed MSA for Fast Screening

When screening multiple ligands against the same protein, mount a pre-computed MSA directory to skip the slow MSA server query (~5 min saved per run):

```bash
claude mcp add boltz -- docker run -i --rm \
  --user `id -u`:`id -g` --gpus all --ipc=host \
  -v ~/.boltz:/opt/boltz_cache:ro \
  -v /path/to/msa_files:/opt/msa:ro \
  -v `pwd`:`pwd` \
  boltz_mcp:latest
```

Then pass `msa_path="/opt/msa/protein.a3m"` to any prediction tool. The MSA `.a3m` file is generated automatically on the first run with `--use_msa_server` and can be found in the output directory under `msa/`.

---

## Verify Installation

```bash
claude mcp list
# You should see 'boltz' in the output
```

Available tools (13 total):
- `simple_structure_prediction` / `simple_affinity_prediction` — sync predictions
- `submit_structure_prediction` / `submit_affinity_prediction` / `submit_batch_structure_prediction` — async jobs
- `get_job_status` / `get_job_result` / `get_job_log` / `cancel_job` / `list_jobs` — job management
- `validate_protein_sequence` / `validate_ligand_smiles` — input validation
- `list_example_data` — list bundled examples

---

## Usage Examples

### Quick Structure Prediction

```
Predict the structure of this protein: MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG. Save to /path/to/results/.
```

### Protein-Ligand Affinity

```
Predict binding affinity between protein MVLSE... and aspirin (SMILES: CC(=O)Oc1ccccc1C(=O)O). Use simple_affinity_prediction.
```

### Fast Ligand Screening with Pre-computed MSA

```
Screen these 10 ligands against KRAS using simple_affinity_prediction with msa_path="/opt/msa/kras.a3m" for each.
```

### High-Quality Structure with Potentials

```
Submit a structure prediction with use_potentials=True for the sequence in /path/to/protein.fasta. Monitor until complete.
```

---

## CLI Usage (without MCP)

```bash
# Structure prediction
./env/bin/python scripts/structure_prediction.py --sequence "MVLSE..." --output results/out

# Affinity prediction
./env/bin/python scripts/affinity_prediction.py \
  --protein-seq "MVLSE..." --ligand-smiles "CC(=O)O" --output results/out

# With pre-computed MSA (skips MSA server, much faster)
./env/bin/python scripts/affinity_prediction.py \
  --protein-seq "MVLSE..." --ligand-smiles "CC(=O)O" \
  --msa-path /path/to/protein.a3m --output results/out
```

---

## Troubleshooting

**Docker not found?**
```bash
docker --version  # Install Docker if missing
```

**GPU not accessible?**
- Ensure NVIDIA Docker runtime is installed
- Check with `docker run --gpus all ubuntu nvidia-smi`

**Model checkpoints missing?**
- Run a local prediction first to auto-download to `~/.boltz`
- Or set `BOLTZ_CACHE=/path/to/cache` before running

**Claude Code not found?**
```bash
npm install -g @anthropic-ai/claude-code
```

---

## Next Steps

See [detail.md](detail.md) for comprehensive guides on available tools, YAML config format, local setup, and performance optimization.

## License

MIT
