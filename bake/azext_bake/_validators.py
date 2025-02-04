# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
# pylint: disable=line-too-long, logging-fstring-interpolation, unused-argument

import ipaddress
import os

from datetime import datetime, timezone
from pathlib import Path
from re import match

from azure.cli.core.azclierror import (ArgumentUsageError, CLIError, InvalidArgumentValueError,
                                       MutuallyExclusiveArgumentError, RequiredArgumentMissingError, ValidationError)
from azure.cli.core.commands.parameters import get_resources_in_subscription
from azure.cli.core.commands.validators import validate_tags
from azure.cli.core.extension import get_extension
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id

from ._constants import (AZ_BAKE_BUILD_IMAGE_NAME, AZ_BAKE_IMAGE_BUILDER, AZ_BAKE_IMAGE_BUILDER_VERSION,
                         DEVOPS_PROVIDER_NAME, GITHUB_PROVIDER_NAME, IN_BUILDER, REPO_DIR, STORAGE_DIR, tag_key)
from ._data import BakeConfig, Gallery, Image
from ._github import get_github_latest_release_version, github_release_version_exists
from ._packer import check_packer_install
from ._repos import CI, Repo
from ._sandbox import get_sandbox_from_group
from ._utils import get_logger, get_yaml_file_data, get_yaml_file_path

logger = get_logger(__name__)


def process_sandbox_create_namespace(cmd, ns):

    if not ns.sandbox_resource_group_name:
        logger.info('No sandbox resource group name provided, using sandbox name')
        ns.sandbox_resource_group_name = ns.name_prefix

    templates_version_validator(cmd, ns)
    if _none_or_empty(ns.vnet_address_prefix):
        raise InvalidArgumentValueError('--vnet-address-prefix/--vnet-prefix must be a valid CIDR prefix')

    for subnet in ['default', 'builders']:
        validate_subnet(cmd, ns, subnet, [ns.vnet_address_prefix])

    validate_sandbox_tags(cmd, ns)
    gallery_resource_id_validator(cmd, ns)


def process_bake_repo_build_namespace(cmd, ns):
    # if hasattr(ns, 'sandbox_resource_group_name') and ns.sandbox_resource_group_name \
    #     and hasattr(ns, 'gallery_resource_id') and ns.gallery_resource_id:

    repository_path_validator(cmd, ns)
    repository_images_validator(cmd, ns)
    bake_yaml_validator(cmd, ns)

    if CI.is_ci():
        logger.info('Running in CI environment')
        if ns.repository_url or ns.repository_token or ns.repository_revision:
            raise ArgumentUsageError('--repo-url, --repo-token, and --repo-revision can not be used in a CI environment')

        ci = CI()

        if ci.token is None:
            env_key = 'GITHUB_TOKEN' if ci.provider == GITHUB_PROVIDER_NAME else 'SYSTEM_ACCESSTOKEN'
            logger.warning(f'WARNING: {env_key} environment variable not set. This is required for private repositories.')

        repo = Repo(url=ci.url, token=ci.token, ref=ci.ref, revision=ci.revision)

    else:
        logger.info('Running in local environment')
        if not ns.repository_url:
            raise RequiredArgumentMissingError('--repo-url is required when not running in a CI environment')

        if not ns.repository_token:
            logger.warning('WARNING: --repo-token is not set. This is required for private repositories.')

        repo = Repo(url=ns.repository_url, token=ns.repository_token, revision=ns.repository_revision)

    if repo.clone_url is None:
        raise CLIError(f'Unable to parse repository url: {repo.url}')

    ns.repo = repo


def process_bake_repo_validate_namespace(cmd, ns):
    repository_path_validator(cmd, ns)
    repository_images_validator(cmd, ns)
    bake_yaml_validator(cmd, ns)


def builder_validator(cmd, ns):
    if not IN_BUILDER:
        from azure.cli.core.extension.operations import show_extension
        if not (ext := show_extension('bake')) or 'extensionType' not in ext or ext['extensionType'] != 'dev':
            raise ValidationError('Running outside of the builder container.')
        logger.warning('WARNING: Running outside of the builder container. This should only be done during testing. '
                       'This will fail if the extension is not installed in dev mode.')

    builder_version = os.environ.get(AZ_BAKE_IMAGE_BUILDER_VERSION, 'unknown') if IN_BUILDER else 'local'

    logger.info(f'{AZ_BAKE_IMAGE_BUILDER}: {IN_BUILDER}')
    logger.info(f'{AZ_BAKE_IMAGE_BUILDER_VERSION}: {builder_version}')

    check_packer_install(raise_error=True)

    _validate_dir_path(REPO_DIR, 'repo')
    _validate_dir_path(STORAGE_DIR, 'storage')

    # check for required environment variables
    for env in [AZ_BAKE_BUILD_IMAGE_NAME]:
        if not os.environ.get(env, False):
            raise ValidationError(f'Missing environment variable: {env}')

    image_name = os.environ[AZ_BAKE_BUILD_IMAGE_NAME]
    image_path = REPO_DIR / 'images' / image_name

    _validate_dir_path(image_path, image_name)

    logger.info(f'Image name: {image_name}')
    logger.info(f'Image path: {image_path}')

    if not ns.suffix:
        ns.suffix = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')

    logger.info(f'Build suffix: {ns.suffix}')

    bake_yaml = get_yaml_file_path(REPO_DIR, 'bake', required=True)
    bake_yaml_validator(cmd, ns, bake_yaml)

    image_yaml = get_yaml_file_path(image_path, 'image', required=True)
    image_yaml_validator(cmd, ns, image_yaml)


def repository_images_validator(cmd, ns):
    if not ns.repository_path:
        raise RequiredArgumentMissingError('--repo-path/--repo is required')

    images_path = _validate_dir_path(ns.repository_path / 'images', name='images')

    image_dirs = []
    image_names = []

    images = getattr(ns, 'image_names', None)

    all_images = not images or not isinstance(images, list) or len(images) == 0

    # walk the images directory and find all the child directories
    for dirpath, _, _ in os.walk(images_path):
        # os.walk includes the root directory (i.e. repo/images) so we need to skip it
        if not images_path.samefile(dirpath) and Path(dirpath).parent.samefile(images_path):
            image_dirs.append(Path(dirpath))
            image_names.append(Path(dirpath).name)

    # if specific images were specified, validate they exist
    if not all_images:
        bad_names = [i for i in images if i not in image_names]
        if bad_names:
            raise InvalidArgumentValueError(f'--images/-i {bad_names} are not a valid images')

    ns.images = []

    # for each image, validate the image.yaml file exists and get the path
    for image_dir in image_dirs:
        if all_images or image_dir.name in images:
            image_yaml = get_yaml_file_path(image_dir, 'image', required=True)
            ns.images.append(image_yaml_validator(cmd, ns, image_yaml))


def repository_path_validator(cmd, ns):
    '''Ensure the repository path is valid, transforms to a path object, and validates a .git directory exists'''
    if not ns.repository_path:
        raise RequiredArgumentMissingError('--repo-path/--repo is required')

    repo_path = _validate_dir_path(ns.repository_path, name='repository')
    ns.repository_path = repo_path

    git_path = _validate_dir_path(repo_path / '.git', name='.git')
    if hasattr(ns, 'git_path'):
        ns.git_path = git_path

    if hasattr(ns, 'repository_provider'):
        if ns.repository_provider and ns.repository_provider not in [GITHUB_PROVIDER_NAME, DEVOPS_PROVIDER_NAME]:
            raise InvalidArgumentValueError(f'--repo-provider/--provider must be one of {GITHUB_PROVIDER_NAME} '
                                            f'or {DEVOPS_PROVIDER_NAME}')

        # if the repository provider is not specified, try to determine it from the git config
        git_config = _validate_file_path(git_path / 'config', 'git config')
        config_lines = git_config.read_text(encoding='UTF-8').splitlines()
        remote_url = None
        for line in config_lines:
            line_clean = line.strip()
            if line_clean.startswith('url = '):
                remote_url = line_clean.replace('url = ', '')

        if not remote_url:
            raise ValidationError('Unable to determine repository provider from git config. '
                                  'Please specify --repo-provider/--provider')

        if 'github.com' in remote_url:
            ns.repository_provider = GITHUB_PROVIDER_NAME
        elif 'dev.azure.com' in remote_url or 'visualstudio.com' in remote_url:
            ns.repository_provider = DEVOPS_PROVIDER_NAME
        else:
            raise ValidationError('Unable to determine repository provider from git config. '
                                  'Please specify --repo-provider/--provider')


def image_names_validator(cmd, ns):
    if ns.image_names:
        if not isinstance(ns.image_names, list):
            raise InvalidArgumentValueError('--image/-i must be a list of strings')


def validate_sandbox_tags(cmd, ns):
    if ns.tags:
        validate_tags(ns)

    tags_dict = {} if ns.tags is None else ns.tags

    if ns.template_file:
        tags_dict.update({tag_key('sandbox-version'): 'local'})
    else:
        if ns.version:
            tags_dict.update({tag_key('sandbox-version'): ns.version})
        if ns.prerelease:
            tags_dict.update({tag_key('sandbox-prerelease'): ns.prerelease})

    ext = get_extension('bake')
    ext_version = ext.get_version()
    cur_version_str = f'v{ext_version}'

    tags_dict.update({tag_key('cli-version'): cur_version_str})

    ns.tags = tags_dict


def validate_subnet(cmd, ns, subnet, vnet_prefixes):
    subnet_name_option = f'--{subnet}-subnet-name/--{subnet}-subnet'
    subnet_prefix_option = f'--{subnet}-subnet-prefix/--{subnet}-prefix'

    subnet_name_arg = f'{subnet}_subnet_name'
    subnet_prefix_arg = f'{subnet}_subnet_address_prefix'

    subnet_name_val = getattr(ns, subnet_name_arg, None)
    if _none_or_empty(subnet_name_val):
        raise InvalidArgumentValueError(f'{subnet_name_option} must have a value')

    subnet_prefix_val = getattr(ns, subnet_prefix_arg, None)
    if _none_or_empty(subnet_prefix_val):
        raise InvalidArgumentValueError(f'{subnet_prefix_option} must be a valid CIDR prefix')

    # subnet_prefix_is_default = hasattr(getattr(ns, subnet_prefix_arg), 'is_default')

    vnet_networks = [ipaddress.ip_network(p) for p in vnet_prefixes]
    if not all(any(h in n for n in vnet_networks) for h in ipaddress.ip_network(subnet_prefix_val).hosts()):
        raise InvalidArgumentValueError(
            f'{subnet_prefix_option} {subnet_prefix_val} is not within the vnet address space '
            f'(prefixed: {", ".join(vnet_prefixes)})')


def bake_yaml_validator(cmd, ns, path=None):

    if path is None:
        if hasattr(ns, 'repository_path') and ns.repository_path:
            # should have already run the repository_path_validator
            path = get_yaml_file_path(ns.repository_path, 'bake', required=True)
        else:
            raise RequiredArgumentMissingError('--repo-path/--repo is required.')

    bake_config = get_yaml_file_data(BakeConfig, path)

    if hasattr(ns, 'bake_obj'):
        ns.bake_obj = bake_config

    if hasattr(ns, 'sandbox'):
        ns.sandbox = bake_config.sandbox

    if hasattr(ns, 'gallery'):
        ns.gallery = bake_config.gallery

    return bake_config


def image_yaml_validator(cmd, ns, path):
    image = get_yaml_file_data(Image, path)

    if hasattr(ns, 'image'):
        ns.image = image

    return image


def sandbox_resource_group_name_validator(cmd, ns):
    if hasattr(ns, 'resource_group_name') and hasattr(ns, 'sandbox_resource_group_name'):
        raise CLIError('Shouldnt specify both resource_group_name and sandbox_resource_group_name')
    if hasattr(ns, 'resource_group_name'):
        rg_name = ns.resource_group_name
    elif hasattr(ns, 'sandbox_resource_group_name'):
        rg_name = ns.sandbox_resource_group_name
    else:
        raise RequiredArgumentMissingError('usage error: --sandbox is required.')

    sandbox = get_sandbox_from_group(cmd, rg_name)

    if hasattr(ns, 'sandbox'):
        ns.sandbox = sandbox


def gallery_resource_id_validator(cmd, ns):
    if ns.gallery_resource_id:
        if not is_valid_resource_id(ns.gallery_resource_id):
            logger.info('gallery arg provided is not a valid resource id, attempting to find gallery by name')

            galleries = get_resources_in_subscription(cmd.cli_ctx, resource_type='Microsoft.Compute/galleries')
            gallery = next((g for g in galleries if g.name == ns.gallery_resource_id), None)

            if gallery:
                ns.gallery_resource_id = gallery.id
            else:
                raise InvalidArgumentValueError('usage error: --gallery/-r is not a valid resource id or gallery name')

        if hasattr(ns, 'gallery'):
            gallery_id = parse_resource_id(ns.gallery_resource_id)
            ns.gallery = Gallery({
                'name': gallery_id['name'],
                'resourceGroup': gallery_id['resource_group'],
                'subscription': gallery_id['subscription'],
            })


def bake_source_version_validator(cmd, ns):
    if ns.version:
        if ns.prerelease:
            raise MutuallyExclusiveArgumentError(
                'Only use one of --version/-v | --pre',
                recommendation='Remove all --version/-v, and --pre to use the latest stable release,'
                ' or only specify --pre to use the latest pre-release')

        _validate_version(cmd, ns)


def templates_version_validator(cmd, ns):
    if ns.local_templates:
        if sum(1 for ct in [ns.template_file, ns.version, ns.prerelease, ns.templates_url] if ct) > 1:
            raise MutuallyExclusiveArgumentError(
                '--local-template cannot be used with --templates-file | --templates-url | --version/-v | --pre',
                recommendation='Remove all templates-file, --templates-url, --version/-v, and --pre to use the latest'
                'stable release, or only specify --local to use templates packaged with the CLI')
    elif ns.template_file:
        if ns.version or ns.prerelease or ns.templates_url:
            raise MutuallyExclusiveArgumentError(
                '--template-file cannont be used with --templates-url | --version/-v | --pre',
                recommendation='Remove all --templates-url, --version/-v, and --pre to use a local template file.')
    else:
        if sum(1 for ct in [ns.version, ns.prerelease, ns.templates_url] if ct) > 1:
            raise MutuallyExclusiveArgumentError(
                'Only use one of --templates-url | --version/-v | --pre',
                recommendation='Remove all --templates-url, --version/-v, and --pre to use the latest'
                'stable release, or only specify --pre to use the latest pre-release')

        if ns.version:
            _validate_version(cmd, ns)

        elif ns.templates_url:
            if not _is_valid_url(ns.templates_url):
                raise InvalidArgumentValueError(
                    '--templates-url should be a valid url to a templates.json file')

        else:
            ns.version = ns.version or get_github_latest_release_version(prerelease=ns.prerelease)
            ns.templates_url = f'https://github.com/rogerbestmsft/az-bake/releases/download/{ns.version}/templates.json'


def yaml_out_validator(cmd, ns):
    if hasattr(ns, 'outfile') and ns.outfile:
        if getattr(ns.outfile, 'is_default', None) is None:
            if ns.outdir or ns.stdout:
                raise MutuallyExclusiveArgumentError(
                    'Only use one of --outdir | --outfile | --stdout',
                    recommendation='Remove all --outdir, --outfile, and --stdout to output a bake.yaml file '
                    'in the current directory, or only specify --stdout to output to stdout.')
        ns.outfile = Path(ns.outfile).resolve()
    elif ns.outdir and ns.stdout:
        raise MutuallyExclusiveArgumentError(
            'Only use one of --outdir | --stdout',
            recommendation='Remove all --outdir and --stdout to output a bake.yaml file '
            'in the current directory, or only specify --stdout to output to stdout.')
    else:
        if hasattr(ns, 'outfile'):
            ns.outfile = None
        if ns.outdir:
            ns.outdir = _validate_dir_path(ns.outdir)


def _validate_dir_path(path, name=None):
    dir_path = (path if isinstance(path, Path) else Path(path)).resolve()
    not_exists = f'Could not find {name} directory at {dir_path}' if name else f'{dir_path} is not a file or directory'
    if not dir_path.exists():
        raise ValidationError(not_exists)
    if not dir_path.is_dir():
        raise ValidationError(f'{dir_path} is not a directory')
    return dir_path


def _validate_file_path(path, name=None):
    file_path = (path if isinstance(path, Path) else Path(path)).resolve()
    not_exists = f'Could not find {name} file at {file_path}' if name else f'{file_path} is not a file or directory'
    if not file_path.exists():
        raise ValidationError(not_exists)
    if not file_path.is_file():
        raise ValidationError(f'{file_path} is not a file')
    return file_path


def _validate_version(cmd, ns):
    ns.version = ns.version.lower()
    if ns.version[:1].isdigit():
        ns.version = 'v' + ns.version

    if not _is_valid_version(ns.version):
        raise InvalidArgumentValueError(
            '--version/-v should be in format v0.0.0 do not include -pre suffix')

    if not github_release_version_exists(version=ns.version):
        raise InvalidArgumentValueError(f'--version/-v {ns.version} does not exist')


def _is_valid_version(version):
    return match(r'^v[0-9]+\.[0-9]+\.[0-9]+$', version) is not None


def _is_valid_url(url):
    return match(
        r'^http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+$', url) is not None


def _none_or_empty(val):
    return val in ('', '""', "''") or val is None


def user_validator(cmd, ns):
    # Make sure these arguments are non-empty strings.
    # When they are accidentally provided as an empty string "", they won't take effect when filtering the role
    # assignments, causing all matched role assignments to be listed/deleted. For example,
    #   az role assignment delete --assignee ""
    # removes all role assignments under the subscription.
    if getattr(ns, 'user_id') == "":
        # Get option name, like user_id -> --user-id
        option_name = cmd.arguments['user_id'].type.settings['options_list'][0]
        raise RequiredArgumentMissingError(f'usage error: {option_name} can\'t be an empty string.')
