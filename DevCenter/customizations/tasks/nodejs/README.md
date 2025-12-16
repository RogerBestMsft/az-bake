Node.js (optional)
===================

Purpose
-------
Some tooling or scripts may require Node.js (e.g., linters, formatters) on Windows Dev Box.

Task Structure
--------------
This task uses the Azure Dev Box customization format:

```yaml
$schema: 1.0
tasks:
  - name: install-nodejs
    description: Install Node.js LTS
    parameters:
      command: winget
      packageId: OpenJS.NodeJS.LTS
      runAsUser: true
```

Verify
------
```bash
node --version
npm --version
```