# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

<#
.SYNOPSIS
    Set up a Python virtual environment for az-bake development and testing.

.DESCRIPTION
    This script creates a Python virtual environment, installs the az-bake
    extension in editable mode along with all development dependencies.

.PARAMETER VenvPath
    Path for the virtual environment (default: .venv)

.PARAMETER PythonPath
    Path to Python executable (default: auto-detect)

.PARAMETER Force
    Remove existing venv and create fresh

.EXAMPLE
    .\setup-venv.ps1
    Create .venv and install dependencies.

.EXAMPLE
    .\setup-venv.ps1 -Force
    Remove existing .venv and create fresh.

.EXAMPLE
    .\setup-venv.ps1 -VenvPath ".venv39" -PythonPath "py -3.9"
    Create venv with specific Python version.
#>

[CmdletBinding()]
param(
    [string]$VenvPath = ".venv",
    [string]$PythonPath = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  az-bake Development Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find Python
if ($PythonPath) {
    $PythonCmd = $PythonPath
} else {
    $PythonCmd = $null
    
    # Try py launcher first (Windows)
    if (Get-Command "py" -ErrorAction SilentlyContinue) {
        $PythonCmd = "py"
    }
    # Try python3
    elseif (Get-Command "python3" -ErrorAction SilentlyContinue) {
        $PythonCmd = "python3"
    }
    # Try python
    elseif (Get-Command "python" -ErrorAction SilentlyContinue) {
        $testPython = python --version 2>&1
        if ($testPython -notmatch "was not found") {
            $PythonCmd = "python"
        }
    }
    
    if (-not $PythonCmd) {
        Write-Host "ERROR: Python not found. Please install Python 3.8+." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Using Python: $PythonCmd" -ForegroundColor Gray
& $PythonCmd --version
Write-Host ""

# Check if venv exists
if (Test-Path $VenvPath) {
    if ($Force) {
        Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $VenvPath
    } else {
        Write-Host "Virtual environment already exists at '$VenvPath'" -ForegroundColor Yellow
        Write-Host "Use -Force to recreate, or activate with:" -ForegroundColor Yellow
        Write-Host "  $VenvPath\Scripts\Activate.ps1" -ForegroundColor White
        Write-Host ""
        
        $response = Read-Host "Do you want to update dependencies? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            exit 0
        }
        
        # Activate and update
        Write-Host ""
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & "$VenvPath\Scripts\Activate.ps1"
        
        Write-Host "Upgrading pip..." -ForegroundColor Yellow
        & python -m pip install --upgrade pip --quiet
        
        Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
        & python -m pip install -e . --quiet
        if (Test-Path "requirements-dev.txt") {
            & python -m pip install -r requirements-dev.txt --quiet
        }
        
        Write-Host ""
        Write-Host "Done! Environment updated." -ForegroundColor Green
        exit 0
    }
}

# Create virtual environment
Write-Host "Creating virtual environment at '$VenvPath'..." -ForegroundColor Yellow
& $PythonCmd -m venv $VenvPath

if (-not (Test-Path "$VenvPath\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "$VenvPath\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& python -m pip install --upgrade pip --quiet

# Install the extension in editable mode (pulls in azure-cli dependencies)
Write-Host "Installing az-bake extension (this may take a few minutes)..." -ForegroundColor Yellow
& python -m pip install -e . --quiet

# Install development dependencies
if (Test-Path "requirements-dev.txt") {
    Write-Host "Installing development dependencies..." -ForegroundColor Yellow
    & python -m pip install -r requirements-dev.txt --quiet
} else {
    Write-Host "Installing pytest and test tools..." -ForegroundColor Yellow
    & python -m pip install pytest pytest-cov pytest-mock pytest-xdist --quiet
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the environment:" -ForegroundColor Cyan
Write-Host "  $VenvPath\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To run tests:" -ForegroundColor Cyan
Write-Host "  python -m pytest tests/ -v" -ForegroundColor White
Write-Host ""
Write-Host "To deactivate:" -ForegroundColor Cyan
Write-Host "  deactivate" -ForegroundColor White
Write-Host ""
