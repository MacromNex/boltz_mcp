"""MCP Server for Boltz

Provides both synchronous and asynchronous (submit) APIs for protein structure and affinity prediction.
"""

from fastmcp import FastMCP
from pathlib import Path
from typing import Optional, List
import sys

# Setup paths
SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_ROOT = SCRIPT_DIR.parent
SCRIPTS_DIR = MCP_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from jobs.manager import job_manager
from loguru import logger

# Create MCP server
mcp = FastMCP("boltz")

# ==============================================================================
# Job Management Tools (for async operations)
# ==============================================================================

@mcp.tool()
def get_job_status(job_id: str) -> dict:
    """
    Get the status of a submitted job.

    Args:
        job_id: The job ID returned from a submit_* function

    Returns:
        Dictionary with job status, timestamps, and any errors
    """
    return job_manager.get_job_status(job_id)

@mcp.tool()
def get_job_result(job_id: str) -> dict:
    """
    Get the results of a completed job.

    Args:
        job_id: The job ID of a completed job

    Returns:
        Dictionary with the job results or error if not completed
    """
    return job_manager.get_job_result(job_id)

@mcp.tool()
def get_job_log(job_id: str, tail: int = 50) -> dict:
    """
    Get log output from a running or completed job.

    Args:
        job_id: The job ID to get logs for
        tail: Number of lines from end (default: 50, use 0 for all)

    Returns:
        Dictionary with log lines and total line count
    """
    return job_manager.get_job_log(job_id, tail)

@mcp.tool()
def cancel_job(job_id: str) -> dict:
    """
    Cancel a running job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Success or error message
    """
    return job_manager.cancel_job(job_id)

@mcp.tool()
def list_jobs(status: Optional[str] = None) -> dict:
    """
    List all submitted jobs.

    Args:
        status: Filter by status (pending, running, completed, failed, cancelled)

    Returns:
        List of jobs with their status
    """
    return job_manager.list_jobs(status)

# ==============================================================================
# Synchronous Tools (for fast operations < 10 min)
# ==============================================================================

@mcp.tool()
def simple_structure_prediction(
    input_file: Optional[str] = None,
    sequence: Optional[str] = None,
    output_dir: Optional[str] = None,
    use_msa_server: bool = True,
    output_format: str = "pdb",
    accelerator: str = "gpu"
) -> dict:
    """
    Generate protein structure predictions using Boltz (fast mode).

    Fast operation that completes in ~5-10 minutes. Use this for single structure prediction.

    Args:
        input_file: Path to input YAML file (mutually exclusive with sequence)
        sequence: Protein amino acid sequence (mutually exclusive with input_file)
        output_dir: Directory to save output files (default: ./boltz_structure_output)
        use_msa_server: Use MSA server for better accuracy (default: True)
        output_format: Output format - pdb or cif (default: pdb)
        accelerator: Accelerator backend - gpu, cpu, or tpu (default: gpu)

    Returns:
        Dictionary with generated structures and metadata
    """
    from structure_prediction import run_structure_prediction

    try:
        result = run_structure_prediction(
            input_file=input_file,
            sequence=sequence,
            output_dir=output_dir,
            use_msa_server=use_msa_server,
            output_format=output_format,
            accelerator=accelerator
        )
        return {"status": "success", **result}
    except FileNotFoundError as e:
        return {"status": "error", "error": f"File not found: {e}"}
    except ValueError as e:
        return {"status": "error", "error": f"Invalid input: {e}"}
    except Exception as e:
        logger.error(f"Structure prediction failed: {e}")
        return {"status": "error", "error": str(e)}

@mcp.tool()
def simple_affinity_prediction(
    input_file: Optional[str] = None,
    protein_sequence: Optional[str] = None,
    ligand_smiles: Optional[str] = None,
    ligand_ccd: Optional[str] = None,
    output_dir: Optional[str] = None,
    use_msa_server: bool = True,
    output_format: str = "pdb",
    accelerator: str = "gpu"
) -> dict:
    """
    Predict protein-ligand binding affinity and structure using Boltz (fast mode).

    Fast operation that completes in ~8-15 minutes. Use this for simple affinity prediction.

    Args:
        input_file: Path to input YAML file (mutually exclusive with sequence/ligand params)
        protein_sequence: Protein amino acid sequence
        ligand_smiles: Ligand SMILES string
        ligand_ccd: Ligand CCD code (alternative to SMILES)
        output_dir: Directory to save output files (default: ./boltz_affinity_output)
        use_msa_server: Use MSA server for better accuracy (default: True)
        output_format: Output format - pdb or cif (default: pdb)
        accelerator: Accelerator backend - gpu, cpu, or tpu (default: gpu)

    Returns:
        Dictionary with affinity predictions and metadata
    """
    from affinity_prediction import run_affinity_prediction

    try:
        result = run_affinity_prediction(
            input_file=input_file,
            protein_sequence=protein_sequence,
            ligand_smiles=ligand_smiles,
            ligand_ccd=ligand_ccd,
            output_dir=output_dir,
            use_msa_server=use_msa_server,
            output_format=output_format,
            accelerator=accelerator
        )
        return {"status": "success", **result}
    except FileNotFoundError as e:
        return {"status": "error", "error": f"File not found: {e}"}
    except ValueError as e:
        return {"status": "error", "error": f"Invalid input: {e}"}
    except Exception as e:
        logger.error(f"Affinity prediction failed: {e}")
        return {"status": "error", "error": str(e)}

# ==============================================================================
# Submit Tools (for long-running operations > 10 min)
# ==============================================================================

@mcp.tool()
def submit_structure_prediction(
    input_file: Optional[str] = None,
    sequence: Optional[str] = None,
    output_dir: Optional[str] = None,
    use_msa_server: bool = True,
    use_potentials: bool = False,
    output_format: str = "pdb",
    accelerator: str = "gpu",
    job_name: Optional[str] = None
) -> dict:
    """
    Submit protein structure prediction for background processing.

    This operation may take >10 minutes for complex sequences. Returns a job_id for tracking.

    Args:
        input_file: Path to input YAML file (mutually exclusive with sequence)
        sequence: Protein amino acid sequence (mutually exclusive with input_file)
        output_dir: Directory for outputs
        use_msa_server: Use MSA server for better accuracy (default: True)
        use_potentials: Use inference-time potentials for better physics (default: False)
        output_format: Output format - pdb or cif (default: pdb)
        accelerator: Accelerator backend - gpu, cpu, or tpu (default: gpu)
        job_name: Optional name for tracking

    Returns:
        Dictionary with job_id. Use:
        - get_job_status(job_id) to check progress
        - get_job_result(job_id) to get results
        - get_job_log(job_id) to see logs
    """
    script_path = str(SCRIPTS_DIR / "structure_prediction.py")

    # Prepare arguments
    args = {
        "output_format": output_format,
        "accelerator": accelerator
    }

    # Add input source
    if input_file:
        args["input"] = input_file
    elif sequence:
        args["sequence"] = sequence
    else:
        return {"status": "error", "error": "Must provide either input_file or sequence"}

    # Add output directory
    if output_dir:
        args["output"] = output_dir

    # Add flags
    if not use_msa_server:
        args["no-msa-server"] = True
    if use_potentials:
        args["use-potentials"] = True

    return job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name or "structure_prediction"
    )

@mcp.tool()
def submit_affinity_prediction(
    input_file: Optional[str] = None,
    protein_sequence: Optional[str] = None,
    ligand_smiles: Optional[str] = None,
    ligand_ccd: Optional[str] = None,
    output_dir: Optional[str] = None,
    use_msa_server: bool = True,
    use_potentials: bool = False,
    output_format: str = "pdb",
    accelerator: str = "gpu",
    job_name: Optional[str] = None
) -> dict:
    """
    Submit protein-ligand affinity prediction for background processing.

    This operation may take >10 minutes for complex systems. Returns a job_id for tracking.

    Args:
        input_file: Path to input YAML file (mutually exclusive with sequence/ligand params)
        protein_sequence: Protein amino acid sequence
        ligand_smiles: Ligand SMILES string
        ligand_ccd: Ligand CCD code (alternative to SMILES)
        output_dir: Directory for outputs
        use_msa_server: Use MSA server for better accuracy (default: True)
        use_potentials: Use inference-time potentials for better physics (default: False)
        output_format: Output format - pdb or cif (default: pdb)
        accelerator: Accelerator backend - gpu, cpu, or tpu (default: gpu)
        job_name: Optional name for tracking

    Returns:
        Dictionary with job_id for tracking the affinity prediction job
    """
    script_path = str(SCRIPTS_DIR / "affinity_prediction.py")

    # Prepare arguments
    args = {
        "output_format": output_format,
        "accelerator": accelerator
    }

    # Add input source
    if input_file:
        args["input"] = input_file
    elif protein_sequence and (ligand_smiles or ligand_ccd):
        args["protein-seq"] = protein_sequence
        if ligand_smiles:
            args["ligand-smiles"] = ligand_smiles
        if ligand_ccd:
            args["ligand-ccd"] = ligand_ccd
    else:
        return {"status": "error", "error": "Must provide either input_file OR (protein_sequence + ligand)"}

    # Add output directory
    if output_dir:
        args["output"] = output_dir

    # Add flags
    if not use_msa_server:
        args["no-msa-server"] = True
    if use_potentials:
        args["use-potentials"] = True

    return job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name or "affinity_prediction"
    )

@mcp.tool()
def submit_batch_structure_prediction(
    sequences: List[str],
    output_dir: Optional[str] = None,
    use_msa_server: bool = True,
    use_potentials: bool = False,
    output_format: str = "pdb",
    accelerator: str = "gpu",
    job_name: Optional[str] = None
) -> dict:
    """
    Submit batch structure prediction for multiple protein sequences.

    This operation may take >30 minutes for large batches. Returns a job_id for tracking.

    Args:
        sequences: List of protein amino acid sequences to predict
        output_dir: Directory for outputs
        use_msa_server: Use MSA server for better accuracy (default: True)
        use_potentials: Use inference-time potentials for better physics (default: False)
        output_format: Output format - pdb or cif (default: pdb)
        accelerator: Accelerator backend - gpu, cpu, or tpu (default: gpu)
        job_name: Optional name for tracking

    Returns:
        Dictionary with job_id. Use get_job_status(job_id) to check progress
    """
    if not sequences:
        return {"status": "error", "error": "No sequences provided"}

    # Create a batch script call - we'll process them sequentially
    script_path = str(SCRIPTS_DIR / "structure_prediction.py")

    # For batch processing, we'll encode multiple sequences as JSON
    import json
    temp_sequences_file = f"/tmp/batch_sequences_{job_manager._generate_temp_id()}.json"

    with open(temp_sequences_file, 'w') as f:
        json.dump({"sequences": sequences}, f)

    args = {
        "batch-sequences-file": temp_sequences_file,
        "output_format": output_format,
        "accelerator": accelerator
    }

    if output_dir:
        args["output"] = output_dir
    if not use_msa_server:
        args["no-msa-server"] = True
    if use_potentials:
        args["use-potentials"] = True

    return job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name or f"batch_structure_{len(sequences)}_sequences"
    )

# ==============================================================================
# Utility Tools
# ==============================================================================

@mcp.tool()
def validate_protein_sequence(sequence: str) -> dict:
    """
    Validate a protein amino acid sequence.

    Args:
        sequence: Protein sequence to validate

    Returns:
        Dictionary with validation results and sequence info
    """
    try:
        import re

        # Remove whitespace
        clean_seq = re.sub(r'\s+', '', sequence.upper())

        # Valid amino acid codes
        valid_aa = set('ACDEFGHIKLMNPQRSTVWY')

        # Check for invalid characters
        invalid_chars = set(clean_seq) - valid_aa

        result = {
            "status": "success",
            "sequence_length": len(clean_seq),
            "valid": len(invalid_chars) == 0,
            "clean_sequence": clean_seq,
            "invalid_characters": list(invalid_chars) if invalid_chars else [],
            "composition": {}
        }

        # Calculate amino acid composition
        for aa in valid_aa:
            count = clean_seq.count(aa)
            if count > 0:
                result["composition"][aa] = {
                    "count": count,
                    "percentage": round((count / len(clean_seq)) * 100, 2)
                }

        return result

    except Exception as e:
        return {"status": "error", "error": str(e)}

@mcp.tool()
def validate_ligand_smiles(smiles: str) -> dict:
    """
    Validate a ligand SMILES string.

    Args:
        smiles: SMILES string to validate

    Returns:
        Dictionary with validation results and ligand info
    """
    try:
        # Try to parse with RDKit if available
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors

            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {
                    "status": "success",
                    "valid": False,
                    "error": "Invalid SMILES string - could not parse"
                }

            # Calculate basic properties
            return {
                "status": "success",
                "valid": True,
                "smiles": smiles,
                "canonical_smiles": Chem.MolToSmiles(mol),
                "molecular_weight": round(Descriptors.MolWt(mol), 2),
                "num_atoms": mol.GetNumAtoms(),
                "num_bonds": mol.GetNumBonds(),
                "num_rings": Chem.GetSSSR(mol),
                "rotatable_bonds": Descriptors.NumRotatableBonds(mol),
                "hbd": Descriptors.NumHDonors(mol),
                "hba": Descriptors.NumHAcceptors(mol)
            }

        except ImportError:
            # Basic validation without RDKit
            return {
                "status": "success",
                "valid": True,
                "smiles": smiles,
                "note": "Basic validation only - RDKit not available for detailed analysis"
            }

    except Exception as e:
        return {"status": "error", "error": str(e)}

@mcp.tool()
def list_example_data() -> dict:
    """
    List available example data files for testing.

    Returns:
        Dictionary with example file paths and descriptions
    """
    try:
        examples_dir = MCP_ROOT / "examples" / "data"

        examples = {
            "status": "success",
            "examples_dir": str(examples_dir),
            "files": []
        }

        if examples_dir.exists():
            for file in examples_dir.rglob("*"):
                if file.is_file():
                    rel_path = file.relative_to(examples_dir)
                    file_info = {
                        "path": str(file),
                        "relative_path": str(rel_path),
                        "name": file.name,
                        "size_bytes": file.stat().st_size,
                        "type": "unknown"
                    }

                    # Determine file type
                    if file.suffix in ['.yaml', '.yml']:
                        file_info["type"] = "yaml_input"
                    elif file.suffix in ['.pdb']:
                        file_info["type"] = "protein_structure"
                    elif file.suffix in ['.fasta', '.fa']:
                        file_info["type"] = "sequence"
                    elif file.suffix in ['.sdf', '.mol']:
                        file_info["type"] = "ligand"

                    examples["files"].append(file_info)

        return examples

    except Exception as e:
        return {"status": "error", "error": str(e)}

# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    mcp.run()