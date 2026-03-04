#!/usr/bin/env bash
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
#
# Remove Development Environment for az-bake
# Works on Linux and macOS
#
# Usage:
#   ./remove-dev.sh [--force]
#

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE=false

# ------------------------------------
# Parse arguments
# ------------------------------------
while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f) FORCE=true; shift ;;
        -h|--help)
            echo "Usage: $0 [--force]"
            echo ""
            echo "Options:"
            echo "  --force, -f   Skip confirmation prompt"
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

echo ""
echo -e "\033[35maz-bake Development Environment Removal\033[0m"
echo -e "\033[35m========================================\033[0m"

# ------------------------------------
# Confirm unless --force is specified
# ------------------------------------
if ! $FORCE; then
    echo ""
    echo -e "\033[33mThis will remove the virtual environment and all build artifacts.\033[0m"
    read -r -p "Are you sure you want to continue? (y/N) " response
    if [[ ! "$response" =~ ^[Yy](es)?$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# ------------------------------------
# Deactivate any active virtual environment
# ------------------------------------
step "Deactivating virtual environment"

if [[ -n "$VIRTUAL_ENV" ]]; then
    deactivate 2>/dev/null || true
    success "Deactivated existing virtual environment"
else
    success "No active virtual environment to deactivate"
fi

# ------------------------------------
# Remove .venv directories
# ------------------------------------
step "Removing virtual environment directories"

found=false
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

# ------------------------------------
# Clean build artifacts
# ------------------------------------
step "Removing build artifacts"

find "$REPO_ROOT/bake" -type d \( -name "build" -o -name "dist" -o -name "*.egg-info" \) -exec rm -rf {} + 2>/dev/null || true
success "Cleaned build artifacts"

# ------------------------------------
# Clean __pycache__ directories
# ------------------------------------
step "Removing __pycache__ directories"

pycache_count=$(find "$REPO_ROOT" -type d -name "__pycache__" 2>/dev/null | wc -l)
find "$REPO_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
if [[ "$pycache_count" -gt 0 ]]; then
    success "Removed $pycache_count __pycache__ directories"
else
    success "No __pycache__ directories to remove"
fi

# ------------------------------------
# Done
# ------------------------------------
echo ""
echo -e "\033[32m=============================================\033[0m"
echo -e "\033[32m Development environment removed!\033[0m"
echo -e "\033[32m=============================================\033[0m"
echo ""
echo -e "\033[33mTo set up the environment again, run:\033[0m"
echo ""
echo "  ./setup-dev.sh"
echo ""
