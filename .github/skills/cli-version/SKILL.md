---
name: cli-version
description: "Read the current az-bake CLI version and release notes. USE FOR: querying the current extension version, extracting release notes from HISTORY.rst, checking version before a release, verifying version output matches setup.py."
---

# CLI Version

Read the current az-bake extension version and its release notes by running `tools/cli-version.py`. The script extracts `VERSION` from `bake/setup.py` and parses the matching changelog section in `bake/HISTORY.rst`.

> **Non-interactive:** Run the command automatically without asking the user for confirmation. Detect the OS, resolve paths, and choose the correct activation command autonomously.

## When to Use

- Checking the current extension version
- Extracting release notes for the current version from HISTORY.rst
- Verifying version output before a release or version bump
- Debugging version mismatch issues between setup.py and HISTORY.rst

## Prerequisites

Python must be available. No venv or azdev install is required — the script uses only the standard library.

Verify by checking that `bake/setup.py` and `bake/HISTORY.rst` exist in the repo root.

## Procedure

### 1. Run cli-version.py

From the repo root, run:

```bash
python tools/cli-version.py
```

### 2. Interpret Output

The script prints two things:

1. **Version string** — the value of `VERSION` from `bake/setup.py` (e.g. `0.4.0`)
2. **Release notes** — the changelog entries under that version heading in `bake/HISTORY.rst`, printed both line-by-line and as a comma-separated `changes=` line

If the version in `setup.py` has no matching heading in `HISTORY.rst`, only the version is printed and no release notes appear.

### 3. Report Results

Summarize to the user:

- **Version**: the current version string
- **Release notes**: the extracted changelog entries, or a note that none were found

## CI Behavior

When running in GitHub Actions (`CI=true` and `GITHUB_OUTPUT` is set), the script writes outputs to `$GITHUB_OUTPUT` instead of printing to stdout:

- `version=<version>`
- `changes=<comma-separated notes>`

These outputs are consumed by the `release.yml` and `preview-release.yml` workflows to tag releases and generate release notes.

## Troubleshooting

| Symptom | Fix |
|---|---|
| No version printed | Ensure `bake/setup.py` contains a `VERSION = '...'` line |
| Version printed but no release notes | Add a matching version heading and entries to `bake/HISTORY.rst` |
| Wrong version shown | Check that `bake/setup.py` has been updated (run **bump-version** skill) |

## Reference Script

The script is at [tools/cli-version.py](../../../tools/cli-version.py).
