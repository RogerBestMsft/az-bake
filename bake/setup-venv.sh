#!/bin/bash
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

# Set up a Python virtual environment for az-bake development and testing.
#
# Usage:
#   ./setup-venv.sh              - Create .venv and install dependencies
#   ./setup-venv.sh --force      - Remove existing and recreate
#   ./setup-venv.sh --venv .venv39 --python python3.9
#
# Options:
#   --venv PATH      Path for virtual environment (default: .venv)
#   --python CMD     Python command to use (default: auto-detect)
#   --force          Remove existing venv and create fresh
#   --help           Show this help

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Defaults
VENV_PATH=".venv"
PYTHON_CMD=""
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --venv)
            VENV_PATH="$2"
            shift 2
            ;;
        --python)
            PYTHON_CMD="$2"
            shift 2
            ;;
        --force|-f)
            FORCE=true
            shift
            ;;
        --help|-h)
            head -25 "$0" | tail -15
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}========================================"
echo -e "  az-bake Development Environment Setup"
echo -e "========================================${NC}"
echo ""

# Find Python
if [ -z "$PYTHON_CMD" ]; then
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}ERROR: Python not found. Please install Python 3.8+.${NC}"
        exit 1
    fi
fi

echo -e "Using Python: ${PYTHON_CMD}"
$PYTHON_CMD --version
echo ""

# Check if venv exists
if [ -d "$VENV_PATH" ]; then
    if [ "$FORCE" = true ]; then
        echo -e "${YELLOW}Removing existing virtual environment...${NC}"
        rm -rf "$VENV_PATH"
    else
        echo -e "${YELLOW}Virtual environment already exists at '$VENV_PATH'${NC}"
        echo -e "${YELLOW}Use --force to recreate, or activate with:${NC}"
        echo -e "${WHITE}  source $VENV_PATH/bin/activate${NC}"
        echo ""
        
        read -p "Do you want to update dependencies? (y/N) " response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 0
        fi
        
        # Activate and update
        echo ""
        echo -e "${YELLOW}Activating virtual environment...${NC}"
        source "$VENV_PATH/bin/activate"
        
        echo -e "${YELLOW}Upgrading pip...${NC}"
        python -m pip install --upgrade pip --quiet
        
        echo -e "${YELLOW}Installing/updating dependencies...${NC}"
        python -m pip install -e . --quiet
        if [ -f "requirements-dev.txt" ]; then
            python -m pip install -r requirements-dev.txt --quiet
        fi
        
        echo ""
        echo -e "${GREEN}Done! Environment updated.${NC}"
        exit 0
    fi
fi

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment at '$VENV_PATH'...${NC}"
$PYTHON_CMD -m venv "$VENV_PATH"

if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo -e "${RED}ERROR: Failed to create virtual environment${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
python -m pip install --upgrade pip --quiet

# Install the extension in editable mode
echo -e "${YELLOW}Installing az-bake extension (this may take a few minutes)...${NC}"
python -m pip install -e . --quiet

# Install development dependencies
if [ -f "requirements-dev.txt" ]; then
    echo -e "${YELLOW}Installing development dependencies...${NC}"
    python -m pip install -r requirements-dev.txt --quiet
else
    echo -e "${YELLOW}Installing pytest and test tools...${NC}"
    python -m pip install pytest pytest-cov pytest-mock pytest-xdist --quiet
fi

echo ""
echo -e "${GREEN}========================================"
echo -e "  Setup Complete!"
echo -e "========================================${NC}"
echo ""
echo -e "${CYAN}To activate the environment:${NC}"
echo -e "${WHITE}  source $VENV_PATH/bin/activate${NC}"
echo ""
echo -e "${CYAN}To run tests:${NC}"
echo -e "${WHITE}  python -m pytest tests/ -v${NC}"
echo ""
echo -e "${CYAN}To deactivate:${NC}"
echo -e "${WHITE}  deactivate${NC}"
echo ""
