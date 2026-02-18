# Contributing to `az bake`

Thank you for your interest in contributing to the `az bake` Azure CLI extension! This guide will help you set up your development environment and get started.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Setup](#manual-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [VS Code Integration](#vs-code-integration)
- [Testing](#testing)
- [Building](#building)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required

| Tool | Version | Install |
|------|---------|---------|
| **Python** | 3.8+ | [python.org/downloads](https://www.python.org/downloads/) |
| **pip** | Latest | Included with Python |
| **Git** | Any | [git-scm.com](https://git-scm.com/) |

### Recommended

| Tool | Purpose | Install |
|------|---------|---------|
| **Azure CLI** | Run and test the extension | [aka.ms/installazurecli](https://aka.ms/installazurecli) |
| **VS Code** | IDE with integrated tasks | [code.visualstudio.com](https://code.visualstudio.com/) |
| **Packer** | Image building (optional) | [packer.io](https://www.packer.io/downloads) |
| **Docker** | Builder image (optional) | [docker.com](https://www.docker.com/get-started) |

### VS Code Extensions

When you open this project in VS Code, you'll be prompted to install recommended extensions:

- **ms-python.python** — Python language support
- **ms-python.vscode-pylance** — Python type checking
- **ms-azuretools.vscode-bicep** — Bicep template support
- **ms-azuretools.vscode-docker** — Docker support
- **hashicorp.hcl** — HCL/Packer syntax highlighting

## Quick Start

### Automated Setup (Recommended)

Choose the script for your platform:

**Windows (PowerShell):**
```powershell
.\setup-dev.ps1
```

**Linux / macOS (Bash):**
```bash
chmod +x setup-dev.sh
./setup-dev.sh
```

The setup script will:

1. Verify prerequisites (Python 3, pip, Azure CLI)
2. Create a Python virtual environment at `.venv/`
3. Install `azdev` (Azure CLI Dev Tools)
4. Pin `setuptools==70.0.0` (fixes azdev linter compatibility)
5. Run `azdev setup` to register the `bake` extension for development
6. Verify the installation

### Setup Script Options

| Flag | Description |
|------|-------------|
| `--clean` / `-Clean` | Remove `.venv` and build artifacts before setup |
| `--skip-venv` / `-SkipVenv` | Skip virtual environment creation |
| `--skip-azdev` / `-SkipAzdev` | Skip azdev installation and setup |
| `--python <cmd>` / `-PythonCommand <cmd>` | Use a specific Python executable |

**Examples:**

```powershell
# Clean rebuild of the dev environment
.\setup-dev.ps1 -Clean

# Use a specific Python version
.\setup-dev.ps1 -PythonCommand python3.11

# Recreate venv but skip azdev reinstall
.\setup-dev.ps1 -Clean -SkipAzdev
```

```bash
# Clean rebuild
./setup-dev.sh --clean

# Specific Python version
./setup-dev.sh --python python3.11
```

## Manual Setup

If you prefer to set up manually, follow these steps:

### 1. Clone the repository

```bash
git clone https://github.com/rogerbestmsft/az-bake.git
cd az-bake
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate the virtual environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (cmd.exe):**
```cmd
.venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 4. Install azdev and setuptools

```bash
pip install azdev
pip install setuptools==70.0.0
```

### 5. Setup azdev with the bake extension

```bash
azdev setup -r . -e bake
```

### 6. Verify

```bash
az bake --help
```

## Project Structure

```
az-bake/
├── bake/                       # Main extension package
│   ├── setup.py                # Package metadata & version
│   ├── azext_bake/
│   │   ├── __init__.py         # Extension loader (BakeCommandsLoader)
│   │   ├── commands.py         # Command group definitions
│   │   ├── custom.py           # Command implementations
│   │   ├── _params.py          # CLI parameter definitions
│   │   ├── _validators.py      # Input validators
│   │   ├── _help.py            # Help text for commands
│   │   ├── _arm.py             # ARM/resource management helpers
│   │   ├── _packer.py          # Packer integration
│   │   ├── _constants.py       # Shared constants
│   │   ├── _data.py            # Data models
│   │   ├── _utils.py           # Utility functions
│   │   ├── _repos.py           # Repository operations
│   │   ├── _sandbox.py         # Sandbox operations
│   │   ├── _github.py          # GitHub API helpers
│   │   ├── _transformers.py    # Output transformers
│   │   ├── _completers.py      # Tab completion
│   │   ├── _client_factory.py  # Azure SDK client creation
│   │   └── templates/          # Bicep, Packer, and installer templates
│   │       ├── builder/        # Bicep templates for builder infra
│   │       ├── install/        # Choco/Winget install configs
│   │       ├── packer/         # Packer HCL templates
│   │       └── sandbox/        # Sandbox Bicep templates
│   └── HISTORY.rst             # Changelog
├── builder/                    # Docker builder image
│   └── Dockerfile
├── examples/                   # Example image definitions & scripts
│   ├── images/                 # Sample image.yml files
│   └── scripts/                # Sample provisioning scripts
├── schema/                     # JSON schemas for bake/image YAML
├── tools/                      # Build and release utilities
│   ├── build-cli.sh            # CI build script
│   ├── bump-version.py         # Version bumping utility
│   ├── cli-version.py          # Version query utility
│   ├── clear-images.py         # Image cleanup utility
│   └── prepare-assets.py       # Release asset preparation
├── setup-dev.ps1               # PowerShell dev setup (Windows/cross-platform)
├── setup-dev.sh                # Bash dev setup (Linux/macOS)
└── .vscode/                    # VS Code workspace configuration
    ├── tasks.json              # Build/dev tasks
    ├── settings.json           # Editor settings
    └── extensions.json         # Recommended extensions
```

## Development Workflow

### Activating the Environment

Always activate the virtual environment before working:

```powershell
# Windows
.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate
```

### Making Changes

1. **Edit code** in `bake/azext_bake/`
2. Changes are picked up automatically since the extension is installed in dev mode
3. Test your changes by running `az bake <command>`
4. Run linter and style checks before committing

### Adding a New Command

1. Add the implementation function in [bake/azext_bake/custom.py](bake/azext_bake/custom.py)
2. Register the command in [bake/azext_bake/commands.py](bake/azext_bake/commands.py)
3. Define parameters in [bake/azext_bake/_params.py](bake/azext_bake/_params.py)
4. Add help text in [bake/azext_bake/_help.py](bake/azext_bake/_help.py)
5. Add validators (if needed) in [bake/azext_bake/_validators.py](bake/azext_bake/_validators.py)

### Code Quality

```bash
# Run the Azure CLI linter
azdev linter bake

# Run style/formatting checks
azdev style bake
```

These commands check for:
- Azure CLI naming conventions
- Parameter naming patterns
- Help text completeness
- PEP 8 style compliance

### Code Style

- Max line length: **200** characters (per autopep8 config)
- Import sorting: **isort** with line length 120
- Follow existing patterns in the codebase
- Prefix internal/private modules with `_` (e.g., `_utils.py`)

## VS Code Integration

The project comes with pre-configured VS Code tasks. Open the Command Palette (`Ctrl+Shift+P`) and select **Tasks: Run Task**:

| Task | Description |
|------|-------------|
| **azdev: setup** | Full environment setup (venv + azdev) |
| **azdev: linter** | Run Azure CLI linter on bake extension |
| **azdev: style** | Run style checks on bake extension |
| **packer: fmt** | Format all Packer HCL files |
| **packer: validate** | Validate Packer templates |
| **docker: build** | Build the builder Docker image |
| **docker: build push (latest)** | Build and push the Docker image |
| **venv: create** | Create the Python virtual environment |
| **venv: delete** | Remove the virtual environment |

## Testing

### Automated Tests

The project uses **pytest** for automated testing. Tests live in `bake/tests/` and cover data models, URL parsing, validators, and integration scenarios.

```bash
# Install the extension with test dependencies
pip install -e ./bake[dev]

# Run all tests
cd bake
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=azext_bake --cov-report=term-missing

# Run a specific test file
pytest tests/test_data.py -v

# Run a specific test class or function
pytest tests/test_repos.py::TestRepoGitHub -v
```

Tests are also run automatically on every push and pull request via the GitHub Actions CI workflow (`.github/workflows/ci.yml`).

#### Writing New Tests

- Add test files to `bake/tests/` following the `test_<module>.py` naming convention
- Use fixtures from `conftest.py` for common objects (`mock_cmd`, `sample_sandbox_dict`, `tmp_repo`, etc.)
- For Azure SDK calls, use `unittest.mock.patch` to mock client factories in `_client_factory.py`
- No Azure credentials are needed — all external calls should be mocked

### Manual Testing

After making changes, test the extension locally:

```bash
# Show extension info
az bake version

# Test sandbox operations
az bake sandbox validate -s <sandbox-rg> -r <gallery>

# Validate a repo
az bake repo validate --repo ./

# Export YAML config
az bake yaml export
```

## Building

### Build the Extension Wheel

```bash
azdev extension build bake --dist-dir ./release_assets
```

This creates a `.whl` file in `./release_assets/` that can be installed with:

```bash
az extension add --source ./release_assets/bake-<version>-py3-none-any.whl -y
```

### Build the Docker Image

```bash
# Using VS Code task
# Run task: "docker: build"

# Or manually
docker build -t ghcr.io/rogerbestmsft/az-bake/builder:latest ./builder
```

### Bump the Version

```bash
# Bump patch version (e.g., 0.3.20 → 0.3.21)
python tools/bump-version.py

# Bump minor version (e.g., 0.3.20 → 0.4.0)
python tools/bump-version.py --minor

# Bump major version (e.g., 0.3.20 → 1.0.0)
python tools/bump-version.py --major

# With release notes
python tools/bump-version.py --notes "Added new feature" "Fixed bug"
```

## Common Tasks

| What you want to do | Command |
|---------------------|---------|
| Setup dev environment | `.\setup-dev.ps1` or `./setup-dev.sh` |
| Activate venv | `.venv\Scripts\Activate.ps1` or `source .venv/bin/activate` |
| Run linter | `azdev linter bake` |
| Run style check | `azdev style bake` |
| Build extension | `azdev extension build bake --dist-dir ./release_assets` |
| Test a command | `az bake --help` |
| Clean environment | `.\setup-dev.ps1 -Clean` or `./setup-dev.sh --clean` |
| Bump version | `python tools/bump-version.py` |

## Troubleshooting

### `azdev` command not found

Make sure your virtual environment is activated:
```powershell
.venv\Scripts\Activate.ps1   # Windows
source .venv/bin/activate      # Linux/macOS
```

### Linter fails with setuptools error

The azdev linter requires a specific version of setuptools:
```bash
pip install setuptools==70.0.0
```

The setup scripts handle this automatically.

### Extension not loading after code changes

The extension is installed in development mode, so changes should be picked up automatically. If not:

```bash
# Re-register the extension
azdev setup -r . -e bake
```

### `ModuleNotFoundError` for `azure.cli.core`

This usually means you're running Python outside the virtual environment. Activate your venv first.

### Permission denied on `setup-dev.sh`

```bash
chmod +x setup-dev.sh
```

### Python version mismatch

If you have multiple Python versions, specify the one to use:
```bash
./setup-dev.sh --python python3.11
.\setup-dev.ps1 -PythonCommand python3.11
```

### Clean slate

If things go wrong, do a full clean reset:
```powershell
.\setup-dev.ps1 -Clean          # Windows
./setup-dev.sh --clean          # Linux/macOS
```
