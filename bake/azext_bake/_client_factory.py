# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
Azure SDK client factory functions.

This module provides factory functions that create Azure SDK management clients.
These factories are used throughout the extension to interact with Azure services:

- Resource management (resource groups, deployments)
- Compute (galleries, images)
- Networking (virtual networks, subnets)
- Key Vault (secrets management)
- Storage (blob storage, file shares)
- Managed Identity (user-assigned identities)
- Container Instance (Packer builder containers)

All factories use the Azure CLI's authentication context, ensuring consistent
credential handling and subscription management across operations.
"""

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType


def cf_resources(cli_ctx, **_):
    """Create a Resource Management client for resource group and deployment operations."""
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)


def cf_storage(cli_ctx, **_):
    """Create a Storage Management client for storage account operations."""
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_STORAGE)


def cf_network(cli_ctx, **_):
    """Create a Network Management client for VNet and subnet operations."""
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK)


def cf_keyvault(cli_ctx, **_):
    """Create a Key Vault Management client for vault operations."""
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_KEYVAULT)


def cf_auth(cli_ctx, scope=None):
    """
    Create an Authorization client for RBAC role assignment operations.

    Args:
        cli_ctx: Azure CLI context.
        scope: Optional resource scope to extract subscription ID from.
               If provided, the client targets that subscription.

    Returns:
        Authorization management client.
    """
    import re
    subscription_id = None
    if scope:
        matched = re.match('/subscriptions/(?P<subscription>[^/]*)/', scope)
        if matched:
            subscription_id = matched.groupdict()['subscription']
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION, subscription_id=subscription_id)


def get_graph_client(cli_ctx):
    """Create a Microsoft Graph client for Azure AD operations."""
    from azure.cli.command_modules.role import graph_client_factory
    return graph_client_factory(cli_ctx)


def cf_compute(cli_ctx, **kwargs):
    """
    Create a Compute Management client for gallery and image operations.

    Args:
        cli_ctx: Azure CLI context.
        subscription_id: Optional target subscription (from kwargs).
        aux_subscriptions: Optional auxiliary subscriptions for cross-sub operations.

    Returns:
        Compute management client.
    """
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_COMPUTE,
                                   subscription_id=kwargs.get('subscription_id'),
                                   aux_subscriptions=kwargs.get('aux_subscriptions'))


def cf_galleries(cli_ctx, _):
    """Create a client for Azure Compute Gallery operations."""
    return cf_compute(cli_ctx).galleries


def cf_gallery_images(cli_ctx, _):
    """Create a client for gallery image definition operations."""
    return cf_compute(cli_ctx).gallery_images


def cf_gallery_image_versions(cli_ctx, _):
    """Create a client for gallery image version operations."""
    return cf_compute(cli_ctx).gallery_image_versions


def cf_gallery_application(cli_ctx, *_):
    """Create a client for gallery application operations."""
    return cf_compute(cli_ctx).gallery_applications


def cf_gallery_application_version(cli_ctx, *_):
    """Create a client for gallery application version operations."""
    return cf_compute(cli_ctx).gallery_application_versions


def cf_msi(cli_ctx, **_):
    """Create a Managed Service Identity client for identity operations."""
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_MSI)


def cf_user_identities(cli_ctx, _):
    """Create a client for user-assigned managed identity operations."""
    return cf_msi(cli_ctx).user_assigned_identities


def cf_container(cli_ctx, *_):
    """Create a client for container instance operations (logs, exec)."""
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
    return get_mgmt_service_client(cli_ctx, ContainerInstanceManagementClient).containers


def cf_container_groups(cli_ctx, *_):
    """
    Create a client for container group lifecycle operations.

    Used to manage the ACI containers that execute Packer builds.
    """
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
    return get_mgmt_service_client(cli_ctx, ContainerInstanceManagementClient).container_groups


# def _msi_operations_operations(cli_ctx, _):
#     return cf_msi(cli_ctx).operations


# def _msi_federated_identity_credentials_operations(cli_ctx, _):
#     return cf_msi(cli_ctx).federated_identity_credentials
