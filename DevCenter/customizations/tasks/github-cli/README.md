GitHub CLI (`gh`)
==================

Purpose
-------
Optional tool for interacting with GitHub (issues, PRs) from the command line on Windows Dev Box.

Task Structure
--------------
This task uses the Azure Dev Box customization format:

```yaml
$schema: 1.0
tasks:
  - name: install-github-cli
    description: Install GitHub CLI
    parameters:
      command: winget
      packageId: GitHub.cli
      runAsUser: true
```

Verify
------
```bash
gh --version
gh auth login
```