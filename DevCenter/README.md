DevCenter
=========

This folder holds artifacts for provisioning and configuring Azure DevCenter environments for this repository.

Subfolders
----------

- customizations/
  - Purpose: store customization artifacts applied to DevCenter environments (role assignments, policy snippets, scripts, gallery/custom images, ARM/Bicep snippets).
  - Recommended files: `README.md` per customization, Bicep/ARM templates, JSON parameter files, scripts, and any policy or role definitions.

- environment/
  - Purpose: environment definitions used to create dev boxes or environment-level configurations (environment templates, parameters, variables, and provisioning scripts).
  - Recommended files: per-environment folder or named files like `dev.json`, `prod.json`, `environment.bicep`, and example parameter files.

Notes
-----
- Each subfolder includes a `.gitkeep` placeholder to ensure the directory is tracked. Replace these with actual content as you add customizations and environment definitions.
- Use clear naming conventions and include a `README.md` in each subfolder you add to explain its purpose and usage.

Examples you might add
---------------------
- `customizations/windows-image/` — bicep + scripts to produce a Windows builder image.
- `environment/dev/` — parameters and scripts for a developer workstation environment.

If you want, I can add example templates for a sample environment and a customization (Bicep + parameters).