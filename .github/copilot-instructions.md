# az-bake Development Instructions

## Project Overview

`az-bake` is an Azure CLI extension (`az bake`) for building custom VM images using Packer. The extension source lives in `bake/azext_bake/` and is packaged via `azdev`.

## Code Quality — Linter & Style Checks

All changes to extension source code **must** pass both checks before committing:

```bash
azdev linter bake
azdev style bake
```

- **Linter**: Validates Azure CLI conventions (parameter naming, help text, command structure, etc.). Exclusions are defined in `linter_exclusions.yml`.
- **Style**: Enforces PEP 8 with a **max line length of 200** characters (configured in `.vscode/settings.json` for autopep8). Import sorting uses isort with a line length of **120**.

The CI workflow (`ci.yml`) runs both checks on every push and PR via `tools/build-cli.sh`. Merges to `main` will be blocked if either check fails.

## Project Structure

| Path | Purpose |
|------|---------|
| `bake/azext_bake/` | Extension source code |
| `bake/azext_bake/custom.py` | Command implementations |
| `bake/azext_bake/commands.py` | Command registration and grouping |
| `bake/azext_bake/_params.py` | Parameter definitions |
| `bake/azext_bake/_help.py` | Help text |
| `bake/azext_bake/_validators.py` | Input validators |
| `bake/azext_bake/templates/` | Bicep, Packer, and install templates |
| `bake/setup.py` | Package config — `VERSION` is the single source of truth |
| `bake/HISTORY.rst` | Release notes — must have an entry for each version |
| `tests/` | Pytest test suite |
| `tools/` | CI/CD helper scripts used by GitHub Actions workflows |
| `builder/` | Docker image for the bake builder |
| `schema/` | JSON schemas for `bake.yml` and `image.yml` |

## Adding or Modifying Commands

Follow this order when adding a new command:

1. **`custom.py`** — Implement the function
2. **`commands.py`** — Register the command in the appropriate group
3. **`_params.py`** — Define parameters
4. **`_help.py`** — Add help text
5. **`_validators.py`** — Add validators if needed

## Tools Scripts (used by CI/CD workflows)

| Script | Used By | Purpose |
|--------|---------|---------|
| `tools/cli-version.py` | `release.yml`, `preview-release.yml` | Reads `VERSION` from `bake/setup.py` and extracts release notes from `HISTORY.rst` |
| `tools/build-cli.sh` | `release.yml`, `preview-release.yml`, `ci.yml` | Runs linter, style checks, and builds the extension wheel |
| `tools/prepare-assets.py` | `release.yml`, `preview-release.yml` | Creates `index.json`, compiles Bicep templates, copies schemas to release assets |
| `tools/bump-version.py` | Manual | Bumps version in `bake/setup.py`, `HISTORY.rst`, `builder/Dockerfile`, `README.md` |

## Version Management

- The canonical version is `VERSION` in `bake/setup.py`.
- Use `tools/bump-version.py` to bump versions — it updates all files that reference the version.
- Preview releases append a PEP 440 suffix: `{VERSION}.{suffix}{run_number}` (e.g. `0.4.0.dev42`).
- The `builder/Dockerfile` uses `IMAGE_VERSION` and `REPO_URL` build args — these are passed in by the workflows.

## Testing

```bash
pip install -e ./bake[dev]
pytest tests/ -v --tb=short
```

- **All tests must pass** before any change is considered complete.
- Any code change should include new or updated tests covering the modified behavior.
- **Never modify or delete existing tests without explicit user approval.** If a test needs to change, propose the change and wait for confirmation before applying it.
- Config is in `bake/pytest.ini` (test paths, short tracebacks, quiet by default).
- Tests stub out Azure CLI internals via `conftest.py` — no live Azure CLI install needed to run tests.
- CI runs: `pytest tests/ -v --tb=short --cov=azext_bake --cov-report=term-missing`

## Development Environment Setup

Use the setup scripts which handle venv creation, azdev installation, and extension registration:

- **Windows**: `.\setup-dev.ps1`
- **Linux/macOS**: `./setup-dev.sh`

Both accept `--clean`, `--skip-venv`, `--skip-azdev`, and `--python <command>` flags.

Requires: Python 3.8+, pip, Git. Azure CLI recommended for runtime testing.

## Dependencies

- Runtime: `azure-cli-core`
- Dev: `azdev`, `setuptools==70.0.0` (pinned for azdev linter compatibility), `pytest>=7.0`, `pytest-cov>=4.0`

## Docker (Builder Image)

The `builder/Dockerfile` builds the bake builder image pushed to `ghcr.io/rogerbestmsft/az-bake/builder`. It accepts these build args:

- `IMAGE_VERSION` — the bake extension version
- `BUILD_DATE` — ISO 8601 build timestamp
- `REPO_URL` — repository URL (defaults to `https://github.com/rogerbestmsft/az-bake`)
