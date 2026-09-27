#!/usr/bin/env python3
"""
Simple integration test for Boltz MCP server tools.
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import tool functions
from server import (
    list_example_data,
    validate_protein_sequence,
    validate_ligand_smiles,
    simple_structure_prediction,
    simple_affinity_prediction,
    submit_structure_prediction,
    list_jobs
)

def test_tool(tool_func, name, description, expect_error=False, **kwargs):
    """Test a single tool.
    
    Args:
        tool_func: The tool function to test
        name: Name of the tool
        description: Description of the test
        expect_error: If True, test expects an error response (for error handling tests)
        **kwargs: Arguments to pass to the tool
    """
    print(f"\n🧪 Testing {name}: {description}")
    print(f"   Input: {kwargs}")

    try:
        # FastMCP @mcp.tool() decorator wraps functions in FunctionTool objects
        # Access the underlying function via .fn attribute
        fn = getattr(tool_func, 'fn', tool_func)
        result = fn(**kwargs)

        if result.get("status") == "error":
            if expect_error:
                print(f"✅ PASSED (expected error): {result.get('error', 'Unknown error')}")
                return True
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
                return False
        elif result.get("status") == "success":
            if expect_error:
                print(f"❌ FAILED: Expected error but got success")
                return False
            print(f"✅ PASSED: {description}")
            if "files" in result:
                print(f"   Found {len(result['files'])} files")
            if "sequence_length" in result:
                print(f"   Sequence length: {result['sequence_length']}")
            if "valid" in result:
                print(f"   Valid: {result['valid']}")
            if "job_id" in result:
                print(f"   Job ID: {result['job_id']}")
            return True
        else:
            print(f"✅ PASSED: {description}")
            return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("🧪 Starting Simple Boltz MCP Tests")

    examples_dir = Path(__file__).parent.parent / "examples" / "data"
    print(f"📁 Examples directory: {examples_dir}")

    results = []

    # Test 1: List example data
    results.append(test_tool(
        list_example_data,
        "list_example_data",
        "List available example files"
    ))

    # Test 2: Validate protein sequence
    results.append(test_tool(
        validate_protein_sequence,
        "validate_protein_sequence",
        "Validate protein sequence",
        sequence="MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD"
    ))

    # Test 3: Validate invalid protein sequence
    results.append(test_tool(
        validate_protein_sequence,
        "validate_protein_sequence",
        "Validate invalid protein sequence",
        sequence="MVTXYZ123"
    ))

    # Test 4: Validate ligand SMILES
    results.append(test_tool(
        validate_ligand_smiles,
        "validate_ligand_smiles",
        "Validate ligand SMILES",
        smiles="N[C@@H](Cc1ccc(O)cc1)C(=O)O"
    ))

    # Test 5: Test error handling with non-existent file (expects error)
    results.append(test_tool(
        simple_structure_prediction,
        "simple_structure_prediction",
        "Test error handling with non-existent file",
        expect_error=True,
        input_file="/nonexistent/file.yaml"
    ))

    # Test 6: Test missing required parameters (expects error)
    results.append(test_tool(
        simple_structure_prediction,
        "simple_structure_prediction",
        "Test missing required parameters",
        expect_error=True
        # No input_file or sequence provided
    ))

    # Test 7: Submit structure prediction job
    results.append(test_tool(
        submit_structure_prediction,
        "submit_structure_prediction",
        "Submit structure prediction job",
        sequence="MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD",
        job_name="test_job"
    ))

    # Test 8: List jobs
    results.append(test_tool(
        list_jobs,
        "list_jobs",
        "List all jobs"
    ))

    # Summary
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\n📊 Test Summary:")
    print(f"   Total: {total}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Pass Rate: {passed/total*100:.1f}%")

    # Save results
    report = {
        "test_date": datetime.now().isoformat(),
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{passed/total*100:.1f}%"
    }

    results_file = Path(__file__).parent.parent / "reports" / "simple_test_results.json"
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"💾 Results saved to: {results_file}")

    if failed > 0:
        print("🚨 Some tests failed")
        return 1
    else:
        print("🎉 All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())