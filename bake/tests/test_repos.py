# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
Tests for the _repos.py module.

Tests cover repository URL parsing, CI environment detection,
and clone URL generation for GitHub and Azure DevOps.
"""

import pytest
import os
from pathlib import Path

from azure.cli.core.azclierror import CLIError

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from azext_bake._repos import Repo, CI
from azext_bake._constants import GITHUB_PROVIDER_NAME, DEVOPS_PROVIDER_NAME


class TestRepoGitHub:
    """Tests for GitHub repository URL parsing."""
    
    def test_github_https_url(self):
        repo = Repo(url='https://github.com/testorg/testrepo.git')
        
        assert repo.provider == GITHUB_PROVIDER_NAME
        assert repo.org == 'testorg'
        assert repo.repo == 'testrepo'
        assert repo.project is None
        assert 'github.com' in repo.url
    
    def test_github_https_without_git(self):
        repo = Repo(url='https://github.com/testorg/testrepo')
        
        assert repo.provider == GITHUB_PROVIDER_NAME
        assert repo.org == 'testorg'
        assert repo.repo == 'testrepo'
    
    def test_github_ssh_url(self):
        repo = Repo(url='git@github.com:testorg/testrepo.git')
        
        assert repo.provider == GITHUB_PROVIDER_NAME
        assert repo.org == 'testorg'
        assert repo.repo == 'testrepo'
    
    def test_github_git_protocol(self):
        repo = Repo(url='git://github.com/testorg/testrepo.git')
        
        assert repo.provider == GITHUB_PROVIDER_NAME
        assert repo.org == 'testorg'
        assert repo.repo == 'testrepo'
    
    def test_github_clone_url_without_token(self):
        repo = Repo(url='https://github.com/testorg/testrepo.git')
        
        assert repo.clone_url == 'https://github.com/testorg/testrepo'
    
    def test_github_clone_url_with_token(self):
        repo = Repo(url='https://github.com/testorg/testrepo.git', token='mytoken')
        
        assert 'gituser:mytoken@' in repo.clone_url
        assert repo.clone_url.startswith('https://gituser:mytoken@github.com')
    
    def test_github_preserves_ref_and_revision(self):
        repo = Repo(
            url='https://github.com/testorg/testrepo',
            ref='refs/heads/main',
            revision='abc123'
        )
        
        assert repo.ref == 'refs/heads/main'
        assert repo.revision == 'abc123'


class TestRepoAzureDevOps:
    """Tests for Azure DevOps repository URL parsing."""
    
    def test_devops_https_url(self):
        repo = Repo(url='https://dev.azure.com/testorg/TestProject/_git/testrepo')
        
        assert repo.provider == DEVOPS_PROVIDER_NAME
        assert repo.org == 'testorg'
        assert repo.project == 'testproject'  # lowercased
        assert repo.repo == 'testrepo'
    
    def test_devops_visualstudio_url(self):
        repo = Repo(url='https://testorg.visualstudio.com/DefaultCollection/TestProject/_git/testrepo')
        
        assert repo.provider == DEVOPS_PROVIDER_NAME
        assert repo.org == 'testorg'
        assert repo.project == 'testproject'
        assert repo.repo == 'testrepo'
    
    def test_devops_with_username_in_url(self):
        repo = Repo(url='https://user@dev.azure.com/testorg/TestProject/_git/testrepo')
        
        assert repo.provider == DEVOPS_PROVIDER_NAME
        assert repo.org == 'testorg'
        assert '@' not in repo.url  # username should be stripped
    
    def test_devops_ssh_url(self):
        repo = Repo(url='git@ssh.dev.azure.com:v3/testorg/TestProject/testrepo')
        
        assert repo.provider == DEVOPS_PROVIDER_NAME
        assert repo.org == 'testorg'
        assert repo.project == 'testproject'
        assert repo.repo == 'testrepo'
    
    def test_devops_clone_url_with_token(self):
        repo = Repo(
            url='https://dev.azure.com/testorg/TestProject/_git/testrepo',
            token='mytoken'
        )
        
        assert 'azurereposuser:mytoken@' in repo.clone_url


class TestRepoInvalidUrls:
    """Tests for invalid repository URLs."""
    
    def test_invalid_url_raises_error(self):
        with pytest.raises(CLIError):
            Repo(url='https://gitlab.com/testorg/testrepo')
    
    def test_malformed_github_url(self):
        with pytest.raises(CLIError):
            Repo(url='https://github.com/invalid')
    
    def test_malformed_devops_url(self):
        with pytest.raises(CLIError):
            Repo(url='https://dev.azure.com/invalid')


class TestCIDetection:
    """Tests for CI environment detection."""
    
    def test_is_ci_github_actions(self, github_ci_env):
        # is_ci() returns truthy value in CI environment
        assert CI.is_ci()
    
    def test_is_ci_azure_devops(self, devops_ci_env):
        # is_ci() returns truthy value in CI environment  
        assert CI.is_ci()
    
    def test_is_ci_not_in_ci(self, clean_env):
        assert not CI.is_ci()


class TestCIGitHub:
    """Tests for GitHub Actions CI context."""
    
    def test_ci_github_context(self, github_ci_env):
        ci = CI()
        
        assert ci.provider == GITHUB_PROVIDER_NAME
        assert ci.url == 'https://github.com/testorg/testrepo'
        assert ci.token == 'test-token'
        assert ci.ref == 'refs/heads/main'
        assert ci.revision == 'abc123def456'
    
    def test_ci_github_without_token(self, clean_env):
        os.environ['CI'] = 'true'
        os.environ['GITHUB_ACTION'] = 'test-action'
        os.environ['GITHUB_SERVER_URL'] = 'https://github.com'
        os.environ['GITHUB_REPOSITORY'] = 'testorg/testrepo'
        os.environ['GITHUB_REF'] = 'refs/heads/main'
        os.environ['GITHUB_SHA'] = 'abc123'
        
        ci = CI()
        
        assert ci.provider == GITHUB_PROVIDER_NAME
        assert ci.token is None
        
        # Cleanup
        for var in ['CI', 'GITHUB_ACTION', 'GITHUB_SERVER_URL', 
                    'GITHUB_REPOSITORY', 'GITHUB_REF', 'GITHUB_SHA']:
            os.environ.pop(var, None)
    
    def test_ci_github_missing_url_raises(self, clean_env):
        os.environ['CI'] = 'true'
        os.environ['GITHUB_ACTION'] = 'test-action'
        # Missing GITHUB_SERVER_URL and GITHUB_REPOSITORY
        
        with pytest.raises(CLIError):
            CI()
        
        os.environ.pop('CI', None)
        os.environ.pop('GITHUB_ACTION', None)


class TestCIAzureDevOps:
    """Tests for Azure DevOps CI context."""
    
    def test_ci_devops_context(self, devops_ci_env):
        ci = CI()
        
        assert ci.provider == DEVOPS_PROVIDER_NAME
        assert ci.url == 'https://dev.azure.com/testorg/testproject/_git/testrepo'
        assert ci.token == 'test-token'
        assert ci.ref == 'refs/heads/main'
        assert ci.revision == 'abc123def456'
    
    def test_ci_devops_missing_url_raises(self, clean_env):
        os.environ['TF_BUILD'] = 'True'
        # Missing BUILD_REPOSITORY_URI
        
        with pytest.raises(CLIError):
            CI()
        
        os.environ.pop('TF_BUILD', None)


class TestCINotInCI:
    """Tests for non-CI environment."""
    
    def test_ci_init_outside_ci_raises(self, clean_env):
        with pytest.raises(CLIError) as exc_info:
            CI()
        
        assert 'CI environment' in str(exc_info.value)
