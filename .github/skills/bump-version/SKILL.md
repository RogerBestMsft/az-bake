---
name: bump-version
description: "Bump the az-bake extension version using bump-version.py. USE FOR: bumping major/minor/patch versions, creating prerelease versions, updating version across all project files, preparing a release."
argument-hint: "Describe version bump: major, minor, patch, or prerelease with optional notes"
---

# Bump Version

Bump the az-bake extension version by running `tools/bump-version.py`. The script updates version strings in `setup.py`, `HISTORY.rst`, `Dockerfile`, and `README.md`.

> **Non-interactive:** Parse the user's request to determine the bump type and release notes, then run the command without asking for confirmation. Default to a **patch** bump when the user doesn't specify.

## When to Use

- Bumping the version before a release (major, minor, or patch)
- Creating a prerelease version for CI/preview workflows
- Adding release notes to HISTORY.rst as part of a version bump

## Prerequisites

The development environment must be set up with the venv created. The `packaging` module must be available (installed with the dev extras).

Verify by checking that `.venv` exists. If not, tell the user to run the **setup-dev** skill first.

## Arguments

The script accepts these flags — map the user request to the right combination:

| User says | Flags |
|---|---|
| "bump version" / "patch bump" / no specifics | `--patch` (default) |
| "major bump" / "bump major" | `--major` |
| "minor bump" / "bump minor" | `--minor` |
| "prerelease" / "preview" / "pre" | `--pre` |
| "prerelease with suffix dev" | `--pre dev` |
| "prerelease number 42" | `--pre --pre-number 42` |
| "major prerelease" | `--major --pre` |

Only one of `--major`, `--minor`, `--patch` can be specified. `--pre` can combine with any of them.

### Prerelease Decision Tree

```
Is this a prerelease / preview / dev / CI build?
├─ NO → Use --major, --minor, or --patch (default: --patch)
└─ YES → Start with --pre
     │
     ├─ Did the user specify a suffix (e.g. "dev", "alpha", "rc")?
     │   ├─ YES → --pre <suffix>       (e.g. --pre dev)
     │   └─ NO  → --pre                (defaults to "pre")
     │
     ├─ Did the user specify a run/build number?
     │   ├─ YES → --pre-number <N>     (e.g. --pre-number 42)
     │   └─ NO  → omit --pre-number    (defaults to 0)
     │
     └─ Did the user specify a base bump level?
         ├─ "major prerelease"  → --major --pre
         ├─ "minor prerelease"  → --minor --pre
         ├─ "patch prerelease"  → --patch --pre
         └─ No bump specified   → --patch --pre (default)
```

**Result format:** `MAJOR.MINOR.PATCH.SUFFIX<NUMBER>` (e.g. `0.5.0.dev42`)

Release notes default to "Bug fixes and minor improvements" if the user doesn't provide any. When the user provides notes, pass each note as a separate string argument to `--notes`.

## Procedure

### 1. Activate the virtual environment

**Windows (PowerShell):**
```powershell
& .venv\Scripts\Activate.ps1
```

**Linux/macOS (bash):**
```bash
source .venv/bin/activate
```

### 2. Run bump-version.py

From the repo root, run:

```bash
python tools/bump-version.py <flags>
```

**Examples:**

Patch bump with default notes:
```bash
python tools/bump-version.py --patch
```

Minor bump with custom notes:
```bash
python tools/bump-version.py --minor --notes "Added new bake command" "Improved error handling"
```

Major bump:
```bash
python tools/bump-version.py --major --notes "Breaking: redesigned configuration format"
```

Prerelease with custom suffix and run number:
```bash
python tools/bump-version.py --pre dev --pre-number 42
```

### 3. Report Results

After the script completes, summarize:

- Previous version → new version (shown in script output)
- Which files were updated and which were skipped
- The release notes that were added to HISTORY.rst

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: packaging` | Run `pip install packaging` in the venv |
| `no version found in HISTORY.rst` | Ensure HISTORY.rst has a version line matching `X.Y.Z` |
| `no version found in setup.py` | Ensure `setup.py` contains `VERSION = 'X.Y.Z'` |
| Version string not found in Dockerfile/README | Script skips gracefully — this is normal when those files use build args |

## Reference

The bump-version script is at [tools/bump-version.py](../../../tools/bump-version.py).
