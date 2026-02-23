# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
Tests for the _data.py module.

Tests cover domain model validation, serialization, and error handling
for all dataclasses: Image, Sandbox, Gallery, BakeConfig, and their
nested types.
"""

import pytest
from pathlib import Path

from azure.cli.core.azclierror import ValidationError

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from azext_bake._data import (
    Sandbox, Gallery, Image, ImageBase, ImagePlan, ImageInstall,
    ImageInstallChoco, ImageInstallScripts, ImageInstallWinget,
    ChocoPackage, ChocoDefaults, PowershellScript, WingetPackage,
    BakeConfig, ImageInstallActiveSetup, get_dict, _snake_to_camel, _camel_to_snake
)


class TestNameConversion:
    """Tests for snake_case <-> camelCase conversion."""
    
    def test_snake_to_camel_single_word(self):
        assert _snake_to_camel('name') == 'name'
    
    def test_snake_to_camel_multiple_words(self):
        assert _snake_to_camel('resource_group') == 'resourceGroup'
        assert _snake_to_camel('virtual_network_resource_group') == 'virtualNetworkResourceGroup'
    
    def test_camel_to_snake_single_word(self):
        assert _camel_to_snake('name') == 'name'
    
    def test_camel_to_snake_multiple_words(self):
        assert _camel_to_snake('resourceGroup') == 'resource_group'
        assert _camel_to_snake('virtualNetworkResourceGroup') == 'virtual_network_resource_group'


class TestSandbox:
    """Tests for Sandbox dataclass."""
    
    def test_sandbox_valid(self, sample_sandbox_dict):
        sandbox = Sandbox(sample_sandbox_dict)
        
        assert sandbox.resource_group == 'test-sandbox-rg'
        assert sandbox.subscription == '00000000-0000-0000-0000-000000000001'
        assert sandbox.virtual_network == 'test-vnet'
        assert sandbox.default_subnet == 'default'
        assert sandbox.builder_subnet == 'builders'
        assert sandbox.key_vault == 'test-kv'
        assert sandbox.storage_account == 'teststorage'
    
    def test_sandbox_missing_required(self, sample_sandbox_dict):
        del sample_sandbox_dict['resourceGroup']
        
        with pytest.raises(ValidationError) as exc_info:
            Sandbox(sample_sandbox_dict)
        
        assert 'resourceGroup' in str(exc_info.value)
    
    def test_sandbox_invalid_subscription(self, sample_sandbox_dict):
        sample_sandbox_dict['subscription'] = 'not-a-guid'
        
        with pytest.raises(ValidationError) as exc_info:
            Sandbox(sample_sandbox_dict)
        
        assert 'subscription' in str(exc_info.value).lower()
    
    def test_sandbox_invalid_identity_id(self, sample_sandbox_dict):
        sample_sandbox_dict['identityId'] = 'not-a-resource-id'
        
        with pytest.raises(ValidationError) as exc_info:
            Sandbox(sample_sandbox_dict)
        
        assert 'identityId' in str(exc_info.value)
    
    def test_sandbox_invalid_property(self, sample_sandbox_dict):
        sample_sandbox_dict['unknownProperty'] = 'value'
        
        with pytest.raises(ValidationError) as exc_info:
            Sandbox(sample_sandbox_dict)
        
        assert 'invalid property' in str(exc_info.value).lower()


class TestGallery:
    """Tests for Gallery dataclass."""
    
    def test_gallery_valid(self, sample_gallery_dict):
        gallery = Gallery(sample_gallery_dict)
        
        assert gallery.name == 'test_gallery'
        assert gallery.resource_group == 'gallery-rg'
        assert gallery.subscription == '00000000-0000-0000-0000-000000000002'
    
    def test_gallery_without_subscription(self, sample_gallery_dict):
        del sample_gallery_dict['subscription']
        
        gallery = Gallery(sample_gallery_dict)
        assert gallery.subscription is None
    
    def test_gallery_missing_name(self, sample_gallery_dict):
        del sample_gallery_dict['name']
        
        with pytest.raises(ValidationError) as exc_info:
            Gallery(sample_gallery_dict)
        
        assert 'name' in str(exc_info.value)
    
    def test_gallery_invalid_subscription(self, sample_gallery_dict):
        sample_gallery_dict['subscription'] = 'invalid-guid'
        
        with pytest.raises(ValidationError) as exc_info:
            Gallery(sample_gallery_dict)
        
        assert 'subscription' in str(exc_info.value).lower()


class TestImageBase:
    """Tests for ImageBase dataclass."""
    
    def test_image_base_valid(self):
        base = ImageBase({
            'publisher': 'microsoftwindowsdesktop',
            'offer': 'windows-ent-cpc',
            'sku': 'win11-22h2-ent-cpc-m365'
        })
        
        assert base.publisher == 'microsoftwindowsdesktop'
        assert base.offer == 'windows-ent-cpc'
        assert base.sku == 'win11-22h2-ent-cpc-m365'
        assert base.version == 'latest'  # default
    
    def test_image_base_with_version(self):
        base = ImageBase({
            'publisher': 'microsoftwindowsdesktop',
            'offer': 'windows-ent-cpc',
            'sku': 'win11-22h2-ent-cpc-m365',
            'version': '1.0.0'
        })
        
        assert base.version == '1.0.0'
    
    def test_image_base_missing_publisher(self):
        with pytest.raises(ValidationError) as exc_info:
            ImageBase({
                'offer': 'windows-ent-cpc',
                'sku': 'win11-22h2-ent-cpc-m365'
            })
        
        assert 'publisher' in str(exc_info.value)


class TestChocoPackage:
    """Tests for ChocoPackage dataclass."""
    
    def test_choco_package_simple(self):
        pkg = ChocoPackage({'id': 'git'})
        
        assert pkg.id == 'git'
        assert pkg.user is False
        assert pkg.restart is False
        assert pkg.source is None
    
    def test_choco_package_full(self):
        pkg = ChocoPackage({
            'id': 'vscode',
            'source': 'chocolatey',
            'version': '1.80.0',
            'installArguments': '/quiet',
            'packageParameters': '/NoDesktopIcon',
            'user': True,
            'restart': True
        })
        
        assert pkg.id == 'vscode'
        assert pkg.source == 'chocolatey'
        assert pkg.version == '1.80.0'
        assert pkg.install_arguments == '/quiet'
        assert pkg.package_parameters == '/NoDesktopIcon'
        assert pkg.user is True
        assert pkg.restart is True
    
    def test_choco_package_id_only_property(self):
        pkg_simple = ChocoPackage({'id': 'git'})
        pkg_complex = ChocoPackage({'id': 'git', 'version': '2.40.0'})
        
        assert pkg_simple.id_only is True
        assert pkg_complex.id_only is False
    
    def test_choco_package_apply_defaults(self):
        defaults = ChocoDefaults({
            'source': 'custom-feed',
            'installArguments': '--force'
        })
        
        pkg = ChocoPackage({'id': 'git'})
        pkg.apply_defaults(defaults)
        
        assert pkg.source == 'custom-feed'
        assert pkg.install_arguments == '--force'
    
    def test_choco_package_no_override_existing(self):
        defaults = ChocoDefaults({'source': 'custom-feed'})
        
        pkg = ChocoPackage({'id': 'git', 'source': 'chocolatey'})
        pkg.apply_defaults(defaults)
        
        assert pkg.source == 'chocolatey'  # should not be overridden


class TestWingetPackage:
    """Tests for WingetPackage dataclass."""
    
    def test_winget_package_with_id(self):
        pkg = WingetPackage({'id': 'Microsoft.VSCode'})
        
        assert pkg.id == 'Microsoft.VSCode'
        assert pkg.name is None
        assert pkg.moniker is None
    
    def test_winget_package_with_name(self):
        pkg = WingetPackage({'name': 'Visual Studio Code'})
        
        assert pkg.name == 'Visual Studio Code'
        assert pkg.id is None
    
    def test_winget_package_with_any(self):
        pkg = WingetPackage({'any': 'vscode'})
        
        assert pkg.any == 'vscode'
    
    def test_winget_package_no_identifier(self):
        with pytest.raises(ValidationError) as exc_info:
            WingetPackage({'source': 'winget'})
        
        assert 'missing required property' in str(exc_info.value).lower()
    
    def test_winget_package_multiple_identifiers(self):
        with pytest.raises(ValidationError) as exc_info:
            WingetPackage({'id': 'Microsoft.VSCode', 'name': 'Visual Studio Code'})
        
        assert 'only one' in str(exc_info.value).lower()


class TestPowershellScript:
    """Tests for PowershellScript dataclass."""
    
    def test_powershell_script_simple(self):
        script = PowershellScript({'path': 'scripts/install.ps1'})
        
        assert script.path == 'scripts/install.ps1'
        assert script.restart is False
    
    def test_powershell_script_with_restart(self):
        script = PowershellScript({
            'path': 'scripts/install-hyperv.ps1',
            'restart': True
        })
        
        assert script.restart is True


class TestImage:
    """Tests for Image dataclass."""
    
    def test_image_valid(self, sample_image_dict):
        # sample_image_dict now has 'name' field so no path needed
        image = Image(sample_image_dict)
        
        assert image.name == 'test-image'
        assert image.publisher == 'TestPublisher'
        assert image.offer == 'TestOffer'
        assert image.sku == 'test-sku'
        assert image.version == '1.0.0'
        assert image.os == 'Windows'
        assert image.replica_locations == ['eastus', 'westus']
        assert image.update is True
    
    def test_image_with_choco(self, sample_image_with_choco):
        image = Image(sample_image_with_choco)
        
        assert image.install is not None
        assert image.install.choco is not None
        assert len(image.install.choco.packages) == 3
    
    def test_image_missing_required(self, sample_image_dict):
        del sample_image_dict['publisher']
        
        with pytest.raises(ValidationError) as exc_info:
            Image(sample_image_dict)
        
        assert 'publisher' in str(exc_info.value)
    
    def test_image_windows_default_base(self, sample_image_dict):
        del sample_image_dict['base']
        
        image = Image(sample_image_dict)
        
        assert image.base is not None
        assert image.base.publisher == 'microsoftwindowsdesktop'
    
    def test_image_linux_requires_base(self, sample_image_dict):
        sample_image_dict['os'] = 'Linux'
        del sample_image_dict['base']
        
        with pytest.raises(ValidationError) as exc_info:
            Image(sample_image_dict)
        
        assert 'base' in str(exc_info.value).lower()
    
    def test_image_with_plan(self, sample_image_dict):
        sample_image_dict['plan'] = {
            'publisher': 'publisher-id',
            'name': 'plan-name',
            'product': 'product-id'
        }
        
        image = Image(sample_image_dict)
        
        assert image.plan is not None
        assert image.plan.publisher == 'publisher-id'
        assert image.plan.name == 'plan-name'
        assert image.plan.product == 'product-id'
    
    def test_image_from_file_path(self, temp_image_dir):
        image_file = temp_image_dir / 'image.yml'
        
        import yaml
        with open(image_file, 'r') as f:
            obj = yaml.safe_load(f)
        
        image = Image(obj, image_file)
        
        assert image.name == 'TestImage'
        assert image.dir == temp_image_dir
        assert image.file == image_file


class TestImageInstallActiveSetup:
    """Tests for ImageInstallActiveSetup dataclass."""
    
    def test_activesetup_with_commands(self):
        setup = ImageInstallActiveSetup({
            'commands': ['cmd1', 'cmd2', 'cmd3']
        })
        
        assert setup.commands == ['cmd1', 'cmd2', 'cmd3']
    
    def test_activesetup_empty_commands_raises(self):
        """Empty commands list should raise ValidationError."""
        with pytest.raises(ValidationError):
            ImageInstallActiveSetup({'commands': []})


class TestGetDict:
    """Tests for get_dict helper function."""
    
    def test_get_dict_sandbox(self, sample_sandbox_dict):
        sandbox = Sandbox(sample_sandbox_dict)
        result = get_dict(sandbox)
        
        assert 'resourceGroup' in result
        assert 'subscription' in result
        assert result['resourceGroup'] == 'test-sandbox-rg'
    
    def test_get_dict_filters_none(self, sample_gallery_dict):
        del sample_gallery_dict['subscription']
        gallery = Gallery(sample_gallery_dict)
        result = get_dict(gallery)
        
        assert 'subscription' not in result
    
    def test_get_dict_filters_false(self):
        pkg = ChocoPackage({'id': 'git', 'user': False})
        result = get_dict(pkg)
        
        assert 'user' not in result


class TestBakeConfig:
    """Tests for BakeConfig dataclass."""
    
    def test_bake_config_valid(self, temp_bake_yaml, sample_bake_config_dict):
        config = BakeConfig(sample_bake_config_dict, temp_bake_yaml)
        
        assert config.version == 1.0
        assert config.sandbox is not None
        assert config.gallery is not None
        assert config.file == temp_bake_yaml
    
    def test_bake_config_missing_version(self, temp_bake_yaml, sample_bake_config_dict):
        del sample_bake_config_dict['version']
        
        with pytest.raises(ValidationError) as exc_info:
            BakeConfig(sample_bake_config_dict, temp_bake_yaml)
        
        assert 'version' in str(exc_info.value)
