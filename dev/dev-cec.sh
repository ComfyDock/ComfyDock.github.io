#!/bin/bash
# dev/scripts/dev-cec.sh
# Development script for testing CEC in containers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEV_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$DEV_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build       Build the CEC development container"
    echo "  shell       Enter the CEC dev container shell"
    echo "  test        Run CEC tests in container"
    echo "  scan        Scan a test ComfyUI installation"
    echo "  recreate    Recreate from a manifest file"
    echo "  clean       Clean up containers and volumes"
    echo ""
    echo "Options:"
    echo "  --target PATH   Path to ComfyUI installation to scan"
    echo "  --manifest PATH Path to manifest file for recreation"
    echo "  --output PATH   Output path for scan results"
}

# Ensure docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}docker-compose is required but not installed.${NC}"
    exit 1
fi

cd "$DEV_DIR"

case "$1" in
    build)
        echo -e "${GREEN}Building CEC development container...${NC}"
        docker-compose -f docker-compose.yml build cec-dev
        ;;
    
    shell)
        echo -e "${GREEN}Starting CEC development shell...${NC}"
        docker-compose -f docker-compose.yml run --rm cec-dev
        ;;
    
    test)
        echo -e "${GREEN}Running CEC tests in container...${NC}"
        docker-compose -f docker-compose.yml run --rm cec-dev \
            bash -c "cd /workspace/cec && uv run pytest tests/"
        ;;
    
    scan)
        TARGET="${2:-/test-comfyui/default}"
        OUTPUT="${3:-/test-environments/scanned-manifest.json}"
        
        echo -e "${GREEN}Scanning ComfyUI installation at: $TARGET${NC}"
        docker-compose -f docker-compose.yml run --rm cec-dev \
            bash -c "cd /workspace/cec && uv run python -m comfydock_cec scan --target '$TARGET' --output '$OUTPUT'"
        ;;
    
    recreate)
        MANIFEST="${2:-/test-environments/scanned-manifest.json}"
        TARGET="${3:-/test-environments/recreated}"
        
        echo -e "${GREEN}Recreating environment from: $MANIFEST${NC}"
        echo -e "${GREEN}Target directory: $TARGET${NC}"
        
        docker-compose -f docker-compose.yml run --rm cec-dev \
            bash -c "cd /workspace/cec && uv run python -m comfydock_cec recreate --manifest '$MANIFEST' --target '$TARGET'"
        ;;
    
    clean)
        echo -e "${YELLOW}Cleaning up development containers...${NC}"
        docker-compose -f docker-compose.yml down -v
        ;;
    
    *)
        print_usage
        exit 1
        ;;
esac