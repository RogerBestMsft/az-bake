Visual Studio Code
===================

Purpose
-------
Editor/IDE used by the team for Python and Azure development on Windows Dev Box.

Task Structure
--------------
This task uses the Azure Dev Box customization format:

```yaml
$schema: 1.0
tasks:
  - name: install-vscode
    description: Install Visual Studio Code
    parameters:
      command: winget
      packageId: Microsoft.VisualStudioCode
      runAsUser: true
```

Verify
------
```bash
code --version
```