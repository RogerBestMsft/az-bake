# Analyze Business Logic

Analyze the business logic of the az-bake project. Focus on:

1. **Data models** (`bake/azext_bake/_data.py`): Review dataclass definitions, validation logic, and `__init__` methods to ensure all fields are correctly initialized from YAML input and all optional fields have appropriate defaults.

2. **Packer integration** (`bake/azext_bake/_packer.py`): Review provisioner injection logic, including how choco, winget, powershell, and update provisioners are injected into packer build files.

3. **Command handlers** (`bake/azext_bake/custom.py`): Review the `bake_sandbox_create`, `bake_repo_build`, `bake_image_create`, `bake_image_bump`, `bake_builder_build`, and `bake_yaml_export` functions for correctness.

4. **Validators** (`bake/azext_bake/_validators.py`): Review how YAML config files are parsed and validated before commands run.

5. **Constants** (`bake/azext_bake/_constants.py`): Verify packer provisioner templates, schema URLs, and environment constants.

Report any bugs, missing field initializations, or logic errors found, along with suggested fixes.
