Git
===

Purpose
-------
Install and configure Git for source control on Windows Dev Box.

Task Structure
--------------
This task uses the Azure Dev Box customization format:

```yaml
$schema: 1.0
tasks:
  - name: install-git
    description: Install and configure Git for source control
    parameters:
      command: winget
      packageId: Git.Git
      runAsUser: true
```

Verify
------
```bash
git --version
```