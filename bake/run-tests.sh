#!/bin/bash
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

# Run tests for the az-bake Azure CLI extension
#
# Usage:
#   ./run-tests.sh              - Run all tests
#   ./run-tests.sh --coverage   - Run with coverage report
#   ./run-tests.sh --html       - Generate HTML coverage report
#   ./run-tests.sh --parallel   - Run tests in parallel
#   ./run-tests.sh --install    - Install deps first
#   ./run-tests.sh tests/test_data.py - Run specific test file

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default values
COVERAGE=false
COVERAGE_HTML=false
PARALLEL=false
VERBOSE=false
INSTALL=false
TEST_PATH=""
MARKER=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --html)
            COVERAGE=true
            COVERAGE_HTML=true
            shift
            ;;
        --parallel|-p)
            PARALLEL=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --install|-i)
            INSTALL=true
            shift
            ;;
        --marker|-m)
            MARKER="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options] [test_path]"
            echo ""
            echo "Options:"
            echo "  --coverage, -c    Generate coverage report"
            echo "  --html            Generate HTML coverage report"
            echo "  --parallel, -p    Run tests in parallel"
            echo "  --verbose, -v     Verbose output"
            echo "  --install, -i     Install dependencies first"
            echo "  --marker, -m      Run tests with specific marker"
            echo "  --help, -h        Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                         Run all tests"
            echo "  $0 --coverage              Run with coverage"
            echo "  $0 tests/test_data.py      Run specific file"
            exit 0
            ;;
        *)
            TEST_PATH="$1"
            shift
            ;;
    esac
done

echo -e "${CYAN}========================================"
echo -e "  az-bake Test Runner"
echo -e "========================================${NC}"
echo ""

# Find Python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo -e "Using Python: ${PYTHON_CMD}"
$PYTHON_CMD --version

# Install dependencies if requested
if [ "$INSTALL" = true ]; then
    echo ""
    echo -e "${YELLOW}Installing development dependencies...${NC}"
    
    if [ -f "requirements-dev.txt" ]; then
        $PYTHON_CMD -m pip install -r requirements-dev.txt
    else
        $PYTHON_CMD -m pip install pytest pytest-cov pytest-mock pytest-xdist
    fi
    
    echo -e "${YELLOW}Installing az-bake in editable mode...${NC}"
    $PYTHON_CMD -m pip install -e .
    
    echo -e "${GREEN}Dependencies installed.${NC}"
    echo ""
fi

# Build pytest command
PYTEST_ARGS=()

# Add test path or default
if [ -n "$TEST_PATH" ]; then
    PYTEST_ARGS+=("$TEST_PATH")
else
    PYTEST_ARGS+=("tests/")
fi

# Coverage options
if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS+=("--cov=azext_bake" "--cov-report=term-missing")
    
    if [ "$COVERAGE_HTML" = true ]; then
        PYTEST_ARGS+=("--cov-report=html:htmlcov")
    fi
fi

# Parallel execution
if [ "$PARALLEL" = true ]; then
    PYTEST_ARGS+=("-n" "auto")
fi

# Verbose output
if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS+=("-vv")
else
    PYTEST_ARGS+=("-v")
fi

# Marker filter
if [ -n "$MARKER" ]; then
    PYTEST_ARGS+=("-m" "$MARKER")
fi

# Run tests
echo -e "${YELLOW}Running: pytest ${PYTEST_ARGS[*]}${NC}"
echo ""

set +e
$PYTHON_CMD -m pytest "${PYTEST_ARGS[@]}"
EXIT_CODE=$?
set -e

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================"
    echo -e "  All tests passed!"
    echo -e "========================================${NC}"
else
    echo ""
    echo -e "${RED}========================================"
    echo -e "  Some tests failed (exit code: $EXIT_CODE)"
    echo -e "========================================${NC}"
fi

# Show HTML coverage location
if [ "$COVERAGE_HTML" = true ] && [ -f "htmlcov/index.html" ]; then
    echo ""
    echo -e "${CYAN}Coverage report: $(pwd)/htmlcov/index.html${NC}"
fi

exit $EXIT_CODE
