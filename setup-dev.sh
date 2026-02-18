#!/usr/bin/env bash
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
#
# Development Environment Setup Script for az-bake
# Works on Linux and macOS
#
# Usage:
#   ./setup-dev.sh [--clean] [--skip-venv] [--skip-azdev] [--python <command>]
#

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKIP_VENV=false
SKIP_AZDEV=false
CLEAN=false
PYTHON_CMD=""

# ------------------------------------
# Parse arguments
# ------------------------------------
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)      CLEAN=true; shift ;;
        --skip-venv)  SKIP_VENV=true; shift ;;
        --skip-azdev) SKIP_AZDEV=true; shift ;;
        --python)     PYTHON_CMD="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [--clean] [--skip-venv] [--skip-azdev] [--python <command>]"
            echo ""
            echo "Options:"
            echo "  --clean       Remove existing .venv and build artifacts before setup"
            echo "  --skip-venv   Skip virtual environment creation"
            echo "  --skip-azdev  Skip azdev installation and setup"
            echo "  --python CMD  Use a specific Python command (e.g., python3.11)"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ------------------------------------
# Helper functions
# ------------------------------------
step()    { echo -e "\n\033[36m===> $1\033[0m"; }
success() { echo -e "  \033[32m[OK]\033[0m $1"; }
warn()    { echo -e "  \033[33m[WARN]\033[0m $1"; }
fail()    { echo -e "  \033[31m[FAIL]\033[0m $1"; exit 1; }

# ------------------------------------
# Find Python 3
# ------------------------------------
find_python() {
    if [[ -n "$PYTHON_CMD" ]]; then
        if command -v "$PYTHON_CMD" &>/dev/null; then
            PYTHON="$PYTHON_CMD"
            return
        fi
        fail "Specified Python command '$PYTHON_CMD' not found."
    fi

    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            version=$("$cmd" --version 2>&1)
            if [[ "$version" == *"Python 3."* ]]; then
                PYTHON="$cmd"
                return
            fi
        fi
    done

    fail "Python 3 not found. Please install Python 3.8+ and ensure it is on your PATH."
}

# ------------------------------------
# Pre-flight checks
# ------------------------------------
check_prerequisites() {
    step "Checking prerequisites"

    find_python
    py_version=$($PYTHON --version 2>&1)
    success "Python found: $py_version ($PYTHON)"

    if $PYTHON -m pip --version &>/dev/null; then
        pip_version=$($PYTHON -m pip --version 2>&1 | awk '{print $1, $2}')
        success "pip found: $pip_version"
    else
        fail "pip not found. Please install pip."
    fi

    if command -v az &>/dev/null; then
        az_version=$(az version 2>&1 | python3 -c "import sys, json; print(json.load(sys.stdin)['azure-cli'])" 2>/dev/null || echo "unknown")
        success "Azure CLI found: $az_version"
    else
        warn "Azure CLI not found. Install from: https://aka.ms/installazurecli"
        warn "Azure CLI is required to run/test the extension but not to develop it."
    fi

    if command -v git &>/dev/null; then
        git_version=$(git --version | sed 's/git version //')
        success "Git found: $git_version"
    else
        warn "Git not found. Recommended for development."
    fi
}

# ------------------------------------
# Clean existing environment
# ------------------------------------
clean_environment() {
    step "Cleaning existing development environment"

    # Deactivate any active virtual environment first
    if [[ -n "$VIRTUAL_ENV" ]]; then
        deactivate 2>/dev/null || true
        success "Deactivated existing virtual environment"
    fi

    # Remove .venv and any .venv* variants (e.g. .venv2, .venv-old, .venv_backup)
    local found=false
    for d in "$REPO_ROOT"/.venv*/; do
        if [[ -d "$d" ]]; then
            rm -rf "$d"
            success "Removed $(basename "$d")"
            found=true
        fi
    done
    if ! $found; then
        success "No .venv directories to remove"
    fi

    # Clean build artifacts
    find "$REPO_ROOT/bake" -type d \( -name "build" -o -name "dist" -o -name "*.egg-info" \) -exec rm -rf {} + 2>/dev/null || true
    success "Cleaned build artifacts"
}

# ------------------------------------
# Create virtual environment
# ------------------------------------
create_venv() {
    step "Creating Python virtual environment"

    if [[ -d "$REPO_ROOT/.venv" ]]; then
        success "Virtual environment already exists at .venv"
        return
    fi

    $PYTHON -m venv "$REPO_ROOT/.venv"
    success "Virtual environment created at .venv"
}

# ------------------------------------
# Install azdev and setup extension
# ------------------------------------
install_azdev() {
    step "Activating virtual environment"
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.venv/bin/activate"
    success "Virtual environment activated"

    step "Installing Azure CLI Dev Tools (azdev)"
    pip install azdev > /dev/null 2>&1 || pip install azdev
    success "azdev installed"

    step "Installing compatible setuptools"
    pip install "setuptools==70.0.0" > /dev/null 2>&1
    success "setuptools 70.0.0 installed"

    step "Installing additional dependencies"
    pip install msrestazure > /dev/null 2>&1
    success "msrestazure installed"
}

setup_azdev() {
    step "Setting up azdev with bake extension"
    azdev setup -r "$REPO_ROOT" -e bake
    success "azdev setup complete - 'az bake' extension is registered for development"
}

# ------------------------------------
# Verify the setup
# ------------------------------------
verify_setup() {
    step "Verifying development environment"

    if [[ -f "$REPO_ROOT/.venv/bin/az" ]]; then
        ext_name=$("$REPO_ROOT/.venv/bin/az" extension list 2>/dev/null | python3 -c "
import sys, json
exts = json.load(sys.stdin)
for e in exts:
    if e['name'] == 'bake':
        print(f\"Extension 'bake' v{e['version']} is installed and registered\")
        break
else:
    print('WARN')
" 2>/dev/null || echo "WARN")

        if [[ "$ext_name" == "WARN" ]]; then
            warn "Extension 'bake' not found in az extension list"
        else
            success "$ext_name"
        fi
    else
        warn "Could not verify - az CLI not found in venv"
    fi
}

# ------------------------------------
# Print activation instructions
# ------------------------------------
print_instructions() {
    echo ""
    echo -e "\033[32m=============================================\033[0m"
    echo -e "\033[32m Development environment setup complete!\033[0m"
    echo -e "\033[32m=============================================\033[0m"
    echo ""
    echo -e "\033[33mTo activate the virtual environment:\033[0m"
    echo ""
    echo "  source .venv/bin/activate"
    echo ""
    echo -e "\033[33mCommon development commands:\033[0m"
    echo "  azdev linter bake           # Run linter checks"
    echo "  azdev style bake            # Run style checks"
    echo "  azdev extension build bake  # Build the extension"
    echo "  az bake --help              # Test the extension"
    echo ""
    echo -e "\033[33mOr use VS Code tasks (Ctrl+Shift+P > Tasks: Run Task)\033[0m"
    echo ""
}

# ------------------------------------
# Main
# ------------------------------------
echo ""
echo -e "\033[35maz-bake Development Environment Setup\033[0m"
echo -e "\033[35m======================================\033[0m"

if $CLEAN; then
    clean_environment
fi

check_prerequisites

if ! $SKIP_VENV; then
    create_venv
fi

if ! $SKIP_AZDEV; then
    install_azdev
    setup_azdev
fi

verify_setup
print_instructions
