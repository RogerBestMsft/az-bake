---
name: prepare-assets
description: "Prepare release assets for the az-bake extension. USE FOR: generating index.json, compiling Bicep templates, copying schemas, building local release artifacts, verifying release asset output."
---

# Prepare Release Assets

Prepare release assets for the az-bake CLI extension by running `tools/prepare-assets.py`. This generates `index.json`, compiles Bicep templates to ARM JSON, copies schemas, and assembles all artifacts into a release-ready folder.

> **Non-interactive:** Run all steps automatically without asking the user for confirmation. Detect the OS, resolve paths, and choose the correct activation command autonomously.

## When to Use

- Preparing release assets locally before a release
- Verifying that Bicep templates compile correctly
- Generating `index.json`, `templates.json`, and schema files for distribution
- Testing the release asset pipeline locally (CI uses this script in `release.yml` and `preview-release.yml`)

## Prerequisites

Check these automatically before starting — do not prompt the user:

| Requirement | Required | How to check |
|---|---|---|
| Dev environment | Yes | `.venv` directory exists in the repo root |
| Azure CLI | Yes | `az version` |
| Bicep CLI | Yes | `az bicep version` — install with `az bicep install` if missing |

If the `.venv` directory does not exist, stop and tell the user to run the **setup-dev** skill first.

If `az bicep version` fails, run `az bicep install` automatically to install it, then proceed.

## What the Script Does

1. Reads `VERSION` from `bake/setup.py`
2. Creates `.local/release_assets/` output directory (local mode; CI uses `release_assets/`)
3. Generates `index.json` with extension metadata and download URLs
4. Copies `bake/azext_bake/templates/` to the output directory
5. Compiles all `.bicep` files to ARM JSON using `az bicep build`
6. Generates `templates.json` listing all template files
7. Copies all template files to the output root
8. Copies `schema/bake.schema.json` and `schema/image.schema.json` to the output
9. Generates `assets.json` listing all output files (local mode only)

## Procedure

Run these steps sequentially in the terminal from the repo root.

### 1. Activate the virtual environment

**Windows (PowerShell):**
```powershell
& .venv\Scripts\Activate.ps1
```

**Linux/macOS (bash):**
```bash
source .venv/bin/activate
```

### 2. Verify Bicep is available

```bash
az bicep version
```

If this fails, install Bicep:

```bash
az bicep install
```

### 3. Run prepare-assets.py

```bash
python tools/prepare-assets.py
```

The script auto-detects local vs CI mode using the `CI` environment variable. When running locally (no `CI` env var), output goes to `.local/release_assets/`.

### 4. Report Results

After the script completes, summarize:

- Output directory: `.local/release_assets/` (local) or `release_assets/` (CI)
- Files generated (list the contents of the output directory)
- Any Bicep compilation errors encountered

If Bicep compilation fails, report the specific template and error output.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `az: command not found` | Install Azure CLI from https://aka.ms/installazurecli |
| `az bicep` fails | Run `az bicep install` to install the Bicep CLI |
| `FileNotFoundError` on templates | Ensure `bake/azext_bake/templates/` exists and contains Bicep files |
| `FileNotFoundError` on schemas | Ensure `schema/bake.schema.json` and `schema/image.schema.json` exist |
| `No VERSION found` | Ensure `bake/setup.py` contains `VERSION = 'X.Y.Z'` |
| Output directory already exists (local) | The script uses `dirs_exist_ok=True` locally; safe to re-run |

## Reference

The prepare-assets script is at [tools/prepare-assets.py](../../../tools/prepare-assets.py). It is called by the [release workflow](../../../.github/workflows/release.yml) and [preview-release workflow](../../../.github/workflows/preview-release.yml).
