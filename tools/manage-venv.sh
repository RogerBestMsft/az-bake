#!/bin/bash
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

# Manage Python virtual environment for az-bake development.
#
# Usage:
#   ./manage-venv.sh <action> [options]
#
# Actions:
#   setup   - Create and configure the virtual environment
#   start   - Activate the virtual environment
#   clean   - Remove cache files, __pycache__, .pyc, etc.
#   remove  - Completely remove the virtual environment
#   help    - Show this help message
#
# Options:
#   --venv PATH      Path for virtual environment (default: .venv)
#   --python CMD     Python command to use (default: auto-detect)
#   --force, -f      Force action without prompts

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
ACTION=""
VENV_PATH=".venv"
PYTHON_CMD=""
FORCE=false

# ============================================================================
# Helper Functions
# ============================================================================

write_header() {
    echo ""
    echo -e "${CYAN}========================================"
    echo -e "  $1"
    echo -e "========================================${NC}"
    echo ""
}

write_success() {
    echo -e "${GREEN}$1${NC}"
}

write_info() {
    echo -e "${YELLOW}$1${NC}"
}

write_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

find_python() {
    if [ -n "$PYTHON_CMD" ]; then
        echo "$PYTHON_CMD"
        return
    fi
    
    if command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        echo "python"
    else
        echo ""
    fi
}

test_venv_exists() {
    [ -f "$VENV_PATH/bin/activate" ]
}

# ============================================================================
# Action: Setup
# ============================================================================

do_setup() {
    write_header "az-bake Virtual Environment Setup"
    
    PYTHON_CMD=$(find_python)
    if [ -z "$PYTHON_CMD" ]; then
        write_error "Python not found. Please install Python 3.8+."
        exit 1
    fi
    
    echo -e "Using Python: ${GRAY}$PYTHON_CMD${NC}"
    $PYTHON_CMD --version
    echo ""
    
    # Check if venv exists
    if test_venv_exists; then
        if [ "$FORCE" = true ]; then
            write_info "Removing existing virtual environment..."
            rm -rf "$VENV_PATH"
        else
            write_info "Virtual environment already exists at '$VENV_PATH'"
            write_info "Use --force to recreate, or run 'start' to activate."
            echo ""
            
            read -p "Do you want to update dependencies? (y/N) " response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                exit 0
            fi
            
            # Activate and update
            echo ""
            write_info "Activating virtual environment..."
            source "$VENV_PATH/bin/activate"
            
            write_info "Upgrading pip..."
            python -m pip install --upgrade pip --quiet
            
            write_info "Installing/updating dependencies..."
            python -m pip install -e . --quiet
            if [ -f "requirements-dev.txt" ]; then
                python -m pip install -r requirements-dev.txt --quiet
            fi
            
            echo ""
            write_success "Done! Environment updated."
            exit 0
        fi
    fi
    
    # Create virtual environment
    write_info "Creating virtual environment at '$VENV_PATH'..."
    $PYTHON_CMD -m venv "$VENV_PATH"
    
    if ! test_venv_exists; then
        write_error "Failed to create virtual environment"
        exit 1
    fi
    
    # Activate virtual environment
    write_info "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
    
    # Upgrade pip
    write_info "Upgrading pip..."
    python -m pip install --upgrade pip --quiet
    
    # Install the extension in editable mode
    write_info "Installing az-bake extension (this may take a few minutes)..."
    python -m pip install -e . --quiet
    
    # Install development dependencies
    if [ -f "requirements-dev.txt" ]; then
        write_info "Installing development dependencies..."
        python -m pip install -r requirements-dev.txt --quiet
    else
        write_info "Installing pytest and test tools..."
        python -m pip install pytest pytest-cov pytest-mock pytest-xdist --quiet
    fi
    
    echo ""
    write_success "Setup Complete!"
    echo ""
    echo -e "${CYAN}To activate: ${WHITE}./manage-venv.sh start${NC}"
    echo -e "${CYAN}To run tests: ${WHITE}python -m pytest tests/ -v${NC}"
    echo ""
}

# ============================================================================
# Action: Start (Activate)
# ============================================================================

do_start() {
    write_header "Activating Virtual Environment"
    
    if ! test_venv_exists; then
        write_error "Virtual environment not found at '$VENV_PATH'"
        echo -e "${YELLOW}Run './manage-venv.sh setup' first to create it.${NC}"
        exit 1
    fi
    
    write_info "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
    
    write_success "Virtual environment activated!"
    echo ""
    echo -e "${GRAY}Python: $(python --version)${NC}"
    echo -e "${GRAY}Location: $(which python)${NC}"
    echo ""
    echo -e "${CYAN}To deactivate, run: ${WHITE}deactivate${NC}"
    echo ""
    
    # Spawn a new shell with the venv activated
    echo -e "${YELLOW}Starting a new shell with the virtual environment...${NC}"
    $SHELL
}

# ============================================================================
# Action: Clean
# ============================================================================

do_clean() {
    write_header "Cleaning Up Cache Files"
    
    local cleaned_items=0
    
    # Clean __pycache__ directories
    write_info "Removing __pycache__ directories..."
    local pycache_count=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo -e "  ${GRAY}Removed $pycache_count __pycache__ directories${NC}"
    cleaned_items=$((cleaned_items + pycache_count))
    
    # Clean .pyc files
    write_info "Removing .pyc files..."
    local pyc_count=$(find . -type f -name "*.pyc" 2>/dev/null | wc -l)
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    echo -e "  ${GRAY}Removed $pyc_count .pyc files${NC}"
    cleaned_items=$((cleaned_items + pyc_count))
    
    # Clean .pyo files
    write_info "Removing .pyo files..."
    local pyo_count=$(find . -type f -name "*.pyo" 2>/dev/null | wc -l)
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    echo -e "  ${GRAY}Removed $pyo_count .pyo files${NC}"
    cleaned_items=$((cleaned_items + pyo_count))
    
    # Clean .pytest_cache
    write_info "Removing .pytest_cache directories..."
    local pytest_count=$(find . -type d -name ".pytest_cache" 2>/dev/null | wc -l)
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    echo -e "  ${GRAY}Removed $pytest_count .pytest_cache directories${NC}"
    cleaned_items=$((cleaned_items + pytest_count))
    
    # Clean .coverage files
    write_info "Removing coverage files..."
    local coverage_count=$(find . -type f -name ".coverage*" 2>/dev/null | wc -l)
    find . -type f -name ".coverage*" -delete 2>/dev/null || true
    echo -e "  ${GRAY}Removed $coverage_count coverage files${NC}"
    cleaned_items=$((cleaned_items + coverage_count))
    
    # Clean egg-info directories
    write_info "Removing .egg-info directories..."
    local egg_count=$(find . -type d -name "*.egg-info" 2>/dev/null | wc -l)
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    echo -e "  ${GRAY}Removed $egg_count .egg-info directories${NC}"
    cleaned_items=$((cleaned_items + egg_count))
    
    # Clean build and dist directories
    write_info "Removing build artifacts..."
    for dir in build dist; do
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            echo -e "  ${GRAY}Removed $dir directory${NC}"
            cleaned_items=$((cleaned_items + 1))
        fi
    done
    
    echo ""
    write_success "Cleanup complete! Removed $cleaned_items items."
    echo ""
}

# ============================================================================
# Action: Remove
# ============================================================================

do_remove() {
    write_header "Removing Virtual Environment"
    
    if [ ! -d "$VENV_PATH" ]; then
        write_info "Virtual environment not found at '$VENV_PATH'. Nothing to remove."
        exit 0
    fi
    
    if [ "$FORCE" != true ]; then
        echo -e "${YELLOW}This will completely remove the virtual environment at '$VENV_PATH'${NC}"
        read -p "Are you sure? (y/N) " response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            write_info "Aborted."
            exit 0
        fi
    fi
    
    # Deactivate if currently active
    if [ -n "$VIRTUAL_ENV" ] && [ "$VIRTUAL_ENV" = "$(cd "$VENV_PATH" 2>/dev/null && pwd)" ]; then
        write_info "Deactivating current virtual environment..."
        deactivate 2>/dev/null || true
    fi
    
    write_info "Removing virtual environment at '$VENV_PATH'..."
    rm -rf "$VENV_PATH"
    
    echo ""
    write_success "Virtual environment removed!"
    echo ""
    echo -e "${CYAN}To recreate, run: ${WHITE}./manage-venv.sh setup${NC}"
    echo ""
}

# ============================================================================
# Action: Help
# ============================================================================

show_help() {
    echo ""
    echo -e "${CYAN}az-bake Virtual Environment Manager"
    echo -e "=====================================${NC}"
    echo ""
    echo -e "${WHITE}Usage: ${YELLOW}./manage-venv.sh <action> [options]${NC}"
    echo ""
    echo -e "${WHITE}Actions:${NC}"
    echo -e "  ${GREEN}setup${NC}   Create and configure the virtual environment"
    echo -e "  ${GREEN}start${NC}   Activate the virtual environment"
    echo -e "  ${GREEN}clean${NC}   Remove cache files, __pycache__, .pyc, etc."
    echo -e "  ${GREEN}remove${NC}  Completely remove the virtual environment"
    echo -e "  ${GREEN}help${NC}    Show this help message"
    echo ""
    echo -e "${WHITE}Options:${NC}"
    echo -e "  ${GRAY}--venv PATH${NC}      Path for venv (default: .venv)"
    echo -e "  ${GRAY}--python CMD${NC}     Python command to use"
    echo -e "  ${GRAY}--force, -f${NC}      Force action without prompts"
    echo ""
    echo -e "${WHITE}Examples:${NC}"
    echo -e "  ${GRAY}./manage-venv.sh setup${NC}              # Create venv and install deps"
    echo -e "  ${GRAY}./manage-venv.sh setup --force${NC}      # Force recreate venv"
    echo -e "  ${GRAY}./manage-venv.sh start${NC}              # Activate the venv"
    echo -e "  ${GRAY}./manage-venv.sh clean${NC}              # Clean up cache files"
    echo -e "  ${GRAY}./manage-venv.sh remove${NC}             # Remove venv completely"
    echo -e "  ${GRAY}./manage-venv.sh remove --force${NC}     # Remove without prompt"
    echo ""
}

# ============================================================================
# Parse Arguments
# ============================================================================

# Get the action (first positional argument)
if [ $# -gt 0 ]; then
    ACTION="$1"
    shift
fi

# Parse remaining arguments
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
            show_help
            exit 0
            ;;
        *)
            write_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# ============================================================================
# Main Entry Point
# ============================================================================

case "$ACTION" in
    setup)
        do_setup
        ;;
    start)
        do_start
        ;;
    clean)
        do_clean
        ;;
    remove)
        do_remove
        ;;
    help|"")
        show_help
        ;;
    *)
        write_error "Unknown action: $ACTION"
        show_help
        exit 1
        ;;
esac
