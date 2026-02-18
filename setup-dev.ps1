#!/usr/bin/env pwsh
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
#
# Development Environment Setup Script for az-bake
# Works on Windows (PowerShell 5.1+) and cross-platform (PowerShell 7+)
#

param(
    [switch]$SkipVenv,
    [switch]$SkipAzdev,
    [switch]$Clean,
    [string]$PythonCommand
)

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "===> $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  [WARN] $Message" -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  [FAIL] $Message" -ForegroundColor Red
}

# ------------------------------------
# Determine Python executable
# ------------------------------------
function Find-Python {
    if ($PythonCommand) {
        if (Get-Command $PythonCommand -ErrorAction SilentlyContinue) {
            return $PythonCommand
        }
        Write-Fail "Specified Python command '$PythonCommand' not found."
        exit 1
    }

    # Try common Python executable names
    foreach ($cmd in @("python3", "python", "py")) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) {
            $version = & $cmd --version 2>&1
            if ($version -match "Python 3\.") {
                return $cmd
            }
        }
    }

    Write-Fail "Python 3 not found. Please install Python 3.8+ and ensure it is on your PATH."
    Write-Fail "Download from: https://www.python.org/downloads/"
    exit 1
}

# ------------------------------------
# Pre-flight checks
# ------------------------------------
function Test-Prerequisites {
    Write-Step "Checking prerequisites"

    # Check Python
    $script:Python = Find-Python
    $pyVersion = & $script:Python --version 2>&1
    Write-Success "Python found: $pyVersion ($script:Python)"

    # Check pip
    $pipCheck = & $script:Python -m pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "pip found: $($pipCheck -split ' ' | Select-Object -First 2 | Join-String -Separator ' ')"
    } else {
        Write-Fail "pip not found. Please install pip."
        exit 1
    }

    # Check Azure CLI (optional but recommended)
    if (Get-Command "az" -ErrorAction SilentlyContinue) {
        $azVersion = (az version 2>&1 | ConvertFrom-Json).'azure-cli'
        Write-Success "Azure CLI found: $azVersion"
    } else {
        Write-Warn "Azure CLI not found. Install from: https://aka.ms/installazurecli"
        Write-Warn "Azure CLI is required to run/test the extension but not to develop it."
    }

    # Check Git
    if (Get-Command "git" -ErrorAction SilentlyContinue) {
        $gitVersion = (git --version) -replace 'git version ', ''
        Write-Success "Git found: $gitVersion"
    } else {
        Write-Warn "Git not found. Recommended for development."
    }
}

# ------------------------------------
# Clean existing environment
# ------------------------------------
function Remove-DevEnvironment {
    Write-Step "Cleaning existing development environment"

    # Deactivate any active virtual environment first
    if ($env:VIRTUAL_ENV) {
        try { deactivate } catch {}
        Write-Success "Deactivated existing virtual environment"
    }

    # Remove .venv and any .venv* variants (e.g. .venv2, .venv-old, .venv_backup)
    $venvDirs = Get-ChildItem -Path $RepoRoot -Filter ".venv*" -Directory -Force -ErrorAction SilentlyContinue
    if ($venvDirs) {
        foreach ($dir in $venvDirs) {
            Remove-Item -Recurse -Force $dir.FullName
            Write-Success "Removed $($dir.Name)"
        }
    } else {
        Write-Success "No .venv directories to remove"
    }

    # Clean egg-info and build artifacts
    $cleanDirs = @("build", "dist", "*.egg-info")
    foreach ($pattern in $cleanDirs) {
        Get-ChildItem -Path (Join-Path $RepoRoot "bake") -Filter $pattern -Recurse -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            Remove-Item -Recurse -Force $_.FullName
            Write-Success "Removed $($_.FullName)"
        }
    }
}

# ------------------------------------
# Create virtual environment
# ------------------------------------
function New-VirtualEnvironment {
    Write-Step "Creating Python virtual environment"
    $venvPath = Join-Path $RepoRoot ".venv"

    if (Test-Path $venvPath) {
        Write-Success "Virtual environment already exists at .venv"
        return
    }

    & $script:Python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to create virtual environment"
        exit 1
    }
    Write-Success "Virtual environment created at .venv"
}

# ------------------------------------
# Get the venv python/pip executables
# ------------------------------------
function Get-VenvPaths {
    $venvPath = Join-Path $RepoRoot ".venv"
    if ($IsLinux -or $IsMacOS) {
        $script:VenvPython = Join-Path $venvPath "bin/python"
        $script:VenvPip = Join-Path $venvPath "bin/pip"
        $script:VenvActivate = Join-Path $venvPath "bin/activate"
    } else {
        $script:VenvPython = Join-Path $venvPath "Scripts/python.exe"
        $script:VenvPip = Join-Path $venvPath "Scripts/pip.exe"
        $script:VenvActivate = Join-Path $venvPath "Scripts/Activate.ps1"
    }
}

# ------------------------------------
# Install azdev and setup extension
# ------------------------------------
function Enter-Venv {
    # Deactivate any existing venv to prevent stacking
    if ($env:VIRTUAL_ENV) {
        try { deactivate } catch {}
    }
    # Activate the virtual environment in the current session
    if ($IsLinux -or $IsMacOS) {
        $activateScript = Join-Path $RepoRoot ".venv/bin/Activate.ps1"
    } else {
        $activateScript = Join-Path $RepoRoot ".venv/Scripts/Activate.ps1"
    }
    if (Test-Path $activateScript) {
        & $activateScript
    } else {
        Write-Fail "Virtual environment activation script not found at $activateScript"
        exit 1
    }
}

function Install-AzDev {
    Write-Step "Activating virtual environment"
    Enter-Venv
    Write-Success "Virtual environment activated"

    Write-Step "Installing Azure CLI Dev Tools (azdev)"
    pip install azdev 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        # Retry with output visible
        pip install azdev
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Failed to install azdev"
            exit 1
        }
    }
    Write-Success "azdev installed"

    # Pin setuptools to fix azdev linter compatibility
    Write-Step "Installing compatible setuptools"
    pip install "setuptools==70.0.0" 2>&1 | Out-Null
    Write-Success "setuptools 70.0.0 installed"

    # Install msrestazure (required by the bake extension at runtime)
    Write-Step "Installing additional dependencies"
    pip install msrestazure 2>&1 | Out-Null
    Write-Success "msrestazure installed"
}

function Initialize-AzDevSetup {
    Write-Step "Setting up azdev with bake extension"

    azdev setup -r $RepoRoot -e bake
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to setup azdev. You can retry manually:"
        Write-Fail "  azdev setup -r $RepoRoot -e bake"
        exit 1
    }
    Write-Success "azdev setup complete - 'az bake' extension is registered for development"
}

# ------------------------------------
# Verify the setup
# ------------------------------------
function Test-Setup {
    Write-Step "Verifying development environment"

    try {
        $extList = az extension list 2>&1 | ConvertFrom-Json
        $bakeExt = $extList | Where-Object { $_.name -eq "bake" }
        if ($bakeExt) {
            Write-Success "Extension 'bake' v$($bakeExt.version) is installed and registered"
        } else {
            Write-Warn "Extension 'bake' not found in az extension list"
        }
    } catch {
        Write-Warn "Could not verify - az CLI not available or extension list failed"
    }
}

# ------------------------------------
# Print activation instructions
# ------------------------------------
function Write-ActivationInstructions {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host " Development environment setup complete!" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "To activate the virtual environment:" -ForegroundColor Yellow
    Write-Host ""

    if ($IsLinux -or $IsMacOS) {
        Write-Host "  source .venv/bin/activate" -ForegroundColor White
    } else {
        Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor White
    }

    Write-Host ""
    Write-Host "Common development commands:" -ForegroundColor Yellow
    Write-Host "  azdev linter bake        # Run linter checks" -ForegroundColor White
    Write-Host "  azdev style bake         # Run style checks" -ForegroundColor White
    Write-Host "  azdev extension build bake  # Build the extension" -ForegroundColor White
    Write-Host "  az bake --help           # Test the extension" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use VS Code tasks (Ctrl+Shift+P > Tasks: Run Task)" -ForegroundColor Yellow
    Write-Host ""
}

# ------------------------------------
# Main
# ------------------------------------
Write-Host ""
Write-Host "az-bake Development Environment Setup" -ForegroundColor Magenta
Write-Host "======================================" -ForegroundColor Magenta

if ($Clean) {
    Remove-DevEnvironment
    if (-not $SkipVenv) {
        # Continue with setup after clean
    } else {
        Write-Success "Clean complete."
        exit 0
    }
}

Test-Prerequisites

if (-not $SkipVenv) {
    New-VirtualEnvironment
}

Get-VenvPaths

if (-not $SkipAzdev) {
    Install-AzDev
    Initialize-AzDevSetup
}

Test-Setup
Write-ActivationInstructions
