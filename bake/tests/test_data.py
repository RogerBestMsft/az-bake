# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

from pathlib import Path

import pytest
from azure.cli.core.azclierror import ValidationError

from azext_bake._data import (
    BakeConfig,
    ChocoDefaults,
    ChocoPackage,
    Gallery,
    Image,
    ImageBase,
    ImageInstall,
    ImageInstallChoco,
    ImageInstallScripts,
    ImagePlan,
    PowershellScript,
    Sandbox,
    WingetPackage,
    _camel_to_snake,
    _snake_to_camel,
    _validate_data_object,
    get_dict,
)


# -------------------------------------------------------
# _snake_to_camel / _camel_to_snake
# -------------------------------------------------------

class TestSnakeToCamel:
    def test_single_word(self):
        assert _snake_to_camel('name') == 'name'

    def test_two_words(self):
        assert _snake_to_camel('resource_group') == 'resourceGroup'

    def test_three_words(self):
        assert _snake_to_camel('virtual_network_resource_group') == 'virtualNetworkResourceGroup'

    def test_already_camel(self):
        # single word stays the same
        assert _snake_to_camel('resourceGroup') == 'resourceGroup'


class TestCamelToSnake:
    def test_single_word(self):
        assert _camel_to_snake('name') == 'name'

    def test_two_words(self):
        assert _camel_to_snake('resourceGroup') == 'resource_group'

    def test_three_words(self):
        assert _camel_to_snake('virtualNetworkResourceGroup') == 'virtual_network_resource_group'

    def test_already_snake(self):
        assert _camel_to_snake('resource_group') == 'resource_group'


class TestRoundTrip:
    @pytest.mark.parametrize('snake', [
        'name',
        'resource_group',
        'virtual_network_resource_group',
        'install_arguments',
        'identity_id',
    ])
    def test_snake_to_camel_to_snake(self, snake):
        assert _camel_to_snake(_snake_to_camel(snake)) == snake


# -------------------------------------------------------
# _validate_data_object
# -------------------------------------------------------

class TestValidateDataObject:
    def test_valid_object(self):
        # ImageBase requires publisher, offer, sku -- version is optional
        obj = {'publisher': 'pub', 'offer': 'off', 'sku': 'sku1'}
        _validate_data_object(ImageBase, obj)  # should not raise

    def test_missing_required_field(self):
        obj = {'publisher': 'pub', 'offer': 'off'}  # missing 'sku'
        with pytest.raises(ValidationError, match='missing required property'):
            _validate_data_object(ImageBase, obj)

    def test_empty_required_field(self):
        obj = {'publisher': '', 'offer': 'off', 'sku': 'sku1'}
        with pytest.raises(ValidationError, match='missing a value for required property'):
            _validate_data_object(ImageBase, obj)

    def test_invalid_field(self):
        obj = {'publisher': 'pub', 'offer': 'off', 'sku': 'sku1', 'bogus': 'bad'}
        with pytest.raises(ValidationError, match='invalid property.*bogus'):
            _validate_data_object(ImageBase, obj)

    def test_path_in_error_message(self, tmp_path):
        obj = {'publisher': 'pub'}  # missing offer, sku
        path = tmp_path / 'image.yml'
        with pytest.raises(ValidationError, match=str(path).replace('\\', '\\\\')):
            _validate_data_object(ImageBase, obj, path=path)

    def test_parent_key_in_error_message(self):
        obj = {'publisher': 'pub'}
        with pytest.raises(ValidationError, match='base\\.offer'):
            _validate_data_object(ImageBase, obj, parent_key='base')


# -------------------------------------------------------
# get_dict
# -------------------------------------------------------

class TestGetDict:
    def test_outputs_camel_case_keys(self):
        base = ImageBase({'publisher': 'pub', 'offer': 'off', 'sku': 'sku1', 'version': 'latest'})
        d = get_dict(base)
        assert 'publisher' in d
        assert 'offer' in d
        assert 'sku' in d
        assert 'version' in d

    def test_filters_none_values(self):
        pkg = ChocoPackage({'id': 'git'})
        d = get_dict(pkg)
        assert d['id'] == 'git'
        # Optional fields that are None should be excluded
        assert 'source' not in d
        assert 'version' not in d

    def test_filters_false_values(self):
        pkg = ChocoPackage({'id': 'git'})
        d = get_dict(pkg)
        # Boolean defaults to False -> should be excluded
        assert 'user' not in d
        assert 'restart' not in d


# -------------------------------------------------------
# PowershellScript
# -------------------------------------------------------

class TestPowershellScript:
    def test_basic(self):
        ps = PowershellScript({'path': 'install.ps1'})
        assert ps.path == 'install.ps1'
        assert ps.restart is False

    def test_with_restart(self):
        ps = PowershellScript({'path': 'install.ps1', 'restart': True})
        assert ps.restart is True

    def test_missing_path(self):
        with pytest.raises(ValidationError, match='missing required property'):
            PowershellScript({})


# -------------------------------------------------------
# ImageInstallScripts
# -------------------------------------------------------

class TestImageInstallScripts:
    def test_string_shorthand(self):
        scripts = ImageInstallScripts({'powershell': ['install.ps1', 'setup.ps1']})
        assert len(scripts.powershell) == 2
        assert scripts.powershell[0].path == 'install.ps1'
        assert scripts.powershell[1].path == 'setup.ps1'

    def test_dict_form(self):
        scripts = ImageInstallScripts({'powershell': [{'path': 'install.ps1', 'restart': True}]})
        assert scripts.powershell[0].restart is True


# -------------------------------------------------------
# ChocoDefaults / ChocoPackage
# -------------------------------------------------------

class TestChocoDefaults:
    def test_basic(self):
        d = ChocoDefaults({'source': 'chocolatey', 'installArguments': '--no-progress'})
        assert d.source == 'chocolatey'
        assert d.install_arguments == '--no-progress'

    def test_empty(self):
        d = ChocoDefaults({})
        assert d.source is None
        assert d.install_arguments is None


class TestChocoPackage:
    def test_basic(self):
        pkg = ChocoPackage({'id': 'git'})
        assert pkg.id == 'git'
        assert pkg.source is None

    def test_full(self):
        pkg = ChocoPackage({
            'id': 'git',
            'source': 'chocolatey',
            'version': '2.40.0',
            'installArguments': '--ia "/NOICONS"',
            'packageParameters': '/NoAutoCrlf',
            'user': True,
            'restart': True,
        })
        assert pkg.version == '2.40.0'
        assert pkg.user is True
        assert pkg.restart is True

    def test_missing_id(self):
        with pytest.raises(ValidationError):
            ChocoPackage({})

    def test_id_only_true(self):
        pkg = ChocoPackage({'id': 'git'})
        assert pkg.id_only is True

    def test_id_only_false_when_source_set(self):
        pkg = ChocoPackage({'id': 'git', 'source': 'chocolatey'})
        assert pkg.id_only is False

    def test_id_only_false_when_user_set(self):
        pkg = ChocoPackage({'id': 'git', 'user': True})
        assert pkg.id_only is False

    def test_apply_defaults_source(self):
        defaults = ChocoDefaults({'source': 'mychoco'})
        pkg = ChocoPackage({'id': 'git'})
        pkg.apply_defaults(defaults)
        assert pkg.source == 'mychoco'

    def test_apply_defaults_does_not_override(self):
        defaults = ChocoDefaults({'source': 'mychoco'})
        pkg = ChocoPackage({'id': 'git', 'source': 'other'})
        pkg.apply_defaults(defaults)
        assert pkg.source == 'other'

    def test_apply_defaults_install_arguments(self):
        defaults = ChocoDefaults({'installArguments': '--ia'})
        pkg = ChocoPackage({'id': 'git'})
        pkg.apply_defaults(defaults)
        assert pkg.install_arguments == '--ia'


# -------------------------------------------------------
# ImageInstallChoco
# -------------------------------------------------------

class TestImageInstallChoco:
    def test_string_shorthand(self):
        choco = ImageInstallChoco({'packages': ['git', 'vscode']})
        assert len(choco.packages) == 2
        assert choco.packages[0].id == 'git'
        assert choco.packages[1].id == 'vscode'

    def test_dict_form(self):
        choco = ImageInstallChoco({'packages': [{'id': 'git', 'version': '2.40.0'}]})
        assert choco.packages[0].version == '2.40.0'


# -------------------------------------------------------
# WingetPackage
# -------------------------------------------------------

class TestWingetPackage:
    def test_with_id(self):
        pkg = WingetPackage({'id': 'Microsoft.VSCode'})
        assert pkg.id == 'Microsoft.VSCode'

    def test_with_name(self):
        pkg = WingetPackage({'name': 'Visual Studio Code'})
        assert pkg.name == 'Visual Studio Code'

    def test_with_moniker(self):
        pkg = WingetPackage({'moniker': 'vscode'})
        assert pkg.moniker == 'vscode'

    def test_with_any(self):
        pkg = WingetPackage({'any': 'vscode'})
        assert pkg.any == 'vscode'

    def test_missing_all_identifiers(self):
        with pytest.raises(ValidationError, match='missing required property'):
            WingetPackage({})


# -------------------------------------------------------
# ImageBase
# -------------------------------------------------------

class TestImageBase:
    def test_basic(self):
        base = ImageBase({'publisher': 'pub', 'offer': 'off', 'sku': 'sku1'})
        assert base.publisher == 'pub'
        assert base.version == 'latest'

    def test_custom_version(self):
        base = ImageBase({'publisher': 'pub', 'offer': 'off', 'sku': 'sku1', 'version': '1.0.0'})
        assert base.version == '1.0.0'


# -------------------------------------------------------
# ImagePlan
# -------------------------------------------------------

class TestImagePlan:
    def test_basic(self):
        plan = ImagePlan({'publisher': 'pub', 'name': 'plan1', 'product': 'prod1'})
        assert plan.publisher == 'pub'
        assert plan.name == 'plan1'
        assert plan.product == 'prod1'

    def test_missing_field(self):
        with pytest.raises(ValidationError):
            ImagePlan({'publisher': 'pub'})


# -------------------------------------------------------
# Image
# -------------------------------------------------------

class TestImage:
    def test_windows_default_base(self, sample_image_dict):
        img = Image(sample_image_dict)
        assert img.os == 'Windows'
        assert img.base is not None
        assert img.base.publisher == 'microsoftwindowsdesktop'

    def test_linux_requires_base(self):
        obj = {
            'publisher': 'pub', 'offer': 'off', 'replicaLocations': ['eastus'],
            'sku': 'sku1', 'version': '1.0.0', 'os': 'Linux',
        }
        with pytest.raises(ValidationError, match='base is required'):
            Image(obj)

    def test_linux_with_explicit_base(self, sample_linux_image_dict):
        img = Image(sample_linux_image_dict)
        assert img.base.publisher == 'Canonical'

    def test_path_sets_name_and_dir(self, tmp_path):
        image_dir = tmp_path / 'images' / 'MyImage'
        image_dir.mkdir(parents=True)
        image_file = image_dir / 'image.yml'
        image_file.touch()

        obj = {
            'publisher': 'pub', 'offer': 'off', 'replicaLocations': ['eastus'],
            'sku': 'sku1', 'version': '1.0.0', 'os': 'Windows',
        }
        img = Image(obj, path=image_file)
        assert img.name == 'MyImage'
        assert img.dir == image_dir
        assert img.file == image_file

    def test_no_path_no_name_raises(self):
        obj = {
            'publisher': 'pub', 'offer': 'off', 'replicaLocations': ['eastus'],
            'sku': 'sku1', 'version': '1.0.0', 'os': 'Windows',
        }
        with pytest.raises(ValidationError, match='name is required'):
            Image(obj)

    def test_no_path_with_name(self, sample_image_dict):
        sample_image_dict['name'] = 'TestImage'
        img = Image(sample_image_dict)
        assert img.name == 'TestImage'

    def test_update_defaults_true(self, sample_image_dict):
        sample_image_dict['name'] = 'TestImage'
        img = Image(sample_image_dict)
        assert img.update is True

    def test_hibernate_defaults_false(self, sample_image_dict):
        sample_image_dict['name'] = 'TestImage'
        img = Image(sample_image_dict)
        assert img.hibernate is False

    def test_with_install_section(self, tmp_path):
        image_dir = tmp_path / 'images' / 'Img'
        image_dir.mkdir(parents=True)
        image_file = image_dir / 'image.yml'
        image_file.touch()

        obj = {
            'publisher': 'pub', 'offer': 'off', 'replicaLocations': ['eastus'],
            'sku': 'sku1', 'version': '1.0.0', 'os': 'Windows',
            'install': {
                'choco': {
                    'packages': ['git', 'vscode'],
                },
            },
        }
        img = Image(obj, path=image_file)
        assert img.install is not None
        assert len(img.install.choco.packages) == 2

    def test_with_plan(self, tmp_path):
        image_dir = tmp_path / 'images' / 'Img'
        image_dir.mkdir(parents=True)
        image_file = image_dir / 'image.yml'
        image_file.touch()

        obj = {
            'publisher': 'pub', 'offer': 'off', 'replicaLocations': ['eastus'],
            'sku': 'sku1', 'version': '1.0.0', 'os': 'Windows',
            'plan': {'publisher': 'pub', 'name': 'plan1', 'product': 'prod1'},
        }
        img = Image(obj, path=image_file)
        assert img.plan.name == 'plan1'


# -------------------------------------------------------
# Sandbox
# -------------------------------------------------------

class TestSandbox:
    def test_valid(self, sample_sandbox_dict):
        sb = Sandbox(sample_sandbox_dict)
        assert sb.resource_group == 'my-sandbox-rg'
        assert sb.subscription == '00000000-0000-0000-0000-000000000001'
        assert sb.location is None

    def test_with_location(self, sample_sandbox_dict):
        sample_sandbox_dict['location'] = 'eastus'
        sb = Sandbox(sample_sandbox_dict)
        assert sb.location == 'eastus'

    def test_invalid_subscription_guid(self, sample_sandbox_dict):
        sample_sandbox_dict['subscription'] = 'not-a-guid'
        with pytest.raises(ValidationError, match='subscription is not a valid GUID'):
            Sandbox(sample_sandbox_dict)

    def test_invalid_identity_id(self, sample_sandbox_dict):
        sample_sandbox_dict['identityId'] = 'not-a-resource-id'
        with pytest.raises(ValidationError, match='identityId is not a valid resource ID'):
            Sandbox(sample_sandbox_dict)

    def test_missing_required_field(self, sample_sandbox_dict):
        del sample_sandbox_dict['keyVault']
        with pytest.raises(ValidationError, match='missing required property'):
            Sandbox(sample_sandbox_dict)


# -------------------------------------------------------
# Gallery
# -------------------------------------------------------

class TestGallery:
    def test_valid(self, sample_gallery_dict):
        g = Gallery(sample_gallery_dict)
        assert g.name == 'MyGallery'
        assert g.resource_group == 'my-gallery-rg'
        assert g.subscription == '00000000-0000-0000-0000-000000000002'

    def test_no_subscription(self):
        g = Gallery({'name': 'gal', 'resourceGroup': 'rg'})
        assert g.subscription is None

    def test_invalid_subscription_guid(self, sample_gallery_dict):
        sample_gallery_dict['subscription'] = 'not-a-guid'
        with pytest.raises(ValidationError, match='subscription is not a valid GUID'):
            Gallery(sample_gallery_dict)


# -------------------------------------------------------
# BakeConfig
# -------------------------------------------------------

class TestBakeConfig:
    def test_valid(self, sample_bake_config_dict, tmp_path):
        config_path = tmp_path / 'bake.yml'
        config_path.touch()

        bc = BakeConfig(sample_bake_config_dict, path=config_path)
        assert bc.version == 1
        assert bc.sandbox.resource_group == 'my-sandbox-rg'
        assert bc.gallery.name == 'MyGallery'
        assert bc.file == config_path
        assert bc.dir == tmp_path
        assert bc.name == 'bake.yml'

    def test_missing_sandbox(self, sample_bake_config_dict, tmp_path):
        del sample_bake_config_dict['sandbox']
        config_path = tmp_path / 'bake.yml'
        config_path.touch()
        with pytest.raises(ValidationError, match='missing required property'):
            BakeConfig(sample_bake_config_dict, path=config_path)
