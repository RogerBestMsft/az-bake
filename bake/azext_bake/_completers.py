# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
# pylint: disable=inconsistent-return-statements, unused-argument

"""
CLI tab completion providers for the 'az bake' extension.

This module implements completers that provide tab-completion suggestions for
CLI parameters. These enhance the user experience by enabling auto-completion
of values like GitHub release versions and Azure resource names.

Completers are decorated with @Completer and registered with parameters in
_params.py to provide context-aware suggestions.
"""

# import requests

from azure.cli.core.commands.parameters import get_resources_in_resource_group, get_resources_in_subscription
from azure.cli.core.decorators import Completer

# from ._client_factory import cf_network, cf_resources
from ._github import get_github_releases
from ._utils import get_logger

logger = get_logger(__name__)


# @Completer
# def subnet_completion_list(cmd, prefix, ns, **kwargs):
#     client = network_client_factory(cmd.cli_ctx)
#     if ns.resource_group_name and ns.vnet_name:
#         rg = ns.resource_group_name
#         vnet = ns.vnet_name
#         return [r.name for r in client.subnets.list(resource_group_name=rg, virtual_network_name=vnet)]


@Completer
def get_version_completion_list(cmd, prefix, ns, **kwargs):
    """
    Provide tab completion for az bake extension versions.

    Returns a list of available release versions from GitHub releases,
    enabling users to easily select a specific version for upgrade.
    """
    return [r['tag_name'] for r in get_github_releases()]


def get_resource_name_completion_list(group_option='resource_group_name', resource_type=None):
    """
    Factory for creating resource name completers.

    Creates a completer that suggests Azure resource names, either from a
    specific resource group (if provided) or from the entire subscription.

    Args:
        group_option: Name of the namespace attribute containing the resource group.
        resource_type: Optional filter for specific Azure resource types.

    Returns:
        A Completer function for resource name suggestions.
    """

    @Completer
    def completer(cmd, prefix, ns, **kwargs):
        rg = getattr(ns, group_option, None)
        if rg:
            return [r.name for r in get_resources_in_resource_group(cmd.cli_ctx, rg, resource_type=resource_type)]
        return [r.name for r in get_resources_in_subscription(cmd.cli_ctx, resource_type)]

    return completer


# def get_default_location_from_sandbox_resource_group(cmd, ns):
#     if not ns.location:
#         # We don't use try catch here to let azure.cli.core.parser.AzCliCommandParser.validation_error
#         # handle exceptions, such as azure.core.exceptions.ResourceNotFoundError
#         resource_client = cf_resources(cmd.cli_ctx)
#         rg = resource_client.resource_groups.get(ns.sandbox_resource_group_name)
#         ns.location = rg.location  # pylint: disable=no-member

#         logger.debug("using location '%s' from sandbox resource group '%s'", ns.location, rg.name)
