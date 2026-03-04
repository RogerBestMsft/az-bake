#!/usr/bin/env pwsh
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
#
# Remove Development Environment for az-bake
# Works on Windows (PowerShell 5.1+) and cross-platform (PowerShell 7+)
#

param(
    [switch]$Force
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

Write-Host ""
Write-Host "az-bake Development Environment Removal" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

# ------------------------------------
# Confirm unless -Force is specified
# ------------------------------------
if (-not $Force) {
    Write-Host ""
    Write-Host "This will remove the virtual environment and all build artifacts." -ForegroundColor Yellow
    $response = Read-Host "Are you sure you want to continue? (y/N)"
    if ($response -notin @("y", "Y", "yes", "Yes")) {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
}

# ------------------------------------
# Deactivate any active virtual environment
# ------------------------------------
Write-Step "Deactivating virtual environment"

if ($env:VIRTUAL_ENV) {
    try { deactivate } catch {}
    Write-Success "Deactivated existing virtual environment"
} else {
    Write-Success "No active virtual environment to deactivate"
}

# ------------------------------------
# Remove .venv directories
# ------------------------------------
Write-Step "Removing virtual environment directories"

$venvDirs = Get-ChildItem -Path $RepoRoot -Filter ".venv*" -Directory -Force -ErrorAction SilentlyContinue
if ($venvDirs) {
    foreach ($dir in $venvDirs) {
        Remove-Item -Recurse -Force $dir.FullName
        Write-Success "Removed $($dir.Name)"
    }
} else {
    Write-Success "No .venv directories to remove"
}

# ------------------------------------
# Clean egg-info and build artifacts
# ------------------------------------
Write-Step "Removing build artifacts"

$cleanDirs = @("build", "dist", "*.egg-info")
foreach ($pattern in $cleanDirs) {
    Get-ChildItem -Path (Join-Path $RepoRoot "bake") -Filter $pattern -Recurse -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item -Recurse -Force $_.FullName
        Write-Success "Removed $($_.FullName)"
    }
}

# ------------------------------------
# Clean __pycache__ directories
# ------------------------------------
Write-Step "Removing __pycache__ directories"

$pycacheDirs = Get-ChildItem -Path $RepoRoot -Filter "__pycache__" -Recurse -Directory -Force -ErrorAction SilentlyContinue
if ($pycacheDirs) {
    foreach ($dir in $pycacheDirs) {
        Remove-Item -Recurse -Force $dir.FullName
        Write-Success "Removed $($dir.FullName)"
    }
} else {
    Write-Success "No __pycache__ directories to remove"
}

# ------------------------------------
# Done
# ------------------------------------
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host " Development environment removed!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "To set up the environment again, run:" -ForegroundColor Yellow
Write-Host ""
if ($IsLinux -or $IsMacOS) {
    Write-Host "  ./setup-dev.ps1" -ForegroundColor White
} else {
    Write-Host "  .\setup-dev.ps1" -ForegroundColor White
}
Write-Host ""
