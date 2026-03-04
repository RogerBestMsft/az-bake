---
name: build-cli
description: "Build the az-bake CLI extension: run linter, style checks, and produce the extension wheel. USE FOR: building the extension, running linter checks, running style checks, producing the .whl artifact."
---

# Build CLI Extension

Build the az-bake CLI extension by running linter checks, style checks, and producing the extension wheel in `release_assets/`. This skill automates the `tools/build-cli.sh` workflow.

> **Non-interactive:** Run all steps automatically without asking the user for confirmation. Detect the OS, resolve paths, and choose the correct activation command autonomously.

## When to Use

- Building the extension wheel for release or local testing
- Running linter and style checks before committing
- Validating that the extension builds cleanly

## Prerequisites

The development environment must already be set up (venv created, azdev installed, bake extension registered). If it is not, run the **setup-dev** skill first before proceeding.

Verify the environment is ready by checking:

1. The `.venv` directory exists in the repo root
2. The venv can be activated

If the venv does not exist, stop and tell the user to run the **setup-dev** skill first.

## Procedure

Run these steps sequentially in the terminal from the repo root. Detect the OS to choose the correct activation command.

### 1. Activate the virtual environment

**Windows (PowerShell):**
```powershell
& .venv\Scripts\Activate.ps1
```

**Linux/macOS (bash):**
```bash
source .venv/bin/activate
```

### 2. Run Linter

```bash
azdev linter bake
```

If the linter fails, stop and report the errors to the user. Do not continue to the next step.

### 3. Run Style Checks

```bash
azdev style bake
```

If style checks fail, stop and report the errors to the user. Do not continue to the next step.

### 4. Build the Extension

```bash
azdev extension build bake --dist-dir ./release_assets
```

### 5. Report Results

After all steps complete successfully, summarize:

- Linter: passed
- Style: passed
- Build artifact location: `release_assets/`

If any step failed, report which step failed and include the error output.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `azdev: command not found` | Activate the venv first, or run the **setup-dev** skill |
| Linter crashes with setuptools error | Run `pip install "setuptools==70.0.0"` |
| `ModuleNotFoundError: azext_bake` | Run `azdev setup -r <repo-root> -e bake` |
| Style check fails | Fix the reported PEP 8 violations (max line length is 200) |
| Build fails with missing dependencies | Ensure `pip install -e ./bake` has been run |

## Reference Script

The original build script used by CI is at [tools/build-cli.sh](../../../tools/build-cli.sh).
