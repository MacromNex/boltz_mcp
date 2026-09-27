# Test Prompts for Boltz MCP Integration

## Tool Discovery Tests

### Test 1: Basic Tool Discovery
**Prompt:** "What MCP tools are available? List them with their descriptions."

**Expected Response:** Should list all 13 Boltz tools with categories:
- Job management tools (5): get_job_status, get_job_result, get_job_log, cancel_job, list_jobs
- Sync tools (2): simple_structure_prediction, simple_affinity_prediction
- Submit tools (3): submit_structure_prediction, submit_affinity_prediction, submit_batch_structure_prediction
- Utility tools (3): validate_protein_sequence, validate_ligand_smiles, list_example_data

### Test 2: Specific Tool Details
**Prompt:** "Explain how to use the validate_protein_sequence tool, including all parameters."

**Expected Response:** Should provide parameter details and examples.

## Utility Tool Tests

### Test 3: List Example Data
**Prompt:** "Use the list_example_data tool to show what example files are available."

**Expected Response:** Should return JSON with 12+ files including .yaml, .fasta, etc.

### Test 4: Validate Protein Sequence
**Prompt:** "Use validate_protein_sequence to validate this sequence: MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD"

**Expected Response:** Should return valid=True, length=63, composition analysis

### Test 5: Validate Invalid Sequence
**Prompt:** "Use validate_protein_sequence to check this invalid sequence: MVTXYZ123"

**Expected Response:** Should return valid=False with invalid characters listed

### Test 6: Validate SMILES
**Prompt:** "Use validate_ligand_smiles to validate this SMILES string: N[C@@H](Cc1ccc(O)cc1)C(=O)O"

**Expected Response:** Should return valid=True with molecular properties if RDKit available

## Error Handling Tests

### Test 7: Non-existent File
**Prompt:** "Try using simple_structure_prediction with input_file='/nonexistent/file.yaml'"

**Expected Response:** Should return error status with "File not found" message

### Test 8: Missing Parameters
**Prompt:** "Try using simple_structure_prediction without any input_file or sequence parameters"

**Expected Response:** Should return error about missing required parameters

### Test 9: Invalid Affinity Parameters
**Prompt:** "Try using simple_affinity_prediction with only protein_sequence='MVTPEGNVSLVDESLLVGVTDEDRAV' but no ligand information"

**Expected Response:** Should return error about missing ligand information

## Submit API Workflow Tests

### Test 10: Submit Job
**Prompt:** "Submit a structure prediction job using submit_structure_prediction with sequence='MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD' and job_name='test_structure'"

**Expected Response:** Should return job_id and status="submitted"

### Test 11: Check Job Status
**Prompt:** "After submitting a job, check its status using get_job_status with the job_id from the previous response"

**Expected Response:** Should return status (pending/running/completed) with timestamps

### Test 12: List All Jobs
**Prompt:** "Use list_jobs to show all submitted jobs"

**Expected Response:** Should return array of jobs with their current status

### Test 13: Filter Jobs by Status
**Prompt:** "Use list_jobs with status='pending' to show only pending jobs"

**Expected Response:** Should return filtered list

### Test 14: Get Job Logs
**Prompt:** "Use get_job_log with a job_id to show the last 20 lines of logs"

**Expected Response:** Should return log lines and total count

## Real-World Scenario Tests

### Test 15: Complete Structure Prediction Workflow
**Prompt:** "I want to predict the structure for this protein sequence: MVTPEGNVSLVDESLLVGVTDEDRAV. First validate the sequence, then submit a structure prediction job, and check the status."

**Expected Response:** Should:
1. Validate sequence successfully
2. Submit job and return job_id
3. Check status of submitted job

### Test 16: Affinity Prediction with YAML
**Prompt:** "Use simple_affinity_prediction with input_file='examples/data/affinity.yaml' to predict protein-ligand binding"

**Expected Response:** Should process the YAML file and return affinity prediction results

### Test 17: Batch Processing
**Prompt:** "Submit a batch structure prediction for these sequences: ['MVTPEGNVSL', 'QLEDSEVEAVAKGL'] using submit_batch_structure_prediction"

**Expected Response:** Should submit batch job with job_id

### Test 18: Error Recovery
**Prompt:** "Submit a job and if it fails, show me the error log and suggest what might be wrong"

**Expected Response:** Should handle job submission, check status, and provide logs if failed

## Performance Tests

### Test 19: Sync Tool Response Time
**Prompt:** "Time how long it takes to run validate_protein_sequence on a 100 amino acid sequence"

**Expected Response:** Should complete in < 1 second

### Test 20: Job Management Speed
**Prompt:** "Submit 3 jobs quickly and then list them all to verify they're tracked properly"

**Expected Response:** Should handle multiple rapid submissions correctly

## Edge Cases

### Test 21: Empty Sequence
**Prompt:** "Try validate_protein_sequence with an empty sequence"

**Expected Response:** Should handle gracefully with error message

### Test 22: Very Long Sequence
**Prompt:** "Try submitting a structure prediction for a 1000+ amino acid sequence"

**Expected Response:** Should submit successfully for long-running processing

### Test 23: Special Characters
**Prompt:** "Try validate_protein_sequence with sequence containing spaces and newlines"

**Expected Response:** Should clean and validate properly

### Test 24: Cancel Job
**Prompt:** "Submit a job and then immediately cancel it using cancel_job"

**Expected Response:** Should successfully cancel the job

## Integration Verification

### Test 25: Tool Availability Check
**Prompt:** "Verify that all 13 expected Boltz tools are available and callable"

**Expected Response:** All tools should be discoverable and functional

### Test 26: Path Resolution
**Prompt:** "Use examples/data/prot.yaml (relative path) as input to simple_structure_prediction"

**Expected Response:** Should resolve path correctly and process file

### Test 27: Output Directory Creation
**Prompt:** "Use simple_structure_prediction with output_dir='/tmp/boltz_test' to verify directory creation"

**Expected Response:** Should create output directory and save results

### Test 28: Configuration Options
**Prompt:** "Test simple_structure_prediction with use_msa_server=False and output_format='cif'"

**Expected Response:** Should respect configuration options

## Status Validation

✅ **Pass Criteria:**
- All tools discoverable and callable
- Sync tools respond within 30 seconds
- Submit API returns valid job_ids
- Job management tools work correctly
- Error handling provides helpful messages
- Real-world scenarios complete successfully

❌ **Failure Indicators:**
- Tools not found or not callable
- Timeouts on sync operations
- Invalid job_id format
- Missing error handling
- Path resolution failures