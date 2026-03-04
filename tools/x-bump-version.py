# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

import argparse

from pathlib import Path

from packaging.version import parse as parse_version  # pylint: disable=unresolved-import

parser = argparse.ArgumentParser()
parser.add_argument('--major', action='store_true', help='bump major version')
parser.add_argument('--minor', action='store_true', help='bump minor version')
parser.add_argument('--patch', action='store_true', help='bump patch version (default when no bump flag is specified)')
parser.add_argument('--pre', nargs='?', const='pre', default=None, metavar='SUFFIX',
                    help='add a prerelease suffix (default: pre). '
                         'Produces VERSION.SUFFIX<NUMBER> format. '
                         'Can combine with --major/--minor/--patch.')
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

path_root = Path(__file__).resolve().parent.parent
path_bake = path_root / 'bake'

# Read the current version from the VERSION file (single source of truth)
with open(path_root / 'VERSION', 'r') as f:
    version = f.read().strip()

version_old = parse_version(version)

# Compute the new version
if pre is not None:
    # Prerelease: bump base version (patch by default), then add suffix
    n_major = version_old.major + 1 if major else version_old.major
    n_minor = 0 if major else version_old.minor + 1 if minor else version_old.minor
    n_patch = 0 if major or minor else version_old.micro + 1 if patch else version_old.micro
    base = f'{n_major}.{n_minor}.{n_patch}'
    version_new_str = f'{base}.{pre}{pre_number}'
else:
    # Standard version bump
    n_major = version_old.major + 1 if major else version_old.major
    n_minor = 0 if major else version_old.minor + 1 if minor else version_old.minor
    n_patch = 0 if major or minor else version_old.micro + 1
    version_new_str = f'{n_major}.{n_minor}.{n_patch}'

print(f'bumping version: {version_old.public} -> {version_new_str}')

fmt_history = '{}\n++++++\n{}\n\n{}'


print('..updating VERSION')

with open(path_root / 'VERSION', 'w') as f:
    f.write(version_new_str + '\n')


print('..updating HISTORY.rst')

with open(path_bake / 'HISTORY.rst', 'r') as f:
    history = f.read()

if version_old.public not in history:
    raise ValueError('version string not found in HISTORY.rst')

history = history.replace(version_old.public, fmt_history.format(version_new_str, notes, version_old.public))

with open(path_bake / 'HISTORY.rst', 'w') as f:
    f.write(history)

print('done.')
