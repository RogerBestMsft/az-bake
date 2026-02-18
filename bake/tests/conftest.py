# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

import sys
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

# Stub out azure.cli.command_modules and its submodules so that the
# azext_bake import chain (→ _params → _validators → _sandbox → _arm)
# does not fail when azure-cli is not fully installed (e.g. in CI).
for _mod in (
    'azure.cli.command_modules',
    'azure.cli.command_modules.role',
    'azure.cli.command_modules.role.custom',
):
    sys.modules.setdefault(_mod, MagicMock())

import pytest


@pytest.fixture
def mock_cmd():
    """Creates a mock Azure CLI cmd object with stubbed cli_ctx."""
    cmd = MagicMock()
    cmd.cli_ctx = MagicMock()
    cmd.cli_ctx.cloud = MagicMock()
    cmd.cli_ctx.cloud.endpoints = MagicMock()
    cmd.arguments = {}
    return cmd


@pytest.fixture
def sample_sandbox_dict():
    """Valid sandbox dict in camelCase (as read from YAML)."""
    return {
        'resourceGroup': 'my-sandbox-rg',
        'subscription': '00000000-0000-0000-0000-000000000001',
        'virtualNetwork': 'my-vnet',
        'virtualNetworkResourceGroup': 'my-vnet-rg',
        'defaultSubnet': 'default',
        'builderSubnet': 'builders',
        'keyVault': 'my-keyvault',
        'storageAccount': 'mystorageaccount',
        'identityId': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/my-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/my-identity',
    }


@pytest.fixture
def sample_gallery_dict():
    """Valid gallery dict in camelCase."""
    return {
        'name': 'MyGallery',
        'resourceGroup': 'my-gallery-rg',
        'subscription': '00000000-0000-0000-0000-000000000002',
    }


@pytest.fixture
def sample_image_dict():
    """Valid image dict in camelCase (Windows with minimal config)."""
    return {
        'name': 'TestImage',
        'publisher': 'TestPublisher',
        'offer': 'TestOffer',
        'replicaLocations': ['eastus', 'westus2'],
        'sku': 'test-sku',
        'version': '1.0.0',
        'os': 'Windows',
    }


@pytest.fixture
def sample_linux_image_dict():
    """Valid Linux image dict requiring an explicit base."""
    return {
        'name': 'TestLinuxImage',
        'publisher': 'TestPublisher',
        'offer': 'TestOffer',
        'replicaLocations': ['eastus'],
        'sku': 'test-sku',
        'version': '1.0.0',
        'os': 'Linux',
        'base': {
            'publisher': 'Canonical',
            'offer': '0001-com-ubuntu-server-jammy',
            'sku': '22_04-lts-gen2',
        },
    }


@pytest.fixture
def sample_bake_config_dict(sample_sandbox_dict, sample_gallery_dict):
    """Valid BakeConfig dict."""
    return {
        'version': 1,
        'sandbox': sample_sandbox_dict,
        'gallery': sample_gallery_dict,
    }


@pytest.fixture
def tmp_repo(tmp_path):
    """Creates a minimal repo layout with bake.yaml and an image dir."""
    # .git directory
    git_dir = tmp_path / '.git'
    git_dir.mkdir()
    (git_dir / 'config').write_text(
        '[remote "origin"]\n\turl = https://github.com/testorg/testrepo.git\n',
        encoding='utf-8',
    )

    # images directory with one image
    images_dir = tmp_path / 'images' / 'TestImage'
    images_dir.mkdir(parents=True)
    (images_dir / 'image.yml').write_text(
        'publisher: TestPublisher\n'
        'offer: TestOffer\n'
        'replicaLocations:\n  - eastus\n'
        'sku: test-sku\n'
        'version: "1.0.0"\n'
        'os: Windows\n',
        encoding='utf-8',
    )

    # bake.yaml
    (tmp_path / 'bake.yml').write_text(
        'version: 1\n'
        'sandbox:\n'
        '  resourceGroup: my-sandbox-rg\n'
        '  subscription: "00000000-0000-0000-0000-000000000001"\n'
        '  virtualNetwork: my-vnet\n'
        '  virtualNetworkResourceGroup: my-vnet-rg\n'
        '  defaultSubnet: default\n'
        '  builderSubnet: builders\n'
        '  keyVault: my-keyvault\n'
        '  storageAccount: mystorageaccount\n'
        '  identityId: /subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/my-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/my-identity\n'
        'gallery:\n'
        '  name: MyGallery\n'
        '  resourceGroup: my-gallery-rg\n'
        '  subscription: "00000000-0000-0000-0000-000000000002"\n',
        encoding='utf-8',
    )

    return tmp_path


@pytest.fixture
def clean_env(monkeypatch):
    """Remove CI-related env vars so tests start from a known state."""
    for var in ['CI', 'GITHUB_ACTION', 'GITHUB_TOKEN', 'GITHUB_REF', 'GITHUB_SHA',
                'GITHUB_SERVER_URL', 'GITHUB_REPOSITORY', 'TF_BUILD', 'SYSTEM_ACCESSTOKEN',
                'BUILD_SOURCEBRANCH', 'BUILD_SOURCEVERSION', 'BUILD_REPOSITORY_URI',
                'AZ_BAKE_IMAGE_BUILDER', 'AZ_BAKE_BUILD_IMAGE_NAME']:
        monkeypatch.delenv(var, raising=False)


def make_namespace(**kwargs):
    """Helper to create a SimpleNamespace with the given attributes."""
    return SimpleNamespace(**kwargs)
