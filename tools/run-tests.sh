#!/bin/bash
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

# Run tests for the az-bake extension.
#
# Usage:
#   ./run-tests.sh [options] [test_path]
#
# Options:
#   --coverage, -c     Generate coverage report
#   --parallel, -p     Run tests in parallel
#   --verbose, -v      Run with verbose output
#   --filter, -k       Filter tests by name pattern
#   --markers, -m      Run tests matching markers (e.g., "not slow")
#   --failfast, -x     Stop on first failure
#   --html             Generate HTML coverage report
#   --help, -h         Show this help
#
# Examples:
#   ./run-tests.sh                           # Run all tests
#   ./run-tests.sh --coverage                # Run with coverage
#   ./run-tests.sh -k "test_validate"        # Filter by name
#   ./run-tests.sh -m "not slow"             # Exclude slow tests
#   ./run-tests.sh -p -c --html              # Parallel with HTML coverage

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m'

# Defaults
COVERAGE=false
PARALLEL=false
VERBOSE=false
FILTER=""
MARKERS=""
FAILFAST=false
HTML=false
TEST_PATH="tests/"

# Helper functions
write_header() {
    echo ""
    echo -e "${CYAN}========================================"
    echo -e "  $1"
    echo -e "========================================${NC}"
    echo ""
}

write_info() {
    echo -e "${YELLOW}$1${NC}"
}

write_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

show_help() {
    head -27 "$0" | tail -20
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            COVERAGE=true
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
        --filter|-k)
            FILTER="$2"
            shift 2
            ;;
        --markers|-m)
            MARKERS="$2"
            shift 2
            ;;
        --failfast|-x)
            FAILFAST=true
            shift
            ;;
        --html)
            HTML=true
            shift
            ;;
        --help|-h)
            show_help
            ;;
        -*)
            write_error "Unknown option: $1"
            show_help
            ;;
        *)
            TEST_PATH="$1"
            shift
            ;;
    esac
done

write_header "az-bake Test Runner"

# Get script directory and navigate to bake
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAKE_DIR="$(dirname "$SCRIPT_DIR")/bake"

if [ ! -d "$BAKE_DIR" ]; then
    write_error "Cannot find bake directory at '$BAKE_DIR'"
    exit 1
fi

cd "$BAKE_DIR"

# Check for virtual environment
VENV_PATH=".venv"
if [ -f "$VENV_PATH/bin/activate" ]; then
    write_info "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
else
    echo -e "${GRAY}No virtual environment found. Using system Python.${NC}"
fi

# Verify pytest is available
if ! command -v pytest &> /dev/null; then
    write_error "pytest not found. Install with: pip install pytest"
    exit 1
fi

# Build pytest arguments
PYTEST_ARGS=()

# Verbose output
if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS+=("-v" "--tb=long")
else
    PYTEST_ARGS+=("-v" "--tb=short")
fi

# Coverage
if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS+=("--cov=azext_bake" "--cov-report=term-missing")
    
    if [ "$HTML" = true ]; then
        PYTEST_ARGS+=("--cov-report=html:coverage_html")
    fi
fi

# Parallel execution
if [ "$PARALLEL" = true ]; then
    PYTEST_ARGS+=("-n" "auto")
fi

# Filter by name
if [ -n "$FILTER" ]; then
    PYTEST_ARGS+=("-k" "$FILTER")
fi

# Filter by markers
if [ -n "$MARKERS" ]; then
    PYTEST_ARGS+=("-m" "$MARKERS")
fi

# Fail fast
if [ "$FAILFAST" = true ]; then
    PYTEST_ARGS+=("-x")
fi

# Test path
PYTEST_ARGS+=("$TEST_PATH")

# Display command
write_info "Running: pytest ${PYTEST_ARGS[*]}"
echo ""

# Run pytest
pytest "${PYTEST_ARGS[@]}"
EXIT_CODE=$?

# Report coverage location
if [ "$COVERAGE" = true ] && [ "$HTML" = true ] && [ -d "coverage_html" ]; then
    echo ""
    echo -e "${CYAN}Coverage report: ${WHITE}$(pwd)/coverage_html/index.html${NC}"
fi

exit $EXIT_CODE
