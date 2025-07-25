#!/bin/bash

# Script to run ComfyUI from a specific test environment
# Usage: ./scripts/run_test_env.sh [--original] <test_environment_name>
# Examples: 
#   ./scripts/run_test_env.sh test_5
#   ./scripts/run_test_env.sh --original test_3

# Parse arguments
USE_ORIGINAL=false
if [ "$1" = "--original" ]; then
    USE_ORIGINAL=true
    shift
fi

if [ $# -eq 0 ]; then
    echo "Usage: $0 [--original] <test_environment_name>"
    echo "Examples:"
    echo "  $0 test_5"
    echo "  $0 --original test_3"
    exit 1
fi

TEST_ENV_NAME="$1"

# Determine the base path based on the --original flag
if [ "$USE_ORIGINAL" = true ]; then
    TEST_ENV_PATH=".test_data/environments/original/$TEST_ENV_NAME"
else
    TEST_ENV_PATH=".test_data/environments/replicated/$TEST_ENV_NAME"
fi
PYTHON_PATH="$TEST_ENV_PATH/.venv/bin/python"
COMFYUI_MAIN="$TEST_ENV_PATH/ComfyUI/main.py"

# Check if the test environment exists
if [ ! -d "$TEST_ENV_PATH" ]; then
    echo "Error: Test environment '$TEST_ENV_NAME' not found at $TEST_ENV_PATH"
    exit 1
fi

# Check if the Python executable exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Python executable not found at $PYTHON_PATH"
    exit 1
fi

# Check if ComfyUI main.py exists
if [ ! -f "$COMFYUI_MAIN" ]; then
    echo "Error: ComfyUI main.py not found at $COMFYUI_MAIN"
    exit 1
fi

echo "Running ComfyUI from test environment: $TEST_ENV_NAME"
echo "Python: $PYTHON_PATH"
echo "ComfyUI: $COMFYUI_MAIN"
echo ""

# Execute the command
exec "$PYTHON_PATH" "$COMFYUI_MAIN" "${@:2}"