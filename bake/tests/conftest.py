# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
Pytest fixtures and configuration for az bake tests.

This module provides shared fixtures for testing the az bake extension:
- Mock CLI contexts
- Sample configuration data
- Temporary file/directory helpers
- Azure SDK client mocks
"""

import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


# ------------------------------------
# Sample Data Fixtures
# ------------------------------------

@pytest.fixture
def sample_sandbox_dict():
    """Sample sandbox configuration dictionary."""
    return {
        'resourceGroup': 'test-sandbox-rg',
        'subscription': '00000000-0000-0000-0000-000000000001',
        'virtualNetwork': 'test-vnet',
        'virtualNetworkResourceGroup': 'test-sandbox-rg',
        'defaultSubnet': 'default',
        'builderSubnet': 'builders',
        'keyVault': 'test-kv',
        'storageAccount': 'teststorage',
        'identityId': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/test-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/test-id'
    }


@pytest.fixture
def sample_gallery_dict():
    """Sample gallery configuration dictionary."""
    return {
        'name': 'test_gallery',
        'resourceGroup': 'gallery-rg',
        'subscription': '00000000-0000-0000-0000-000000000002'
    }


@pytest.fixture
def sample_image_dict():
    """Sample image configuration dictionary."""
    return {
        'name': 'test-image',  # Required when no file path
        'publisher': 'TestPublisher',
        'offer': 'TestOffer',
        'sku': 'test-sku',
        'version': '1.0.0',
        'os': 'Windows',
        'replicaLocations': ['eastus', 'westus'],
        'description': 'Test image description',
        'update': True,
        'base': {
            'publisher': 'microsoftwindowsdesktop',
            'offer': 'windows-ent-cpc',
            'sku': 'win11-22h2-ent-cpc-m365'
        }
    }


@pytest.fixture
def sample_image_with_choco(sample_image_dict):
    """Sample image configuration with Chocolatey packages."""
    sample_image_dict['install'] = {
        'choco': {
            'packages': ['git', 'vscode', 'nodejs']
        }
    }
    return sample_image_dict


@pytest.fixture
def sample_image_with_scripts(sample_image_dict):
    """Sample image configuration with PowerShell scripts."""
    sample_image_dict['install'] = {
        'scripts': {
            'powershell': [
                {'path': 'scripts/Install-Tools.ps1', 'restart': False},
                {'path': 'scripts/Configure-System.ps1', 'restart': True}
            ]
        }
    }
    return sample_image_dict


@pytest.fixture
def sample_bake_config_dict(sample_sandbox_dict, sample_gallery_dict):
    """Sample bake.yml configuration dictionary."""
    return {
        'version': 1.0,
        'sandbox': sample_sandbox_dict,
        'gallery': sample_gallery_dict
    }


# ------------------------------------
# Temporary File/Directory Fixtures
# ------------------------------------

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_repo(temp_dir):
    """Create a temporary repository structure."""
    # Create .git directory
    git_dir = temp_dir / '.git'
    git_dir.mkdir()
    
    # Create git config
    git_config = git_dir / 'config'
    git_config.write_text('''[core]
    repositoryformatversion = 0
[remote "origin"]
    url = https://github.com/testorg/testrepo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
''')
    
    # Create images directory
    images_dir = temp_dir / 'images'
    images_dir.mkdir()
    
    return temp_dir


@pytest.fixture
def temp_image_dir(temp_repo, sample_image_dict):
    """Create a temporary image directory with image.yml."""
    import yaml
    
    image_dir = temp_repo / 'images' / 'TestImage'
    image_dir.mkdir(parents=True)
    
    image_file = image_dir / 'image.yml'
    image_file.write_text(yaml.safe_dump(sample_image_dict))
    
    return image_dir


@pytest.fixture
def temp_bake_yaml(temp_repo, sample_bake_config_dict):
    """Create a temporary bake.yml file."""
    import yaml
    
    bake_file = temp_repo / 'bake.yml'
    bake_file.write_text(yaml.safe_dump(sample_bake_config_dict))
    
    return bake_file


# ------------------------------------
# Mock Fixtures
# ------------------------------------

@pytest.fixture
def mock_cli_ctx():
    """Create a mock Azure CLI context."""
    ctx = MagicMock()
    ctx.cli_ctx = MagicMock()
    ctx.cli_ctx.get_progress_controller.return_value = MagicMock()
    return ctx


@pytest.fixture
def mock_github_releases():
    """Mock GitHub releases response."""
    return [
        {
            'tag_name': 'v1.0.0',
            'prerelease': False,
            'assets': [
                {
                    'name': 'templates.json',
                    'browser_download_url': 'https://example.com/templates.json'
                },
                {
                    'name': 'index.json',
                    'browser_download_url': 'https://example.com/index.json'
                }
            ]
        },
        {
            'tag_name': 'v0.9.0',
            'prerelease': False,
            'assets': []
        },
        {
            'tag_name': 'v1.1.0-pre',
            'prerelease': True,
            'assets': []
        }
    ]


@pytest.fixture
def mock_templates_json():
    """Mock templates.json content."""
    return {
        'builder': {
            'builder.json': {
                'downloadUrl': 'https://example.com/builder.json'
            }
        },
        'sandbox': {
            'sandbox.json': {
                'downloadUrl': 'https://example.com/sandbox.json'
            }
        },
        'packer': {
            'build.pkr.hcl': {
                'downloadUrl': 'https://example.com/build.pkr.hcl'
            }
        },
        'install': {
            'choco.json': {
                'downloadUrl': 'https://example.com/choco.json'
            }
        }
    }


# ------------------------------------
# Environment Fixtures
# ------------------------------------

@pytest.fixture
def clean_env():
    """Ensure clean environment without builder-specific variables."""
    env_vars = [
        'AZ_BAKE_IMAGE_BUILDER',
        'AZ_BAKE_BUILD_IMAGE_NAME',
        'AZ_BAKE_IMAGE_BUILDER_VERSION',
        'CI',
        'GITHUB_ACTION',
        'TF_BUILD'
    ]
    
    old_values = {}
    for var in env_vars:
        old_values[var] = os.environ.pop(var, None)
    
    yield
    
    # Restore original values
    for var, value in old_values.items():
        if value is not None:
            os.environ[var] = value


@pytest.fixture
def github_ci_env(clean_env):
    """Set up GitHub Actions CI environment variables."""
    os.environ['CI'] = 'true'
    os.environ['GITHUB_ACTION'] = 'test-action'
    os.environ['GITHUB_SERVER_URL'] = 'https://github.com'
    os.environ['GITHUB_REPOSITORY'] = 'testorg/testrepo'
    os.environ['GITHUB_REF'] = 'refs/heads/main'
    os.environ['GITHUB_SHA'] = 'abc123def456'
    os.environ['GITHUB_TOKEN'] = 'test-token'
    
    yield
    
    for var in ['CI', 'GITHUB_ACTION', 'GITHUB_SERVER_URL', 'GITHUB_REPOSITORY', 
                'GITHUB_REF', 'GITHUB_SHA', 'GITHUB_TOKEN']:
        os.environ.pop(var, None)


@pytest.fixture
def devops_ci_env(clean_env):
    """Set up Azure DevOps CI environment variables."""
    os.environ['TF_BUILD'] = 'True'
    os.environ['BUILD_REPOSITORY_URI'] = 'https://dev.azure.com/testorg/testproject/_git/testrepo'
    os.environ['BUILD_SOURCEBRANCH'] = 'refs/heads/main'
    os.environ['BUILD_SOURCEVERSION'] = 'abc123def456'
    os.environ['SYSTEM_ACCESSTOKEN'] = 'test-token'
    
    yield
    
    for var in ['TF_BUILD', 'BUILD_REPOSITORY_URI', 'BUILD_SOURCEBRANCH',
                'BUILD_SOURCEVERSION', 'SYSTEM_ACCESSTOKEN']:
        os.environ.pop(var, None)
