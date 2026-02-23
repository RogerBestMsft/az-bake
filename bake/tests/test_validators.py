# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
Tests for the _validators.py module.

Tests cover input validation functions for CLI commands.
"""

import pytest
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

from azure.cli.core.azclierror import InvalidArgumentValueError, ValidationError, MutuallyExclusiveArgumentError

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from azext_bake._validators import (
    gallery_resource_id_validator,
    bake_source_version_validator,
    templates_version_validator,
    validate_subnet,
)


class TestGalleryResourceIdValidator:
    """Tests for gallery_resource_id_validator function."""
    
    def test_valid_resource_id(self):
        cmd = MagicMock()
        cmd.cli_ctx = MagicMock()
        ns = Namespace()
        ns.gallery_resource_id = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Compute/galleries/gallery'
        
        gallery_resource_id_validator(cmd, ns)
        
        # Should not raise, resource ID is valid format
        assert ns.gallery_resource_id is not None
    
    def test_none_gallery_skipped(self):
        cmd = MagicMock()
        cmd.cli_ctx = MagicMock()
        ns = Namespace()
        ns.gallery_resource_id = None
        
        # Should not raise when gallery is None
        gallery_resource_id_validator(cmd, ns)


class TestBakeSourceVersionValidator:
    """Tests for bake_source_version_validator function."""
    
    def test_no_version_no_action(self):
        """When version is None, validator should do nothing."""
        cmd = MagicMock()
        ns = Namespace()
        ns.version = None
        ns.prerelease = False
        
        bake_source_version_validator(cmd, ns)
        
        assert ns.version is None
    
    def test_version_with_prerelease_raises(self):
        """Using both --version and --pre should raise error."""
        cmd = MagicMock()
        ns = Namespace()
        ns.version = 'v1.0.0'
        ns.prerelease = True
        
        with pytest.raises(MutuallyExclusiveArgumentError):
            bake_source_version_validator(cmd, ns)
    
    def test_specific_version_exists(self):
        cmd = MagicMock()
        ns = Namespace()
        ns.version = 'v1.2.3'
        ns.prerelease = False
        
        with patch('azext_bake._validators.github_release_version_exists') as mock_exists:
            mock_exists.return_value = True
            bake_source_version_validator(cmd, ns)
        
        assert ns.version == 'v1.2.3'
    
    def test_specific_version_not_exists(self):
        cmd = MagicMock()
        ns = Namespace()
        ns.version = 'v99.99.99'
        ns.prerelease = False
        
        with patch('azext_bake._validators.github_release_version_exists') as mock_exists:
            mock_exists.return_value = False
            
            with pytest.raises(InvalidArgumentValueError):
                bake_source_version_validator(cmd, ns)


class TestTemplatesVersionValidator:
    """Tests for templates_version_validator function."""
    
    def test_local_templates_only(self):
        """Using --local-templates should skip version fetching."""
        cmd = MagicMock()
        ns = Namespace()
        ns.local_templates = True
        ns.template_file = None
        ns.version = None
        ns.prerelease = False
        ns.templates_url = None
        
        templates_version_validator(cmd, ns)
        # Should not raise
    
    def test_local_templates_with_multiple_options_raises(self):
        """Using --local-templates with multiple other options should raise."""
        cmd = MagicMock()
        ns = Namespace()
        ns.local_templates = True
        ns.template_file = None
        ns.version = 'v1.0.0'
        ns.prerelease = True  # Two options set
        ns.templates_url = None
        
        with pytest.raises(MutuallyExclusiveArgumentError):
            templates_version_validator(cmd, ns)
    
    def test_none_version_fetches_latest(self):
        """When no version specified, should fetch latest."""
        cmd = MagicMock()
        ns = Namespace()
        ns.local_templates = False
        ns.template_file = None
        ns.version = None
        ns.prerelease = False
        ns.templates_url = None
        
        with patch('azext_bake._validators.get_github_latest_release_version') as mock_get:
            mock_get.return_value = 'v2.0.0'
            templates_version_validator(cmd, ns)
        
        assert ns.version == 'v2.0.0'
        assert 'v2.0.0' in ns.templates_url


class TestValidateSubnet:
    """Tests for validate_subnet function."""
    
    def test_valid_cidr(self):
        """Test that valid CIDR subnet passes validation."""
        cmd = MagicMock()
        ns = Namespace()
        ns.default_subnet_name = 'default'
        ns.default_subnet_address_prefix = '10.0.1.0/24'
        
        # Should not raise for valid CIDR within VNet range
        validate_subnet(cmd, ns, 'default', ['10.0.0.0/16'])
    
    def test_invalid_cidr_format(self):
        """Test that invalid CIDR format fails validation."""
        cmd = MagicMock()
        ns = Namespace()
        ns.default_subnet_name = 'default'
        ns.default_subnet_address_prefix = 'not-a-cidr'
        
        with pytest.raises((InvalidArgumentValueError, ValueError)):
            validate_subnet(cmd, ns, 'default', ['10.0.0.0/16'])
    
    def test_missing_subnet_name_raises(self):
        """Test that missing subnet name raises error."""
        cmd = MagicMock()
        ns = Namespace()
        ns.default_subnet_name = None
        ns.default_subnet_address_prefix = '10.0.1.0/24'
        
        with pytest.raises(InvalidArgumentValueError):
            validate_subnet(cmd, ns, 'default', ['10.0.0.0/16'])


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_empty_gallery_id(self):
        cmd = MagicMock()
        cmd.cli_ctx = MagicMock()
        ns = Namespace()
        ns.gallery_resource_id = ''
        
        # Empty string should be treated as falsy
        gallery_resource_id_validator(cmd, ns)
    
    def test_gallery_name_lookup(self):
        """Test that gallery name without full ID triggers lookup."""
        cmd = MagicMock()
        cmd.cli_ctx = MagicMock()
        ns = Namespace()
        ns.gallery_resource_id = 'my-gallery'  # Just name, not full ID
        
        # Create mock gallery object with name attribute
        mock_gallery = MagicMock()
        mock_gallery.name = 'my-gallery'
        mock_gallery.id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/galleries/my-gallery'
        
        with patch('azext_bake._validators.get_resources_in_subscription') as mock_get:
            mock_get.return_value = [mock_gallery]
            gallery_resource_id_validator(cmd, ns)
        
        # Should resolve to full resource ID
        assert 'Microsoft.Compute/galleries' in ns.gallery_resource_id
