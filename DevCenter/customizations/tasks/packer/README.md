HashiCorp Packer
=================

Purpose
-------
Build machine images used by this repository (`templates/packer`) on Windows Dev Box.

Task Structure
--------------
This task uses the Azure Dev Box customization format:

```yaml
$schema: 1.0
tasks:
  - name: install-packer
    description: Install HashiCorp Packer
    parameters:
      command: winget
      packageId: HashiCorp.Packer
      runAsUser: true
```

Verify
------
```bash
packer --version
```