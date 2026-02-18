# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

import os

import pytest
from azure.cli.core.azclierror import CLIError

from azext_bake._constants import DEVOPS_PROVIDER_NAME, GITHUB_PROVIDER_NAME
from azext_bake._repos import CI, Repo


# -------------------------------------------------------
# Repo — GitHub URL parsing
# -------------------------------------------------------

class TestRepoGitHub:
    @pytest.mark.parametrize('url', [
        'git://github.com/rogerbestmsft/az-bake.git',
        'https://github.com/rogerbestmsft/az-bake.git',
        'git@github.com:rogerbestmsft/az-bake.git',
    ])
    def test_github_urls(self, url):
        repo = Repo(url=url)
        assert repo.provider == GITHUB_PROVIDER_NAME
        assert repo.org == 'rogerbestmsft'
        assert repo.repo == 'az-bake'
        assert '@' not in repo.url  # credentials should not leak into normalized url

    def test_github_url_without_git_suffix(self):
        repo = Repo(url='https://github.com/myorg/myrepo')
        assert repo.org == 'myorg'
        assert repo.repo == 'myrepo'

    def test_github_clone_url_with_token(self):
        repo = Repo(url='https://github.com/myorg/myrepo.git', token='tok123')
        assert 'tok123' in repo.clone_url
        assert repo.clone_url.startswith('https://gituser:tok123@')

    def test_github_clone_url_without_token(self):
        repo = Repo(url='https://github.com/myorg/myrepo.git')
        assert repo.clone_url == repo.url

    def test_invalid_github_url(self):
        with pytest.raises(CLIError):
            Repo(url='https://github.com/')


# -------------------------------------------------------
# Repo — Azure DevOps URL parsing
# -------------------------------------------------------

class TestRepoDevOps:
    @pytest.mark.parametrize('url', [
        'https://dev.azure.com/rogerbestmsft/MyProject/_git/az-bake',
        'https://rogerbestmsft.visualstudio.com/DefaultCollection/MyProject/_git/az-bake',
        'https://user@dev.azure.com/rogerbestmsft/MyProject/_git/az-bake',
    ])
    def test_devops_urls(self, url):
        repo = Repo(url=url, token='mytoken')
        assert repo.provider == DEVOPS_PROVIDER_NAME
        assert repo.org == 'rogerbestmsft'
        assert repo.project == 'myproject'
        assert repo.repo == 'az-bake'
        assert '@' not in repo.url

    def test_devops_clone_url_with_token(self):
        repo = Repo(url='https://dev.azure.com/org/proj/_git/repo', token='tok123')
        assert 'tok123' in repo.clone_url

    def test_devops_clone_url_without_token(self):
        repo = Repo(url='https://dev.azure.com/org/proj/_git/repo')
        assert repo.clone_url == repo.url

    def test_invalid_devops_url(self):
        with pytest.raises(CLIError):
            Repo(url='https://dev.azure.com/')


# -------------------------------------------------------
# Repo — unknown provider
# -------------------------------------------------------

class TestRepoUnknown:
    def test_unknown_provider_raises(self):
        with pytest.raises(CLIError, match='not a valid'):
            Repo(url='https://gitlab.com/org/repo')


# -------------------------------------------------------
# Repo — ref and revision passthrough
# -------------------------------------------------------

class TestRepoMetadata:
    def test_ref_and_revision(self):
        repo = Repo(url='https://github.com/org/repo', ref='refs/heads/main', revision='abc123')
        assert repo.ref == 'refs/heads/main'
        assert repo.revision == 'abc123'


# -------------------------------------------------------
# CI — environment-based detection
# -------------------------------------------------------

class TestCIIsCI:
    def test_not_ci(self, clean_env):
        assert CI.is_ci() is False

    def test_github_actions(self, clean_env, monkeypatch):
        monkeypatch.setenv('CI', 'true')
        monkeypatch.setenv('GITHUB_ACTION', 'run1')
        assert CI.is_ci() is True

    def test_azure_devops(self, clean_env, monkeypatch):
        monkeypatch.setenv('TF_BUILD', 'True')
        assert CI.is_ci() is True

    def test_ci_env_alone_not_enough(self, clean_env, monkeypatch):
        monkeypatch.setenv('CI', 'true')
        # GITHUB_ACTION not set -> not GitHub Actions; TF_BUILD not set -> not DevOps
        assert CI.is_ci() is False


class TestCIInit:
    def test_github_actions_init(self, clean_env, monkeypatch):
        monkeypatch.setenv('CI', 'true')
        monkeypatch.setenv('GITHUB_ACTION', 'run1')
        monkeypatch.setenv('GITHUB_TOKEN', 'ghp_abc')
        monkeypatch.setenv('GITHUB_REF', 'refs/heads/main')
        monkeypatch.setenv('GITHUB_SHA', 'abc123')
        monkeypatch.setenv('GITHUB_SERVER_URL', 'https://github.com')
        monkeypatch.setenv('GITHUB_REPOSITORY', 'myorg/myrepo')

        ci = CI()
        assert ci.provider == GITHUB_PROVIDER_NAME
        assert ci.token == 'ghp_abc'
        assert ci.ref == 'refs/heads/main'
        assert ci.revision == 'abc123'
        assert ci.url == 'https://github.com/myorg/myrepo'

    def test_github_actions_missing_server_url(self, clean_env, monkeypatch):
        monkeypatch.setenv('CI', 'true')
        monkeypatch.setenv('GITHUB_ACTION', 'run1')
        with pytest.raises(CLIError, match='GitHub repository url'):
            CI()

    def test_devops_init(self, clean_env, monkeypatch):
        monkeypatch.setenv('TF_BUILD', 'True')
        monkeypatch.setenv('SYSTEM_ACCESSTOKEN', 'ado_tok')
        monkeypatch.setenv('BUILD_SOURCEBRANCH', 'refs/heads/main')
        monkeypatch.setenv('BUILD_SOURCEVERSION', 'def456')
        monkeypatch.setenv('BUILD_REPOSITORY_URI', 'https://dev.azure.com/org/proj/_git/repo')

        ci = CI()
        assert ci.provider == DEVOPS_PROVIDER_NAME
        assert ci.token == 'ado_tok'
        assert ci.url == 'https://dev.azure.com/org/proj/_git/repo'

    def test_devops_missing_url(self, clean_env, monkeypatch):
        monkeypatch.setenv('TF_BUILD', 'True')
        with pytest.raises(CLIError, match='Azure DevOps repository url'):
            CI()

    def test_no_ci_env(self, clean_env):
        with pytest.raises(CLIError, match='Could not determine CI environment'):
            CI()
