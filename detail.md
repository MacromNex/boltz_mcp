# Boltz MCP

> Protein structure and affinity prediction using Boltz2 deep learning models via MCP (Model Context Protocol)

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Local Usage (Scripts)](#local-usage-scripts)
- [MCP Server Installation](#mcp-server-installation)
- [Using with Claude Code](#using-with-claude-code)
- [Available Tools](#available-tools)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

The Boltz MCP provides powerful protein structure prediction and protein-ligand affinity prediction capabilities using the Boltz2 deep learning model. This MCP server enables both quick interactive analysis and long-running batch processing through a unified interface compatible with Claude Code and other MCP-enabled applications.

### Features
- **Protein Structure Prediction**: Generate 3D protein structures from amino acid sequences using state-of-the-art deep learning
- **Protein-Ligand Affinity Prediction**: Predict binding affinity and complex structures for protein-ligand interactions
- **Batch Processing**: Process multiple protein variants or sequences in parallel
- **Multi-Modal Interface**: Use through both synchronous (quick) and asynchronous (submit/job) APIs
- **MSA Integration**: Automatic Multiple Sequence Alignment generation for improved accuracy
- **Inference-Time Potentials**: Enhanced physics-based refinement for higher quality structures
- **CUDA Acceleration**: GPU support for faster processing on NVIDIA hardware

---

## Installation

### Quick Setup (Recommended)

Run the automated setup script:

```bash
cd boltz_mcp
bash quick_setup.sh
```

The script will create the conda environment, clone the Boltz2 repository, install all dependencies, and display the Claude Code configuration. See `quick_setup.sh --help` for options like `--skip-env` or `--skip-repo`.

### Prerequisites
- Conda or Mamba (mamba recommended for faster installation)
- Python 3.10+
- NVIDIA GPU with 8+ GB VRAM (recommended for optimal performance)
- 16+ GB RAM for large proteins
- ~10 GB storage for models and temporary data

### Manual Installation (Alternative)

If you prefer manual installation or need to customize the setup, follow `reports/step3_environment.md`:

```bash
# Navigate to the MCP directory
cd /path/to/boltz_mcp

# Create conda environment (use mamba if available)
mamba create -p ./env python=3.10 -y

# Activate environment
mamba activate ./env

# Install Boltz2 from the repository
cd repo/boltz
pip install -e .
cd ../..

# Install MCP dependencies
pip install fastmcp loguru --ignore-installed
```

**Important Notes:**
- The environment will be ~5+ GB due to CUDA libraries and PyTorch
- Models will be downloaded automatically on first use (~2-4 GB additional)
- Some package downgrades may occur for Boltz2 compatibility (numpy, pyyaml, etc.)

---

## Local Usage (Scripts)

You can use the scripts directly without MCP for local processing.

### Available Scripts

| Script | Description | Example |
|--------|-------------|---------|
| `scripts/structure_prediction.py` | Predict protein 3D structure from sequence | See below |
| `scripts/affinity_prediction.py` | Predict protein-ligand binding affinity | See below |

### Script Examples

#### Structure Prediction

```bash
# Activate environment
mamba activate ./env

# Predict from YAML configuration file
python scripts/structure_prediction.py \
  --input examples/data/prot.yaml \
  --output results/structure_output \
  --use-potentials

# Predict from raw sequence
python scripts/structure_prediction.py \
  --sequence "MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG" \
  --output results/myoglobin_structure
```

**Parameters:**
- `--input, -i`: YAML configuration file (required if no sequence)
- `--sequence, -s`: Raw protein sequence (required if no input file)
- `--output, -o`: Output directory (default: auto-generated)
- `--use-potentials`: Use inference-time potentials for better physics
- `--no-msa-server`: Disable MSA server (faster but less accurate)
- `--output-format`: Output format - pdb or cif (default: pdb)

#### Affinity Prediction

```bash
# Predict from YAML configuration file
python scripts/affinity_prediction.py \
  --input examples/data/affinity.yaml \
  --output results/affinity_output

# Predict from protein sequence and ligand SMILES
python scripts/affinity_prediction.py \
  --protein-seq "MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG" \
  --ligand-smiles "N[C@@H](Cc1ccc(O)cc1)C(=O)O" \
  --output results/tyrosine_binding
```

**Parameters:**
- `--input, -i`: YAML configuration file
- `--protein-seq`: Protein amino acid sequence
- `--ligand-smiles`: Ligand SMILES string
- `--ligand-ccd`: Ligand CCD code (alternative to SMILES)
- `--output, -o`: Output directory (default: auto-generated)
- `--use-potentials`: Use inference-time potentials
- `--no-msa-server`: Disable MSA server

---

## MCP Server Installation

### Option 1: Using fastmcp (Recommended)

```bash
# Install MCP server for Claude Code
fastmcp install src/server.py --name boltz
```

### Option 2: Manual Installation for Claude Code

```bash
# Add MCP server to Claude Code
claude mcp add boltz -- $(pwd)/env/bin/python $(pwd)/src/server.py

# Verify installation
claude mcp list
```

### Option 3: Configure in settings.json

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "boltz": {
      "command": "/path/to/boltz_mcp/env/bin/python",
      "args": ["/path/to/boltz_mcp/src/server.py"]
    }
  }
}
```

---

## Using with Claude Code

After installing the MCP server, you can use it directly in Claude Code.

### Quick Start

```bash
# Start Claude Code
claude
```

### Example Prompts

#### Tool Discovery
```
What tools are available from Boltz?
```

#### Basic Structure Prediction
```
Use simple_structure_prediction with sequence "MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG" and save to results/myoglobin/
```

#### Protein-Ligand Affinity Prediction
```
Use simple_affinity_prediction with protein_sequence "MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG" and ligand_smiles "N[C@@H](Cc1ccc(O)cc1)C(=O)O"
```

#### Using Configuration Files
```
Run simple_structure_prediction with input file @examples/data/prot.yaml
```

#### Long-Running Tasks (Submit API)
```
Submit structure prediction for sequence "MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG" with use_potentials True
Then check the job status every few minutes
```

---

## Available Tools

### Quick Operations (Sync API)

These tools return results immediately (5-15 minutes):

| Tool | Description | Est. Time | Parameters |
|------|-------------|-----------|------------|
| `simple_structure_prediction` | Protein structure prediction (fast mode) | 5-10 min | `sequence` or `input_file`, `output_dir`, `use_msa_server`, `output_format` |
| `simple_affinity_prediction` | Protein-ligand affinity prediction (fast mode) | 8-15 min | `protein_sequence`, `ligand_smiles`/`ligand_ccd`, `output_dir`, `use_msa_server` |

### Long-Running Tasks (Submit API)

These tools return a job_id for tracking (>10 minutes):

| Tool | Description | Est. Time | Parameters |
|------|-------------|-----------|------------|
| `submit_structure_prediction` | Background structure prediction with advanced options | >10 min | `sequence` or `input_file`, `use_potentials`, `job_name` |
| `submit_affinity_prediction` | Background affinity prediction with advanced options | >10 min | `protein_sequence`, `ligand_smiles`, `use_potentials`, `job_name` |

### Job Management Tools

| Tool | Description |
|------|-------------|
| `get_job_status` | Check job progress and current status |
| `get_job_result` | Get results when job completed |
| `get_job_log` | View job execution logs with optional tail |
| `cancel_job` | Cancel running job |
| `list_jobs` | List all jobs with optional status filtering |

---

## Examples

### Example 1: Basic Structure Prediction

**Goal:** Predict the 3D structure of myoglobin from its amino acid sequence

**Using Script:**
```bash
python scripts/structure_prediction.py \
  --sequence "MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG" \
  --output results/myoglobin/
```

**Using MCP (in Claude Code):**
```
Predict the structure for myoglobin using this sequence: MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG
Save the results to results/myoglobin/
```

**Expected Output:**
- PDB structure file with 3D coordinates
- Confidence scores for each residue
- Processing logs

### Example 2: Protein-Ligand Affinity Prediction

**Goal:** Predict the binding affinity between a protein and tyrosine

**Using Script:**
```bash
python scripts/affinity_prediction.py \
  --protein-seq "MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG" \
  --ligand-smiles "N[C@@H](Cc1ccc(O)cc1)C(=O)O" \
  --output results/tyrosine_binding/
```

**Using MCP (in Claude Code):**
```
Use simple_affinity_prediction to predict binding between this protein: MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG
and tyrosine: N[C@@H](Cc1ccc(O)cc1)C(=O)O
```

**Expected Output:**
- Complex structure (protein + ligand)
- Binding affinity scores
- Confidence metrics

---

## Demo Data

The `examples/data/` directory contains sample data for testing:

| File | Description | Use With |
|------|-------------|----------|
| `affinity.yaml` | Protein-ligand affinity prediction example | `simple_affinity_prediction`, `submit_affinity_prediction` |
| `prot.yaml` | Basic protein structure prediction example | `simple_structure_prediction`, `submit_structure_prediction` |
| `multimer.yaml` | Protein-protein complex prediction | `simple_structure_prediction` |
| `ligand.yaml` | Multi-ligand complex structure | `simple_affinity_prediction` |

---

## Troubleshooting

### Environment Issues

**Problem:** Environment not found
```bash
# Recreate environment
mamba create -p ./env python=3.10 -y
mamba activate ./env
pip install fastmcp loguru
```

**Problem:** Import errors
```bash
# Verify Boltz installation
python -c "import boltz; print('Boltz installed successfully')"
```

### MCP Issues

**Problem:** Server not found in Claude Code
```bash
# Check MCP registration
claude mcp list

# Re-add if needed
claude mcp remove boltz
claude mcp add boltz -- $(pwd)/env/bin/python $(pwd)/src/server.py
```

### Job Issues

**Problem:** Job stuck in pending
```bash
# Check job directory
ls -la jobs/

# View job log
cat jobs/<job_id>/job.log
```

**Problem:** Job failed
```
Use get_job_log with job_id "<job_id>" and tail 100 to see error details
```

---

## License

Based on the Boltz2 model and repository. Please refer to the original license in `repo/boltz/` for details.

## Credits

Based on [Boltz2](https://github.com/jwohlwend/boltz) - A biomolecular structure prediction model
