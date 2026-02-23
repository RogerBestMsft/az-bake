# Comment Improvement Review - Todo List

This file tracks the progress of reviewing and improving comments in the az-bake Python CLI extension.

## Files to Review

| File | Status | Notes |
|------|--------|-------|
| `bake/azext_bake/__init__.py` | ✅ Done | Added module and class docstrings |
| `bake/azext_bake/commands.py` | ✅ Done | Added module docstring explaining command groups |
| `bake/azext_bake/custom.py` | ✅ Done | Added module docstring and function docstrings for all handlers |
| `bake/azext_bake/_data.py` | ✅ Done | Added module docstring explaining domain models and validation |
| `bake/azext_bake/_arm.py` | ✅ Done | Added module docstring and key function docstrings |
| `bake/azext_bake/_packer.py` | ✅ Done | Added module docstring explaining provisioner injection |
| `bake/azext_bake/_sandbox.py` | ✅ Done | Added module docstring explaining naming conventions |
| `bake/azext_bake/_client_factory.py` | ✅ Done | Added module and function docstrings |
| `bake/azext_bake/_completers.py` | ✅ Done | Added module and function docstrings |
| `bake/azext_bake/_constants.py` | ✅ Done | Added module docstring and inline comments for key constants |
| `bake/azext_bake/_github.py` | ✅ Done | Added module and function docstrings |
| `bake/azext_bake/_help.py` | ✅ Done | Added module docstring |
| `bake/azext_bake/_params.py` | ✅ Done | Added module docstring explaining parameter framework |
| `bake/azext_bake/_repos.py` | ✅ Done | Added module and class docstrings |
| `bake/azext_bake/_transformers.py` | ✅ Done | Added module docstring |
| `bake/azext_bake/_utils.py` | ✅ Done | Added module docstring and key function docstrings |
| `bake/azext_bake/_validators.py` | ✅ Done | Added module docstring and key validator docstrings |

## Progress Summary

- Total Files: 17
- Completed: 17
- In Progress: 0
- Pending: 0

## Review Complete

All files have been reviewed and comments improved. Key improvements made:
- Added Python module-level docstrings to all files explaining their purpose
- Added function/class docstrings explaining behavior and parameters
- Added inline comments for important constants and configuration values
- Focused on explaining "why" rather than "what" the code does
- Used consistent docstring formatting throughout

## Review Criteria

Comments should:
- Use Python docstrings for modules, classes, and functions
- Explain business logic and domain-specific rules
- Clarify complex algorithms or non-obvious implementation choices
- Document assumptions, constraints, or limitations
- Explain "why" decisions were made

Comments should NOT:
- Restate what the code does (e.g., "# increment counter")
- Duplicate function/variable names
- Be outdated or incorrect
