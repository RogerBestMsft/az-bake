# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
Azure CLI extension entry point for the 'bake' command group.

This module defines the BakeCommandsLoader, which is the main entry point for the
Azure CLI extension. It follows the Azure CLI extension pattern where a single loader
class is responsible for registering all commands, parameters, and help text.

The loader is discovered by Azure CLI through the COMMAND_LOADER_CLS export.
"""

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import CliCommandType

from ._help import helps  # pylint: disable=unused-import
from ._params import load_arguments
from .commands import load_command_table


class BakeCommandsLoader(AzCommandsLoader):
    """
    Command loader for the 'az bake' extension.

    This loader registers all bake commands, parameters, and validators with the
    Azure CLI framework. It uses custom command operations defined in custom.py."""

    def __init__(self, cli_ctx=None):
        bake_custom = CliCommandType(operations_tmpl='azext_bake.custom#{}')
        super().__init__(cli_ctx=cli_ctx, custom_command_type=bake_custom)

    def load_command_table(self, args):
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        load_arguments(self, command)


COMMAND_LOADER_CLS = BakeCommandsLoader
