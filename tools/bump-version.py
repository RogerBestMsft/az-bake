# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

import argparse

from pathlib import Path
from re import search

from packaging.version import parse as parse_version  # pylint: disable=unresolved-import

parser = argparse.ArgumentParser()
parser.add_argument('--major', action='store_true', help='bump major version')
parser.add_argument('--minor', action='store_true', help='bump minor version')
parser.add_argument('--patch', action='store_true', help='bump patch version (default when no bump flag is specified)')
parser.add_argument('--pre', nargs='?', const='prerel', default=None, metavar='SUFFIX',
                    help='add a prerelease suffix (default: dev). '
                         'Matches preview-release workflow format: VERSION.SUFFIX<NUMBER>. '
                         'Only updates setup.py. Can combine with --major/--minor.')
parser.add_argument('--pre-number', type=int, default=0,
                    help='prerelease number appended to the suffix (default: 0). '
                         'In CI this maps to GITHUB_RUN_NUMBER.')
parser.add_argument('--notes', nargs='*', default=['Bug fixes and minor improvements'], help='space seperated strings with release notes')

args = parser.parse_args()

major = args.major
minor = args.minor
patch = args.patch
pre = args.pre
pre_number = args.pre_number
notes = '* {}'.format('\n* '.join(args.notes))

if sum([major, minor, patch]) > 1:
    raise ValueError('usage error: --major | --minor | --patch')

# Default to patch bump when no bump flag is specified
if not major and not minor:
    patch = True

version = None

path_root = Path(__file__).resolve().parent.parent
path_bake = path_root / 'bake'
path_builder = path_root / 'builder'

with open(path_bake / 'setup.py', 'r') as f:
    for line in f:
        if line.startswith('VERSION'):
            txt = str(line).rstrip()
            match = search(r'VERSION = [\'\"](.*)[\'\"]$', txt)
            if match:
                version = match.group(1)

if not version:
    raise ValueError('no version found in setup.py')

version_old = parse_version(version)

# Compute the new version
if pre is not None:
    # Prerelease mode: matches preview-release.yml workflow format
    # Bump base version (patch by default), then add prerelease suffix
    n_major = version_old.major + 1 if major else version_old.major
    n_minor = 0 if major else version_old.minor + 1 if minor else version_old.minor
    n_patch = 0 if major or minor else version_old.micro + 1 if patch else version_old.micro
    base = f'{n_major}.{n_minor}.{n_patch}'

    version_new_str = f'{base}.{pre}{pre_number}'
    print(f'setting prerelease version: {version_old.public} -> {version_new_str}')

    # Only update setup.py for prerelease versions (matches workflow behavior)
    fmt_setup = 'VERSION = \'{}\''

    print('..updating setup.py')

    with open(path_bake / 'setup.py', 'r') as f:
        setup = f.read()

    if fmt_setup.format(version) not in setup:
        raise ValueError('version string not found in setup.py')

    setup = setup.replace(fmt_setup.format(version), fmt_setup.format(version_new_str))

    with open(path_bake / 'setup.py', 'w') as f:
        f.write(setup)

    print(f'done: {version_new_str}')

else:
    # Standard version bump (existing behavior)
    n_major = version_old.major + 1 if major else version_old.major
    n_minor = 0 if major else version_old.minor + 1 if minor else version_old.minor
    n_patch = 0 if major or minor else version_old.micro + 1

    version_new = parse_version(f'{n_major}.{n_minor}.{n_patch}')

    print(f'bumping version: {version_old.public} -> {version_new.public}')

    fmt_setup = 'VERSION = \'{}\''
    fmt_readme = 'https://github.com/rogerbestmsft/az-bake/releases/latest/download/bake-{}-py3-none-any.whl'
    fmt_docker = 'https://github.com/rogerbestmsft/az-bake/releases/latest/download/bake-{}-py3-none-any.whl'
    fmt_history = '{}\n++++++\n{}\n\n{}'

    print('..updating setup.py')

    with open(path_bake / 'setup.py', 'r') as f:
        setup = f.read()

    if fmt_setup.format(version_old.public) not in setup:
        raise ValueError('version string not found in setup.py')

    setup = setup.replace(fmt_setup.format(version_old.public), fmt_setup.format(version_new.public))

    with open(path_bake / 'setup.py', 'w') as f:
        f.write(setup)

    print('..updating HISTORY.rst')

    with open(path_bake / 'HISTORY.rst', 'r') as f:
        history = f.read()

    if version_old.public not in history:
        raise ValueError('version string not found in HISTORY.rst')

    history = history.replace(version_old.public, fmt_history.format(version_new.public, notes, version_old.public))

    with open(path_bake / 'HISTORY.rst', 'w') as f:
        f.write(history)

    print('..updating Dockerfile')

    with open(path_builder / 'Dockerfile', 'r') as f:
        docker = f.read()

    if fmt_docker.format(version_old.public) not in docker:
        raise ValueError('version string not found in Dockerfile')

    docker = docker.replace(fmt_docker.format(version_old.public), fmt_docker.format(version_new.public))

    with open(path_builder / 'Dockerfile', 'w') as f:
        f.write(docker)

    print('..updating README.md')

    with open(path_root / 'README.md', 'r') as f:
        readme = f.read()

    if fmt_readme.format(version_old.public) not in readme:
        raise ValueError('version string not found in README.md')

    readme = readme.replace(fmt_readme.format(version_old.public), fmt_readme.format(version_new.public))

    with open(path_root / 'README.md', 'w') as f:
        f.write(readme)
