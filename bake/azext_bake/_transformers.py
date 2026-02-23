# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
Output transformers for CLI command results.

This module provides functions to transform command output before displaying
to the user. Transformers are registered in commands.py via the 'transformer'
parameter and can reshape, filter, or format output data.

Currently minimal, but designed for future output formatting needs.
"""

# from collections import OrderedDict

from ._utils import get_logger

logger = get_logger(__name__)
