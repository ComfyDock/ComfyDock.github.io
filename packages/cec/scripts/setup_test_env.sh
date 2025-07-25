#!/bin/bash

# Script to create a new ComfyUI test environment
# Usage: ./scripts/setup_test_env.sh <test_environment_name>
# Example: ./scripts/setup_test_env.sh test_4

set -e  # Exit on any error

if [ $# -eq 0 ]; then
    echo "Usage: $0 <test_environment_name>"
    echo "Example: $0 test_4"
    exit 1
fi

TEST_ENV_NAME="$1"
ORIGINAL_DIR=".test_data/environments/original"
TEST_ENV_PATH="$ORIGINAL_DIR/$TEST_ENV_NAME"

# Check if test environment already exists
if [ -d "$TEST_ENV_PATH" ]; then
    echo "Error: Test environment '$TEST_ENV_NAME' already exists at $TEST_ENV_PATH"
    exit 1
fi

echo "Creating test environment: $TEST_ENV_NAME"
echo "Location: $TEST_ENV_PATH"
echo ""

# Create the test environment directory
mkdir -p "$TEST_ENV_PATH"
cd "$TEST_ENV_PATH"

echo "Step 1: Cloning ComfyUI..."
git clone https://github.com/comfyanonymous/ComfyUI.git
echo ""

echo "Step 2: Creating Python virtual environment..."
uv venv --python 3.12 .venv
echo ""

echo "Step 3: Installing ComfyUI requirements..."
uv pip install -r ComfyUI/requirements.txt
echo ""

echo "Step 4: Cloning ComfyUI-Manager..."
cd ComfyUI/custom_nodes
git clone https://github.com/Comfy-Org/ComfyUI-Manager.git
cd ../..
echo ""

echo "Step 5: Installing ComfyUI-Manager requirements..."
uv pip install -r ComfyUI/custom_nodes/ComfyUI-Manager/requirements.txt
echo ""

echo "✅ Test environment '$TEST_ENV_NAME' created successfully!"
echo ""
echo "To run ComfyUI in this environment, use:"
echo "  ./scripts/run_test_env.sh --original $TEST_ENV_NAME"
echo ""
echo "Environment location: $TEST_ENV_PATH"
echo "Python executable: $TEST_ENV_PATH/.venv/bin/python"
echo "ComfyUI main: $TEST_ENV_PATH/ComfyUI/main.py"