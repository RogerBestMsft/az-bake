# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

<#
.SYNOPSIS
    Run tests for the az-bake Azure CLI extension.

.DESCRIPTION
    This script sets up the test environment and runs pytest tests
    for the az-bake extension. It supports various options for 
    coverage reporting, parallel execution, and specific test selection.

.PARAMETER Coverage
    Generate code coverage report.

.PARAMETER CoverageHtml
    Generate HTML coverage report in htmlcov/ directory.

.PARAMETER Parallel
    Run tests in parallel using pytest-xdist.

.PARAMETER Verbose
    Show verbose test output.

.PARAMETER TestPath
    Specific test file or directory to run (default: all tests).

.PARAMETER Marker
    Run only tests with specific marker (e.g., 'not slow').

.PARAMETER Install
    Install development dependencies before running tests.

.EXAMPLE
    .\run-tests.ps1
    Run all tests.

.EXAMPLE
    .\run-tests.ps1 -Coverage
    Run all tests with coverage report.

.EXAMPLE
    .\run-tests.ps1 -TestPath "tests/test_data.py"
    Run only tests in test_data.py.

.EXAMPLE
    .\run-tests.ps1 -Coverage -CoverageHtml -Verbose
    Run tests with coverage and generate HTML report.

.EXAMPLE
    .\run-tests.ps1 -Install
    Install dependencies and run all tests.
#>

[CmdletBinding()]
param(
    [switch]$Coverage,
    [switch]$CoverageHtml,
    [switch]$Parallel,
    [switch]$Verbose,
    [string]$TestPath = "",
    [string]$Marker = "",
    [switch]$Install
)

$ErrorActionPreference = "Stop"

# Get script directory and change to bake folder
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BakeDir = $ScriptDir

if ((Split-Path -Leaf $BakeDir) -ne "bake") {
    $BakeDir = Join-Path $ScriptDir "bake"
}

if (-not (Test-Path $BakeDir)) {
    $BakeDir = $ScriptDir
}

Push-Location $BakeDir

try {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  az-bake Test Runner" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # Check Python environment
    $PythonCmd = $null
    
    # Try python first
    if (Get-Command "python" -ErrorAction SilentlyContinue) {
        $testPython = python --version 2>&1
        if ($testPython -notmatch "was not found") {
            $PythonCmd = "python"
        }
    }
    
    # Try python3
    if (-not $PythonCmd -and (Get-Command "python3" -ErrorAction SilentlyContinue)) {
        $PythonCmd = "python3"
    }
    
    # Try py launcher (Windows)
    if (-not $PythonCmd -and (Get-Command "py" -ErrorAction SilentlyContinue)) {
        $PythonCmd = "py"
    }
    
    if (-not $PythonCmd) {
        Write-Host "ERROR: Python not found. Please install Python 3.8+." -ForegroundColor Red
        exit 1
    }

    Write-Host "Using Python: $($PythonCmd)" -ForegroundColor Gray
    & $PythonCmd --version

    # Install dependencies if requested
    if ($Install) {
        Write-Host ""
        Write-Host "Installing development dependencies..." -ForegroundColor Yellow
        
        if (Test-Path "requirements-dev.txt") {
            & $PythonCmd -m pip install -r requirements-dev.txt
        } else {
            & $PythonCmd -m pip install pytest pytest-cov pytest-mock pytest-xdist
        }
        
        # Install the extension in editable mode
        Write-Host "Installing az-bake in editable mode..." -ForegroundColor Yellow
        & $PythonCmd -m pip install -e .
        
        Write-Host "Dependencies installed." -ForegroundColor Green
        Write-Host ""
    }

    # Build pytest command
    $PytestArgs = @()

    # Add test path or default to tests/
    if ($TestPath) {
        $PytestArgs += $TestPath
    } else {
        $PytestArgs += "tests/"
    }

    # Coverage options
    if ($Coverage -or $CoverageHtml) {
        $PytestArgs += "--cov=azext_bake"
        $PytestArgs += "--cov-report=term-missing"
        
        if ($CoverageHtml) {
            $PytestArgs += "--cov-report=html:htmlcov"
        }
    }

    # Parallel execution
    if ($Parallel) {
        $PytestArgs += "-n"
        $PytestArgs += "auto"
    }

    # Verbose output
    if ($Verbose) {
        $PytestArgs += "-vv"
    } else {
        $PytestArgs += "-v"
    }

    # Marker filter
    if ($Marker) {
        $PytestArgs += "-m"
        $PytestArgs += "`"$Marker`""
    }

    # Show the command being run
    Write-Host "Running: pytest $($PytestArgs -join ' ')" -ForegroundColor Yellow
    Write-Host ""

    # Run pytest
    & $PythonCmd -m pytest $PytestArgs

    $ExitCode = $LASTEXITCODE

    if ($ExitCode -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  All tests passed!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "  Some tests failed (exit code: $ExitCode)" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
    }

    # Show HTML coverage location if generated
    if ($CoverageHtml -and (Test-Path "htmlcov/index.html")) {
        Write-Host ""
        Write-Host "Coverage report: $(Resolve-Path 'htmlcov/index.html')" -ForegroundColor Cyan
    }

    exit $ExitCode
}
finally {
    Pop-Location
}
