7-Zip (archive utility)
========================

Purpose
-------
Useful for handling archives during image builds and asset preparation on Windows Dev Box.

Task Structure
--------------
This task uses the Azure Dev Box customization format:

```yaml
$schema: 1.0
tasks:
  - name: install-7zip
    description: Install 7-Zip archive utility
    parameters:
      command: winget
      packageId: 7zip.7zip
      runAsUser: true
```

Verify
------
```bash
7z --help
```