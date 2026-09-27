#!/usr/bin/env python3
"""
Integration test runner for Boltz MCP server.
Tests all tools with various inputs to ensure they work correctly.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import all tool functions directly
from server import (
    list_example_data,
    validate_protein_sequence,
    validate_ligand_smiles,
    simple_structure_prediction,
    simple_affinity_prediction,
    submit_structure_prediction,
    submit_affinity_prediction,
    submit_batch_structure_prediction,
    list_jobs,
    get_job_status,
    get_job_result,
    get_job_log,
    cancel_job
)

class BoltzMCPTester:
    def __init__(self):
        self.results = {
            "test_date": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        self.examples_dir = Path(__file__).parent.parent / "examples" / "data"

    def run_tool_test(self, tool_func, tool_name: str, description: str, **kwargs):
        """Run a single tool test and capture results."""
        print(f"Testing {tool_name}: {description}")
        try:
            # Call the tool function directly
            result = tool_func(**kwargs)

            self.results["tests"][f"{tool_name}_{len(self.results['tests'])}"] = {
                "tool": tool_name,
                "description": description,
                "status": "passed" if result.get("status") != "error" else "failed",
                "input": kwargs,
                "output": result
            }
            if result.get("status") == "error":
                print(f"❌ FAILED: {description} - {result.get('error', 'Unknown error')}")
                return False
            else:
                print(f"✅ PASSED: {description}")
                return True

        except Exception as e:
            self.results["tests"][f"{tool_name}_{len(self.results['tests'])}"] = {
                "tool": tool_name,
                "description": description,
                "status": "error",
                "input": kwargs,
                "error": str(e)
            }
            print(f"❌ ERROR: {description} - {e}")
            return False

    def test_utility_tools(self):
        """Test utility tools."""
        print("\n=== Testing Utility Tools ===")

        # Test example data listing
        self.run_tool_test(
            list_example_data,
            "list_example_data",
            "List available example files"
        )

        # Test protein sequence validation
        self.run_tool_test(
            validate_protein_sequence,
            "validate_protein_sequence",
            "Validate a protein sequence",
            sequence="QLEDSEVEAVAKGLEEMYANGVTEDNFKNYVKNNFAQQEISSVEEELNVNISDSCVANKIKDEFFAMISISAIVKAAQKKAWKELAVTVLRFAKANGLKTNAIIVAGQLALWAVQCG"
        )

        # Test invalid protein sequence
        self.run_tool_test(
            validate_protein_sequence,
            "validate_protein_sequence",
            "Validate invalid protein sequence",
            sequence="QLEDSEVXYZ123"  # Contains invalid amino acids
        )

        # Test ligand SMILES validation
        self.run_tool_test(
            validate_ligand_smiles,
            "validate_ligand_smiles",
            "Validate ligand SMILES",
            smiles="N[C@@H](Cc1ccc(O)cc1)C(=O)O"  # Tyrosine
        )

        # Test invalid SMILES
        self.run_tool_test(
            validate_ligand_smiles,
            "validate_ligand_smiles",
            "Validate invalid SMILES",
            smiles="C1CCCC(invalid)CC1"
        )

    async def test_sync_tools(self):
        """Test synchronous tools with real data."""
        print("\n=== Testing Sync Tools ===")

        # Test simple structure prediction with YAML input
        prot_yaml = str(self.examples_dir / "prot.yaml")
        await self.run_tool_test(
            "simple_structure_prediction",
            "Structure prediction with YAML input",
            input_file=prot_yaml,
            output_dir="/tmp/boltz_test_structure"
        )

        # Test simple structure prediction with sequence
        await self.run_tool_test(
            "simple_structure_prediction",
            "Structure prediction with sequence",
            sequence="MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD",
            output_dir="/tmp/boltz_test_sequence"
        )

        # Test affinity prediction with YAML
        affinity_yaml = str(self.examples_dir / "affinity.yaml")
        await self.run_tool_test(
            "simple_affinity_prediction",
            "Affinity prediction with YAML input",
            input_file=affinity_yaml,
            output_dir="/tmp/boltz_test_affinity"
        )

        # Test affinity prediction with direct inputs
        await self.run_tool_test(
            "simple_affinity_prediction",
            "Affinity prediction with direct inputs",
            protein_sequence="MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD",
            ligand_smiles="N[C@@H](Cc1ccc(O)cc1)C(=O)O",
            output_dir="/tmp/boltz_test_direct"
        )

    async def test_submit_tools(self):
        """Test submit tools."""
        print("\n=== Testing Submit Tools ===")

        # Test submit structure prediction
        job_result = await self.run_tool_test(
            "submit_structure_prediction",
            "Submit structure prediction job",
            sequence="MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD",
            job_name="test_structure_job"
        )

        # If job was submitted, test job management tools
        if job_result:
            # Give time for job to start
            await asyncio.sleep(1)

            # Test list jobs
            await self.run_tool_test(
                "list_jobs",
                "List all jobs"
            )

            # Test list jobs with filter
            await self.run_tool_test(
                "list_jobs",
                "List pending jobs",
                status="pending"
            )

        # Test submit affinity prediction
        await self.run_tool_test(
            "submit_affinity_prediction",
            "Submit affinity prediction job",
            protein_sequence="MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD",
            ligand_smiles="N[C@@H](Cc1ccc(O)cc1)C(=O)O",
            job_name="test_affinity_job"
        )

        # Test batch submission
        await self.run_tool_test(
            "submit_batch_structure_prediction",
            "Submit batch structure prediction",
            sequences=[
                "MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD",
                "QLEDSEVEAVAKGLEEMYANGVTEDNFKNYVKNNFAQQEISSVEEELNVNISDSCVANKIKDEFFAMISISAIVKAAQKKAWKELAVTVLRFAKANGLKTNAIIVAGQLALWAVQCG"
            ],
            job_name="test_batch_job"
        )

    async def test_error_handling(self):
        """Test error handling with invalid inputs."""
        print("\n=== Testing Error Handling ===")

        # Test with non-existent file
        await self.run_tool_test(
            "simple_structure_prediction",
            "Test with non-existent file",
            input_file="/nonexistent/file.yaml"
        )

        # Test with missing required parameters
        await self.run_tool_test(
            "simple_structure_prediction",
            "Test missing required parameters"
            # No input_file or sequence provided
        )

        # Test affinity prediction missing ligand
        await self.run_tool_test(
            "simple_affinity_prediction",
            "Test affinity prediction missing ligand",
            protein_sequence="MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD"
            # No ligand_smiles or ligand_ccd provided
        )

    async def run_all_tests(self):
        """Run all tests."""
        print("🧪 Starting Boltz MCP Server Integration Tests")
        print(f"📁 Examples directory: {self.examples_dir}")

        # Test each category
        await self.test_utility_tools()
        await self.test_sync_tools()
        await self.test_submit_tools()
        await self.test_error_handling()

        # Calculate summary
        total_tests = len(self.results["tests"])
        passed = sum(1 for t in self.results["tests"].values() if t["status"] == "passed")
        failed = sum(1 for t in self.results["tests"].values() if t["status"] == "failed")
        errors = sum(1 for t in self.results["tests"].values() if t["status"] == "error")

        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": f"{passed/total_tests*100:.1f}%" if total_tests > 0 else "N/A"
        }

        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   🚨 Errors: {errors}")
        print(f"   📈 Pass Rate: {self.results['summary']['pass_rate']}")

        return self.results

async def main():
    tester = BoltzMCPTester()
    results = await tester.run_all_tests()

    # Save results
    results_file = Path(__file__).parent.parent / "reports" / "step7_integration_test_results.json"
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: {results_file}")

    # Return exit code based on results
    if results["summary"]["failed"] > 0 or results["summary"]["errors"] > 0:
        sys.exit(1)
    else:
        print("🎉 All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())