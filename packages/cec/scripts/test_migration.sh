#!/bin/bash

# Simple script to test ComfyUI environment detection and recreation
# Usage: ./scripts/test_migration.sh test_name [--original original_env_name] [--replicated replicated_env_name]
# Example: ./scripts/test_migration.sh test_3
# Example: ./scripts/test_migration.sh test_3 --original test_1
# Example: ./scripts/test_migration.sh test_4 --replicated test_3

if [ $# -eq 0 ]; then
    echo "Usage: $0 <test_name> [--original <original_env_name>] [--replicated <replicated_env_name>]"
    echo "Example: $0 test_3"
    echo "Example: $0 test_3 --original test_1"
    echo "Example: $0 test_4 --replicated test_3"
    exit 1
fi

TEST_NAME="$1"
SOURCE_ENV="$1"  # Default to same as test name
SOURCE_TYPE="original"  # Default to original

# Parse optional arguments
shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --original)
            SOURCE_ENV="$2"
            SOURCE_TYPE="original"
            shift 2
            ;;
        --replicated)
            SOURCE_ENV="$2"
            SOURCE_TYPE="replicated"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🔍 Starting migration test for: $TEST_NAME"
if [ "$SOURCE_ENV" != "$TEST_NAME" ] || [ "$SOURCE_TYPE" != "original" ]; then
    echo "   Using source environment: $SOURCE_ENV (from $SOURCE_TYPE)"
fi

# Step 1: Detect the environment
echo "📋 Step 1: Detecting environment..."
uv run cec detect ".test_data/environments/${SOURCE_TYPE}/${SOURCE_ENV}/ComfyUI/" \
    --python ".test_data/environments/${SOURCE_TYPE}/${SOURCE_ENV}/.venv/bin/python" \
    --validate-registry \
    --output-dir ".test_data/manifests/${TEST_NAME}/"

if [ $? -ne 0 ]; then
    echo "❌ Detection failed for $TEST_NAME"
    exit 1
fi

echo ""

# Step 2: Recreate the environment
echo "🔄 Step 2: Recreating environment..."
uv run cec recreate \
    --uv-cache-path ".test_data/environments/uv_cache/" \
    --python-install-path ".test_data/environments/uv/python/" \
    ".test_data/manifests/${TEST_NAME}/comfyui_migration.json" \
    ".test_data/environments/replicated/${TEST_NAME}/"

if [ $? -ne 0 ]; then
    echo "❌ Recreation failed for $TEST_NAME"
    exit 1
fi

echo ""
echo "✅ Migration test completed successfully for: $TEST_NAME"