# Testing the az-bake Extension

This document describes how to run tests for the az-bake Azure CLI extension.

## Prerequisites

- Python 3.8 or later
- pip (Python package manager)

## Quick Start

### Windows (PowerShell)

```powershell
cd bake

# Set up virtual environment (first time)
.\setup-venv.ps1

# Activate the environment
.venv\Scripts\Activate.ps1

# Run tests
python -m pytest tests/ -v
```

### Linux/macOS (Bash)

```bash
cd bake

# Make scripts executable
chmod +x setup-venv.sh run-tests.sh

# Set up virtual environment (first time)
./setup-venv.sh

# Activate the environment
source .venv/bin/activate

# Run tests
python -m pytest tests/ -v
```

## Setup Scripts

The `setup-venv` scripts create an isolated Python environment with all dependencies:

### PowerShell (`setup-venv.ps1`)

```powershell
.\setup-venv.ps1              # Create .venv
.\setup-venv.ps1 -Force       # Recreate from scratch
.\setup-venv.ps1 -VenvPath ".venv39" -PythonPath "py -3.9"  # Custom Python
```

### Bash (`setup-venv.sh`)

```bash
./setup-venv.sh               # Create .venv
./setup-venv.sh --force       # Recreate from scratch
./setup-venv.sh --venv .venv39 --python python3.9  # Custom Python
```

## Manual Setup

If you prefer to set up manually:

```bash
cd bake

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install the extension in editable mode
pip install -e .

# Run tests
pytest tests/ -v
```

## Test Runner Options

### PowerShell (`run-tests.ps1`)

| Option | Description |
|--------|-------------|
| `-Install` | Install dependencies before running tests |
| `-Coverage` | Generate code coverage report |
| `-CoverageHtml` | Generate HTML coverage report in `htmlcov/` |
| `-Parallel` | Run tests in parallel (requires pytest-xdist) |
| `-Verbose` | Show verbose test output |
| `-TestPath <path>` | Run specific test file or directory |
| `-Marker <marker>` | Run tests with specific pytest marker |

**Examples:**

```powershell
# Run with coverage
.\run-tests.ps1 -Coverage

# Run specific test file
.\run-tests.ps1 -TestPath "tests/test_data.py"

# Run with HTML coverage report
.\run-tests.ps1 -Coverage -CoverageHtml

# Run tests in parallel
.\run-tests.ps1 -Parallel

# Skip slow tests
.\run-tests.ps1 -Marker "not slow"
```

### Bash (`run-tests.sh`)

| Option | Description |
|--------|-------------|
| `--install`, `-i` | Install dependencies before running |
| `--coverage`, `-c` | Generate coverage report |
| `--html` | Generate HTML coverage report |
| `--parallel`, `-p` | Run tests in parallel |
| `--verbose`, `-v` | Verbose output |
| `--marker`, `-m` | Run tests with specific marker |

**Examples:**

```bash
# Run with coverage
./run-tests.sh --coverage

# Run specific test file
./run-tests.sh tests/test_data.py

# Run with HTML coverage
./run-tests.sh --html

# Run in parallel
./run-tests.sh --parallel
```

## Test Structure

```
bake/
├── tests/
│   ├── __init__.py          # Test package marker
│   ├── conftest.py          # Pytest fixtures
│   ├── test_data.py         # Tests for data classes
│   ├── test_repos.py        # Tests for repo/CI handling
│   ├── test_utils.py        # Tests for utility functions
│   └── test_validators.py   # Tests for input validation
├── pytest.ini               # Pytest configuration
├── requirements-dev.txt     # Development dependencies
├── run-tests.ps1            # Windows test runner
└── run-tests.sh             # Linux/macOS test runner
```

## Writing Tests

### Using Fixtures

The `conftest.py` file provides common fixtures:

```python
def test_example(temp_dir, sample_image_dict):
    """Example test using fixtures."""
    # temp_dir: A temporary directory that's cleaned up after the test
    # sample_image_dict: A valid image configuration dictionary
    
    yaml_file = temp_dir / 'image.yaml'
    yaml_file.write_text(yaml.dump(sample_image_dict))
    
    # Test logic here...
```

### Available Fixtures

| Fixture | Description |
|---------|-------------|
| `temp_dir` | Temporary directory (pathlib.Path) |
| `sample_image_dict` | Valid image configuration dictionary |
| `sample_sandbox_dict` | Valid sandbox configuration dictionary |
| `sample_gallery_dict` | Valid gallery configuration dictionary |
| `sample_image_with_choco` | Image config with Chocolatey packages |
| `mock_cli_ctx` | Mocked Azure CLI context |
| `ci_env_github` | GitHub Actions environment variables |
| `ci_env_devops` | Azure DevOps environment variables |

### Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    """This test takes a long time."""
    pass

@pytest.mark.integration
def test_with_azure():
    """This test requires Azure connectivity."""
    pass
```

Run specific markers:

```bash
# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration
```

## Coverage Reports

After running with coverage, view the report:

```bash
# Terminal report (shown automatically)
pytest --cov=azext_bake --cov-report=term-missing

# HTML report
pytest --cov=azext_bake --cov-report=html
# Open htmlcov/index.html in a browser
```

## Troubleshooting

### pytest not found

Install pytest in your environment:

```bash
pip install pytest pytest-cov pytest-mock
```

### Import errors

Ensure the extension is installed in editable mode:

```bash
cd bake
pip install -e .
```

### Azure CLI not found

Some tests require azure-cli-core. Install it:

```bash
pip install azure-cli-core
```

Or install all development dependencies:

```bash
pip install -r requirements-dev.txt
```
