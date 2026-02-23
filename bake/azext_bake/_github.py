# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
# pylint: disable=logging-fstring-interpolation, too-many-statements, too-many-locals, too-many-lines

"""
GitHub API integration for release management.

This module handles interactions with the GitHub API to:

- Retrieve release information (latest, prerelease, specific versions)
- Download release assets (templates.json, extension packages)
- Check version availability for upgrade detection

All API calls include retry logic for transient network failures.
"""

from typing import Optional, Tuple, Union

import requests

from azure.cli.core.azclierror import ClientRequestError, MutuallyExclusiveArgumentError, ResourceNotFoundError
from azure.cli.core.util import should_disable_connection_verify

from ._utils import get_logger

ERR_TMPL_PRDR_TEMPLATES = 'Unable to get templates.\n'
ERR_TMPL_NON_200 = f'{ERR_TMPL_PRDR_TEMPLATES}Server returned status code {{}} for {{}}'
ERR_TMPL_NO_NETWORK = f'{ERR_TMPL_PRDR_TEMPLATES}Please ensure you have network connection. Error detail: {{}}'
ERR_TMPL_BAD_JSON = f'{ERR_TMPL_PRDR_TEMPLATES}Response body does not contain valid json. Error detail: {{}}'

TRIES = 3

logger = get_logger(__name__)


def get_github_releases(org: str = 'rogerbestmsft', repo: str = 'az-bake', prerelease: bool = False) -> list:
    """
    Retrieve all GitHub releases for the repository.

    Args:
        org: GitHub organization name.
        repo: Repository name.
        prerelease: If True, return only prereleases; if False, return only stable releases.

    Returns:
        List of release objects filtered by prerelease status.
    """
    url = f'https://api.github.com/repos/{org}/{repo}/releases'

    version_res = requests.get(url, verify=not should_disable_connection_verify())
    version_json = version_res.json()

    return [v for v in version_json if v['prerelease'] == prerelease]


def get_github_release(org: str = 'rogerbestmsft', repo: str = 'az-bake', version: str = None, prerelease: bool = False) -> dict:
    """
    Get a specific GitHub release.

    Args:
        org: GitHub organization name.
        repo: Repository name.
        version: Specific version tag to retrieve (e.g., 'v1.0.0').
        prerelease: If True and no version specified, return latest prerelease.

    Returns:
        Release object with tag_name, assets, and other metadata.

    Raises:
        MutuallyExclusiveArgumentError: If both version and prerelease are specified.
        ClientRequestError: If no matching release is found.
    """
    if version and prerelease:
        raise MutuallyExclusiveArgumentError('Only use one of --version/-v | --pre')

    url = f'https://api.github.com/repos/{org}/{repo}/releases'

    if prerelease:
        if (prereleases := get_github_releases(org, repo, prerelease=True)):
            return prereleases[0]
        raise ClientRequestError(f'--pre no prerelease versions found for {org}/{repo}')

    url += (f'/tags/{version}' if version else '/latest')

    version_res = requests.get(url, verify=not should_disable_connection_verify())

    if version_res.status_code == 404:
        raise ClientRequestError(
            f'No release version exists for {org}/{repo}. Specify a specific prerelease version with --version '
            'or use latest prerelease with --pre')

    return version_res.json()


def get_github_latest_release_version(org: str = 'rogerbestmsft', repo: str = 'az-bake', prerelease: bool = False) -> str:
    """Get the tag name of the latest release (e.g., 'v1.2.3')."""
    logger.info(f'Getting latest release version from GitHub ({org}/{repo})')
    version_json = get_github_release(org, repo, prerelease=prerelease)
    return version_json['tag_name']


def github_release_version_exists(version: str, org: str = 'rogerbestmsft', repo: str = 'az-bake') -> bool:
    """Check if a specific release version tag exists in the repository."""
    logger.info(f'Checking if release version {version} exists on GitHub ({org}/{repo})')
    version_url = f'https://api.github.com/repos/{org}/{repo}/releases/tags/{version}'
    version_res = requests.get(version_url, verify=not should_disable_connection_verify())
    return version_res.status_code < 400


def get_release_asset(asset_url: str, to_json: bool = True) -> Union[dict, requests.Response]:  # pylint: disable=inconsistent-return-statements
    """
    Download a release asset with retry logic and exponential backoff.

    Args:
        asset_url: Direct download URL for the asset.
        to_json: If True, parse response as JSON; otherwise return raw response.

    Returns:
        Parsed JSON object or raw response depending on to_json parameter.

    Raises:
        ClientRequestError: On network failures or non-200 responses after retries.
    """
    for try_number in range(TRIES):
        try:
            response = requests.get(asset_url, verify=not should_disable_connection_verify())
            if response.status_code == 200:
                return response.json() if to_json else response
            msg = ERR_TMPL_NON_200.format(response.status_code, asset_url)
            raise ClientRequestError(msg)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
            msg = ERR_TMPL_NO_NETWORK.format(str(err))
            raise ClientRequestError(msg) from err
        except ValueError as err:
            # Indicates that url is not redirecting properly to intended index url, we stop retrying after TRIES calls
            if try_number == TRIES - 1:
                msg = ERR_TMPL_BAD_JSON.format(str(err))
                raise ClientRequestError(msg) from err
            import time  # pylint: disable=import-outside-toplevel
            # Exponential backoff: 0.5s, 1s, 2s, ...
            time.sleep(0.5 * (2 ** try_number))
            continue


def get_release_templates(version: str = None, prerelease: bool = False, templates_url: str = None) -> Tuple[str, dict]:
    """
    Retrieve the templates.json manifest from a GitHub release.

    The templates.json file contains download URLs for ARM/Bicep templates
    used during sandbox creation and image building.

    Args:
        version: Specific version to retrieve templates from.
        prerelease: If True, use latest prerelease.
        templates_url: Override URL for templates.json (for testing).

    Returns:
        Tuple of (version_string, templates_dict).
    """
    if templates_url is None:
        version = version or get_github_latest_release_version(prerelease=prerelease)
        templates_url = f'https://github.com/rogerbestmsft/az-bake/releases/download/{version}/templates.json'
    logger.info(f'Getting templates.json from GitHub release ({version})')
    templates = get_release_asset(asset_url=templates_url)
    for k in ['builder', 'install', 'packer', 'sandbox']:
        if not templates.get(k):
            raise ClientRequestError(f'Unable to get {k} node from templates.json. Improper json format.')
    return version, templates


def get_template_url(templates: dict, parent: str, name: str) -> str:
    """
    Extract a template download URL from the templates.json structure.

    Args:
        templates: Parsed templates.json object.
        parent: Parent node name (e.g., 'builder', 'sandbox').
        name: Template name within the parent (e.g., 'builder.json').

    Returns:
        Download URL string for the requested template.

    Raises:
        ResourceNotFoundError: If the template path doesn't exist.
    """
    logger.info(f'Getting url from template.json for {parent}.{name}')
    if not (parent_node := templates.get(parent)):
        raise ResourceNotFoundError(f'Unable to get {parent} node from templates.json. Improper json format.')
    if not (template := parent_node.get(name)):
        raise ResourceNotFoundError(f'Unable to get template {name} from {parent} in templates.json.')
    if not (template_url := template.get('downloadUrl')):
        raise ResourceNotFoundError(f'Unable to get template downloadUrl from {parent}.{name} in templates.json.')
    return template_url


# def get_artifact(artifacts, name):
#     artifact = artifacts.get(name)
#     if artifact is None:
#         raise ResourceNotFoundError(f'Unable to get artifact {name} from templates.json.')
#     artifact_url = artifact.get('url')
#     artifact_name = artifact.get('name')
#     if artifact_url is None:
#         raise ResourceNotFoundError(f'Unable to get artifact {name} url from templates.json.')
#     if artifact_name is None:
#         raise ResourceNotFoundError(f'Unable to get artifact {name} name from templates.json.')

#     return artifact_name, artifact_url
