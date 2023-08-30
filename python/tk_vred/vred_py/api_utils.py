# Copyright (c) 2023 Autodesk.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk.

from .base import VREDPyBase
from . import constants


class VREDPyUtils(VREDPyBase):
    """VRED Python API utility class."""

    def __init__(self, vred_py):
        """Initialize"""
        super(VREDPyUtils, self).__init__(vred_py)

    # -------------------------------------------------------------------------------------------------------
    # VRED API Versioning
    # -------------------------------------------------------------------------------------------------------

    def v1(self):
        """Return the VRED API version 1 string."""
        return constants.VRED_API_V1

    def v2(self):
        """Return the VRED API version 2 string."""
        return constants.VRED_API_V2

    def supported_api_versions(self):
        """Return the supported VRED API versions."""
        return constants.SUPPORTED_VRED_API_VERSIONS

    def check_api_version(self, version):
        """
        Check if the given VRED APi version is supported.

        :param version: The VRED API version to check.
        :type version: str

        :throws VREDPyError: If the given version is not supported.
        """

        if version not in self.supported_api_versions():
            raise self.vred_py.VREDPyError(
                "Unsupported VRED API version '{}'. Supported versions are {}".format(
                    version,
                    ", ".join(constants.SUPPORTED_VRED_API_VERSIONS),
                )
            )

    # -------------------------------------------------------------------------------------------------------
    # VRED API Types
    # -------------------------------------------------------------------------------------------------------

    def clip_type(self):
        """Return the Animation Clip type name."""
        return constants.VRED_TYPE_CLIP

    def anim_type(self):
        """Return the Animation Wizard Clip type name."""
        return constants.VRED_TYPE_ANIM

    def switch_node_type(self, api_version=None):
        """
        Return the Switch node type for the specified api version.

        :param api_version: The VRED API version to get the type from.
        :type api_version: str (v1|v2)

        :return: The switch node type.
        :rtype: str (for v1) or class (for v2)
        """

        api_version = api_version or self.v1()

        self.check_api_version(api_version)

        if api_version == constants.VRED_API_V1:
            return constants.NODE_TYPE_V1_SWITCH
        return self.vred_py.vrdSwitchNode

    # -------------------------------------------------------------------------------------------------------
    # Objects
    # -------------------------------------------------------------------------------------------------------

    def get_id(self, obj):
        """
        Return the ID for the given object.

        :param obj: The object to get the ID for.
        :type obj: VRED object

        :return: The object ID.
        :rtype: int
        """

        if isinstance(obj, self.vred_py.vrdNode):
            return obj.getObjectId()

        if isinstance(obj, self.vred_py.vrNodePtr.vrNodePtr):
            return obj.getID()

        # Default to returning the object itself as the id if could not determine the id based
        # on object type.
        return obj

    def get_type_as_str(self, obj):
        """
        Determine the object type and return the string representation.

        :param obj: The object to get the type as string for.
        :type obj: VRED object
        """

        if not obj:
            return None

        if hasattr(obj, "getType"):
            return obj.getType()

        try:
            is_vrd_object = isinstance(obj, self.vred_py.vrdObject)
        except:
            is_vrd_object = False

        if is_vrd_object:
            # Object is a VRED API v2 object.
            return type(obj).__name__

        # Object type not found. Log an error and just return None to not interrupt the user.
        try:
            obj_type = type(obj).__name__
            error_msg = "Object type '{}' not found.".format(obj_type)
        except:
            error_msg = "Object type not found."
        self.__logger.error(error_msg)

        return None
