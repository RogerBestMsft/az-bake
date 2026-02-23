# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
Tests for the _utils.py module.

Tests cover utility functions for YAML handling, path validation,
Chocolatey package config generation, and PowerShell script extraction.
"""

import json
import pytest
import tempfile
import yaml
from pathlib import Path

from azure.cli.core.azclierror import FileOperationError, ValidationError

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from azext_bake._utils import (
    get_yaml_file_path, get_yaml_file_contents, get_yaml_file_data,
    get_choco_package_setup, get_choco_package_config,
    get_install_choco_packages, get_templates_path
)
from azext_bake._data import ChocoPackage, Image


class TestGetYamlFilePath:
    """Tests for get_yaml_file_path function."""
    
    def test_yaml_file_exists(self, temp_dir):
        yaml_file = temp_dir / 'config.yaml'
        yaml_file.write_text('key: value')
        
        result = get_yaml_file_path(temp_dir, 'config')
        
        assert result == yaml_file
    
    def test_yml_file_exists(self, temp_dir):
        yml_file = temp_dir / 'config.yml'
        yml_file.write_text('key: value')
        
        result = get_yaml_file_path(temp_dir, 'config')
        
        assert result == yml_file
    
    def test_yaml_preferred_over_yml(self, temp_dir):
        yaml_file = temp_dir / 'config.yaml'
        yml_file = temp_dir / 'config.yml'
        yaml_file.write_text('key: yaml')
        yml_file.write_text('key: yml')
        
        with pytest.raises(ValidationError) as exc_info:
            get_yaml_file_path(temp_dir, 'config')
        
        assert 'both' in str(exc_info.value).lower()
    
    def test_file_not_found_required(self, temp_dir):
        with pytest.raises(ValidationError) as exc_info:
            get_yaml_file_path(temp_dir, 'nonexistent', required=True)
        
        assert 'not found' in str(exc_info.value).lower()
    
    def test_file_not_found_not_required(self, temp_dir):
        result = get_yaml_file_path(temp_dir, 'nonexistent', required=False)
        
        assert result is None
    
    def test_directory_not_found_required(self):
        with pytest.raises(ValidationError):
            get_yaml_file_path(Path('/nonexistent/path'), 'config', required=True)
    
    def test_directory_not_found_not_required(self):
        result = get_yaml_file_path(Path('/nonexistent/path'), 'config', required=False)
        
        assert result is None


class TestGetYamlFileContents:
    """Tests for get_yaml_file_contents function."""
    
    def test_valid_yaml(self, temp_dir):
        yaml_file = temp_dir / 'config.yaml'
        yaml_file.write_text('''
name: test
version: 1.0
items:
  - item1
  - item2
''')
        
        result = get_yaml_file_contents(yaml_file)
        
        assert result['name'] == 'test'
        assert result['version'] == 1.0
        assert result['items'] == ['item1', 'item2']
    
    def test_file_not_found(self):
        with pytest.raises(FileOperationError):
            get_yaml_file_contents(Path('/nonexistent/file.yaml'))
    
    def test_empty_yaml(self, temp_dir):
        yaml_file = temp_dir / 'empty.yaml'
        yaml_file.write_text('')
        
        with pytest.raises(FileOperationError) as exc_info:
            get_yaml_file_contents(yaml_file)
        
        assert 'empty' in str(exc_info.value).lower()
    
    def test_invalid_yaml(self, temp_dir):
        yaml_file = temp_dir / 'invalid.yaml'
        yaml_file.write_text('key: value\n  invalid indent:')
        
        with pytest.raises(FileOperationError) as exc_info:
            get_yaml_file_contents(yaml_file)
        
        assert 'error' in str(exc_info.value).lower()


class TestGetChocoPackageSetup:
    """Tests for get_choco_package_setup function."""
    
    def test_simple_package(self):
        pkg = ChocoPackage({'id': 'git'})
        
        result = get_choco_package_setup(pkg)
        
        assert '--yes' in result
        assert '--no-progress' in result
    
    def test_package_with_source(self):
        pkg = ChocoPackage({'id': 'git', 'source': 'chocolatey'})
        
        result = get_choco_package_setup(pkg)
        
        assert "--source 'chocolatey'" in result
    
    def test_package_with_version(self):
        pkg = ChocoPackage({'id': 'git', 'version': '2.40.0'})
        
        result = get_choco_package_setup(pkg)
        
        assert "--version '2.40.0'" in result
    
    def test_package_with_install_args(self):
        pkg = ChocoPackage({
            'id': 'vscode',
            'installArguments': '/quiet /norestart'
        })
        
        result = get_choco_package_setup(pkg)
        
        assert "--installArguments '/quiet /norestart'" in result
    
    def test_user_flag_not_included(self):
        pkg = ChocoPackage({'id': 'git', 'user': True})
        
        result = get_choco_package_setup(pkg)
        
        assert 'user' not in result.lower()
    
    def test_restart_flag_not_included(self):
        pkg = ChocoPackage({'id': 'git', 'restart': True})
        
        result = get_choco_package_setup(pkg)
        
        assert 'restart' not in result.lower()
    
    def test_has_leading_space(self):
        """Verify leading space before --yes --no-progress."""
        pkg = ChocoPackage({'id': 'git'})
        
        result = get_choco_package_setup(pkg)
        
        # Should have space before --yes
        assert result.endswith(' --yes --no-progress')


class TestGetChocoPackageConfig:
    """Tests for get_choco_package_config function."""
    
    def test_single_package(self):
        packages = [ChocoPackage({'id': 'git'})]
        
        result = get_choco_package_config(packages)
        
        assert '<packages>' in result
        assert '</packages>' in result
        assert 'id="git"' in result
    
    def test_multiple_packages(self):
        packages = [
            ChocoPackage({'id': 'git'}),
            ChocoPackage({'id': 'vscode'}),
            ChocoPackage({'id': 'nodejs'})
        ]
        
        result = get_choco_package_config(packages)
        
        assert 'id="git"' in result
        assert 'id="vscode"' in result
        assert 'id="nodejs"' in result
    
    def test_package_with_attributes(self):
        packages = [
            ChocoPackage({
                'id': 'git',
                'version': '2.40.0',
                'source': 'chocolatey'
            })
        ]
        
        result = get_choco_package_config(packages)
        
        assert 'version="2.40.0"' in result
        assert 'source="chocolatey"' in result


class TestGetTemplatesPath:
    """Tests for get_templates_path function."""
    
    def test_returns_path(self):
        result = get_templates_path()
        
        assert isinstance(result, Path)
        assert result.exists()
    
    def test_returns_subfolder(self):
        result = get_templates_path('packer')
        
        assert result.name == 'packer'
        assert result.parent.name == 'templates'
    
    def test_install_folder_exists(self):
        result = get_templates_path('install')
        
        assert result.exists()
        assert (result / 'choco.json').exists()


class TestGetInstallChocoPackages:
    """Tests for get_install_choco_packages function."""
    
    def test_no_install_returns_none(self, temp_dir, sample_image_dict):
        # Image needs a path to extract name from
        image_file = temp_dir / 'image.yml'
        image_file.write_text('name: test')
        
        # Remove install key if present
        sample_image_dict.pop('install', None)
        image = Image(sample_image_dict, image_file)
        
        result = get_install_choco_packages(image)
        
        assert result is None
    
    def test_extracts_packages(self, temp_dir, sample_image_with_choco):
        image_file = temp_dir / 'image.yml'
        image_file.write_text('name: test')
        
        image = Image(sample_image_with_choco, image_file)
        
        result = get_install_choco_packages(image)
        
        assert result is not None
        assert len(result) == 3
        assert all(isinstance(p, ChocoPackage) for p in result)
    
    def test_applies_defaults(self, temp_dir, sample_image_dict):
        """Test that defaults are applied to packages not in choco.json index."""
        image_file = temp_dir / 'image.yml'
        image_file.write_text('name: test')
        
        # Use a package NOT in choco.json so defaults get applied
        sample_image_dict['install'] = {
            'choco': {
                'defaults': {
                    'source': 'custom-feed'
                },
                'packages': [{'id': 'unknown-package-xyz'}]  # Not in choco.json
            }
        }
        image = Image(sample_image_dict, image_file)
        
        result = get_install_choco_packages(image)
        
        # Defaults should be applied to packages not in choco index
        assert result is not None
        assert len(result) == 1
        assert result[0].source == 'custom-feed'


class TestIntegration:
    """Integration tests for utility functions."""
    
    def test_yaml_to_image_workflow(self, temp_dir, sample_image_with_choco):
        """Test complete workflow from YAML file to Image object."""
        # Write YAML file
        yaml_file = temp_dir / 'image.yaml'
        yaml_file.write_text(yaml.safe_dump(sample_image_with_choco))
        
        # Read and parse
        path = get_yaml_file_path(temp_dir, 'image')
        contents = get_yaml_file_contents(path)
        image = Image(contents, path)
        
        # Extract packages
        packages = get_install_choco_packages(image)
        
        assert len(packages) == 3
        assert packages[0].id == 'git'
