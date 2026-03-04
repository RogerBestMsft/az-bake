---
name: setup-dev
description: "Set up, reset, or remove the az-bake development environment. USE FOR: creating the Python venv, installing azdev, registering the bake extension, cleaning build artifacts, troubleshooting dev environment issues, onboarding new contributors."
argument-hint: "Describe what you need: setup, clean, remove, or troubleshoot"
---

# Development Environment Setup

Set up, clean, or remove the az-bake development environment. This skill replaces the manual `setup-dev.ps1` / `setup-dev.sh` and `remove-dev.ps1` / `remove-dev.sh` scripts with guided agent-driven steps.

> **Non-interactive:** Run all steps automatically without asking the user for confirmation. Detect the OS, resolve paths, and choose the correct Python command autonomously. Only stop to inform the user if a hard prerequisite (Python 3.8+) is missing and cannot be resolved.

## When to Use

- Setting up the dev environment from scratch
- Cleaning and recreating the venv after dependency issues
- Removing the dev environment entirely
- Troubleshooting dev environment problems (missing modules, broken venv, azdev errors)
- Onboarding: a new contributor needs to get started

## Prerequisites

Check these automatically before starting — do not prompt the user:

| Requirement | Required | How to check |
|---|---|---|
| Python 3.8+ | Yes | Try `python3 --version`, `python --version`, and `py --version` in order; use the first one that succeeds |
| pip | Yes | `<python_cmd> -m pip --version` |
| Git | Recommended | `git --version` |
| Azure CLI | Recommended (runtime only) | `az version` |

**Python detection:** Try `python3`, `python`, and `py` in order. Use whichever returns a valid Python 3.8+ version. Store the working command as `<python_cmd>` and use it for all subsequent steps.

If none of these commands produce Python 3.8+, stop and inform the user to install it from https://www.python.org/downloads/.
If Azure CLI is not found, note it in the final summary but do not block setup (needed for runtime testing, not development).

## Procedure: Full Setup

Run these steps sequentially in the terminal. Detect the OS to choose the correct activation path.

### 1. Create the virtual environment

Use `<python_cmd>` (detected in prerequisites) to create the venv:

```bash
# From the repo root
<python_cmd> -m venv .venv
```

### 2. Activate the virtual environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux/macOS (bash):**
```bash
source .venv/bin/activate
```

### 3. Install azdev

```bash
pip install azdev
```

### 4. Pin setuptools for azdev linter compatibility

```bash
pip install "setuptools==70.0.0"
```

### 5. Register the bake extension with azdev

Automatically resolve the repo root from the workspace folder path (do not prompt the user):

```bash
azdev setup -r <repo-root> -e bake
```

Replace `<repo-root>` with the absolute workspace root path. On Windows PowerShell use `(Get-Location).Path`; on bash use `$PWD`.

### 6. Verify the setup

```bash
az extension list
```

Confirm the `bake` extension appears in the output.

### 7. Print common commands

After setup, remind the user of these common development commands:

- `azdev linter bake` — Run linter checks
- `azdev style bake` — Run style checks
- `azdev extension build bake` — Build the extension wheel
- `az bake --help` — Test the extension
- `pytest tests/ -v --tb=short` — Run tests

## Procedure: Clean Setup (reset)

Use when the venv is broken or dependencies are corrupt.

1. Deactivate any active virtual environment (`deactivate`)
2. Remove all `.venv*` directories in the repo root
3. Remove build artifacts under `bake/`: `build/`, `dist/`, `*.egg-info/`
4. Remove `__pycache__/` directories recursively
5. Follow the **Full Setup** procedure above

## Procedure: Remove Environment

Use when the user explicitly asks to remove the dev environment. Proceed without confirmation since the user already requested the removal.

1. Deactivate any active virtual environment (`deactivate`)
2. Remove all `.venv*` directories in the repo root
3. Remove build artifacts under `bake/`: `build/`, `dist/`, `*.egg-info/`
4. Remove `__pycache__/` directories recursively

## Troubleshooting

| Symptom | Fix |
|---|---|
| `azdev: command not found` | Activate the venv first, then `pip install azdev` |
| `ModuleNotFoundError: azext_bake` | Run `azdev setup -r <repo-root> -e bake` |
| Linter crashes with setuptools error | Run `pip install "setuptools==70.0.0"` |
| `python3: command not found` (Windows) | Use `python` or `py` instead |
| Venv exists but is broken | Run the **Clean Setup** procedure |
| `az bake` not recognized | Ensure venv is activated and `azdev setup` completed |

## Reference Scripts

The original shell scripts are kept in the repo root for manual/CI use:

- [setup-dev.ps1](../../../setup-dev.ps1) — Windows/cross-platform PowerShell setup
- [setup-dev.sh](../../../setup-dev.sh) — Linux/macOS bash setup
- [remove-dev.ps1](../../../remove-dev.ps1) — Windows/cross-platform PowerShell removal
- [remove-dev.sh](../../../remove-dev.sh) — Linux/macOS bash removal
