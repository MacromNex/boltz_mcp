#!/usr/bin/env python3
"""
Script: affinity_prediction.py
Description: Predict protein-ligand binding affinity and structure using Boltz2

Original Use Case: examples/use_case_2_affinity_prediction.py
Dependencies Removed: None (script was already clean)

Usage:
    python scripts/affinity_prediction.py --input <input_file> --output <output_dir>

Example:
    python scripts/affinity_prediction.py --input examples/data/affinity.yaml --output results/affinity_out
    python scripts/affinity_prediction.py --protein-seq "MVLSE..." --ligand-smiles "N[C@@H](Cc1ccc(O)cc1)C(=O)O" --output results/
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import os
import sys
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
    "temp_prefix": "temp_affinity",
    "protein_id": "A",
    "ligand_id": "B"
}

# ==============================================================================
# Core Utility Functions
# ==============================================================================
def create_affinity_yaml(protein_sequence: str, ligand_smiles: str, output_path: Union[str, Path],
                         ligand_ccd: Optional[str] = None, protein_id: str = "A",
                         ligand_id: str = "B") -> Path:
    """Create a protein-ligand affinity prediction YAML configuration file.

    Args:
        protein_sequence: Protein amino acid sequence
        ligand_smiles: Ligand SMILES string
        output_path: Path to save YAML file
        ligand_ccd: Optional CCD code instead of SMILES
        protein_id: Protein chain ID (default: A)
        ligand_id: Ligand ID (default: B)

    Returns:
        Path to created YAML file
    """
    config = {
        "version": 1,
        "sequences": [
            {
                "protein": {
                    "id": protein_id,
                    "sequence": protein_sequence
                }
            },
            {
                "ligand": {
                    "id": ligand_id
                }
            }
        ],
        "properties": [
            {
                "affinity": {
                    "binder": ligand_id
                }
            }
        ]
    }

    # Add ligand as either SMILES or CCD code
    if ligand_ccd:
        config["sequences"][1]["ligand"]["ccd"] = ligand_ccd
    else:
        config["sequences"][1]["ligand"]["smiles"] = ligand_smiles

    output_path = Path(output_path)
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    return output_path

def run_boltz_affinity_command(input_yaml: Union[str, Path], output_dir: Union[str, Path],
                               use_msa_server: bool = True, use_potentials: bool = False,
                               output_format: str = "pdb",
                               accelerator: str = "gpu") -> Dict[str, Any]:
    """Run Boltz affinity prediction command.

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

def parse_affinity_results(output_dir: Union[str, Path]) -> Dict[str, Any]:
    """Parse and extract affinity prediction results.

    Args:
        output_dir: Directory containing prediction results

    Returns:
        Dict with parsed affinity results
    """
    output_dir = Path(output_dir)
    pred_dir = output_dir / "predictions"

    results = {
        "affinity_files": [],
        "affinity_values": {},
        "confidence_files": [],
        "structure_files": []
    }

    if not pred_dir.exists():
        return results

    # Find all result files
    for file in pred_dir.rglob("*"):
        if file.is_file():
            rel_path = str(file.relative_to(output_dir))

            if file.suffix == '.json':
                if 'affinity' in file.name and 'confidence' not in file.name:
                    results["affinity_files"].append(rel_path)
                    # Try to parse affinity values
                    try:
                        with open(file) as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                for key, value in data.items():
                                    if isinstance(value, (int, float)):
                                        results["affinity_values"][key] = value
                    except (json.JSONDecodeError, Exception):
                        pass
                elif 'confidence' in file.name:
                    results["confidence_files"].append(rel_path)
            elif file.suffix in ['.pdb', '.cif']:
                results["structure_files"].append(rel_path)

    return results

def find_output_files(output_dir: Union[str, Path]) -> Dict[str, list]:
    """Find all generated output files in the output directory.

    Args:
        output_dir: Directory to search for outputs

    Returns:
        Dict with categorized file paths
    """
    output_dir = Path(output_dir)
    pred_dir = output_dir / "predictions"

    files = {
        "structures": [],
        "affinity": [],
        "confidence": [],
        "other": []
    }

    if pred_dir.exists():
        for file in pred_dir.rglob("*"):
            if file.is_file():
                rel_path = str(file.relative_to(output_dir))
                if file.suffix in ['.pdb', '.cif']:
                    files["structures"].append(rel_path)
                elif 'affinity' in file.name and file.suffix == '.json':
                    files["affinity"].append(rel_path)
                elif 'confidence' in file.name and file.suffix == '.json':
                    files["confidence"].append(rel_path)
                else:
                    files["other"].append(rel_path)

    return files

# ==============================================================================
# Main Function (MCP-ready)
# ==============================================================================
def run_affinity_prediction(
    input_file: Optional[Union[str, Path]] = None,
    protein_sequence: Optional[str] = None,
    ligand_smiles: Optional[str] = None,
    ligand_ccd: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for protein-ligand binding affinity prediction.

    Args:
        input_file: Path to input YAML file (mutually exclusive with sequence/ligand params)
        protein_sequence: Protein amino acid sequence
        ligand_smiles: Ligand SMILES string
        ligand_ccd: Ligand CCD code (alternative to SMILES)
        output_dir: Output directory (default: ./boltz_affinity_output)
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - success: Boolean indicating if prediction succeeded
            - result: Prediction results including affinity values
            - output_dir: Path to output directory
            - output_files: Dict of categorized output files
            - metadata: Execution metadata

    Example:
        >>> # From YAML file
        >>> result = run_affinity_prediction(
        ...     input_file="affinity.yaml",
        ...     output_dir="results/affinity"
        ... )

        >>> # From sequence and SMILES
        >>> result = run_affinity_prediction(
        ...     protein_sequence="MVLSEGEWQLVLHVWAK...",
        ...     ligand_smiles="N[C@@H](Cc1ccc(O)cc1)C(=O)O",
        ...     output_dir="results/tyrosine_binding"
        ... )
        >>> print(result['result']['affinity_values'])
    """
    # Setup configuration
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    # Validate input
    if input_file and (protein_sequence or ligand_smiles or ligand_ccd):
        raise ValueError("Provide either input_file OR (protein_sequence + ligand), not both")

    if not input_file:
        if not protein_sequence:
            raise ValueError("Must provide protein_sequence when not using input_file")
        if not ligand_smiles and not ligand_ccd:
            raise ValueError("Must provide either ligand_smiles or ligand_ccd when not using input_file")

    # Setup output directory
    if not output_dir:
        output_dir = "./boltz_affinity_output"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle input
    input_yaml_path = None
    cleanup_temp = False

    if input_file:
        input_file = Path(input_file)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        input_yaml_path = input_file
    else:
        # Create temporary YAML file from sequence and ligand
        temp_yaml = output_dir / f"{config['temp_prefix']}.yaml"
        input_yaml_path = create_affinity_yaml(
            protein_sequence,
            ligand_smiles,
            temp_yaml,
            ligand_ccd=ligand_ccd,
            protein_id=config['protein_id'],
            ligand_id=config['ligand_id']
        )
        cleanup_temp = True

    # Run prediction
    prediction_result = run_boltz_affinity_command(
        input_yaml_path,
        output_dir,
        use_msa_server=config['use_msa_server'],
        use_potentials=config['use_potentials'],
        output_format=config['output_format'],
        accelerator=config['accelerator']
    )

    # Parse results
    affinity_results = parse_affinity_results(output_dir)
    output_files = find_output_files(output_dir)

    # Cleanup temporary file if created
    if cleanup_temp and input_yaml_path.exists():
        input_yaml_path.unlink()

    # Prepare result
    result = {
        "success": prediction_result["success"],
        "result": {
            "command_output": prediction_result.get("stdout", ""),
            "command_used": prediction_result.get("command", ""),
            "affinity_values": affinity_results.get("affinity_values", {}),
            "protein_length": len(protein_sequence) if protein_sequence else None,
            "ligand_input": ligand_smiles or ligand_ccd,
            "ligand_type": "smiles" if ligand_smiles else "ccd" if ligand_ccd else None,
            "input_source": "sequence+ligand" if protein_sequence else "file"
        },
        "output_dir": str(output_dir),
        "output_files": output_files,
        "metadata": {
            "config": config,
            "input_file": str(input_file) if input_file else None,
            "protein_sequence": protein_sequence if protein_sequence and len(protein_sequence) < 100 else f"{protein_sequence[:50]}..." if protein_sequence else None,
            "ligand_smiles": ligand_smiles,
            "ligand_ccd": ligand_ccd
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

    # Input options (mutually exclusive groups)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', '-i', help='Input YAML file path')

    # Sequence inputs (when not using file)
    sequence_group = input_group.add_argument_group('sequence')
    input_group.add_argument('--protein-seq', help='Protein sequence string')

    # Ligand options
    parser.add_argument('--ligand-smiles', help='Ligand SMILES string')
    parser.add_argument('--ligand-ccd', help='Ligand CCD code')

    # Output options
    parser.add_argument('--output', '-o', default="./boltz_affinity_output",
                       help='Output directory (default: ./boltz_affinity_output)')

    # Configuration options
    parser.add_argument('--config', '-c', help='Config file (JSON)')
    parser.add_argument('--no-msa-server', action='store_true',
                       help="Don't use MSA server (faster but less accurate)")
    parser.add_argument('--use-potentials', action='store_true',
                       help='Use inference-time potentials for better physics')
    parser.add_argument('--output-format', choices=['pdb', 'cif'], default='pdb',
                       help='Output format (default: pdb)')
    parser.add_argument('--accelerator', choices=['gpu', 'cpu', 'tpu'], default='gpu',
                       help='Accelerator backend (default: gpu). Use cpu if no GPU available.')

    args = parser.parse_args()

    # Validate sequence-based inputs
    if args.protein_seq and not (args.ligand_smiles or args.ligand_ccd):
        parser.error("When using --protein-seq, must also provide --ligand-smiles or --ligand-ccd")

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
        result = run_affinity_prediction(
            input_file=args.input,
            protein_sequence=args.protein_seq,
            ligand_smiles=args.ligand_smiles,
            ligand_ccd=args.ligand_ccd,
            output_dir=args.output,
            config=config,
            **cli_overrides
        )

        if result["success"]:
            print(f"✅ Affinity prediction completed!")
            print(f"   Output directory: {result['output_dir']}")

            # Show affinity values
            if result["result"]["affinity_values"]:
                print("   Affinity results:")
                for key, value in result["result"]["affinity_values"].items():
                    print(f"     {key}: {value}")

            # Show output files
            if result["output_files"]["structures"]:
                print("   Structure files:")
                for f in result["output_files"]["structures"]:
                    print(f"     - {f}")

            if result["output_files"]["affinity"]:
                print("   Affinity files:")
                for f in result["output_files"]["affinity"]:
                    print(f"     - {f}")

            if result["result"]["protein_length"]:
                print(f"   Protein length: {result['result']['protein_length']} residues")

            if result["result"]["ligand_input"]:
                print(f"   Ligand ({result['result']['ligand_type']}): {result['result']['ligand_input']}")

        else:
            print(f"❌ Affinity prediction failed!")
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