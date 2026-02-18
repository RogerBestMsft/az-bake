# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

from azext_bake._constants import (
    DEFAULT_TAGS,
    IMAGE_DEFAULT_BASE_WINDOWS,
    PKR_DEFAULT_VARS,
    TAG_PREFIX,
    tag_key,
)


class TestTagKey:
    def test_basic(self):
        assert tag_key('cli-version') == f'{TAG_PREFIX}cli-version'

    def test_prefix_value(self):
        assert TAG_PREFIX == 'hidden-bake:'
        assert tag_key('foo') == 'hidden-bake:foo'

    def test_empty_string(self):
        assert tag_key('') == 'hidden-bake:'


class TestConstants:
    def test_image_default_base_windows_has_required_keys(self):
        assert 'publisher' in IMAGE_DEFAULT_BASE_WINDOWS
        assert 'offer' in IMAGE_DEFAULT_BASE_WINDOWS
        assert 'sku' in IMAGE_DEFAULT_BASE_WINDOWS
        assert 'version' in IMAGE_DEFAULT_BASE_WINDOWS

    def test_image_default_base_windows_values(self):
        assert IMAGE_DEFAULT_BASE_WINDOWS['version'] == 'latest'
        assert isinstance(IMAGE_DEFAULT_BASE_WINDOWS['publisher'], str)

    def test_pkr_default_vars_has_sections(self):
        assert 'image' in PKR_DEFAULT_VARS
        assert 'gallery' in PKR_DEFAULT_VARS
        assert 'sandbox' in PKR_DEFAULT_VARS

    def test_default_tags_is_set(self):
        assert isinstance(DEFAULT_TAGS, set)
        assert len(DEFAULT_TAGS) > 0
        # Every tag should start with the prefix
        for t in DEFAULT_TAGS:
            assert t.startswith(TAG_PREFIX)
