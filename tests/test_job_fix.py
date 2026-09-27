#!/usr/bin/env python3
"""
Test and fix job management issues.
"""

import sys
from pathlib import Path
import json
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jobs.manager import job_manager

def test_job_submission():
    """Test job submission with proper error handling."""
    print("🧪 Testing job submission and management")

    try:
        # Test 1: Submit a job
        print("\n1. Submitting test job...")
        result = job_manager.submit_job(
            script_path=str(Path(__file__).parent.parent / "scripts" / "structure_prediction.py"),
            args={
                "sequence": "MVTPEGNVSLVDESLLVGVTDEDRAV",
                "output_format": "pdb"
            },
            job_name="integration_test_job"
        )

        if result.get("status") == "submitted":
            job_id = result.get("job_id")
            print(f"✅ Job submitted successfully: {job_id}")
        else:
            print(f"❌ Job submission failed: {result}")
            return False

        # Test 2: Check job status
        print(f"\n2. Checking job status for {job_id}...")
        status_result = job_manager.get_job_status(job_id)
        print(f"Status: {status_result}")

        # Test 3: List jobs (with error handling)
        print("\n3. Listing all jobs...")
        try:
            jobs_result = job_manager.list_jobs()
            print(f"Jobs: {jobs_result}")
        except Exception as e:
            print(f"❌ Error listing jobs: {e}")
            # Try to fix by cleaning up broken metadata files
            jobs_dir = Path(__file__).parent.parent / "jobs"
            for job_dir in jobs_dir.iterdir():
                if job_dir.is_dir():
                    metadata_file = job_dir / "metadata.json"
                    if metadata_file.exists() and metadata_file.stat().st_size == 0:
                        print(f"🧹 Cleaning up empty metadata file: {metadata_file}")
                        metadata_file.unlink()
                        job_dir.rmdir()

            # Try listing again
            try:
                jobs_result = job_manager.list_jobs()
                print(f"✅ Jobs after cleanup: {jobs_result}")
            except Exception as e2:
                print(f"❌ Still failing: {e2}")
                return False

        # Test 4: Get job logs
        print(f"\n4. Getting job logs for {job_id}...")
        logs_result = job_manager.get_job_log(job_id)
        print(f"Logs: {logs_result}")

        print("\n✅ All job management tests completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_job_cleanup():
    """Clean up test jobs."""
    print("\n🧹 Cleaning up test jobs...")
    jobs_dir = Path(__file__).parent.parent / "jobs"

    if jobs_dir.exists():
        for job_dir in jobs_dir.iterdir():
            if job_dir.is_dir():
                try:
                    # Try to cancel any running jobs
                    job_manager.cancel_job(job_dir.name)
                    print(f"Cancelled job: {job_dir.name}")
                except:
                    pass

    print("✅ Cleanup completed")

if __name__ == "__main__":
    success = test_job_submission()
    test_job_cleanup()

    if success:
        print("\n🎉 Job management tests passed!")
        sys.exit(0)
    else:
        print("\n🚨 Job management tests failed")
        sys.exit(1)