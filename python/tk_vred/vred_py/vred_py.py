# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import builtins
import importlib
import inspect
import sys
import types

from . import (
    api_animation,
    api_material,
    api_node,
    api_settings,
    api_utils,
)


class VREDPy:
    """A wrapper class for interacting with the VRED API."""

    # VREDPy Exception Classes
    # ----------------------------------------------------------------------------------------
    class VREDPyError(Exception):
        """Base VREDPy exception class."""

    class VREDPyNotSupportedError(VREDPyError):
        """Exception class to report unsupported VRED API functionality."""

    def __init__(self):
        """
        Initialize.

        :param logger: The logger object to report messages to.
        :type logger: Standard python logger.
        """

        # The VRED API module. Initialize with class since this is not specific to each instance.
        self.__vred_api = self.__get_vred_api_module()

        # Define patch functiosn for VRED api attributes.
        self.__patch_attributes = {}

    def __getattr__(self, name):
        """
        Get the attribute from the VRED api module.

        From the Python docs:

            Called when the default attribute access fails with an AttributeError (either
            __getattribute__() raises an AttributeError because name is not an instance
            attribute or an attribute in the class tree for self; or __get__() of a name
            property raises AttributeError). Note that if the attribute is found through the
            normal mechanism, __getattr__() is not called.

        The VREDPy class is a wrapper for the VRED api module. Accessing an attribute through
        the VREDPy class will return attribute from the VRED api module, unless the attribute
        is defined on the VREDPy class. For this reason, the VREDPy class should not define any
        other functionality, with the exception to methods that are used to provide patches for
        VRED api attributes (for version handling).

        :param name: The name of the attribute to get.
        :type name: str

        :raises AttributeError: If the attribute not found for the VRED api.

        :return: The VRED api attribute for the given name.
        :rtype: Any
        """

        try:
            # Get the attribute from the api module
            #
            # NOTE if attributes exist in multiple api versions, but require different
            # handling (e.g. function signature changed), then a patch function will need
            # to be run before returning the attribute immediately if it exists.
            return getattr(self.__vred_api, name)

        except AttributeError:
            # Attribute not found in the api, try to patch it.
            patch_func = self.__patch_attributes.get(name)
            if patch_func:
                patched_attr = patch_func()
            else:
                patched_attr = None

            if patched_attr is None:
                # hasattr call this method and expects AttributeError to be raised when the
                # attribute is not found.
                raise AttributeError(
                    f"This VRED version does not support the API attribute: {name}"
                )

            return patched_attr

    # Private methods
    # ----------------------------------------------------------------------------------------

    def __get_vred_api_module(self):
        """
        Return an object that wraps the VRED API functionality.

        The module created will be named `vred_py`.

        VRED API functionality search method:

            - v1 functionality is found in `sys.builtin_module_names`
            - v2  functionality is found in the `builtins` module
            - The module is decided as a VRED module if the module name starts with `vr` (this
              is not guaranteed to ONLY get VRED modules, but more importantly it should at
              least get all VRED modules. TODO investigate better way to determine VRED module)

        :return: The VRED API wrapper object, called `vred_py`.
        :rtype: module
        """

        # Create a Python module for the VRED API
        vred_py = types.ModuleType("vred_py")
        existing_attribute_names = set()

        # Get the v1 modules
        module_names = sys.builtin_module_names
        for module_name in module_names:
            if not module_name.startswith("vr"):
                continue  # Not a VRED module
            # First the module must be imported
            module = importlib.import_module(module_name)
            # Add the VRED module as an attribute on the vred_py wrapper
            setattr(vred_py, module_name, module)
            existing_attribute_names.add(module_name)
            # For vrKernelServices, add its members as vred_py attributes; e.g. vrdNode is
            # defined as a built-in, which means it can be directly accessible without import,
            # so make sure our wrapper also has direct acces to it.
            if module_name == "vrKernelServices":
                kernel_members = inspect.getmembers(module)
                for kernel_member_name, kernel_member in kernel_members:
                    if kernel_member_name.startswith("_"):
                        continue  # Skip protected and private members
                    setattr(vred_py, kernel_member_name, kernel_member)
                    existing_attribute_names.add(kernel_member_name)

        # Get the v2 modules
        builtin_members = inspect.getmembers(builtins)
        for module_name, module in builtin_members:
            if not module_name.startswith("vr"):
                continue  # Not a VRED module
            setattr(vred_py, module_name, module)

        # Add the api helper modules to the wrapper. Make sure there are no attribute naming
        # conflicts.
        api_modules = [
            api_animation.VREDPyAnimation(self),
            api_material.VREDPyMaterial(self),
            api_node.VREDPyNode(self),
            api_settings.VREDPySetting(self),
            api_utils.VREDPyUtils(self),
        ]
        for api_module in api_modules:
            members = inspect.getmembers(api_module)
            for member_name, member in members:
                if member_name.startswith("_"):
                    continue  # Skip protected and private members
                if member_name in existing_attribute_names:
                    raise NameError(f"VREDPy already has attribute '{member_name}'")
                setattr(vred_py, member_name, member)

        return vred_py
