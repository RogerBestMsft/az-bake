Python 3 & dev tools
=====================

Purpose
-------
Python runtime and packaging tools used to develop and run the extension code on Windows Dev Box.

Task Structure
--------------
This task uses the Azure Dev Box customization format:

```yaml
$schema: 1.0
tasks:
  - name: install-python
    description: Install Python 3.11
    parameters:
      command: winget
      packageId: Python.Python.3.11
      runAsUser: true
```

Post-Installation Setup
-----------------------
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pip install azdev
```

Verify
------
```bash
python --version
pip --version
```