# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

# try:
#     import builtins
# except ImportError:
#     try:
#         import __builtins__ as builtins
#     except ImportError:
#         import __builtin__ as builtins

# # VRED API v2 imports
# builtins.vrFileIOService = vrFileIOService
# builtins.vrNodeService = vrNodeService
# builtins.vrReferenceService = vrReferenceService
# builtins.vrImageService = vrImageService
# builtins.vrSceneplateService = vrSceneplateService

# try:
#     builtins.vrDecoreService = vrDecoreService
# except NameError:
#     builtins.vrDecoreService = None

# try:
#     builtins.vrMaterialService = vrMaterialService
# except NameError:
#     builtins.vrMaterialService = None

# try:
#     builtins.vrBakeService = vrBakeService
# except NameError:
#     builtins.vrBakeService = None

# try:
#     builtins.vrGUIService = vrGUIService
# except NameError:
#     builtins.vrGUIService = None

# try:
#     builtins.vrUVService = vrUVService
# except NameError:
#     builtins.vrUVService = None

# from vrKernelServices import (
#     vrSceneplateTypes,
#     vrdSceneplateNode,
#     vrGeometryTypes,
#     vrdGeometryNode,
#     vrdTransformNode,
#     vrdSurfaceNode,
#     vrdNode,
#     vrdObject,
#     vrUVTypes,
#     vrdReferenceNode,
#     vrdUVUnfoldSettings,
#     vrdUVLayoutSettings,
# )

# try:
#     from vrKernelServices import (
#         vrdTextureBakeSettings,
#         vrdIlluminationBakeSettings,
#         vrBakeTypes,
#         vrdDecoreSettings,
#         vrdMaterial,
#         vrdMaterialNode,
#     )
# except ImportError:
#     vrdTextureBakeSettings = None
#     vrdIlluminationBakeSettings = None
#     vrBakeTypes = None
#     vrdDecoreSettings = None
#     vrdMaterial = None
#     vrdMaterialNode = None

# VRED API v1 imports
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
