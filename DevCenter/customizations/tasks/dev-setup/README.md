Development Environment Setup
==============================

Purpose
-------
Configures the complete development environment for debugging and developing the Azure CLI `bake` extension on Windows Dev Box.

Task Structure
--------------
This task uses the Azure Dev Box customization format:

```yaml
$schema: 1.0
tasks:
  - name: setup-dev-environment
    description: Set up Python virtual environment and configure Azure CLI extension development
    parameters:
      command: powershell
      script: |
        Set-Location C:\workspaces\az-bake
        python -m venv .venv
        .\.venv\Scripts\Activate.ps1
        pip install --upgrade pip
        pip install -e .\bake
        pip install azdev
        azdev setup -r . -e bake
      runAsUser: true
```

What This Task Does
-------------------
1. **Creates Python virtual environment** - Sets up an isolated `.venv` in the repository root
2. **Activates the environment** - Switches to the virtual environment context
3. **Upgrades pip** - Ensures latest package installer
4. **Installs extension in editable mode** - Links the `bake` extension for development
5. **Installs azdev** - Azure CLI extension development tooling
6. **Configures azdev** - Sets up the extension for debugging and testing

Prerequisites
-------------
- Python must be installed (run `python` task first)
- Azure CLI must be installed (run `azure-cli` task first)
- Repository must be cloned to `C:\workspaces\az-bake`

Post-Setup Usage
----------------
After this task completes, you can:

```powershell
# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Test the extension
az bake --help

# Run extension tests
azdev test bake

# Debug with VS Code
# Open the workspace and use the Python debugger with the configured environment
```

Verify
------
```bash
azdev --version
az extension list | Select-String bake
```
