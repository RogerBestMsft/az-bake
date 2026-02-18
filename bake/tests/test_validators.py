# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from azure.cli.core.azclierror import (
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
    ValidationError,
)

from azext_bake._validators import (
    _is_valid_url,
    _is_valid_version,
    _none_or_empty,
    image_names_validator,
    user_validator,
    validate_subnet,
    yaml_out_validator,
)

from .conftest import make_namespace


# -------------------------------------------------------
# _is_valid_version
# -------------------------------------------------------

class TestIsValidVersion:
    @pytest.mark.parametrize('version', ['v1.2.3', 'v0.0.0', 'v10.20.30'])
    def test_valid(self, version):
        assert _is_valid_version(version) is True

    @pytest.mark.parametrize('version', [
        '1.2.3',       # no 'v' prefix
        'v1.2',        # only two segments
        'v1.2.3-pre',  # pre-release suffix
        'vx.y.z',      # non-numeric
        '',
        'v',
    ])
    def test_invalid(self, version):
        assert _is_valid_version(version) is False


# -------------------------------------------------------
# _is_valid_url
# -------------------------------------------------------

class TestIsValidUrl:
    @pytest.mark.parametrize('url', [
        'https://example.com',
        'http://example.com/path?q=1',
        'https://github.com/rogerbestmsft/az-bake/releases/download/v0.3.21/templates.json',
    ])
    def test_valid(self, url):
        assert _is_valid_url(url) is True

    @pytest.mark.parametrize('url', [
        'ftp://example.com',
        'not-a-url',
        '',
    ])
    def test_invalid(self, url):
        assert _is_valid_url(url) is False


# -------------------------------------------------------
# _none_or_empty
# -------------------------------------------------------

class TestNoneOrEmpty:
    @pytest.mark.parametrize('val', [None, '', '""', "''"])
    def test_truthy(self, val):
        assert _none_or_empty(val) is True

    @pytest.mark.parametrize('val', ['hello', ' ', '0', 'false'])
    def test_falsy(self, val):
        assert _none_or_empty(val) is False


# -------------------------------------------------------
# validate_subnet
# -------------------------------------------------------

class TestValidateSubnet:
    def test_valid_subnet(self, mock_cmd):
        ns = make_namespace(
            default_subnet_name='default',
            default_subnet_address_prefix='10.0.0.0/24',
        )
        # Should NOT raise
        validate_subnet(mock_cmd, ns, 'default', ['10.0.0.0/16'])

    def test_subnet_outside_vnet(self, mock_cmd):
        ns = make_namespace(
            default_subnet_name='default',
            default_subnet_address_prefix='192.168.1.0/24',
        )
        with pytest.raises(InvalidArgumentValueError, match='not within the vnet address space'):
            validate_subnet(mock_cmd, ns, 'default', ['10.0.0.0/16'])

    def test_empty_subnet_name(self, mock_cmd):
        ns = make_namespace(
            default_subnet_name='',
            default_subnet_address_prefix='10.0.0.0/24',
        )
        with pytest.raises(InvalidArgumentValueError, match='must have a value'):
            validate_subnet(mock_cmd, ns, 'default', ['10.0.0.0/16'])

    def test_empty_subnet_prefix(self, mock_cmd):
        ns = make_namespace(
            default_subnet_name='default',
            default_subnet_address_prefix='',
        )
        with pytest.raises(InvalidArgumentValueError, match='must be a valid CIDR prefix'):
            validate_subnet(mock_cmd, ns, 'default', ['10.0.0.0/16'])

    def test_none_subnet_name(self, mock_cmd):
        ns = make_namespace(
            default_subnet_name=None,
            default_subnet_address_prefix='10.0.0.0/24',
        )
        with pytest.raises(InvalidArgumentValueError, match='must have a value'):
            validate_subnet(mock_cmd, ns, 'default', ['10.0.0.0/16'])


# -------------------------------------------------------
# image_names_validator
# -------------------------------------------------------

class TestImageNamesValidator:
    def test_none_is_ok(self, mock_cmd):
        ns = make_namespace(image_names=None)
        image_names_validator(mock_cmd, ns)  # should not raise

    def test_list_is_ok(self, mock_cmd):
        ns = make_namespace(image_names=['img1', 'img2'])
        image_names_validator(mock_cmd, ns)  # should not raise

    def test_string_raises(self, mock_cmd):
        ns = make_namespace(image_names='img1')
        with pytest.raises(InvalidArgumentValueError, match='must be a list'):
            image_names_validator(mock_cmd, ns)


# -------------------------------------------------------
# yaml_out_validator
# -------------------------------------------------------

class TestYamlOutValidator:
    def test_default_outfile_no_conflict(self, mock_cmd):
        """When outfile has is_default attribute, it's not user-specified."""
        outfile = MagicMock()
        outfile.is_default = True
        outfile.__str__ = lambda self: './bake.yml'
        ns = make_namespace(outfile=outfile, outdir=None, stdout=False)
        yaml_out_validator(mock_cmd, ns)  # should not raise

    def test_outdir_and_stdout_conflict(self, mock_cmd):
        ns = make_namespace(outfile=None, outdir='./out', stdout=True)
        with pytest.raises(MutuallyExclusiveArgumentError):
            yaml_out_validator(mock_cmd, ns)

    def test_outfile_and_stdout_conflict(self, mock_cmd):
        ns = make_namespace(outfile='./bake.yml', outdir=None, stdout=True)
        with pytest.raises(MutuallyExclusiveArgumentError):
            yaml_out_validator(mock_cmd, ns)

    def test_outfile_and_outdir_conflict(self, mock_cmd):
        ns = make_namespace(outfile='./bake.yml', outdir='./out', stdout=False)
        with pytest.raises(MutuallyExclusiveArgumentError):
            yaml_out_validator(mock_cmd, ns)

    def test_stdout_only_ok(self, mock_cmd):
        ns = make_namespace(outfile=None, outdir=None, stdout=True)
        yaml_out_validator(mock_cmd, ns)  # should not raise

    def test_outdir_resolves(self, mock_cmd, tmp_path):
        ns = make_namespace(outfile=None, outdir=str(tmp_path), stdout=False)
        yaml_out_validator(mock_cmd, ns)
        assert ns.outdir == tmp_path.resolve()


# -------------------------------------------------------
# user_validator
# -------------------------------------------------------

class TestUserValidator:
    def test_empty_string_raises(self, mock_cmd):
        ns = make_namespace(user_id='')
        # Need to mock cmd.arguments for the error message
        mock_cmd.arguments = {
            'user_id': MagicMock(type=MagicMock(settings={'options_list': ['--user-id']}))
        }
        with pytest.raises(RequiredArgumentMissingError, match="--user-id"):
            user_validator(mock_cmd, ns)

    def test_non_empty_passes(self, mock_cmd):
        ns = make_namespace(user_id='some-guid')
        user_validator(mock_cmd, ns)  # should not raise


# -------------------------------------------------------
# Integration: process_bake_repo_validate_namespace
# -------------------------------------------------------

class TestProcessBakeRepoValidateNamespace:
    """Integration test using a temporary repo directory structure."""

    def test_valid_repo(self, mock_cmd, tmp_repo):
        from azext_bake._validators import process_bake_repo_validate_namespace

        ns = make_namespace(
            repository_path=str(tmp_repo),
            image_names=None,
            images=None,
            sandbox=None,
            gallery=None,
            bake_obj=None,
        )
        # Should not raise — the tmp_repo fixture has a valid layout
        process_bake_repo_validate_namespace(mock_cmd, ns)
        # After validation, sandbox and gallery should be populated from bake.yml
        assert ns.sandbox is not None
        assert ns.gallery is not None
        assert len(ns.images) > 0

    def test_missing_images_dir(self, mock_cmd, tmp_path):
        from azext_bake._validators import process_bake_repo_validate_namespace

        # Create .git but no images/
        git_dir = tmp_path / '.git'
        git_dir.mkdir()
        (git_dir / 'config').write_text(
            '[remote "origin"]\n\turl = https://github.com/org/repo.git\n', encoding='utf-8')
        (tmp_path / 'bake.yml').write_text('version: 1\n', encoding='utf-8')

        ns = make_namespace(
            repository_path=str(tmp_path),
            image_names=None,
            images=None,
            sandbox=None,
            gallery=None,
            bake_obj=None,
        )
        with pytest.raises(ValidationError, match='images'):
            process_bake_repo_validate_namespace(mock_cmd, ns)

    def test_missing_repo_path(self, mock_cmd):
        from azext_bake._validators import process_bake_repo_validate_namespace

        ns = make_namespace(
            repository_path=None,
            image_names=None,
            images=None,
        )
        with pytest.raises(RequiredArgumentMissingError):
            process_bake_repo_validate_namespace(mock_cmd, ns)


# -------------------------------------------------------
# Integration: process_sandbox_create_namespace
# -------------------------------------------------------

class TestProcessSandboxCreateNamespace:
    """Tests for sandbox create validation with mocked external dependencies."""

    @patch('azext_bake._validators.templates_version_validator')
    @patch('azext_bake._validators.gallery_resource_id_validator')
    @patch('azext_bake._validators.validate_sandbox_tags')
    def test_valid_namespace(self, mock_tags, mock_gallery, mock_templates, mock_cmd):
        from azext_bake._validators import process_sandbox_create_namespace

        ns = make_namespace(
            name_prefix='TestSandbox',
            sandbox_resource_group_name=None,
            vnet_address_prefix='10.0.0.0/16',
            default_subnet_name='default',
            default_subnet_address_prefix='10.0.0.0/24',
            builders_subnet_name='builders',
            builders_subnet_address_prefix='10.0.1.0/24',
            tags=None,
            gallery_resource_id=None,
            version=None,
            prerelease=False,
            local_templates=False,
            templates_url=None,
            template_file=None,
        )

        process_sandbox_create_namespace(mock_cmd, ns)

        # sandbox rg name should default to name_prefix
        assert ns.sandbox_resource_group_name == 'TestSandbox'
        mock_templates.assert_called_once()
        mock_gallery.assert_called_once()

    @patch('azext_bake._validators.templates_version_validator')
    def test_empty_vnet_prefix_raises(self, mock_templates, mock_cmd):
        from azext_bake._validators import process_sandbox_create_namespace

        ns = make_namespace(
            name_prefix='TestSandbox',
            sandbox_resource_group_name='my-rg',
            vnet_address_prefix='',
            default_subnet_name='default',
            default_subnet_address_prefix='10.0.0.0/24',
            builders_subnet_name='builders',
            builders_subnet_address_prefix='10.0.1.0/24',
            tags=None,
            gallery_resource_id=None,
            version=None,
            prerelease=False,
            local_templates=False,
            templates_url=None,
            template_file=None,
        )

        with pytest.raises(InvalidArgumentValueError, match='vnet'):
            process_sandbox_create_namespace(mock_cmd, ns)
