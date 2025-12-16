`azdev` (Azure extension dev tool)
==================================

Purpose
-------
Tooling for developing and testing Azure CLI extensions on Windows Dev Box.

Task Structure
--------------
This task uses the Azure Dev Box customization format:

```yaml
$schema: 1.0
tasks:
  - name: install-azdev
    description: Install azdev CLI extension development tool
    parameters:
      command: powershell
      script: pip install azdev
      runAsUser: true
```

Usage
-----
From repository root:
```bash
azdev setup -r . -e bake
azdev test  # run extension tests if configured
```

Verify
------
```bash
azdev --version
```