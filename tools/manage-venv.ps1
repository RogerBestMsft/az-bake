# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

<#
.SYNOPSIS
    Manage Python virtual environment for az-bake development.

.DESCRIPTION
    This script provides commands to setup, activate, clean, and remove
    the Python virtual environment for az-bake development.

.PARAMETER Action
    The action to perform: setup, start, clean, remove

.PARAMETER VenvPath
    Path for the virtual environment (default: .venv)

.PARAMETER PythonPath
    Path to Python executable (default: auto-detect)

.PARAMETER Force
    Force the action without prompts

.EXAMPLE
    .\manage-venv.ps1 setup
    Create .venv and install dependencies.

.EXAMPLE
    .\manage-venv.ps1 start
    Activate the virtual environment.

.EXAMPLE
    .\manage-venv.ps1 clean
    Clean up cache files and __pycache__ directories.

.EXAMPLE
    .\manage-venv.ps1 remove
    Remove the virtual environment completely.

.EXAMPLE
    .\manage-venv.ps1 setup -Force
    Force recreate the virtual environment.
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("setup", "start", "clean", "remove", "help")]
    [string]$Action = "help",
    
    [string]$VenvPath = ".venv",
    [string]$PythonPath = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# ============================================================================
# Helper Functions
# ============================================================================

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host $Text -ForegroundColor Green
}

function Write-Info {
    param([string]$Text)
    Write-Host $Text -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Text)
    Write-Host "ERROR: $Text" -ForegroundColor Red
}

function Find-Python {
    param([string]$PythonPath)
    
    if ($PythonPath) {
        return $PythonPath
    }
    
    # Try py launcher first (Windows)
    if (Get-Command "py" -ErrorAction SilentlyContinue) {
        return "py"
    }
    # Try python3
    elseif (Get-Command "python3" -ErrorAction SilentlyContinue) {
        return "python3"
    }
    # Try python
    elseif (Get-Command "python" -ErrorAction SilentlyContinue) {
        $testPython = python --version 2>&1
        if ($testPython -notmatch "was not found") {
            return "python"
        }
    }
    
    return $null
}

function Test-VenvExists {
    param([string]$VenvPath)
    return (Test-Path "$VenvPath\Scripts\Activate.ps1")
}

# ============================================================================
# Action: Setup
# ============================================================================

function Invoke-Setup {
    Write-Header "az-bake Virtual Environment Setup"
    
    $PythonCmd = Find-Python -PythonPath $PythonPath
    if (-not $PythonCmd) {
        Write-Error "Python not found. Please install Python 3.8+."
        exit 1
    }
    
    Write-Host "Using Python: $PythonCmd" -ForegroundColor Gray
    & $PythonCmd --version
    Write-Host ""
    
    # Check if venv exists
    if (Test-VenvExists -VenvPath $VenvPath) {
        if ($Force) {
            Write-Info "Removing existing virtual environment..."
            Remove-Item -Recurse -Force $VenvPath
        } else {
            Write-Info "Virtual environment already exists at '$VenvPath'"
            Write-Info "Use -Force to recreate, or run 'start' to activate."
            Write-Host ""
            
            $response = Read-Host "Do you want to update dependencies? (y/N)"
            if ($response -ne "y" -and $response -ne "Y") {
                exit 0
            }
            
            # Activate and update
            Write-Host ""
            Write-Info "Activating virtual environment..."
            & "$VenvPath\Scripts\Activate.ps1"
            
            Write-Info "Upgrading pip..."
            & python -m pip install --upgrade pip --quiet
            
            Write-Info "Installing/updating dependencies..."
            & python -m pip install -e . --quiet
            if (Test-Path "requirements-dev.txt") {
                & python -m pip install -r requirements-dev.txt --quiet
            }
            
            Write-Host ""
            Write-Success "Done! Environment updated."
            exit 0
        }
    }
    
    # Create virtual environment
    Write-Info "Creating virtual environment at '$VenvPath'..."
    & $PythonCmd -m venv $VenvPath
    
    if (-not (Test-VenvExists -VenvPath $VenvPath)) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
    
    # Activate virtual environment
    Write-Info "Activating virtual environment..."
    & "$VenvPath\Scripts\Activate.ps1"
    
    # Upgrade pip
    Write-Info "Upgrading pip..."
    & python -m pip install --upgrade pip --quiet
    
    # Install the extension in editable mode
    Write-Info "Installing az-bake extension (this may take a few minutes)..."
    & python -m pip install -e . --quiet
    
    # Install development dependencies
    if (Test-Path "requirements-dev.txt") {
        Write-Info "Installing development dependencies..."
        & python -m pip install -r requirements-dev.txt --quiet
    } else {
        Write-Info "Installing pytest and test tools..."
        & python -m pip install pytest pytest-cov pytest-mock pytest-xdist --quiet
    }
    
    Write-Host ""
    Write-Success "Setup Complete!"
    Write-Host ""
    Write-Host "To activate: " -NoNewline -ForegroundColor Cyan
    Write-Host ".\manage-venv.ps1 start" -ForegroundColor White
    Write-Host "To run tests: " -NoNewline -ForegroundColor Cyan
    Write-Host "python -m pytest tests/ -v" -ForegroundColor White
    Write-Host ""
}

# ============================================================================
# Action: Start (Activate)
# ============================================================================

function Invoke-Start {
    Write-Header "Activating Virtual Environment"
    
    if (-not (Test-VenvExists -VenvPath $VenvPath)) {
        Write-Error "Virtual environment not found at '$VenvPath'"
        Write-Host "Run '.\manage-venv.ps1 setup' first to create it." -ForegroundColor Yellow
        exit 1
    }
    
    Write-Info "Activating virtual environment..."
    & "$VenvPath\Scripts\Activate.ps1"
    
    Write-Success "Virtual environment activated!"
    Write-Host ""
    Write-Host "Python: " -NoNewline -ForegroundColor Gray
    & python --version
    Write-Host "Location: " -NoNewline -ForegroundColor Gray
    Write-Host (Get-Command python).Path
    Write-Host ""
    Write-Host "To deactivate, run: " -NoNewline -ForegroundColor Cyan
    Write-Host "deactivate" -ForegroundColor White
    Write-Host ""
}

# ============================================================================
# Action: Clean
# ============================================================================

function Invoke-Clean {
    Write-Header "Cleaning Up Cache Files"
    
    $cleanedItems = 0
    
    # Clean __pycache__ directories
    Write-Info "Removing __pycache__ directories..."
    $pycacheDirs = Get-ChildItem -Path . -Directory -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue
    foreach ($dir in $pycacheDirs) {
        Remove-Item -Recurse -Force $dir.FullName
        $cleanedItems++
    }
    Write-Host "  Removed $($pycacheDirs.Count) __pycache__ directories" -ForegroundColor Gray
    
    # Clean .pyc files
    Write-Info "Removing .pyc files..."
    $pycFiles = Get-ChildItem -Path . -File -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue
    foreach ($file in $pycFiles) {
        Remove-Item -Force $file.FullName
        $cleanedItems++
    }
    Write-Host "  Removed $($pycFiles.Count) .pyc files" -ForegroundColor Gray
    
    # Clean .pyo files
    Write-Info "Removing .pyo files..."
    $pyoFiles = Get-ChildItem -Path . -File -Recurse -Filter "*.pyo" -ErrorAction SilentlyContinue
    foreach ($file in $pyoFiles) {
        Remove-Item -Force $file.FullName
        $cleanedItems++
    }
    Write-Host "  Removed $($pyoFiles.Count) .pyo files" -ForegroundColor Gray
    
    # Clean .pytest_cache
    Write-Info "Removing .pytest_cache directories..."
    $pytestDirs = Get-ChildItem -Path . -Directory -Recurse -Filter ".pytest_cache" -ErrorAction SilentlyContinue
    foreach ($dir in $pytestDirs) {
        Remove-Item -Recurse -Force $dir.FullName
        $cleanedItems++
    }
    Write-Host "  Removed $($pytestDirs.Count) .pytest_cache directories" -ForegroundColor Gray
    
    # Clean .coverage files
    Write-Info "Removing coverage files..."
    $coverageFiles = Get-ChildItem -Path . -File -Recurse -Filter ".coverage*" -ErrorAction SilentlyContinue
    foreach ($file in $coverageFiles) {
        Remove-Item -Force $file.FullName
        $cleanedItems++
    }
    Write-Host "  Removed $($coverageFiles.Count) coverage files" -ForegroundColor Gray
    
    # Clean egg-info directories
    Write-Info "Removing .egg-info directories..."
    $eggDirs = Get-ChildItem -Path . -Directory -Recurse -Filter "*.egg-info" -ErrorAction SilentlyContinue
    foreach ($dir in $eggDirs) {
        Remove-Item -Recurse -Force $dir.FullName
        $cleanedItems++
    }
    Write-Host "  Removed $($eggDirs.Count) .egg-info directories" -ForegroundColor Gray
    
    # Clean build and dist directories
    Write-Info "Removing build artifacts..."
    foreach ($dirName in @("build", "dist")) {
        if (Test-Path $dirName) {
            Remove-Item -Recurse -Force $dirName
            $cleanedItems++
            Write-Host "  Removed $dirName directory" -ForegroundColor Gray
        }
    }
    
    # Clean pip cache in venv
    if (Test-VenvExists -VenvPath $VenvPath) {
        $pipCache = Join-Path $VenvPath "pip-cache"
        if (Test-Path $pipCache) {
            Write-Info "Removing pip cache..."
            Remove-Item -Recurse -Force $pipCache
            $cleanedItems++
        }
    }
    
    Write-Host ""
    Write-Success "Cleanup complete! Removed $cleanedItems items."
    Write-Host ""
}

# ============================================================================
# Action: Remove
# ============================================================================

function Invoke-Remove {
    Write-Header "Removing Virtual Environment"
    
    if (-not (Test-Path $VenvPath)) {
        Write-Info "Virtual environment not found at '$VenvPath'. Nothing to remove."
        exit 0
    }
    
    if (-not $Force) {
        Write-Host "This will completely remove the virtual environment at '$VenvPath'" -ForegroundColor Yellow
        $response = Read-Host "Are you sure? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Info "Aborted."
            exit 0
        }
    }
    
    # Deactivate if currently active
    if ($env:VIRTUAL_ENV -and $env:VIRTUAL_ENV -eq (Resolve-Path $VenvPath -ErrorAction SilentlyContinue)) {
        Write-Info "Deactivating current virtual environment..."
        deactivate
    }
    
    Write-Info "Removing virtual environment at '$VenvPath'..."
    Remove-Item -Recurse -Force $VenvPath
    
    Write-Host ""
    Write-Success "Virtual environment removed!"
    Write-Host ""
    Write-Host "To recreate, run: " -NoNewline -ForegroundColor Cyan
    Write-Host ".\manage-venv.ps1 setup" -ForegroundColor White
    Write-Host ""
}

# ============================================================================
# Action: Help
# ============================================================================

function Show-Help {
    Write-Host ""
    Write-Host "az-bake Virtual Environment Manager" -ForegroundColor Cyan
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: " -NoNewline -ForegroundColor White
    Write-Host ".\manage-venv.ps1 <action> [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor White
    Write-Host "  setup   " -NoNewline -ForegroundColor Green
    Write-Host "Create and configure the virtual environment"
    Write-Host "  start   " -NoNewline -ForegroundColor Green
    Write-Host "Activate the virtual environment"
    Write-Host "  clean   " -NoNewline -ForegroundColor Green
    Write-Host "Remove cache files, __pycache__, .pyc, etc."
    Write-Host "  remove  " -NoNewline -ForegroundColor Green
    Write-Host "Completely remove the virtual environment"
    Write-Host "  help    " -NoNewline -ForegroundColor Green
    Write-Host "Show this help message"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor White
    Write-Host "  -VenvPath <path>   " -NoNewline -ForegroundColor Gray
    Write-Host "Path for venv (default: .venv)"
    Write-Host "  -PythonPath <cmd>  " -NoNewline -ForegroundColor Gray
    Write-Host "Python command to use"
    Write-Host "  -Force             " -NoNewline -ForegroundColor Gray
    Write-Host "Force action without prompts"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor White
    Write-Host "  .\manage-venv.ps1 setup              " -ForegroundColor Gray -NoNewline
    Write-Host "# Create venv and install deps"
    Write-Host "  .\manage-venv.ps1 setup -Force       " -ForegroundColor Gray -NoNewline
    Write-Host "# Force recreate venv"
    Write-Host "  .\manage-venv.ps1 start              " -ForegroundColor Gray -NoNewline
    Write-Host "# Activate the venv"
    Write-Host "  .\manage-venv.ps1 clean              " -ForegroundColor Gray -NoNewline
    Write-Host "# Clean up cache files"
    Write-Host "  .\manage-venv.ps1 remove             " -ForegroundColor Gray -NoNewline
    Write-Host "# Remove venv completely"
    Write-Host "  .\manage-venv.ps1 remove -Force      " -ForegroundColor Gray -NoNewline
    Write-Host "# Remove without prompt"
    Write-Host ""
}

# ============================================================================
# Main Entry Point
# ============================================================================

switch ($Action) {
    "setup"  { Invoke-Setup }
    "start"  { Invoke-Start }
    "clean"  { Invoke-Clean }
    "remove" { Invoke-Remove }
    "help"   { Show-Help }
    default  { Show-Help }
}
