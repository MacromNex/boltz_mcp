# Boltz MCP Server

**Structure and affinity prediction using Boltz2 via Docker**

An MCP (Model Context Protocol) server for Boltz2 protein modeling with 6 core tools:
- Predict protein 3D structures from sequences or YAML configs
- Predict protein-ligand binding affinity
- Submit long-running jobs with async monitoring
- Track and retrieve job results
- Validate protein sequences and ligand SMILES
- Batch process multiple sequences

## Quick Start with Docker

### Approach 1: Pull Pre-built Image from GitHub

The fastest way to get started. A pre-built Docker image is automatically published to GitHub Container Registry on every release.

```bash
# Pull the latest image
docker pull ghcr.io/macromnex/boltz_mcp:latest

# Register with Claude Code (runs as current user to avoid permission issues)
claude mcp add boltz -- docker run -i --rm --user `id -u`:`id -g` --gpus all --ipc=host -v `pwd`:`pwd` ghcr.io/macromnex/boltz_mcp:latest
```

**Note:** Run from your project directory. `` `pwd` `` expands to the current working directory.

**Requirements:**
- Docker with GPU support (`nvidia-docker` or Docker with NVIDIA runtime)
- Claude Code installed

That's it! The Boltz MCP server is now available in Claude Code.

---

### Approach 2: Build Docker Image Locally

Build the image yourself and install it into Claude Code. Useful for customization or offline environments.

```bash
# Clone the repository
git clone https://github.com/MacromNex/boltz_mcp.git
cd boltz_mcp

# Build the Docker image
docker build -t boltz_mcp:latest .

# Register with Claude Code (runs as current user to avoid permission issues)
claude mcp add boltz -- docker run -i --rm --user `id -u`:`id -g` --gpus all --ipc=host -v `pwd`:`pwd` boltz_mcp:latest
```

**Note:** Run from your project directory. `` `pwd` `` expands to the current working directory.

**Requirements:**
- Docker with GPU support
- Claude Code installed
- Git (to clone the repository)

**About the Docker Flags:**
- `-i` — Interactive mode for Claude Code
- `--rm` — Automatically remove container after exit
- `` --user `id -u`:`id -g` `` — Runs the container as your current user, so output files are owned by you (not root)
- `--gpus all` — Grants access to all available GPUs
- `--ipc=host` — Uses host IPC namespace for better performance
- `-v` — Mounts your project directory so the container can access your data

---

## Verify Installation

After adding the MCP server, you can verify it's working:

```bash
# List registered MCP servers
claude mcp list

# You should see 'boltz' in the output
```

In Claude Code, you can now use all 6 Boltz tools:
- `simple_structure_prediction`
- `simple_affinity_prediction`
- `submit_structure_prediction`
- `submit_affinity_prediction`
- `get_job_status`
- `get_job_result`

---

## Next Steps

- **Detailed documentation**: See [detail.md](detail.md) for comprehensive guides on:
  - Available MCP tools and parameters
  - Local Python environment setup (alternative to Docker)
  - Example workflows and use cases
  - YAML configuration file format
  - Performance optimization tips

---

## Usage Examples

Once registered, you can use the Boltz tools directly in Claude Code. Here are some common workflows:

### Example 1: Quick Structure Prediction

```
Can you predict the structure of this protein sequence using simple_structure_prediction? The sequence is MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG. Save the output to /path/to/results/.
```

### Example 2: Protein-Ligand Affinity

```
I want to predict the binding affinity between my protein at /path/to/protein.fasta and a small molecule with SMILES "CC(=O)Oc1ccccc1C(=O)O" (aspirin). Use simple_affinity_prediction and save the complex structure to /path/to/output/.
```

### Example 3: High-Quality Structure with Potentials

```
Submit a high-quality structure prediction for the sequence in /path/to/protein.fasta using submit_structure_prediction with use_potentials set to True. Monitor the job until it completes and retrieve the results.
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

**Claude Code not found?**
```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code
```

---

## License

MIT
