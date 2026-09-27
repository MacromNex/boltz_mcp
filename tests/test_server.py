#!/usr/bin/env python3
"""Test script for the Boltz MCP server."""

import sys
from pathlib import Path
import subprocess
import time

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_server_import():
    """Test that the server can be imported without errors."""
    try:
        import server
        print("✅ Server imports successfully")
        return True
    except Exception as e:
        print(f"❌ Server import failed: {e}")
        return False

def test_job_manager():
    """Test basic job manager functionality."""
    try:
        from jobs.manager import job_manager

        # Test list_jobs
        result = job_manager.list_jobs()
        assert result["status"] == "success"
        print("✅ Job manager works")
        return True
    except Exception as e:
        print(f"❌ Job manager test failed: {e}")
        return False

def test_validation_tools():
    """Test validation tools."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        import server

        # Test protein sequence validation directly
        result = server.validate_protein_sequence("MVLSEGEWQLVLHVWAK")
        assert result["status"] == "success"
        assert result["valid"] == True
        print("✅ Protein sequence validation works")

        # Test invalid sequence
        result = server.validate_protein_sequence("MVLXXX123")
        assert result["status"] == "success"
        assert result["valid"] == False
        print("✅ Invalid protein sequence detection works")

        return True
    except Exception as e:
        print(f"❌ Validation tools test failed: {e}")
        return False

def test_example_data():
    """Test example data listing."""
    try:
        import server

        result = server.list_example_data()
        assert result["status"] == "success"
        print("✅ Example data listing works")
        return True
    except Exception as e:
        print(f"❌ Example data test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Boltz MCP Server...")
    print("=" * 50)

    tests = [
        test_server_import,
        test_job_manager,
        test_validation_tools,
        test_example_data,
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")

    if passed == len(tests):
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())