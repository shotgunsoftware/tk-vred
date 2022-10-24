# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import traceback

import sgtk
from sgtk.platform.qt import QtCore, QtGui

# VRED API v1 imports. VRED API v2 modules are included in the builtins so no need to
# explicitly import them.
import vrOptimize
import vrScenegraph
import vrGeometryEditor
import vrNodePtr
import vrNodeUtils
import vrVariantSets
import vrAnimWidgets
import vrController
import vrFileDialog
import vrFileIO
import vrRenderSettings
import vrVredUi


# Supported VRED API versions
VRED_API_V1 = "v1"
VRED_API_V2 = "v2"
SUPPORTED_VRED_API_VERSIONS = (VRED_API_V1, VRED_API_V2)

# VRED Types
VRED_TYPE_CLIP = "AnimClip"
VRED_TYPE_ANIM = "AnimWizClip"

# Node Types for v1
NODE_TYPE_V1_SWITCH = "Switch"


class VREDPy:
    """A helper class for interacting with the VRED API."""

    class VREDPyError(Exception):
        """Custom exception class for VRED API errors."""

    class VREDModuleNotSupported(Exception):
        """Custom exception class for reporting VRED API modules that are not supported."""

    class VREDFunctionNotSupported(Exception):
        """Custom exception class for reporting VRED API modules that are not supported."""

    def __init__(self, logger=None):
        """
        Initialize.

        :param logger: The logger object to report messages to.
        :type logger: Standard python logger.
        """

        self.__logger = logger or sgtk.platform.get_logger(__name__)

    #########################################################################################################
    # Properties
    #########################################################################################################

    # -----------------------------------------------------------------------------------------
    # VRED API Modules
    # -----------------------------------------------------------------------------------------
    # Set up properties for each VRED API module so that importing the modules can be done once
    # here in this module, and all other modules can access the modules through the VREDPy
    # properties. This handles importing modules when using different versions of VRED (e.g.
    # handles exceptions when module is not supported by the current version of VRED).

    @property
    def vrUVService(self):
        """Return the VRED v2 API module vrUVService."""
        try:
            return vrUVService
        except (ImportError, NameError):
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported("vrUVService requires VRED >= 2021.2.0")

    @property
    def vrSceneplateService(self):
        """Return the VRED v2 API module vrSceneplateService."""
        try:
            return vrSceneplateService
        except (ImportError, NameError):
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrSceneplateService requires VRED >= 2021.0.0"
            )

    @property
    def vrImageService(self):
        """Return the VRED v2 API module vrImageService."""
        try:
            return vrImageService
        except (ImportError, NameError):
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrImageService requires VRED >= 2021.0.0"
            )

    @property
    def vrGUIService(self):
        """Return the VRED v2 API module vrGUIService."""
        try:
            return vrGUIService
        except (ImportError, NameError):
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrGUIService requires VRED >= 2022.2.0"
            )

    @property
    def vrFileIOService(self):
        """Return the VRED v2 API module vrFileIOService."""
        try:
            return vrFileIOService
        except (ImportError, NameError):
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrFileIOService requires VRED >= 2021.0.0"
            )

    @property
    def vrNodeService(self):
        """Return the VRED v2 API module vrNodeService."""
        try:
            return vrNodeService
        except (ImportError, NameError):
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrNodeService requires VRED >= 2021.0.0"
            )

    @property
    def vrMaterialService(self):
        """Return the VRED v2 API module vrMaterialService."""
        try:
            return vrMaterialService
        except (ImportError, NameError):
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrMaterialService requires VRED >= 2023.0.0"
            )

    @property
    def vrReferenceService(self):
        """Return the VRED v2 API module vrReferenceService."""
        try:
            return vrReferenceService
        except (ImportError, NameError):
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrReferenceService requires VRED >= 2021.0.0"
            )

    @property
    def vrBakeService(self):
        """Return the VRED v2 API module vrBakeService."""
        try:
            return vrBakeService
        except (ImportError, NameError):
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrBakeService requires VRED >= 2022.0.0"
            )

    @property
    def vrDecoreService(self):
        """Return the VRED v2 API module vrDecoreService."""
        try:
            return vrDecoreService
        except (ImportError, NameError):
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrDecoreService requires VRED >= 2023.0.0"
            )

    @property
    def vrdDecoreSettings(self):
        """Return the VRED v2 API module vrdDecoreSettings."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdDecoreSettings
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdDecoreSettings

            return vrdDecoreSettings
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdDecoreSettings requires VRED >= 2023.0.0"
            )

    @property
    def vrGeometryTypes(self):
        """Return the VRED v2 API module vrGeometryTypes."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrGeometryTypes
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            # Attempt to import the module and return it.
            from vrKernelServices import vrGeometryTypes

            return vrGeometryTypes
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrGeometryTypes requires VRED >= 2021.2.0"
            )

    @property
    def vrdGeometryNode(self):
        """Return the VRED v2 API module vrdGeometryNode."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdGeometryNode
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdGeometryNode

            return vrdGeometryNode
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdGeometryNode requires VRED >= 2021.2.0"
            )

    @property
    def vrdTransformNode(self):
        """Return the VRED v2 API module vrdTransformNode."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdTransformNode
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdTransformNode

            return vrdTransformNode
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdTransformNode not supported with current version of VRED"
            )

    @property
    def vrdSwitchNode(self):
        """Return the VRED v2 API module vrdSwitchNode."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdSwitchNode
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdSwitchNode

            return vrdSwitchNode
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdSwitchNode not supported with current version of VRED"
            )

    @property
    def vrdNode(self):
        """Return the VRED v2 API module vrdNode."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdNode
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdNode

            return vrdNode
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported("vrdNode requires VRED >= 2021.0.0")

    @property
    def vrdSceneplateNode(self):
        """Return the VRED v2 API module vrdSceneplateNode."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdSceneplateNode
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdSceneplateNode

            return vrdSceneplateNode
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdSceneplateNode requires VRED >= 2021.0.0"
            )

    @property
    def vrdMaterialNode(self):
        """Return the VRED v2 API module vrdMaterialNode."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdMaterialNode
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdMaterialNode

            return vrdMaterialNode
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdMaterialNode requires VRED >= 2023.0.0"
            )

    @property
    def vrdSurfaceNode(self):
        """Return the VRED v2 API module vrdSurfaceNode."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdSurfaceNode
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdSurfaceNode

            return vrdSurfaceNode
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdSurfaceNode requires VRED >= 2021.2.0"
            )

    @property
    def vrdReferenceNode(self):
        """Return the VRED v2 API module vrdReferenceNode."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdReferenceNode
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdReferenceNode

            return vrdReferenceNode
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdReferenceNode requires VRED >= 2021.0.0"
            )

    @property
    def vrdObject(self):
        """Return the VRED v2 API module vrdObject."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdObject
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdObject

            return vrdObject
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported("vrdObject requires VRED >= 2021.0.0")

    @property
    def vrdMaterial(self):
        """Return the VRED v2 API module vrdMaterial."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdMaterial
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdMaterial

            return vrdMaterial
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported("vrdMaterial requires VRED >= 2023.0.0")

    @property
    def vrSceneplateTypes(self):
        """Return the VRED v2 API module vrSceneplateTypes."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrSceneplateTypes
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrSceneplateTypes

            return vrSceneplateTypes
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrSceneplateTypes requires VRED >= 2021.0.0"
            )

    @property
    def vrUVTypes(self):
        """Return the VRED v2 API module vrUVTypes."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrUVTypes
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrUVTypes

            return vrUVTypes
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported("vrUVTypes requires VRED >= 2021.2.0")

    @property
    def vrBakeTypes(self):
        """Return the VRED v2 API module vrBakeTypes."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrBakeTypes
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrBakeTypes

            return vrBakeTypes
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported("vrBakeTypes requires VRED >= 2022.0.0")

    @property
    def vrdUVUnfoldSettings(self):
        """Return the VRED v2 API module vrdUVUnfoldSettings."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdUVUnfoldSettings
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdUVUnfoldSettings

            return vrdUVUnfoldSettings
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdUVUnfoldSettings requires VRED >= 2021.2.0"
            )

    @property
    def vrdUVLayoutSettings(self):
        """Return the VRED v2 API module vrdUVLayoutSettings."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdUVLayoutSettings
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdUVLayoutSettings

            return vrdUVLayoutSettings
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdUVLayoutSettings requires VRED >= 2021.2.0"
            )

    @property
    def vrdIlluminationBakeSettings(self):
        """Return the VRED v2 API module vrdIlluminationBakeSettings."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdIlluminationBakeSettings
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdIlluminationBakeSettings

            return vrdIlluminationBakeSettings
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdIlluminationBakeSettings requires VRED >= 2022.0.0"
            )

    @property
    def vrdTextureBakeSettings(self):
        """Return the VRED v2 API module vrdTextureBakeSettings."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdTextureBakeSettings
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdTextureBakeSettings

            return vrdTextureBakeSettings
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdTextureBakeSettings requires VRED >= 2022.0.0"
            )

    @property
    def vrdClearcoat(self):
        """Return the VRED v2 API module vrdClearcoat."""
        first_error = None
        try:
            # Attempt to return the module right away.
            return vrdClearcoat
        except (ModuleNotFoundError, UnboundLocalError):
            # Module not found. Continue on to try to import.
            first_error = traceback.format_exc()

        try:
            from vrKernelServices import vrdClearcoat

            return vrdClearcoat
        except (ImportError, NameError):
            if first_error:
                # Log the first error as well, if there was one.
                self.__logger.debug(first_error)
            self.__logger.debug(traceback.format_exc())
            raise VREDPy.VREDModuleNotSupported(
                "vrdClearcoat not supported with current version of VRED"
            )

    @property
    def vrAnimWidgets(self):
        """Return the VRED v1 API module vrAnimWidgets."""
        return vrAnimWidgets

    @property
    def vrVariantSets(self):
        """Return the VRED v1 API module vrVariantSets."""
        return vrVariantSets

    @property
    def vrNodeUtils(self):
        """Return the VRED v1 API module vrNodeUtils."""
        return vrNodeUtils

    @property
    def vrNodePtr(self):
        """Return the VRED v1 API module vrNodePtr."""
        return vrNodePtr

    @property
    def vrGeometryEditor(self):
        """Return the VRED v1 API module vrGeometryEditor."""
        return vrGeometryEditor

    @property
    def vrScenegraph(self):
        """Return the VRED v1 API module vrScenegraph."""
        return vrScenegraph

    @property
    def vrOptimize(self):
        """Return the VRED v1 API module vrOptimize."""
        return vrOptimize

    @property
    def vrVredUi(self):
        """Return the VRED v1 API module vrVredUi."""
        return vrVredUi

    @property
    def vrRenderSettings(self):
        """Return the VRED v1 API module vrRenderSettings."""
        return vrRenderSettings

    @property
    def vrFileIO(self):
        """Return the VRED v1 API module vrFileIO."""
        return vrFileIO

    @property
    def vrFileDialog(self):
        """Return the VRED v1 API module vrFileDialog."""
        return vrFileDialog

    @property
    def vrController(self):
        """Return the VRED v1 API module vrController."""
        return vrController

    #########################################################################################################
    # Static methods
    #########################################################################################################

    # -------------------------------------------------------------------------------------------------------
    # VRED API Versioning
    # -------------------------------------------------------------------------------------------------------

    @staticmethod
    def v1():
        """Return the VRED API version 1 string."""
        return VRED_API_V1

    @staticmethod
    def v2():
        """Return the VRED API version 2 string."""
        return VRED_API_V2

    @staticmethod
    def supported_api_versions():
        """Return the supported VRED API versions."""
        return SUPPORTED_VRED_API_VERSIONS

    @staticmethod
    def check_api_version(version):
        """
        Check if the given VRED APi version is supported.

        :param version: The VRED API version to check.
        :type version: str

        :throws VREDPy.VREDPyError: If the given version is not supported.
        """

        if version not in VREDPy.supported_api_versions():
            raise VREDPy.VREDPyError(
                "Unsupported VRED API version '{}'. Supported versions are {}".format(
                    version,
                    ", ".join(SUPPORTED_VRED_API_VERSIONS),
                )
            )

    # -------------------------------------------------------------------------------------------------------
    # VRED API Types
    # -------------------------------------------------------------------------------------------------------

    @staticmethod
    def clip_type():
        """Return the Animation Clip type name."""
        return VRED_TYPE_CLIP

    @staticmethod
    def anim_type():
        """Return the Animation Wizard Clip type name."""
        return VRED_TYPE_ANIM

    #########################################################################################################
    # Public methods
    #########################################################################################################

    # -------------------------------------------------------------------------------------------------------
    # VRED API Node Types
    # -------------------------------------------------------------------------------------------------------
    def switch_node_type(self, api_version=VRED_API_V1):
        """
        Return the Switch node type for the specified api version.

        :param api_version: The VRED API version to get the type from.
        :type api_version: str (v1|v2)

        :return: The switch node type.
        :rtype: str (for v1) or class (for v2)
        """

        VREDPy.check_api_version(api_version)

        if api_version == VRED_API_V1:
            return NODE_TYPE_V1_SWITCH
        return self.vrdSwitchNode

    # -------------------------------------------------------------------------------------------------------
    # Objects
    # -------------------------------------------------------------------------------------------------------

    def get_id(self, obj):
        """
        Return the ID for the given object.

        :param obj: The object to get the ID for.
        :typeo obj: VRED object

        :return: The object ID.
        :rtype: int
        """

        if isinstance(obj, self.vrdNode):
            return obj.getObjectId()

        if isinstance(obj, self.vrNodePtr.vrNodePtr):
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
            is_vrd_object = isinstance(obj, self.vrdObject)
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

    # -------------------------------------------------------------------------------------------------------
    # Nodes
    # -------------------------------------------------------------------------------------------------------

    def get_root_node(self, api_version=VRED_API_V1):
        """
        Return the root node.

        Use the specified api version to get the root node.

        :param api_version: The VRED API version used to get the root node.
        :type api_version: str (v1|v2)
        """

        VREDPy.check_api_version(api_version)

        if api_version == VREDPy.v1():
            return self.vrScenegraph.getRootNode()
        else:
            try:
                return self.vrNodeService.getRootNode()
            except AttributeError:
                raise VREDPy.VREDFunctionNotSupported(
                    "vrNodeService.getRootNode() function not supported in current version of VRED."
                )

    def is_geometry_node(self, node):
        """
        Return True if the node is a geometry node.

        Do not include surface nodes.

        This method compatible with only VRED API v2.

        :param node: The node to check.
        :type node: vrNodePtr | vrdNode

        :return: True if the node is a geometry node, else False.
        :rtype: bool
        """

        if isinstance(node, self.vrdSurfaceNode):
            # Do not include surface nodes
            return False

        return isinstance(node, self.vrdGeometryNode)

    def get_nodes(self, items, api_version=VRED_API_V1):
        """
        Return a list of node objects.

        :param items: The list of items to convert to nodes. This list may contain one of:
            str - the node name
            int - the node id
            dict - the node data with required key "id"
            vrNodePtr - the node object (v1)
            vrdNode - the node object (v2)
        :type items: list
        :param api_version: The VRED API version to use for conversion. For v1, nodes of type
            vrNodePtr will be returned. For v2, nodes of type vrdNode will be returned.
        :type api_version: str

        :return: The list of nodes converted from the given items.
        :rtype: list<vrNodePtr> | list<vrdNode>
        """

        VREDPy.check_api_version(api_version)

        nodes = []
        if not items:
            return nodes

        if not isinstance(items, (list, tuple)):
            items = [items]

        for item in items:
            if isinstance(item, dict):
                item = item.get("id")

            node = None
            if isinstance(item, self.vrNodePtr.vrNodePtr):
                if api_version == VREDPy.v1():
                    node = item
                else:
                    node = self.vrNodeService.getNodeFromId(item.getID())
            elif isinstance(item, self.vrdNode):
                if api_version == VREDPy.v1():
                    node = self.vrNodePtr.toNode(item.getObjcetId())
                else:
                    node = item
            elif isinstance(item, int):
                if api_version == VREDPy.v1():
                    node = self.vrNodePtr.toNode(item)
                else:
                    node = vrNodeService.getNodeFromId(item)
            else:
                try:
                    if api_version == VREDPy.v1():
                        node = self.vrScenegraph.findNode(item)
                    else:
                        node = self.vrNodeService.findNode(item)
                except Exception:
                    pass

            if node:
                nodes.append(node)
            else:
                raise VREDPy.VREDPyError("Failed to convert {} to node".format(item))

        return nodes

    def get_geometry_nodes(self, root_node=None, has_mat_uvs=None, has_light_uvs=None):
        """
        Return all geometry nodes in the subtree of the root_node.

        Nodes within the subtree of the given root node will be checked. If no root node is given
        then the top root node will be used.

        :param root_node: The subtree of this root node will be checked. If None, the scene
            graph root node will be used.
        :type root_node: vrdNode

        :return: The list of geometry nodes.
        :rtype: list<vrdNode>
        """

        def _get_geometry_nodes(node, result, has_mat_uvs=None, has_light_uvs=None):
            """
            Recursive helper function to get geoemtry nodes.

            :param node: The current node.
            :type node: vrdNode
            :param has_mat_uvs: ...
            """

            if not node:
                return

            is_geom = VREDPy.is_geometry_node(node)

            if is_geom:
                if has_mat_uvs is None and has_light_uvs is None:
                    # Add geometry regardless of material/light UVs
                    result.append(node)
                elif has_mat_uvs is None and has_light_uvs is None:
                    # Add geometry based on both material/light UVs
                    if (
                        node.hasUVSet(self.vrUVTypes.MaterialUVSet) == has_mat_uvs
                        and node.hasUVSet(self.vrUVTypes.LightmapUVSet) == has_light_uvs
                    ):
                        result.append(node)
                elif has_mat_uvs is None:
                    # Add only geometry based on light UVs, ignore material UVs
                    if node.hasUVSet(self.vrUVTypes.LightmapUVSet) == has_light_uvs:
                        result.append(node)
                elif has_light_uvs is None:
                    # Add only geometry based on material UVs, ignore light UVs
                    if node.hasUVSet(self.vrUVTypes.MaterialUVSet) == has_mat_uvs:
                        result.append(node)

            for child in node.getChildren():
                _get_geometry_nodes(
                    child, result, has_mat_uvs=has_mat_uvs, has_light_uvs=has_light_uvs
                )

        root_node = root_node or self.get_root_node(api_version=VREDPy.v2())
        nodes = []
        _get_geometry_nodes(
            root_node, nodes, has_mat_uvs=has_mat_uvs, has_light_uvs=has_light_uvs
        )
        return nodes

    def get_hidden_nodes(
        self, root_node=None, ignore_node_types=None, api_version=VRED_API_V1
    ):
        """
        Return a list of the hidden nodes in the scene graph.

        If a node is hidden, all of its children are hidden but the node's children will
        not be included in the list of hidden nodes returned.

        :param root_node: The node to check subtree only for hidden nodes. If None, then
            the scene graph root node will be used to check all nodes.
        :param root_node: vrNodePtr | vrdNode
        :param ignore_node_types: A list of node types to exclude from the result. All children
            of these types of nodes will also be ignored (regardless of the child node type).
            This list of types must correspond to the `api_version`.
        :type ignore_node_types: list<str> (for v1) | list<class> (for v2)
        :param api_version: The VRED API version used to retrieve and return hidden node.
        :type api_version: str
        """

        VREDPy.check_api_version(api_version)

        ignore_node_types = ignore_node_types or []

        if root_node is None:
            nodes = [self.get_root_node(api_version=api_version)]
        else:
            nodes = [root_node]

        hidden = []
        while nodes:
            node = nodes.pop()

            if isinstance(node, self.vrNodePtr.vrNodePtr):
                # v1
                if node.getType() in ignore_node_types:
                    continue

                if not node.getActive():
                    hidden.append(node)
                else:
                    # Only check children if the parent is not hidden
                    for i in range(node.getNChildren()):
                        nodes.append(node.getChild(i))
            else:
                # v2
                if type(node) in ignore_node_types:
                    continue

                if not node.isVisible():
                    hidden.append(node)
                else:
                    # Only check children if the parent is not hidden
                    for child in node.getChildren():
                        nodes.append(child)

        return hidden

    def delete_nodes(self, nodes, force=False):
        """
        Delete the given nodes.

        :param nodes: The nodes to delete. The elements in the list must be uniform.
        :type nodes: list<vrNodePtr> | list<vrdNode>
        :param force: Applicable for v1 only. Force delete if true, else undeleteable nodes are
            also deleted. Default is false.
        :type force: bool
        """

        if not nodes:
            return

        # Check the first node to detect which api version to use to delete.
        # Assumes the list has uniform elements
        if isinstance(nodes[0], self.vrNodePtr.vrNodePtr):
            self.vrScenegraph.deleteNodes(nodes, force)

        elif isinstance(nodes[0], self.vrdNode):
            self.vrNodeService.removeNodes(nodes)

        else:
            raise VREDPy.VREDPyError("Not a node {}".format(nodes[0]))

    def set_to_b_side(self, nodes, b_side=True):
        """
        Set the given nodes to the B-Side.

        This method handles a list of v1 or v2 VRED APi nodes.

        :param nodes: THe list of nodes to set.
        :type nodes: list<vrNodePtr> | list<vrdNode>
        :param b_side: True to set to B-Side.
        :type b_side:bool
        """

        if not nodes:
            return

        for node in nodes:
            # Check if we're handling a v1 or v2 node object
            if isinstance(node, self.vrNodePtr.vrNodePtr):
                self.vrNodeUtils.setToBSide(node, b_side)
            elif isinstance(node, self.vrdGeometryNode):
                node.setToBSide(b_side)
            else:
                raise VREDPy.VREDPyError("Not a geometry node {}".format(node))

    def show_nodes(self, nodes):
        """
        Show the nodes.

        :param nodes: The nodes to show. The elements in the list must be uniform.
        :type nodes: list<vrNodePtr> | list<vrdNode>
        """

        if not nodes:
            return

        # Check the first node to detect which api version to use to delete.
        # Assumes the list has uniform elements
        if isinstance(nodes[0], self.vrNodePtr.vrNodePtr):
            self.vrScenegraph.showNodes(nodes)

        elif isinstance(nodes[0], self.vrdNode):
            for node in nodes:
                node.setVisibilityFlag(True)

        else:
            raise VREDPy.VREDPyError("Not a node {}".format(nodes[0]))

    def group_nodes(self, nodes):
        """
        Group the given nodes.

        Group the nodes by selecting all nodes, then calling the group selection method, and
        then finally deselecting all nodes.

        NOTE that this will create the group in the scene graph UI and select the text to edit
        the name of the group created.

        This method compatible with only VRED API v1.

        :param nodes: The nodes to group.
        :type nodes: list<vrNodePtr>
        """

        select = True
        self.vrScenegraph.selectNodes(nodes, select)
        self.vrScenegraph.groupSelection()
        self.vrScenegraph.deselectAll()

    # -------------------------------------------------------------------------------------------------------
    # Materials
    # -------------------------------------------------------------------------------------------------------

    def get_materials(self, items):
        """
        Return a list of material objects.

        :param items: The list of items to convert to materials. This list may contain
            material names (str), ids (int), or objects (vrdMaterial).
        :type items: list

        :return: The list of materials converted from the given items.
        :rtype: list<vrdMaterial>
        """

        materials = []
        if not items:
            return materials

        if not isinstance(items, (list, tuple)):
            items = [items]

        for item in items:
            if isinstance(item, dict):
                item = item.get("id")

            mat = None
            if isinstance(item, self.vrdMaterial):
                mat = item
            elif isinstance(item, int):
                mat = self.vrMaterialService.getMaterialFromId(item)
            else:
                try:
                    mat = self.vrMaterialService.findMaterial(item)
                except Exception:
                    pass

            if mat:
                materials.append(mat)
            else:
                raise VREDPy.VREDPyError(
                    "Failed to convert object {} to material".format(item)
                )

        return materials

    def find_materials(self, using_orange_peel=None, using_texture=None):
        """
        Return a list of materials matching the given parameters.

        :param using_orange_peel:
            True  - return materials that have the clearcoat property and have set to use
                    Orange Peel
            False - return materials that have the clearcoat property and have set to not
                    use Orange Peel
            None  - ignore this property (default)
        :type using_orange_peel: bool
        :param using_texture:
            True  - return materials that have the bump texture property and have set to use
                    texture
            False - return materials that have the clearcoat property and have set to not use
                    texture
            None  - ignore this property (default)
        :type using_texture: bool

        :return: The list of materials.
        :rtype: list<vrdMaterial>
        """

        mats = self.vrMaterialService.getAllMaterials()

        if using_orange_peel is None and using_texture is None:
            return mats

        result = []
        for mat in mats:
            # Check clearcoat orange peel property, if specified.
            if using_orange_peel is not None:
                try:
                    clearcoat = mat.getClearcoat()
                except AttributeError:
                    # This material does not have the clearcoat property. Do not accept it.
                    continue

                mat_supports_orange_peel = clearcoat.supportsOrangePeel()
                if not mat_supports_orange_peel:
                    # This material does not support the clearcoat property. Do not accept it.
                    continue

                clearcoat_off = clearcoat.getType() == self.vrdClearcoat.Type.Off
                if clearcoat_off:
                    # This material has clearcoat turned off. Do not accept it.
                    continue

                mat_using_orange_peel = clearcoat.getUseOrangePeel()
                if using_orange_peel != mat_using_orange_peel:
                    # This material clearcoat value does not match the desired value. Do not accept it.
                    continue

            # Check bump texture property, if specified.
            if using_texture is not None:
                try:
                    bump_texture = mat.getBumpTexture()
                except AttributeError:
                    bump_texture = None

                if not bump_texture or using_texture != bump_texture.getUseTexture():
                    continue

            # Material accepted, add it to the results list
            result.append(mat)

        return result

    # -------------------------------------------------------------------------------------------------------
    # Animation
    # -------------------------------------------------------------------------------------------------------

    def is_animation_clip(self, clip_node):
        """
        Return True if the clip is an Animation Clip.

        This method compatible with only VRED API v1.

        :param clip_node: The clip to check.
        :type clip_node: vrNodePtr
        """

        return clip_node.getType() == self.clip_type()

    def get_animation_clips(self, top_level_only=True, anim_type=VRED_TYPE_CLIP):
        """
        Return all animation clip nodes.

        This method compatible with only VRED API v1.

        :param top_level_only: True will return only the top-level animation clip nodes, else
            False will return all animation clip nodes. This only works with type 'AnimClip'.
        :type top_level_only: bool
        :param anim_type: The type of animation clip nodes to return.
        :type anim_type: str

        :return: The animation clip nodes.
        :rtype: list<vrNodePtr>
        """

        # TODO support multiple animation types to accept

        top_level_nodes = self.vrAnimWidgets.getAnimClipNodes()

        if top_level_only and anim_type == self.clip_type():
            return top_level_nodes

        # Recurse to get all child nodes
        nodes = []
        while top_level_nodes:
            node = top_level_nodes.pop()
            node_type = node.getType()
            num_children = node.getNChildren()

            if node_type == anim_type:
                nodes.append(node)

            for i in range(num_children):
                top_level_nodes.append(node.getChild(i))

        return nodes

    def get_empty_animation_clips(self):
        """
        Return all empty animation clips.

        This method compatible with only VRED API v1.

        :return: All empty animation clips.
        :rtype: list<vrNodePtr>
        """

        def _get_empty_clips(clip, empty_clips=None):
            """
            Recursive helper function to get all empty clip nodes.

            If the current clip is empty, addi to the list of empty clips.

            :param clip: The current clip to check if empty.
            :type clip: vrNodePtr
            :param empty_clips: The list of empty clips to append to.
            :type empty_emptys: list

            :return: True if the current clip is empty, else False.
            :rtype: bool
            """

            node_type = clip.getType()
            num_children = clip.getNChildren()

            is_empty = True
            if num_children > 0:
                # Recurse on all children to determine if this clip is empty or not.
                for i in range(num_children):
                    child = clip.getChild(i)
                    if child.getType() != self.clip_type():
                        # Child is not a clip - so this current clip is not empty.
                        # Recurse on the child, but do not alter the is_empty state of this clip, since
                        # we already know it is not empty.
                        is_empty = False
                        _get_empty_clips(child, empty_clips)
                    else:
                        # Recurse on the child clip, set the is_empty state of this clip to not empty,
                        # only if the child clip is also not empty.
                        if not _get_empty_clips(child, empty_clips):
                            is_empty = False

            if is_empty:
                if node_type == self.clip_type():
                    # Only add the clip if it is an Animation Clip
                    empty_clips.append(clip)
                return True
            return False

        top_level_clips = self.vrAnimWidgets.getAnimClipNodes()
        empty_clips = []
        for clip in top_level_clips:
            _get_empty_clips(clip, empty_clips)

        return empty_clips

    def get_empty_variant_set_groups(self):
        """
        Find all empty variant set groups.

        NOTE this does not work because the groups returned by getGroupedVariantSets does not
        include groups that are empty.
        """

        vset_groups = self.vrVariantSets.getGroupedVariantSets()

        empty_groups = []
        for vset_group_name, vsets in vset_groups.items():
            if not vsets:
                empty_groups.append(vset_group_name)

        return empty_groups

    # -------------------------------------------------------------------------------------------------------
    # Settings
    # -------------------------------------------------------------------------------------------------------

    def get_unfold_settings(
        self,
        iterations=1,
        prevent_border_intersections=True,
        prevent_triangle_flips=True,
        map_size=1024,
        room_space=0,
    ):
        """
        Return the settings for unfold.

        Holds settings for UV unfold with Unfold3D.

        Default settings are returned for decore unless specific values passed by parameters.

        :param iterations: Set the number of Optimize iterations being applied when unfolding
            UVs with Unfold3D. Default is 1.
                 -1 - Disables Optimize during Unfold.
                  0 - Enables Optimize only in case triangle flips or border intersections
                      happen during the Unfold.
                >=1 - Optimize also runs after the unfold.
        :type iterations: int
        :param map_size: Sets the texture map size (in pixels) for room space used by
            anti-border self intersection. Default is 1024 pixels.
        :type prevent_border_intersections: bool
        :param prevent_triangle_flips: Activate the anti-triangle flip algorithm. Default is
            True.
        :type prevent_triangle_flips: bool
        :type map_size: int
        :param prevent_border_intersections: Activate the anti-border self intersection
            algorithm. The room space parameter is taken into account for this. Default is
            True.
        :param room_space: Sets the room space in pixels, in relation to the map size. The room
            space is the minimum space allowed between borders within one island for the
            anti-border self intersection algorithm. This setting only has an effect if the
            anti-border self intersection is enabled (with prevent_border_intersections). Avoid
            large values, because it can slow down the unfold calculations and create
            distortion. Default is 0.
        :type room_space: int
        """

        settings = self.vrdUVUnfoldSettings()

        settings.setIterations(iterations)
        settings.setPreventBorderIntersections(prevent_border_intersections)
        settings.setPreventTriangleFlips(prevent_triangle_flips)
        settings.setMapSize(map_size)
        settings.setRoomSpace(room_space)

        return settings

    def get_layout_settings(
        self,
        resolution=256,
        iterations=1,
        pre_rotate_mode=None,
        pre_scale_mode=None,
        translate=True,
        rotate=False,
        rotate_step=90.0,
        rotate_min=0.0,
        rotate_max=360.0,
        island_padding=0.0,
        tile_padding=0.0,
        tiles_u=1,
        tiles_v=1,
        tile_assign_mode=None,
        box=QtGui.QVector4D(0.0, 1.0, 0.0, 1.0),
        post_scale_mode=None,
    ):
        """
        Return the settings for layout.

        Holds settings for UV layout (packing of UV islands in the UV space) with Unfold3D.

        Default settings are returned for decore unless specific values passed by parameters.

        :param resolution: Determines the resolution of the packing grid used to place UV
            islands next to each other in the UV space. Higher values are slower, but produce
            better results when there are a lot of smaller islands. Default 256.
        :type resolution: int
        :param iterations: Set the number of trials the packing algorithm will take to achieve
            the desired result. More iterations are slower, but can increase accuracy. Default
            1.
        :type iterations: int
        :param pre_rotate_mode: Sets how the islands are re-oriented in a pre-process phase
            before packing. Default vrUVTypes.PreRotateMode.YAxisToV
        :param pre_rotate_mode: vrUVTypes.PreRotateMode
        :param pre_scale_mode: Sets how the islands are rescaled in a pre-process phase before
            packing. Default vrUVTypes.PreScaleMode.Keep3DArea
        :type pre_scale_mode: vrUVTypes.PreScaleMode
        :param translate: Default True.
        :type translate:
        :param rotate: Set whether UV islands may be rotated during the packing process.
            Default False.
        :type rotate: bool
        :param rotate_step: Set rotation step for the optimization of island orientation. Only
            used if rotation optimization is enabled with
            vrdUVLayoutSettings.setRotate(enable). Rotation optimization begins at the minimum
            value, see vrdUVLayoutSettings.setRotateMin(rMinDeg), then progressively increases
            by the rotation step as necessary, up to the maximum value, see
            vrdUVLayoutSettings.setRotateMax(rMaxDeg). The angle step in degrees. Please note,
            rotate_step = 0.0 disables the rotation optimization. Small values incur slower
            packing speeds. Default 90 degrees.
        :type rotate_step: float
        :param rotate_min: Set the minimum allowable orientation for UV islands during the
            packing process. Only used if rotation is enabled with
            vrdUVLayoutSettings.setRotate(enable).
        :type rotate_min: float
        :param rotate_max: Set the maximum allowable orientation for UV islands during the
            packing process. Only used if rotation is enabled with
            vrdUVLayoutSettings.setRotate(enable).
        :type rotate_max: float
        :param island_padding: Set padding between islands in UV unit. Padding in UV unit.
            Value must be >= 0.0, negative values are clamped to 0.
        :type island_padding: float
        :param tile_padding: Set padding on top/left/right/bottom of the tiles in UV unit.
            Padding in UV unit. Value must be >= 0.0, negative values are clamped to 0.
            Default 0.0
        :type tile_padding: float
        :param tiles_u: Specify tiling to distribute islands to more than one tile. Default 1.
        :type tiles_u: int
        :param tiles_v: Specify tiling to distribute islands to more than one tile. Default 1.
        :type tiles_v: int
        :param tile_assign_mode: Set how islands are distributed to the available tiles. In
            VRED, this is the UV editor Island Distribution field. Default
            vrUVTypes.TileAssignMode.Distribute
        :type tile_assign_mode: vrUVTypes.TileAssignMode
        :param box: Set the UV space box in which the islands will be packed (packing region).
            Box as (U_min, U_max, V_min, V_max). In VRED, this is the UV Editor Packing Region
            U min/max, V min/max field. Default (0.0, 1.0, 0.0, 1.0).
        :type box: QtGui.QVector4D
        :param post_scale_mode: Sets how the packed islands are scaled into the box after
            packing. In VRED, this is the UV editor Scale Mode field. Default
            vrUVTypes.PostScaleMode.Uniform
        :type post_scale_mode: vrUVTypes.PostScaleMode
        """

        pre_rotate_mode = pre_rotate_mode or self.vrUVTypes.PreRotateMode.YAxisToV
        pre_scale_mode = pre_scale_mode or self.vrUVTypes.PreScaleMode.Keep3DArea
        tile_assign_mode = tile_assign_mode or self.vrUVTypes.TileAssignMode.Distribute
        post_scale_mode = post_scale_mode or self.vrUVTypes.PostScaleMode.Uniform

        settings = self.vrdUVLayoutSettings()

        settings.setBox(box)
        settings.setIslandPadding(island_padding)
        settings.setIterations(iterations)
        settings.setPostScaleMode(post_scale_mode)
        settings.setPreRotateMode(pre_rotate_mode)
        settings.setPreScaleMode(pre_scale_mode)
        settings.setResolution(resolution)
        settings.setRotate(rotate)
        settings.setRotateMax(rotate_max)
        settings.setRotateMin(rotate_min)
        settings.setRotateStep(rotate_step)
        settings.setTileAssignMode(tile_assign_mode)
        settings.setTilePadding(tile_padding)
        settings.setTilesU(tiles_u)
        settings.setTilesV(tiles_v)
        settings.setTranslate(translate)

        return settings

    def get_texture_bake_settings(
        self,
        hide_transparent_objects=True,
        external_reference_location=None,
        renderer=None,
        samples=128,
        share_lightmaps_for_clones=True,
        use_denoising=True,
        use_existing_resolution=False,
        min_resolution=64,
        max_resolution=256,
        texel_density=200.00,
        edge_dilation=2,
    ):
        """
        Return the settings for textures in baking.

        Default settings are returned for decore unless specific values passed by parameters.

        :param hide_tarnsparent_objects: Sets if transparent objects should be hidden. This
            option controls if objects with transparent materials will be hidden during the
            lightmap calculation process. When hidden, they do not have any effect on the
            light and shadow calculation. Default True.
        :type hide_tarnsparent_objects: bool
        :param external_reference_location: Sets an external reference location. The external
            reference location is a path to a folder were the lightmap texture will be stored
            after the baking is done. In that case the lightmap texture is externally
            referenced. If no external reference location is set, the lightmap texture will
            exist only within the project file. Default None.
        :type external_reference_location: str
        :param renderer: Sets which raytracing renderer is used to generate the lightmaps.
            Default vrBakeTypes.Renderer.CPURayTracing
        :type renderer: vrBakeTypes.Renderer
        :param samples: Sets the number of samples. The number of samples per pixel defines
            the quality of the lightmap. The higher the number, the better the quality but the
            longer the calculation. Default 128.
        :type samples: int
        :param share_lightmaps_for_clones: Sets if given clones will share the same lightmap or
            if separate lightmaps will be created for each clone. Default True.
        :type share_lightmaps_for_clones: bool
        :param use_denoising: Sets if denoising should be used or not. Denoising is a
            post-process of the final lightmap texture and tries to reduce noise based on AI
            algorithms. Default True.
        :type use_denoising: bool
        :param use_existing_resolution: Sets if an existing lightmap resolution should be kept.
            If the geometry already has a valid lightmap, its resolution is used for the new
            bake process. Default False.
        :type use_existing_resolution: bool
        :param min_resolution: Sets the minimum resolution for the lightmap.
            - Equal values for minimum and maximum resolution will enforce a fixed resolution.
            - Otherwise a resolution between minimum and maximum is automatically calculated.
        :type min_resolution: int
        :param max_resolution: Sets the maximum resolution for the lightmap.
            - Equal values for minimum and maximum resolution will enforce a fixed resolution.
            - Otherwise a resolution between minimum and maximum is automatically calculated.
        :type max_resolution: int
        :param texel_density: Sets the texel density in pixels per meter. The texel density is
            used for the automatic lightmap resolution calculation. The lightmap resolution
            will be calculated using this value and the object’s size as well as the covered UV
            space, clamped by the minimum and maximum resolution. Default 200.00
        :type texel_density: float
        :param edge_dilation: Sets the edge dilation in pixels. Sets the number of pixels the
            valid bake areas will be extended by. This is necessary to prevent the rendering of
            black seams at UV island borders. Default 2.
        :type edge_dilation: int
        """

        renderer = renderer or self.vrBakeTypes.Renderer.CPURayTracing

        settings = self.vrdTextureBakeSettings()

        settings.setEdgeDilation(edge_dilation)
        settings.setHideTransparentObjects(hide_transparent_objects)
        settings.setMaximumResolution(max_resolution)
        settings.setMinimumResolution(min_resolution)
        settings.setRenderer(renderer)
        settings.setSamples(samples)
        settings.setShareLightmapsForClones(share_lightmaps_for_clones)
        settings.setTexelDensity(texel_density)
        settings.setUseDenoising(use_denoising)
        settings.setUseExistingResoluiton(use_existing_resolution)
        if external_reference_location:
            settings.setExternalReferenceLocation(external_reference_location)

        return settings

    def get_illumination_bake_settings(
        self,
        ambient_occlusion_max_dist=3000.00,
        ambient_occlusion_min_dist=1.00,
        ambient_occlusion_weight=None,
        color_bleeding=False,
        direct_illumination_mode=None,
        indirect_illumination=True,
        indirections=1,
        lights_layer=-1,
        material_override=True,
        material_override_color=QtCore.Qt.white,
    ):
        """
        Return the settings for illumination in baking.

        Settings for texture baking with vrBakeService.bakeToTexture.

        Default settings are returned for decore unless specific values passed by parameters.

        :param ambient_occlusion_max_dist: Sets the ambient occlusion maximum distance. Sets
            the maximum distance of objects to be taken into account for the ambient occlusion
            calculation. Distance in mm. Default 3000.00
        :type ambient_occlusion_max_dist: float
        :param ambient_occlusion_min_dist: Sets the ambient occlusion minimum distance. Sets
            the minimum distance of objects to be taken into account for the ambient occlusion
            calculation. Distance in mm. Default 1.00
        :type ambient_occlusion_min_dist: float
        :param ambient_occlusion_weight: Sets the ambient occlusion weight mode. Sets how the
            ambient occlusion samples in the hemisphere above the calculation point are
            weighted. Default vrBakeTypes.AmbientOcclusionWeight.Unifrom
        :type ambient_occlusion_weight: vrBakeTypes.AmbientOcclusionWeight
        :param color_bleeding: Sets if color bleeding should be used. This affects the indirect
            illumination. If disabled the indirect illumination result is grayscale. Default
            False.
        :type color_bleeding: bool
        :param direct_illumination_mode: Sets the direct illumination mode. This mode defines
            the kind of data which will be baked. Default
            vrBakeTypes.DirectIlluminationMode.AmbientOcclusion
        :type direct_illumination_mode: vrBakeTypes.DirectIlluminationMode
        :param indirect_illumination: Sets if indirect illumination should be evaluated.
            Default True.
        :type indirect_illumination: bool
        :param indirections: Sets the number of indirections. Defines the number of calculated
            light bounces. Default 1.
        :type indirections: int
        :param lights_layer: Only available for texture baking. Sets if only lights from a
            specific layer should be baked. See vrdBaseLightNode.setBakeLayer(layer). For the
            bake layer of incandescence in emissive materials use API v1 vrFieldAccess. -1
            (default) means light layer setting is ignored, i.e. all lights are baked
            regardless of their layer setting. Value >= 0 means only lights with matching layer
            number are evaluated.
        :type lights_layer: int
        :param material_override: Sets if a global material override should be used. If
            enabled, all geometries will have a global diffuse material override during the
            bake calculation. Default True.
        :type material_override: bool
        :param material_override_color: Sets the color of the override material. Default white.
        :type material_override_color: QtGui.QColor

        :return: The settings for illumination in baking.
        :rtype: vrdIlluminationBakeSettings
        """

        direct_illumination_mode = (
            direct_illumination_mode
            or self.vrBakeTypes.DirectIlluminationMode.AmbientOcclusion
        )
        ambient_occlusion_weight = (
            ambient_occlusion_weight or self.vrBakeTypes.AmbientOcclusionWeight.Uniform
        )

        settings = self.vrdIlluminationBakeSettings()

        settings.setAmbientOcclusionMaximumDistance(ambient_occlusion_max_dist)
        settings.setAmbientOcclusionMinimumDistance(ambient_occlusion_min_dist)
        settings.setAmbientOcclusionWeight(ambient_occlusion_weight)
        settings.setColorBleeding(color_bleeding)
        settings.setDirectIlluminationMode(direct_illumination_mode)
        settings.setIndirectIllumination(indirect_illumination)
        settings.setIndirections(indirections)
        settings.setLightsLayer(lights_layer)
        settings.setMaterialOverride(material_override)
        settings.setMaterialOverideColor(material_override_color)

        return settings

    def get_decore_settings(
        self,
        resolution=1024,
        quality_steps=8,
        correct_face_normals=False,
        decore_enabled=False,
        decore_mode=None,
        sub_object_mode=None,
        transparent_object_mode=None,
    ):
        """
        Return settings for object decoring/optimization.

        Decoring removes redundant geometry that is inside other geometry, like screws and
        mountings inside a door covering. A virtual camera flies around the selected object,
        takes screen shots, and removes any non-visible geometry.

        Default settings are returned for decore unless specific values passed by parameters.

        :param resolution: Defines the resolution of the images taken. A higher resolution
            gives more precise results. Default 1024.
        :type resolution: int
        :param quality_steps: Defines the number of images taken during the analysis. A higher
            value gives more accurate results. Default 8.
        :type quality_steps: int
        :param correct_face_normals: If enabled, flips polygon normals pointing away from the
            camera, if they are encountered during the analysis. Default False.
        :type correct_face_normals: bool
        :param decore_enabled: Defines if decoring is enabled. Default False.
        :type decore_enabled: bool
        :param decore_mode: Defines the action to be taken, when geometry is determined to be
            inside another and non-visible. Default vrGeometryTypes.DecoreMode.Remove.
        :type decore_mode: vrGeometryTypes.DecoreMode
        :param sub_object_mode: Defines how sub objects are taken into account. Default
            vrGeometryTypes.DecoreSubObjectMode.Triangles.
        :type sub_object_mode: vrGeometryTypes.DecoreSubObjectMode
        :param transparent_object_mode: Defines how transparent objects should be handled.
            Default vrGeometryTypes.DecoreTransparentObjectMode.Ignore.
        :type transparent_object_mode: vrGeometryTypes.DecoreTransparentObjectMode

        :return: The decore settings.
        :rtype: vrdDecoreSettings
        """

        decore_mode = decore_mode or self.vrGeometryTypes.DecoreMode.Remove
        sub_object_mode = (
            sub_object_mode or self.vrGeometryTypes.DecoreSubObjectMode.Triangles
        )
        transparent_object_mode = (
            transparent_object_mode
            or self.vrGeometryTypes.DecoreTransparentObjectMode.Ignore
        )

        settings = self.vrdDecoreSettings()

        settings.setResolution(resolution)
        settings.setQualitySteps(quality_steps)
        settings.setCorrectFaceNormals(correct_face_normals)
        settings.setDecoreEnabled(decore_enabled)
        settings.setDecoreMode(decore_mode)
        settings.setSubObjectMode(sub_object_mode)
        settings.setTransparentObjectMode(transparent_object_mode)

        return settings
