# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
# pylint: disable=too-many-instance-attributes

"""
Domain data models for the 'az bake' extension.

This module defines dataclass-based domain models that represent the core
business entities used throughout the extension:

- Image: Custom VM image definition (publisher, offer, sku, install config)
- ImageInstall: Software installation specifications (Chocolatey, PowerShell, Winget)
- Sandbox: Azure infrastructure environment for image building
- Gallery: Azure Compute Gallery reference for image publishing
- BakeConfig: Repository-level configuration from bake.yml

All models include validation in their constructors to ensure required fields
are present and data types are correct. Models are initialized from dictionaries
(typically parsed from YAML) and support serialization back to dictionaries
using the get_dict() helper.

The naming convention conversion (snake_case <-> camelCase) enables natural
Python attribute access while maintaining YAML file compatibility.
"""

from dataclasses import MISSING, asdict, dataclass, field, fields
from pathlib import Path
from typing import List, Literal, Optional

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.util import is_guid
from azure.mgmt.core.tools import is_valid_resource_id

from ._constants import IMAGE_DEFAULT_BASE_WINDOWS


def _snake_to_camel(name: str):
    parts = name.split('_')
    return parts[0] + ''.join(word.title() for word in parts[1:])


def _camel_to_snake(name: str):
    return ''.join(['_' + c.lower() if c.isupper() else c for c in name]).lstrip('_')


def _validate_data_object(data_type: type, obj: dict, path: Path = None, parent_key: str = None):
    """
    Validate a dictionary against a dataclass schema.

    Ensures all required fields (those without defaults) are present and have
    values, and that no unknown fields are included. This provides early
    validation with clear error messages for YAML configuration files.

    Args:
        data_type: The dataclass type to validate against.
        obj: Dictionary to validate.
        path: Optional file path for error message context.
        parent_key: Dot-notation prefix for nested property error messages.

    Raises:
        ValidationError: If required fields are missing or invalid fields exist.
    """
    flds = fields(data_type)
    all_fields = [_snake_to_camel(f.name) for f in flds]
    req_fields = [_snake_to_camel(f.name) for f in flds if f.default is MISSING]
    # opt_fields = [f.name for f in flds if f.default is not MISSING]

    key_prefix = f'{parent_key}.' if parent_key else ''

    name = f'{path}' if path else f'{data_type.__name__} object'

    for k in req_fields:
        if k not in obj:
            raise ValidationError(f'{name} is missing required property: {key_prefix}{k}')
        if not obj[k]:
            raise ValidationError(f'{name} is missing a value for required property: {key_prefix}{k}')
        # TODO: Validate types
    for k in obj:
        if k not in all_fields and k not in ['file', 'dir']:
            raise ValidationError(f'{name} contains an invalid property: {key_prefix}{k}')


def get_dict(instance):
    """
    Convert a dataclass instance to a dictionary with camelCase keys.

    Filters out None and False values to produce clean YAML output.
    Used when exporting configuration files or passing data to Packer templates.

    Note: False values are filtered to keep YAML output clean. Boolean properties
    that default to False don't need to be explicitly set in the output.
    """
    return asdict(instance, dict_factory=lambda x: {_snake_to_camel(k): v for k,
                                                    v in x if v is not None and v is not False})


# --------------------------------
# Image > Install > Scripts
# --------------------------------


@dataclass
class PowershellScript:
    # required
    path: str
    # optional
    restart: bool = False

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(PowershellScript, obj, path=path, parent_key='install.scripts.powershell')

        self.path = obj['path']
        self.restart = obj.get('restart', False)


@dataclass
class ImageInstallScripts:
    # optional
    powershell: List[PowershellScript] = field(default_factory=list)

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(ImageInstallScripts, obj, path=path, parent_key='install.scripts')

        self.powershell = [PowershellScript({'path': s}, path) if isinstance(s, str)
                           else PowershellScript(s, path) for s in obj['powershell']]


# --------------------------------
# Image > Install > Choco
# --------------------------------


@dataclass
class ChocoDefaults:
    # optional
    source: str = None
    install_arguments: str = None
    restart: bool = False

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(ChocoDefaults, obj, path=path, parent_key='install.choco.defaults')

        self.source = obj.get('source', None)
        self.install_arguments = obj.get('installArguments', None)
        self.restart = obj.get('restart', False)


@dataclass
class ChocoPackage:
    # required
    id: str
    # optional
    source: Optional[str] = None
    version: Optional[str] = None
    install_arguments: Optional[str] = None
    package_parameters: Optional[str] = None
    user: bool = False
    restart: bool = False

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(ChocoPackage, obj, path=path, parent_key='install.choco')

        self.id = obj['id']
        self.source = obj.get('source', None)
        self.version = obj.get('version', None)
        self.install_arguments = obj.get('installArguments', None)
        self.package_parameters = obj.get('packageParameters', None)
        self.user = obj.get('user', False)
        self.restart = obj.get('restart', False)

    @property
    def id_only(self):
        return self.source is None and self.version is None and self.install_arguments is None \
            and self.package_parameters is None and not self.user

    def apply_defaults(self, defaults: ChocoDefaults):
        if defaults.source is not None and self.source is None:
            self.source = defaults.source
        if defaults.install_arguments is not None and self.install_arguments is None:
            self.install_arguments = defaults.install_arguments


@dataclass
class ImageInstallChoco:
    # required
    packages: List[ChocoPackage] = field(default_factory=list)
    # optional
    defaults: Optional[ChocoDefaults] = None

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(ImageInstallChoco, obj, path=path, parent_key='install.choco')

        self.packages = [ChocoPackage({'id': p}, path) if isinstance(p, str)
                         else ChocoPackage(p, path) for p in obj['packages']]
        self.defaults = ChocoDefaults(obj['defaults'], path) if obj.get('defaults') else None


# --------------------------------
# Image > Install > Winget
# --------------------------------


@dataclass
class WingetDefaults:
    # optional
    source: str = None

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(WingetDefaults, obj, path=path, parent_key='install.winget.defaults')

        self.source = obj.get('source', None)


@dataclass
class WingetPackage:
    # required
    id: str = None
    name: str = None
    moniker: str = None
    any: str = None
    # optional
    source: str = None
    version: str = None

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(WingetPackage, obj, path=path, parent_key='install.winget')

        self.id = obj.get('id', None)
        self.name = obj.get('name', None)
        self.moniker = obj.get('moniker', None)
        self.any = obj.get('any', None)

        # Validate that at least one identifier is set
        identifiers = [self.id, self.name, self.moniker, self.any]
        set_identifiers = [i for i in identifiers if i is not None]
        if not set_identifiers:
            raise ValidationError(f'{path} is missing required property: install.winget.id, install.winget.name, '
                                  'install.winget.moniker, or install.winget.any')
        # Validate that only one identifier is set
        if len(set_identifiers) > 1:
            raise ValidationError(f'{path} must specify only one of: id, name, moniker, or any (found multiple)')

        self.source = obj.get('source', None)
        self.version = obj.get('version', None)


@dataclass
class ImageInstallWinget:
    # required
    packages: List[WingetPackage] = field(default_factory=list)
    # optional
    defaults: Optional[WingetDefaults] = None

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(ImageInstallWinget, obj, path=path, parent_key='install.winget')

        self.packages = [WingetPackage({'any': p}, path) if isinstance(p, str)
                         else WingetPackage(p, path) for p in obj['packages']]
        self.defaults = WingetDefaults(obj['defaults'], path) if 'defaults' in obj else None


@dataclass
class ImageInstallActiveSetup:
    # required
    commands: List[str] = field(default_factory=list)

    def __init__(self, obj: dict) -> None:
        _validate_data_object(ImageInstallActiveSetup, obj, parent_key='install.activesetup')

        self.commands = obj.get('commands', [])

# --------------------------------
# Image > Install
# --------------------------------


@dataclass
class ImageInstall:
    # optional
    scripts: Optional[ImageInstallScripts] = None
    choco: Optional[ImageInstallChoco] = None
    winget: Optional[ImageInstallWinget] = None
    activesetup: Optional[ImageInstallActiveSetup] = None

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(ImageInstall, obj, path=path, parent_key='install')

        self.scripts = ImageInstallScripts(obj['scripts'], path) if 'scripts' in obj else None
        self.choco = ImageInstallChoco(obj['choco'], path) if 'choco' in obj else None
        self.winget = ImageInstallWinget(obj['winget'], path) if 'winget' in obj else None


# --------------------------------
# Image
# --------------------------------


@dataclass
class ImageBase:
    # required
    publisher: str
    offer: str
    sku: str
    # optional
    version: str = 'latest'

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(ImageBase, obj, path=path, parent_key='base')

        self.publisher = obj['publisher']
        self.offer = obj['offer']
        self.sku = obj['sku']
        self.version = obj.get('version', 'latest')


@dataclass
class ImagePlan:
    # required
    publisher: str
    name: str
    product: str
    # optional
    # pippromotionCode: str

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(ImagePlan, obj, path=path, parent_key='plan')

        self.publisher = obj['publisher']
        self.name = obj['name']
        self.product = obj['product']
        # self.pippromotionCode = obj.get('pippromotionCode')


@dataclass
class Image:
    # required
    publisher: str
    offer: str
    replica_locations: List[str]
    sku: str
    version: str
    os: Literal['Windows', 'Linux']
    # optional
    description: str = None
    install: Optional[ImageInstall] = None
    base: ImageBase = None
    # optional
    plan: ImagePlan = None
    update: bool = True
    hibernate: bool = False
    # cli
    name: str = None
    dir: Path = None
    file: Path = None

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(Image, obj, path=path)

        self.publisher = obj['publisher']
        self.offer = obj['offer']
        self.replica_locations = obj['replicaLocations']
        # self.name = obj['name']
        self.sku = obj['sku']
        self.version = obj['version']
        self.os = obj['os']
        self.description = obj.get('description')
        self.install = ImageInstall(obj['install'], path) if 'install' in obj else None

        if 'base' in obj:
            self.base = ImageBase(obj['base'], path)
        elif self.os.lower() == 'windows':
            self.base = ImageBase(IMAGE_DEFAULT_BASE_WINDOWS, path)
        else:
            raise ValidationError('Image base is required for non-Windows images')

        if 'plan' in obj:
            self.plan = ImagePlan(obj['plan'], path)

        self.update = obj.get('update', True)
        self.hibernate = obj.get('hibernate', False)

        if path:
            self.name = path.parent.name
            self.dir = path.parent
            self.file = path
        elif 'name' in obj:
            self.name = obj['name']
        else:
            raise ValidationError('Image name is required if not using a file path')


# --------------------------------
# Sandbox
# --------------------------------


@dataclass
class Sandbox:
    # required
    resource_group: str
    subscription: str
    virtual_network: str
    virtual_network_resource_group: str
    default_subnet: str
    builder_subnet: str
    key_vault: str
    storage_account: str
    identity_id: str
    # optional
    location: str = None

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(Sandbox, obj, path=path, parent_key='sandbox' if path else None)

        self.resource_group = obj['resourceGroup']
        self.subscription = obj['subscription']
        self.virtual_network = obj['virtualNetwork']
        self.virtual_network_resource_group = obj['virtualNetworkResourceGroup']
        self.default_subnet = obj['defaultSubnet']
        self.builder_subnet = obj['builderSubnet']
        self.key_vault = obj['keyVault']
        self.storage_account = obj['storageAccount']
        self.identity_id = obj['identityId']
        self.location = obj.get('location')

        if not is_guid(self.subscription):
            raise ValidationError('sandbox.subscription is not a valid GUID')

        if not is_valid_resource_id(self.identity_id):
            raise ValidationError('sandbox.identityId is not a valid resource ID')


# --------------------------------
# Gallery
# --------------------------------


@dataclass
class Gallery:
    # required
    name: str
    resource_group: str
    # optional
    subscription: str = None
    # location: str

    def __init__(self, obj: dict, path: Path = None) -> None:
        _validate_data_object(Gallery, obj, path=path, parent_key='gallery' if path else None)

        self.name = obj['name']
        self.resource_group = obj['resourceGroup']
        self.subscription = obj.get('subscription')

        if self.subscription and not is_guid(self.subscription):
            raise ValidationError('gallery.subscription is not a valid GUID')


# --------------------------------
# BakeConfig
# --------------------------------


@dataclass
class BakeConfig:
    file: Path
    # required
    version: int
    sandbox: Sandbox
    gallery: Gallery
    # cli
    name: str = None
    dir: Path = None

    def __init__(self, obj: dict, path: Path) -> None:
        if 'file' not in obj:
            obj['file'] = path

        _validate_data_object(BakeConfig, obj, path=path)

        self.file = obj['file']
        self.name = self.file.name
        self.dir = self.file.parent
        # self.name = obj['name']
        # self.dir = obj['dir']

        self.version = obj['version']
        self.sandbox = Sandbox(obj['sandbox'], path)
        self.gallery = Gallery(obj['gallery'], path)
