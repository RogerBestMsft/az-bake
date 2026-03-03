# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from azext_bake._data import Gallery, Image, Sandbox


# -------------------------------------------------------
# bake_repo_build: prerelease parameter
# -------------------------------------------------------

class TestBakeRepoBuildPrerelease:
    """Verify the prerelease flag is forwarded to get_release_templates."""

    def _make_sandbox(self):
        return Sandbox({
            'resourceGroup': 'my-sandbox-rg',
            'subscription': '00000000-0000-0000-0000-000000000001',
            'virtualNetwork': 'my-vnet',
            'virtualNetworkResourceGroup': 'my-vnet-rg',
            'defaultSubnet': 'default',
            'builderSubnet': 'builders',
            'keyVault': 'my-keyvault',
            'storageAccount': 'mystorageaccount',
            'identityId': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/my-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/my-identity',
        })

    def _make_image(self):
        return Image({
            'name': 'TestImage',
            'publisher': 'TestPublisher',
            'offer': 'TestOffer',
            'replicaLocations': ['eastus'],
            'sku': 'test-sku',
            'version': '1.0.0',
            'os': 'Windows',
        })

    def _make_repo(self):
        mock_repo = MagicMock()
        mock_repo.clone_url = 'https://github.com/testorg/testrepo'
        mock_repo.revision = None
        mock_repo.provider = 'github'
        return mock_repo

    def _make_cmd(self):
        cmd = MagicMock()
        hook = MagicMock()
        cmd.cli_ctx.get_progress_controller.return_value = hook
        return cmd

    @patch('azext_bake.custom.deploy_arm_template_at_resource_group')
    @patch('azext_bake.custom.get_template_url', return_value='https://example.com/builder.json')
    @patch('azext_bake.custom.get_release_templates')
    @patch('azext_bake.custom.get_builder_subnet_id', return_value='/sub/net/id')
    def test_prerelease_true_forwarded(self, mock_subnet, mock_get_templates, mock_get_url, mock_deploy):
        from azext_bake.custom import bake_repo_build

        mock_get_templates.return_value = ('v0.5.0-pre', {'builder': {}, 'install': {}, 'packer': {}, 'sandbox': {}})
        mock_deploy.return_value = (MagicMock(), {'logs': {'value': 'log-url'}, 'bake': {'value': 'bake-url'}, 'portal': {'value': 'portal-url'}})

        bake_repo_build(
            cmd=self._make_cmd(),
            repository_path='.',
            sandbox=self._make_sandbox(),
            images=[self._make_image()],
            repo=self._make_repo(),
            prerelease=True,
        )

        mock_get_templates.assert_called_once_with(version=None, prerelease=True, templates_url=None)

    @patch('azext_bake.custom.deploy_arm_template_at_resource_group')
    @patch('azext_bake.custom.get_template_url', return_value='https://example.com/builder.json')
    @patch('azext_bake.custom.get_release_templates')
    @patch('azext_bake.custom.get_builder_subnet_id', return_value='/sub/net/id')
    def test_prerelease_false_by_default(self, mock_subnet, mock_get_templates, mock_get_url, mock_deploy):
        from azext_bake.custom import bake_repo_build

        mock_get_templates.return_value = ('v0.5.0', {'builder': {}, 'install': {}, 'packer': {}, 'sandbox': {}})
        mock_deploy.return_value = (MagicMock(), {'logs': {'value': 'log-url'}, 'bake': {'value': 'bake-url'}, 'portal': {'value': 'portal-url'}})

        bake_repo_build(
            cmd=self._make_cmd(),
            repository_path='.',
            sandbox=self._make_sandbox(),
            images=[self._make_image()],
            repo=self._make_repo(),
        )

        mock_get_templates.assert_called_once_with(version=None, prerelease=False, templates_url=None)

    @patch('azext_bake.custom.deploy_arm_template_at_resource_group')
    @patch('azext_bake.custom.get_template_url', return_value='https://example.com/builder.json')
    @patch('azext_bake.custom.get_release_templates')
    @patch('azext_bake.custom.get_builder_subnet_id', return_value='/sub/net/id')
    def test_prerelease_false_explicit(self, mock_subnet, mock_get_templates, mock_get_url, mock_deploy):
        from azext_bake.custom import bake_repo_build

        mock_get_templates.return_value = ('v0.5.0', {'builder': {}, 'install': {}, 'packer': {}, 'sandbox': {}})
        mock_deploy.return_value = (MagicMock(), {'logs': {'value': 'log-url'}, 'bake': {'value': 'bake-url'}, 'portal': {'value': 'portal-url'}})

        bake_repo_build(
            cmd=self._make_cmd(),
            repository_path='.',
            sandbox=self._make_sandbox(),
            images=[self._make_image()],
            repo=self._make_repo(),
            prerelease=False,
        )

        mock_get_templates.assert_called_once_with(version=None, prerelease=False, templates_url=None)
