#!/usr/bin/env python3
"""
Script: structure_prediction.py
Description: Predict protein 3D structure from sequence using Boltz2

Original Use Case: examples/use_case_1_structure_prediction.py
Dependencies Removed: None (script was already clean)

Usage:
    python scripts/structure_prediction.py --input <input_file> --output <output_dir>

Example:
    python scripts/structure_prediction.py --input examples/data/prot.yaml --output results/structure_out
    python scripts/structure_prediction.py --sequence "MVLSEGEWQLD..." --output results/structure_out
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import os
import sys

# Fix for running as non-existent UID in Docker containers
if 'USER' not in os.environ:
    os.environ['USER'] = 'user'
# Fix numba and torch cache dirs for non-root Docker users
os.environ.setdefault('NUMBA_CACHE_DIR', '/tmp/numba_cache')
os.environ.setdefault('NUMBA_DISABLE_JIT', '0')
os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib')
os.environ.setdefault('TORCHINDUCTOR_CACHE_DIR', '/tmp/torch_cache')
import json
import yaml
import subprocess
from pathlib import Path
from typing import Union, Optional, Dict, Any

# ==============================================================================
# Configuration
# ==============================================================================
DEFAULT_CONFIG = {
    "use_msa_server": True,
    "use_potentials": False,
    "output_format": "pdb",
    "accelerator": "gpu",
    "temp_prefix": "temp_input"
}

# ==============================================================================
# Core Utility Functions
# ==============================================================================
def create_protein_yaml(sequence: str, output_path: Union[str, Path],
                        use_msa_server: bool = True, msa_path: Optional[str] = None) -> Path:
    """Create a protein YAML configuration file.

    Args:
        sequence: Protein amino acid sequence
        output_path: Path to save YAML file
        use_msa_server: Whether to use MSA server for better accuracy
        msa_path: Optional path to pre-computed .a3m MSA file

    Returns:
        Path to created YAML file
    """
    protein_entry = {
        "id": "A",
        "sequence": sequence
    }

    if msa_path:
        protein_entry["msa"] = str(msa_path)
    elif not use_msa_server:
        protein_entry["msa"] = "empty"

    config = {
        "version": 1,
        "sequences": [
            {
                "protein": protein_entry
            }
        ]
    }

    output_path = Path(output_path)
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    return output_path


def create_complex_yaml(sequence: str, ligand_smiles: str, output_path: Union[str, Path],
                        use_msa_server: bool = True, msa_path: Optional[str] = None,
                        protein_id: str = "A", ligand_id: str = "B") -> Path:
    """Create a protein-ligand complex YAML configuration file for structure prediction.

    Args:
        sequence: Protein amino acid sequence
        ligand_smiles: Ligand SMILES string
        output_path: Path to save YAML file
        use_msa_server: Whether to use MSA server for better accuracy
        msa_path: Optional path to pre-computed .a3m MSA file
        protein_id: Protein chain ID (default: A)
        ligand_id: Ligand chain ID (default: B)

    Returns:
        Path to created YAML file
    """
    protein_entry = {
        "id": protein_id,
        "sequence": sequence
    }

    if msa_path:
        protein_entry["msa"] = str(msa_path)
    elif not use_msa_server:
        protein_entry["msa"] = "empty"

    config = {
        "version": 1,
        "sequences": [
            {
                "protein": protein_entry
            },
            {
                "ligand": {
                    "id": ligand_id,
                    "smiles": ligand_smiles
                }
            }
        ]
    }

    output_path = Path(output_path)
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    return output_path

def run_boltz_command(input_yaml: Union[str, Path], output_dir: Union[str, Path],
                      use_msa_server: bool = True, use_potentials: bool = False,
                      output_format: str = "pdb",
                      accelerator: str = "gpu") -> Dict[str, Any]:
    """Run Boltz structure prediction command.

    Args:
        input_yaml: Path to input YAML file
        output_dir: Output directory for results
        use_msa_server: Use MSA server for better accuracy
        use_potentials: Use inference-time potentials for better physics
        output_format: Output format (pdb, cif)
        accelerator: Accelerator backend (gpu, cpu, tpu)

    Returns:
        Dict with success status and output information
    """
    # Use Python interpreter to call boltz CLI directly
    cmd = [
        sys.executable, "-c",
        "from boltz.main import cli; cli()",
        "predict", str(input_yaml),
        "--out_dir", str(output_dir),
        "--output_format", output_format,
        "--accelerator", accelerator
    ]

    if use_msa_server:
        cmd.append("--use_msa_server")

    if use_potentials:
        cmd.append("--use_potentials")

    # Isolate from user site-packages to avoid version conflicts
    env = {**os.environ, "PYTHONNOUSERSITE": "1"}

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd)
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": str(e),
            "stderr": e.stderr,
            "command": " ".join(cmd)
        }

def find_output_files(output_dir: Union[str, Path]) -> Dict[str, list]:
    """Find generated output files in the output directory.

    Args:
        output_dir: Directory to search for outputs

    Returns:
        Dict with categorized file paths
    """
    output_dir = Path(output_dir)
    pred_dir = output_dir / "predictions"

    files = {
        "structures": [],
        "confidence": [],
        "other": []
    }

    if pred_dir.exists():
        for file in pred_dir.rglob("*"):
            if file.is_file():
                rel_path = file.relative_to(output_dir)
                if file.suffix in ['.pdb', '.cif']:
                    files["structures"].append(str(rel_path))
                elif 'confidence' in file.name and file.suffix == '.json':
                    files["confidence"].append(str(rel_path))
                else:
                    files["other"].append(str(rel_path))

    return files

# ==============================================================================
# Main Function (MCP-ready)
# ==============================================================================
def validate_input_yaml(input_path: Union[str, Path]) -> Optional[str]:
    """Validate a Boltz input YAML file for common errors.

    Args:
        input_path: Path to the YAML file

    Returns:
        Error message string if invalid, None if valid
    """
    try:
        with open(input_path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return f"Failed to parse YAML: {e}"

    if not isinstance(data, dict):
        return "YAML must be a dictionary"

    if "sequences" not in data:
        return "YAML must contain a 'sequences' key"

    valid_entity_types = {"protein", "dna", "rna", "ligand"}
    for i, item in enumerate(data["sequences"]):
        if not isinstance(item, dict):
            return f"sequences[{i}] must be a dictionary"
        entity_type = next(iter(item.keys()), None)
        if entity_type and entity_type.lower() not in valid_entity_types:
            if entity_type.lower() == "smiles":
                return (
                    f"sequences[{i}]: Invalid entity type 'smiles'. "
                    f"Use 'ligand' with a 'smiles' field instead. "
                    f"Example: ligand: {{id: B, smiles: \"CC(=O)O\"}}"
                )
            return (
                f"sequences[{i}]: Invalid entity type '{entity_type}'. "
                f"Valid types: {valid_entity_types}"
            )

    return None


def run_structure_prediction(
    input_file: Optional[Union[str, Path]] = None,
    sequence: Optional[str] = None,
    ligand_smiles: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
    msa_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for protein structure prediction.

    Args:
        input_file: Path to input YAML file (mutually exclusive with sequence)
        sequence: Protein sequence string (mutually exclusive with input_file)
        ligand_smiles: Optional ligand SMILES for complex prediction (use with sequence)
        output_dir: Output directory (default: ./boltz_structure_output)
        msa_path: Optional path to pre-computed .a3m MSA file
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - success: Boolean indicating if prediction succeeded
            - result: Prediction metadata
            - output_dir: Path to output directory
            - output_files: Dict of categorized output files
            - metadata: Execution metadata

    Example:
        >>> # From sequence
        >>> result = run_structure_prediction(
        ...     sequence="MVLSEGEWQLVLHVWAK...",
        ...     output_dir="results/my_protein"
        ... )
        >>> print(result['output_files']['structures'])

        >>> # Protein-ligand complex
        >>> result = run_structure_prediction(
        ...     sequence="MVLSE...",
        ...     ligand_smiles="CC(=O)O",
        ...     output_dir="results/complex"
        ... )

        >>> # From YAML file
        >>> result = run_structure_prediction(
        ...     input_file="input.yaml",
        ...     output_dir="results/prediction"
        ... )
    """
    # Setup configuration
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    # Validate input
    if not input_file and not sequence:
        raise ValueError("Must provide either input_file or sequence")

    if input_file and sequence:
        raise ValueError("Provide either input_file OR sequence, not both")

    if ligand_smiles and not sequence:
        raise ValueError("ligand_smiles requires sequence (not input_file)")

    # Setup output directory
    if not output_dir:
        output_dir = "./boltz_structure_output"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle input
    input_yaml_path = None
    cleanup_temp = False

    if input_file:
        input_file = Path(input_file)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        # Validate YAML before running boltz
        validation_error = validate_input_yaml(input_file)
        if validation_error:
            raise ValueError(f"Invalid input YAML: {validation_error}")
        input_yaml_path = input_file
    else:
        # Create temporary YAML file from sequence
        temp_yaml = output_dir / f"{config['temp_prefix']}.yaml"
        if ligand_smiles:
            input_yaml_path = create_complex_yaml(
                sequence,
                ligand_smiles,
                temp_yaml,
                config['use_msa_server'],
                msa_path=msa_path
            )
        else:
            input_yaml_path = create_protein_yaml(
                sequence,
                temp_yaml,
                config['use_msa_server'],
                msa_path=msa_path
            )
        cleanup_temp = True

    # When pre-computed MSA is provided, don't use the MSA server
    use_msa = config['use_msa_server'] and not msa_path

    # Run prediction
    prediction_result = run_boltz_command(
        input_yaml_path,
        output_dir,
        use_msa_server=use_msa,
        use_potentials=config['use_potentials'],
        output_format=config['output_format'],
        accelerator=config['accelerator']
    )

    # Find output files
    output_files = find_output_files(output_dir)

    # Validate that predictions were actually generated (boltz can exit 0 with no output)
    if prediction_result["success"] and not output_files["structures"]:
        # Check manifest for empty records
        manifest_empty = False
        for manifest_path in output_dir.rglob("manifest.json"):
            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
                if not manifest.get("records"):
                    manifest_empty = True
            except Exception:
                pass

        if manifest_empty:
            prediction_result["success"] = False
            stderr = prediction_result.get("stderr", "")
            # Try to extract error from stderr
            error_msg = "Boltz processed 0 inputs - no predictions generated."
            if "Failed to process" in stderr:
                for line in stderr.split("\n"):
                    if "Failed to process" in line:
                        error_msg = line.strip()
                        break
            elif "Invalid entity type" in stderr:
                for line in stderr.split("\n"):
                    if "Invalid entity type" in line:
                        error_msg = line.strip()
                        break
            prediction_result["error"] = error_msg
            prediction_result["stderr"] = stderr

    # Cleanup temporary file if created
    if cleanup_temp and input_yaml_path.exists():
        input_yaml_path.unlink()

    # Prepare result
    result = {
        "success": prediction_result["success"],
        "result": {
            "command_output": prediction_result.get("stdout", ""),
            "command_used": prediction_result.get("command", ""),
            "sequence_length": len(sequence) if sequence else None,
            "input_source": "sequence" if sequence else "file"
        },
        "output_dir": str(output_dir),
        "output_files": output_files,
        "metadata": {
            "config": config,
            "input_file": str(input_file) if input_file else None,
            "sequence": sequence if sequence and len(sequence) < 100 else f"{sequence[:50]}..." if sequence else None
        }
    }

    if not prediction_result["success"]:
        result["error"] = prediction_result.get("error", "Unknown error")
        result["stderr"] = prediction_result.get("stderr", "")

    return result

# ==============================================================================
# CLI Interface
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', '-i', help='Input YAML file path')
    input_group.add_argument('--sequence', '-s', help='Protein sequence string')

    # Ligand options (for protein-ligand complex prediction)
    parser.add_argument('--ligand-smiles', '--ligand_smiles',
                       help='Ligand SMILES string for complex prediction (use with --sequence)')

    # MSA options
    parser.add_argument('--msa-path', help='Path to pre-computed .a3m MSA file (skips MSA server)')

    # Output options
    parser.add_argument('--output', '-o', default="./boltz_structure_output",
                       help='Output directory (default: ./boltz_structure_output)')

    # Configuration options
    parser.add_argument('--config', '-c', help='Config file (JSON)')
    parser.add_argument('--no-msa-server', '--no_msa_server', nargs='?', const=True, default=False,
                       type=lambda x: str(x).lower() in ('true', '1', 'yes', ''),
                       help="Don't use MSA server (faster but less accurate)")
    parser.add_argument('--use-potentials', '--use_potentials', nargs='?', const=True, default=False,
                       type=lambda x: str(x).lower() in ('true', '1', 'yes', ''),
                       help='Use inference-time potentials for better physics')
    parser.add_argument('--output-format', '--output_format', choices=['pdb', 'cif'], default='pdb',
                       help='Output format (default: pdb)')
    parser.add_argument('--accelerator', choices=['gpu', 'cpu', 'tpu'], default='gpu',
                       help='Accelerator backend (default: gpu).')

    args = parser.parse_args()

    # Load config if provided
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Override config with CLI args
    cli_overrides = {
        'use_msa_server': not args.no_msa_server,
        'use_potentials': args.use_potentials,
        'output_format': args.output_format,
        'accelerator': args.accelerator
    }

    try:
        # Run prediction
        result = run_structure_prediction(
            input_file=args.input,
            sequence=args.sequence,
            ligand_smiles=args.ligand_smiles,
            output_dir=args.output,
            msa_path=args.msa_path,
            config=config,
            **cli_overrides
        )

        if result["success"]:
            print(f"✅ Structure prediction completed!")
            print(f"   Output directory: {result['output_dir']}")

            if result["output_files"]["structures"]:
                print("   Structure files:")
                for f in result["output_files"]["structures"]:
                    print(f"     - {f}")

            if result["output_files"]["confidence"]:
                print("   Confidence files:")
                for f in result["output_files"]["confidence"]:
                    print(f"     - {f}")

            if result["result"]["sequence_length"]:
                print(f"   Sequence length: {result['result']['sequence_length']} residues")
        else:
            print(f"❌ Structure prediction failed!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            if result.get('stderr'):
                print(f"   Details: {result['stderr']}")
            sys.exit(1)

        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()