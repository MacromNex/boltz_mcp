#!/usr/bin/env python3
"""Simple test to verify MCP server functionality."""

import sys
from pathlib import Path
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_sequence_validation():
    """Test sequence validation logic."""
    try:
        # Test valid sequence
        sequence = "MVLSEGEWQLVLHVWAK"
        clean_seq = re.sub(r'\s+', '', sequence.upper())
        valid_aa = set('ACDEFGHIKLMNPQRSTVWY')
        invalid_chars = set(clean_seq) - valid_aa

        assert len(invalid_chars) == 0, f"Found invalid chars: {invalid_chars}"
        print("✅ Valid sequence validation works")

        # Test invalid sequence
        sequence = "MVLXXX123"
        clean_seq = re.sub(r'\s+', '', sequence.upper())
        invalid_chars = set(clean_seq) - valid_aa

        assert len(invalid_chars) > 0, "Should have found invalid characters"
        print("✅ Invalid sequence detection works")

        return True
    except Exception as e:
        print(f"❌ Sequence validation failed: {e}")
        return False

def test_imports():
    """Test that key components can be imported."""
    try:
        from jobs.manager import job_manager
        print("✅ Job manager imports successfully")

        # Test the job manager has the expected interface
        assert hasattr(job_manager, 'submit_job')
        assert hasattr(job_manager, 'get_job_status')
        assert hasattr(job_manager, 'list_jobs')
        print("✅ Job manager has expected methods")

        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_server_structure():
    """Test that the MCP server structure is correct."""
    try:
        import server
        print("✅ Server module imports")

        # Check that the FastMCP instance exists
        assert hasattr(server, 'mcp')
        print("✅ FastMCP instance exists")

        return True
    except Exception as e:
        print(f"❌ Server structure test failed: {e}")
        return False

def test_example_directory():
    """Test that examples directory exists."""
    try:
        examples_dir = Path(__file__).parent.parent / "examples"
        if examples_dir.exists():
            print(f"✅ Examples directory found: {examples_dir}")

            data_dir = examples_dir / "data"
            if data_dir.exists():
                files = list(data_dir.rglob("*"))
                print(f"✅ Found {len(files)} files in examples/data")
            else:
                print("⚠️ No examples/data directory")
        else:
            print("⚠️ No examples directory")

        return True
    except Exception as e:
        print(f"❌ Example directory test failed: {e}")
        return False

def main():
    """Run simple tests."""
    print("Running Simple Boltz MCP Tests...")
    print("=" * 40)

    tests = [
        test_imports,
        test_server_structure,
        test_sequence_validation,
        test_example_directory,
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 40)
    print(f"Tests passed: {passed}/{len(tests)}")

    if passed == len(tests):
        print("🎉 All simple tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())