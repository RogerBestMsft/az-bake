Azure CLI
=========

Purpose
-------
CLI for interacting with Azure and testing extension commands on Windows Dev Box.

Task Structure
--------------
This task uses the Azure Dev Box customization format:

```yaml
$schema: 1.0
tasks:
  - name: install-azure-cli
    description: Install Azure CLI
    parameters:
      command: winget
      packageId: Microsoft.AzureCLI
      runAsUser: true
```

Verify
------
```bash
az --version
az login
```