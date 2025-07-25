# Integration Tests

This directory contains integration tests that test the full ComfyUI Environment Detector workflow.

## Tests

### test_cli_integration.py

Tests the complete detect -> recreate -> detect cycle using CLI commands:

1. **Detect**: Runs `cec detect` on an original ComfyUI environment to generate a migration manifest
2. **Recreate**: Runs `cec recreate` to create a new environment from the manifest  
3. **Detect Again**: Runs `cec detect` on the recreated environment to generate a new manifest
4. **Compare**: Compares the two manifests to ensure environment replication was successful

The test handles expected differences like PyTorch CUDA version suffixes (e.g., `2.7.1` vs `2.7.1+cu126`).

## Running Integration Tests

```bash
# Run all integration tests
uv run python -m pytest tests/integration/ -v

# Run specific test
uv run python -m pytest tests/integration/test_cli_integration.py::TestCLIIntegration::test_detect_recreate_detect_cycle -xvs
```

## Test Data

Tests use the existing test data in `test_data/environments/original/test_1/` as the source environment for replication.

## Duration

Integration tests take longer to run (15-30 seconds) as they involve:
- Creating virtual environments
- Installing Python packages
- Running full environment detection and recreation cycles