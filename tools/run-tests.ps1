# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

<#
.SYNOPSIS
    Run tests for the az-bake extension.

.DESCRIPTION
    This script runs pytest with various options for the az-bake extension.
    It supports coverage reporting, parallel execution, and test filtering.

.PARAMETER Coverage
    Generate coverage report

.PARAMETER Parallel
    Run tests in parallel using pytest-xdist

.PARAMETER Verbose
    Run with verbose output

.PARAMETER Filter
    Filter tests by name pattern (pytest -k)

.PARAMETER Markers
    Run tests matching markers (pytest -m), e.g., "not slow"

.PARAMETER FailFast
    Stop on first failure

.PARAMETER Html
    Generate HTML coverage report

.PARAMETER TestPath
    Specific test file or directory to run

.EXAMPLE
    .\run-tests.ps1
    Run all tests with default settings.

.EXAMPLE
    .\run-tests.ps1 -Coverage
    Run tests with coverage reporting.

.EXAMPLE
    .\run-tests.ps1 -Filter "test_validate"
    Run only tests matching "test_validate".

.EXAMPLE
    .\run-tests.ps1 -Markers "not slow"
    Run tests excluding slow tests.

.EXAMPLE
    .\run-tests.ps1 -Parallel -Coverage -Html
    Run tests in parallel with HTML coverage report.
#>

[CmdletBinding()]
param(
    [switch]$Coverage,
    [switch]$Parallel,
    [switch]$Verbose,
    [string]$Filter = "",
    [string]$Markers = "",
    [switch]$FailFast,
    [switch]$Html,
    [string]$TestPath = "tests/"
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Info {
    param([string]$Text)
    Write-Host $Text -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Text)
    Write-Host "ERROR: $Text" -ForegroundColor Red
}

Write-Header "az-bake Test Runner"

# Change to bake directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bakeDir = Join-Path (Split-Path -Parent $scriptDir) "bake"

if (-not (Test-Path $bakeDir)) {
    Write-Error "Cannot find bake directory at '$bakeDir'"
    exit 1
}

Push-Location $bakeDir
try {
    # Check for virtual environment
    $venvPath = ".venv"
    if (Test-Path "$venvPath\Scripts\Activate.ps1") {
        Write-Info "Activating virtual environment..."
        & "$venvPath\Scripts\Activate.ps1"
    } else {
        Write-Host "No virtual environment found. Using system Python." -ForegroundColor Gray
    }

    # Verify pytest is available
    $pytestCmd = Get-Command pytest -ErrorAction SilentlyContinue
    if (-not $pytestCmd) {
        Write-Error "pytest not found. Install with: pip install pytest"
        exit 1
    }

    # Build pytest command
    $pytestArgs = @()

    # Verbose output
    if ($Verbose) {
        $pytestArgs += "-v"
        $pytestArgs += "--tb=long"
    } else {
        $pytestArgs += "-v"
        $pytestArgs += "--tb=short"
    }

    # Coverage
    if ($Coverage) {
        $pytestArgs += "--cov=azext_bake"
        $pytestArgs += "--cov-report=term-missing"
        
        if ($Html) {
            $pytestArgs += "--cov-report=html:coverage_html"
        }
    }

    # Parallel execution
    if ($Parallel) {
        $pytestArgs += "-n"
        $pytestArgs += "auto"
    }

    # Filter by name
    if ($Filter) {
        $pytestArgs += "-k"
        $pytestArgs += $Filter
    }

    # Filter by markers
    if ($Markers) {
        $pytestArgs += "-m"
        $pytestArgs += $Markers
    }

    # Fail fast
    if ($FailFast) {
        $pytestArgs += "-x"
    }

    # Test path
    $pytestArgs += $TestPath

    # Display command
    Write-Info "Running: pytest $($pytestArgs -join ' ')"
    Write-Host ""

    # Run pytest
    & pytest @pytestArgs
    $exitCode = $LASTEXITCODE

    # Report coverage location
    if ($Coverage -and $Html -and (Test-Path "coverage_html")) {
        Write-Host ""
        Write-Host "Coverage report: " -NoNewline -ForegroundColor Cyan
        Write-Host "$(Resolve-Path coverage_html\index.html)" -ForegroundColor White
    }

    exit $exitCode
}
finally {
    Pop-Location
}
