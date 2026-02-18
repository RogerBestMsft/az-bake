# Tests for `az bake`

This directory contains the automated test suite for the `az bake` Azure CLI extension. Tests are written with [pytest](https://docs.pytest.org/) and require **no Azure credentials** — all external calls are mocked.

## Quick Start

```bash
# From the repository root, activate the virtual environment
# Windows
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

# Install the extension in editable mode with test dependencies
pip install -e ./bake[dev]

# Run the full test suite
cd bake
pytest tests/ -v
```

## Running Tests

| Command | Description |
|---------|-------------|
| `pytest tests/ -v` | Run all tests with verbose output |
| `pytest tests/ -v --cov=azext_bake --cov-report=term-missing` | Run with coverage |
| `pytest tests/test_data.py -v` | Run a single test file |
| `pytest tests/test_data.py::TestImage -v` | Run a single test class |
| `pytest tests/test_data.py::TestImage::test_windows_default_base -v` | Run a single test |
| `pytest tests/ -k "sandbox"` | Run tests matching a keyword |
| `pytest tests/ --tb=long` | Run with full tracebacks |

The pytest configuration lives in [`pytest.ini`](../pytest.ini):

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --tb=short -q
```

## Test Structure

```
tests/
├── __init__.py            # Package marker
├── conftest.py            # Shared fixtures used by all test modules
├── README.md              # This file
├── test_constants.py      # Tests for _constants.py (tag helpers, defaults)
├── test_data.py           # Tests for _data.py (data models and YAML parsing)
├── test_repos.py          # Tests for _repos.py (Git URL parsing, CI detection)
└── test_validators.py     # Tests for _validators.py (CLI argument validation)
```

## Test Modules

### `test_constants.py`

Covers the `_constants.py` module:

- **`TestTagKey`** — Verifies `tag_key()` correctly prepends the `hidden-bake:` prefix.
- **`TestConstants`** — Validates structure of `IMAGE_DEFAULT_BASE_WINDOWS`, `PKR_DEFAULT_VARS`, and `DEFAULT_TAGS`.

### `test_data.py`

Covers the `_data.py` module (data models deserialized from YAML):

| Test Class | What It Tests |
|------------|---------------|
| `TestSnakeToCamel` / `TestCamelToSnake` | Case-conversion helpers |
| `TestRoundTrip` | Snake → camel → snake identity |
| `TestValidateDataObject` | Schema validation for data classes |
| `TestGetDict` | Serialization back to camelCase dicts |
| `TestPowershellScript` | `PowershellScript` dataclass |
| `TestImageInstallScripts` | String-shorthand and dict forms for script lists |
| `TestChocoDefaults` / `TestChocoPackage` | Chocolatey install config |
| `TestWingetPackage` | WinGet install config |
| `TestImageInstall` | Composite install section |
| `TestImageBase` | Base image reference |
| `TestImagePlan` | Marketplace plan metadata |
| `TestImage` | Full `Image` model (defaults, base selection, path handling) |
| `TestSandbox` | Sandbox configuration and GUID validation |
| `TestGallery` | Gallery configuration |
| `TestBakeConfig` | Top-level `bake.yml` configuration |

### `test_repos.py`

Covers the `_repos.py` module (Git provider detection and CI environments):

| Test Class | What It Tests |
|------------|---------------|
| `TestRepoGitHub` | GitHub URL parsing (HTTPS, SSH, `git://`) |
| `TestRepoDevOps` | Azure DevOps URL parsing (dev.azure.com and visualstudio.com) |
| `TestRepoUnknown` | Unsupported providers raise `CLIError` |
| `TestRepoMetadata` | `ref` and `revision` passthrough |
| `TestCIIsCI` | `CI.is_ci()` static method for GitHub Actions and Azure DevOps |
| `TestCIInit` | Full CI object construction from environment variables |

### `test_validators.py`

Covers the `_validators.py` module (CLI argument validation):

| Test Class | What It Tests |
|------------|---------------|
| `TestIsValidVersion` | Semver `v1.2.3` format validation |
| `TestIsValidUrl` | HTTP/HTTPS URL validation |
| `TestNoneOrEmpty` | Null / empty-string detection |
| `TestValidateSubnet` | Subnet CIDR range / VNet membership checks |
| `TestImageNamesValidator` | `--image-names` must be a list |
| `TestYamlOutValidator` | Mutually-exclusive output arguments |
| `TestUserValidator` | `--user-id` required-argument check |
| `TestProcessBakeRepoValidateNamespace` | Integration: validates a full repo directory |
| `TestProcessSandboxCreateNamespace` | Integration: validates sandbox-create arguments |

## Fixtures (`conftest.py`)

Shared fixtures are defined in `conftest.py` and automatically available to all test modules:

| Fixture | Description |
|---------|-------------|
| `mock_cmd` | Mock Azure CLI `cmd` object with stubbed `cli_ctx` |
| `sample_sandbox_dict` | Valid sandbox configuration dict (camelCase) |
| `sample_gallery_dict` | Valid gallery configuration dict |
| `sample_image_dict` | Valid Windows image dict (minimal config) |
| `sample_linux_image_dict` | Valid Linux image dict with explicit base |
| `sample_bake_config_dict` | Complete `BakeConfig` dict (sandbox + gallery) |
| `tmp_repo` | Temporary directory with `.git/`, `bake.yml`, and an image dir |
| `clean_env` | Removes CI-related env vars for a known-clean starting state |
| `make_namespace(**kwargs)` | Helper function to create `SimpleNamespace` objects |

## Writing New Tests

1. **Naming**: Create files as `test_<module>.py` in this directory. Use `Test*` classes and `test_*` functions.
2. **Fixtures**: Reuse fixtures from `conftest.py`. Add new shared fixtures there rather than duplicating setup across files.
3. **Mocking**: External calls (Azure SDK, HTTP, file I/O) should be mocked with `unittest.mock.patch`. No Azure credentials should be required.
4. **Assertions**: Use `pytest.raises` with a `match` regex for expected errors. Prefer specific `azure.cli.core.azclierror` types (e.g., `ValidationError`, `InvalidArgumentValueError`).
5. **Parametrize**: Use `@pytest.mark.parametrize` for testing multiple inputs against the same logic.

### Example

```python
import pytest
from azext_bake._data import ImageBase

class TestImageBaseExample:
    def test_valid_base(self):
        base = ImageBase({'publisher': 'pub', 'offer': 'off', 'sku': 'sku1'})
        assert base.publisher == 'pub'

    @pytest.mark.parametrize('missing', ['publisher', 'offer', 'sku'])
    def test_missing_required_field(self, missing):
        obj = {'publisher': 'p', 'offer': 'o', 'sku': 's'}
        del obj[missing]
        with pytest.raises(Exception, match='missing required property'):
            ImageBase(obj)
```

## CI Integration

Tests run automatically on every push and pull request via GitHub Actions. See `.github/workflows/ci.yml` for the workflow configuration.
