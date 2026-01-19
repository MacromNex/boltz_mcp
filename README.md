# Boltz MCP

> Protein structure and affinity prediction using Boltz2 deep learning models via MCP (Model Context Protocol)

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Local Usage (Scripts)](#local-usage-scripts)
- [MCP Server Installation](#mcp-server-installation)
- [Using with Claude Code](#using-with-claude-code)
- [Using with Gemini CLI](#using-with-gemini-cli)
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

### Directory Structure
```
./
├── README.md               # This file
├── env/                    # Conda environment
├── src/
│   ├── server.py           # MCP server
│   └── jobs/               # Job management system
├── scripts/
│   ├── structure_prediction.py    # Protein structure prediction
│   ├── affinity_prediction.py     # Protein-ligand affinity prediction
│   └── lib/                # Shared utilities
├── examples/
│   └── data/               # Demo data
├── configs/                # Configuration files (empty)
├── reports/                # Step documentation
└── repo/                   # Original Boltz2 repository
```

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
cd /home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/boltz_mcp

# Create conda environment (use mamba if available)
mamba create -p ./env python=3.10 -y
# or: conda create -p ./env python=3.10 -y

# Activate environment
mamba activate ./env
# or: conda activate ./env

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
      "command": "/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/boltz_mcp/env/bin/python",
      "args": ["/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/boltz_mcp/src/server.py"]
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

#### Batch Processing
```
Submit batch structure prediction for these sequences:
- MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG
- ACDEFGHIKLMNPQRSTVWY
- MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG
```

#### Job Management
```
List all my Boltz jobs and show their status
Get the results for job "abc123" when it's completed
```

### Using @ References

In Claude Code, use `@` to reference files and directories:

| Reference | Description |
|-----------|-------------|
| `@examples/data/prot.yaml` | Reference a specific protein configuration |
| `@examples/data/affinity.yaml` | Reference an affinity prediction configuration |
| `@results/` | Reference output directory |

---

## Using with Gemini CLI

### Configuration

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "boltz": {
      "command": "/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/boltz_mcp/env/bin/python",
      "args": ["/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/boltz_mcp/src/server.py"]
    }
  }
}
```

### Example Prompts

```bash
# Start Gemini CLI
gemini

# Example prompts (same as Claude Code)
> What tools are available?
> Use simple_structure_prediction with sequence "MVLS..."
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
| `submit_batch_structure_prediction` | Batch processing for multiple sequences | >30 min | `sequences` (list), `use_potentials`, `job_name` |

### Job Management Tools

| Tool | Description |
|------|-------------|
| `get_job_status` | Check job progress and current status |
| `get_job_result` | Get results when job completed |
| `get_job_log` | View job execution logs with optional tail |
| `cancel_job` | Cancel running job |
| `list_jobs` | List all jobs with optional status filtering |

### Utility Tools

| Tool | Description |
|------|-------------|
| `validate_protein_sequence` | Validate amino acid sequence and get composition analysis |
| `validate_ligand_smiles` | Validate SMILES string and calculate molecular properties |
| `list_example_data` | List available example files for testing |

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

### Example 3: Batch Processing

**Goal:** Process multiple protein sequences from a family

**Using MCP (in Claude Code):**
```
Submit batch structure prediction for these globin sequences:
- MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRFKHLKTEREQESRKEAAG
- MVLPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSHGSAQVKGHGKKVADALTNAVAHVDDMPNALSALSDLHAHKLRVDPVNFKLLSHCLLVTLAAHLPAEFTPAVHASLDKFLASVSTVLTSKYR

Then monitor the job progress and get results when complete.
```

**Expected Output:**
- Individual structure predictions for each sequence
- Batch processing summary
- Comparative analysis

### Example 4: Configuration File Usage

**Goal:** Use pre-configured YAML files for complex predictions

**Using MCP (in Claude Code):**
```
Use simple_structure_prediction with @examples/data/prot.yaml and save output to results/configured_prediction/
```

**Expected Output:**
- Structure prediction based on YAML configuration
- MSA data utilization (if specified)
- Custom output formatting

---

## Demo Data

The `examples/data/` directory contains sample data for testing:

| File | Description | Use With |
|------|-------------|----------|
| `affinity.yaml` | Protein-ligand affinity prediction example | `simple_affinity_prediction`, `submit_affinity_prediction` |
| `cyclic_prot.yaml` | Cyclic protein structure prediction | `simple_structure_prediction`, `submit_structure_prediction` |
| `ligand.fasta` | Legacy FASTA format example | Convert to sequence param |
| `ligand.yaml` | Multi-ligand complex structure | `simple_affinity_prediction` |
| `msa/` | Multiple sequence alignment data directory | Used by YAML configs |
| `multimer.yaml` | Protein-protein complex prediction | `simple_structure_prediction` |
| `pocket.yaml` | Pocket-constrained binding prediction | `simple_affinity_prediction` |
| `prot_custom_msa.yaml` | Custom MSA usage example | `simple_structure_prediction` |
| `prot.fasta` | Legacy FASTA format example | Convert to sequence param |
| `prot_no_msa.yaml` | Single-sequence mode (no MSA) | `simple_structure_prediction` |
| `prot.yaml` | Basic protein structure prediction example | `simple_structure_prediction`, `submit_structure_prediction` |

### Configuration Files

The `configs/` directory is available for configuration templates (currently empty).

### Environment Configuration

Key environment settings are managed through:
- Conda environment in `./env`
- Boltz2 model configuration (auto-downloaded)
- CUDA settings (automatic detection)

### Performance Tuning

```bash
# For faster but less accurate results
--use-msa-server=False

# For highest quality (slower)
--use-potentials=True --use-msa-server=True

# GPU memory optimization (set in environment)
export CUDA_VISIBLE_DEVICES=0
```

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

# Verify MCP server
python -c "from src.server import mcp; print('MCP server imports successfully')"
```

**Problem:** CUDA errors
```bash
# Check CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Use CPU fallback if needed
export CUDA_VISIBLE_DEVICES=""
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

**Problem:** Tools not working
```bash
# Test server directly
python src/server.py
# Should start the MCP server without errors

# Test tool listing
python -c "
from src.server import mcp
print('Available tools:')
for tool in mcp.list_tools():
    print(f'- {tool}')
"
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

# Common solutions:
# 1. Check GPU memory: nvidia-smi
# 2. Verify input format
# 3. Ensure sufficient disk space
```

**Problem:** Out of memory errors
```bash
# Use CPU mode
export CUDA_VISIBLE_DEVICES=""

# Or reduce batch size for batch processing
# Split large sequence lists into smaller batches
```

### Input Validation Issues

**Problem:** Invalid protein sequence
```
Use validate_protein_sequence with your sequence first

# Common issues:
# - Non-standard amino acid codes
# - Whitespace or special characters
# - Empty or very short sequences
```

**Problem:** Invalid SMILES string
```
Use validate_ligand_smiles with your SMILES first

# Common issues:
# - Malformed chemical notation
# - Unsupported chemical elements
# - Invalid stereochemistry notation
```

---

## Performance Guidelines

### Use Sync API When:
- Single protein < 500 residues
- Quick validation or testing
- Interactive analysis
- Results needed immediately

### Use Submit API When:
- Large proteins > 500 residues
- Multiple sequences (batch processing)
- Use of expensive options (MSA server + potentials)
- Long-running experiments
- Jobs that may need monitoring/cancellation

### Optimization Tips:
- Use `use_msa_server: False` for faster (but less accurate) results
- Use `use_potentials: True` only when highest accuracy is needed
- Batch multiple sequences together rather than individual submissions
- Monitor GPU memory usage with `nvidia-smi`
- Use appropriate output formats (PDB for compatibility, CIF for precision)

---

## Development

### Running Tests

```bash
# Activate environment
mamba activate ./env

# Test MCP server
python src/server.py --help

# Test scripts directly
python scripts/structure_prediction.py --help
python scripts/affinity_prediction.py --help
```

### Starting Dev Server

```bash
# Run MCP server in dev mode
fastmcp dev src/server.py
```

### Adding New Tools

1. Add tool function to `src/server.py` with `@mcp.tool()` decorator
2. Create corresponding script in `scripts/` if needed
3. Update this README with the new tool documentation
4. Test thoroughly with both sync and submit APIs

---

## License

Based on the Boltz2 model and repository. Please refer to the original license in `repo/boltz/` for details.

## Credits

Based on [Boltz2](https://github.com/jwohlwend/boltz) - A biomolecular structure prediction model