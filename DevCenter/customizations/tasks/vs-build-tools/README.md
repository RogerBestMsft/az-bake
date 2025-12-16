Visual Studio Build Tools (Windows)
===================================

Purpose
-------
Required when compiling native extensions or running Windows-specific builds on Windows Dev Box (optional for purely Python work but recommended for image builds).

Task Structure
--------------
This task uses the Azure Dev Box customization format:

```yaml
$schema: 1.0
tasks:
  - name: install-vs-build-tools
    description: Install Visual Studio Build Tools for native compilation
    parameters:
      command: choco
      packageId: visualstudio2019buildtools
      runAsUser: false
```

Notes
-----
- Requires significant disk space and admin privileges.
- Uses Chocolatey package manager for installation.
