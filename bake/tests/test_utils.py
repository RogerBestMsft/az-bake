# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

import pytest

from azext_bake._data import ChocoPackage
from azext_bake._utils import get_choco_package_setup


# -------------------------------------------------------
# get_choco_package_setup
# -------------------------------------------------------

class TestGetChocoPackageSetup:
    def test_id_only_ends_with_flags(self):
        pkg = ChocoPackage({'id': 'git'})
        result = get_choco_package_setup(pkg)
        assert result.endswith('--yes --no-progress')

    def test_id_only_no_extra_options(self):
        pkg = ChocoPackage({'id': 'git'})
        result = get_choco_package_setup(pkg)
        # Should just be the flags, no extra --source etc.
        assert result == ' --yes --no-progress'

    def test_with_source_has_space_before_flags(self):
        pkg = ChocoPackage({'id': 'git', 'source': 'chocolatey'})
        result = get_choco_package_setup(pkg)
        # Must have a space separating the source value from --yes
        assert " --source 'chocolatey' --yes --no-progress" in result

    def test_with_version(self):
        pkg = ChocoPackage({'id': 'git', 'version': '2.40.0'})
        result = get_choco_package_setup(pkg)
        assert "--version '2.40.0'" in result
        assert result.endswith('--yes --no-progress')

    def test_user_key_excluded(self):
        pkg = ChocoPackage({'id': 'git', 'user': True})
        result = get_choco_package_setup(pkg)
        assert '--user' not in result

    def test_restart_key_excluded(self):
        pkg = ChocoPackage({'id': 'git', 'restart': True})
        result = get_choco_package_setup(pkg)
        assert '--restart' not in result

    def test_no_double_dash_before_yes(self):
        # Regression: previously '--yes' was appended without a leading space
        pkg = ChocoPackage({'id': 'git', 'source': 'chocolatey'})
        result = get_choco_package_setup(pkg)
        assert "'chocolatey'--yes" not in result
        assert "' --yes" in result or result.startswith(' --yes')
