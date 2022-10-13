# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

from sgtk.platform.qt import QtCore, QtGui

try:
    import builtins
except ImportError:
    try:
        import __builtins__ as builtins
    except ImportError:
        import __builtin__ as builtins

# VRED API v2 imports

builtins.vrFileIOService = vrFileIOService # 2021.0.0
builtins.vrImageService = vrImageService # 2021.0.0
builtins.vrNodeService = vrNodeService # 2021.0.0
builtins.vrReferenceService = vrReferenceService # 2021.0.0
builtins.vrSceneplateService = vrSceneplateService # 2021.0.0

builtins.vrUVService = vrUVService # 2021.2.0

builtins.vrBakeService = vrBakeService # 2022.0.0

builtins.vrGUIService = vrGUIService # 2022.2.0

builtins.vrDecoreService = vrDecoreService # 2023.0.0
builtins.vrMaterialService = vrMaterialService # 2023.0.0

from vrKernelServices import (
    vrSceneplateTypes, # 2021.0.0
    vrdNode,  # 2021.0.0
    vrdObject,  # 2021.0.0
    vrdTransformNode,  # 2021.0.0
    vrdReferenceNode, # 2021.0.0
    vrdSceneplateNode, # 2021.0.0

    vrGeometryTypes,  # 2021.2.0
    vrUVTypes, # 2021.2.0
    vrdGeometryNode, # 2021.2.0
    vrdSurfaceNode,  # 2021.2.0
    vrdUVLayoutSettings,  # 2021.2.0
    vrdUVUnfoldSettings,  # 2021.2.0

    vrBakeTypes,  # 2022.0.0
    vrdIlluminationBakeSettings,  # 2022.0.0
    vrdTextureBakeSettings,  # 2022.0.0

    vrdDecoreSettings, # 2023.0.0
    vrdMaterial, # 2023.0.0
    vrdMaterialNode, # 2023.0.0
)

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


# Supported VRED API versions
VRED_API_V1 = "v1"
VRED_API_V2 = "v2"
SUPPORTED_VRED_API_VERSIONS = (VRED_API_V1, VRED_API_V2)

# VRED Types
VRED_TYPE_CLIP = "AnimClip"
VRED_TYPE_ANIM = "AnimWizClip"


class VREDPy:
    """A helper class for interacting with the VRED API."""

    class VREDPyError(Exception):
        """Custom exception class for VRED API errors."""

    #########################################################################################################
    # Properties
    #########################################################################################################

    # -----------------------------------------------------------------------------------------
    # VRED API Modules
    # -----------------------------------------------------------------------------------------
    # Set up properties for each VRED API module so that importing the modules can be done once
    # here in this module, and all other modules can access the modules through the VREDPy
    # properties.

    @property
    def vrUVService(self):
        """Return the VRED v2 API module vrUVService."""
        return vrUVService

    @property
    def vrSceneplateService(self):
        """Return the VRED v2 API module vrSceneplateService."""
        return vrSceneplateService

    @property
    def vrImageService(self):
        """Return the VRED v2 API module vrImageService."""
        return vrImageService

    @property
    def vrGUIService(self):
        """Return the VRED v2 API module vrGUIService."""
        return vrGUIService

    @property
    def vrFileIOService(self):
        """Return the VRED v2 API module vrFileIOService."""
        return vrFileIOService

    @property
    def vrNodeService(self):
        """Return the VRED v2 API module vrNodeService."""
        return vrNodeService

    @property
    def vrMaterialService(self):
        """Return the VRED v2 API module vrMaterialService."""
        return vrMaterialService

    @property
    def vrReferenceService(self):
        """Return the VRED v2 API module vrReferenceService."""
        return vrReferenceService

    @property
    def vrBakeService(self):
        """Return the VRED v2 API module vrBakeService."""
        return vrBakeService

    @property
    def vrDecoreService(self):
        """Return the VRED v2 API module vrDecoreService."""
        return vrDecoreService

    @property
    def vrdDecoreSettings(self):
        """Return the VRED v2 API module vrdDecoreSettings."""
        return vrdDecoreSettings

    @property
    def vrGeometryTypes(self):
        """Return the VRED v2 API module vrGeometryTypes."""
        return vrGeometryTypes

    @property
    def vrdGeometryNode(self):
        """Return the VRED v2 API module vrdGeometryNode."""
        return vrdGeometryNode

    @property
    def vrdNode(self):
        """Return the VRED v2 API module vrdNode."""
        return vrdNode

    @property
    def vrdSceneplateNode(self):
        """Return the VRED v2 API module vrdSceneplateNode."""
        return vrdSceneplateNode

    @property
    def vrdMaterialNode(self):
        """Return the VRED v2 API module vrdMaterialNode."""
        return vrdMaterialNode

    @property
    def vrdSurfaceNode(self):
        """Return the VRED v2 API module vrdSurfaceNode."""
        return vrdSurfaceNode

    @property
    def vrdReferenceNode(self):
        """Return the VRED v2 API module vrdReferenceNode."""
        return vrdObject

    @property
    def vrdObject(self):
        """Return the VRED v2 API module vrdObject."""
        return vrdObject

    @property
    def vrdMaterial(self):
        """Return the VRED v2 API module vrdObject."""
        return vrdObject

    @property
    def vrSceneplateTypes(self):
        """Return the VRED v2 API module vrSceneplateTypes."""
        return vrSceneplateTypes

    @property
    def vrUVTypes(self):
        """Return the VRED v2 API module vrUVTypes."""
        return vrUVTypes

    @property
    def vrBakeTypes(self):
        """Return the VRED v2 API module vrBakeTypes."""
        return vrBakeTypes

    @property
    def vrdUVUnfoldSettings(self):
        """Return the VRED v2 API module vrdUVUnfoldSettings."""
        return vrdUVUnfoldSettings

    @property
    def vrdUVLayoutSettings(self):
        """Return the VRED v2 API module vrdUVLayoutSettings."""
        return vrdUVLayoutSettings

    @property
    def vrdIlluminationBakeSettings(self):
        """Return the VRED v2 API module vrdIlluminationBakeSettings."""
        return vrdIlluminationBakeSettings

    @property
    def vrdTextureBakeSettings(self):
        """Return the VRED v2 API module vrdTextureBakeSettings."""
        return vrdTextureBakeSettings

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

    # -------------------------------------------------------------------------------------------------------
    # Objects
    # -------------------------------------------------------------------------------------------------------

    @staticmethod
    def get_id(obj):
        """
        Return the ID for the given object.

        :param obj: The object to get the ID for.
        :typeo obj: VRED object

        :return: The object ID.
        :rtype: int
        """

        if isinstance(obj, vrdNode):
            return obj.getObjectId()

        if isinstance(obj, vrNodePtr.vrNodePtr):
            return obj.getID()

        # Default to returning the object itself as the id if could not determine the id based
        # on object type.
        return obj

    @staticmethod
    def get_type_as_str(obj):
        """
        Determine the object type and return the string representation.

        TODO: extend method to support all VRED object types.

        :param obj: The object to get the type as string for.
        :type obj: VRED object
        """

        if hasattr(obj, "getType"):
            return obj.getType()

        if isinstance(obj, vrdObject):
            if obj.isType(vrdMaterial):
                return "Material"

            if obj.isType(vrdMaterialNode):
                return "Material Node"

            if obj.isType(vrdReferenceNode):
                return "Reference Node"

            if obj.isType(vrdSurfaceNode):
                return "Surface Node"

            if obj.isType(vrdTransformNode):
                return "Transform Node"

            if obj.isType(vrdGeometryNode):
                return "Geometry Node"

        raise TypeError("VRED object type {} not supported".format(type(obj)))

    # -------------------------------------------------------------------------------------------------------
    # Nodes
    # -------------------------------------------------------------------------------------------------------

    @staticmethod
    def is_geometry_node(node):
        """
        Return True if the node is a geometry node.

        Do not include surface nodes.

        This method compatible with only VRED API v2.

        :param node: The node to check.
        :type node: vrNodePtr | vrdNode

        :return: True if the node is a geometry node, else False.
        :rtype: bool
        """

        if isinstance(node, vrdSurfaceNode):
            # Do not include surface nodes
            return False

        return isinstance(node, vrdGeometryNode)

    @staticmethod
    def get_nodes(items, api_version=VRED_API_V1):
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
            if isinstance(item, vrNodePtr.vrNodePtr):
                if api_version == VREDPy.v1():
                    node = item
                else:
                    node = vrNodeService.getNodeFromId(item.getID())
            elif isinstance(item, vrdNode):
                if api_version == VREDPy.v1():
                    node = vrNodePtr.toNode(item.getObjcetId())
                else:
                    node = item
            elif isinstance(item, int):
                if api_version == VREDPy.v1():
                    node = vrNodePtr.toNode(item)
                else:
                    node = vrNodeService.getNodeFromId(item)
            else:
                try:
                    if api_version == VREDPy.v1():
                        node = vrScenegraph.findNode(item)
                    else:
                        node = vrNodeService.findNode(item)
                except Exception:
                    pass

            if node:
                nodes.append(node)
            else:
                raise VREDPy.VREDPyError("Failed to convert {} to node".format(item))

        return nodes

    @staticmethod
    def get_geometry_nodes(root_node=None, has_mat_uvs=None, has_light_uvs=None):
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
                        node.hasUVSet(vrUVTypes.MaterialUVSet) == has_mat_uvs
                        and node.hasUVSet(vrUVTypes.LightmapUVSet) == has_light_uvs
                    ):
                        result.append(node)
                elif has_mat_uvs is None:
                    # Add only geometry based on light UVs, ignore material UVs
                    if node.hasUVSet(vrUVTypes.LightmapUVSet) == has_light_uvs:
                        result.append(node)
                elif has_light_uvs is None:
                    # Add only geometry based on material UVs, ignore light UVs
                    if node.hasUVSet(vrUVTypes.MaterialUVSet) == has_mat_uvs:
                        result.append(node)

            for child in node.getChildren():
                _get_geometry_nodes(
                    child, result, has_mat_uvs=has_mat_uvs, has_light_uvs=has_light_uvs
                )

        root_node = root_node or vrNodeService.getRootNode()
        nodes = []
        _get_geometry_nodes(
            root_node, nodes, has_mat_uvs=has_mat_uvs, has_light_uvs=has_light_uvs
        )
        return nodes

    @staticmethod
    def get_hidden_nodes(root_node=None, api_version=VRED_API_V1):
        """
        Return a list of the hidden nodes in the scene graph.

        If a node is hidden, all of its children are hidden but the node's children will
        not be included in the list of hidden nodes returned.

        :param root_node: The node to check subtree only for hidden nodes. If None, then
            the scene graph root node will be used to check all nodes.
        :param root_node: vrNodePtr | vrdNode
        :param api_version: The VRED API version used to retrieve and return hidden node.
        :type api_version: str
        """

        VREDPy.check_api_version(api_version)

        if root_node is None:
            if api_version == VREDPy.v1():
                nodes = [vrScenegraph.getRootNode()]
            else:
                # v2
                nodes = [vrNodeService.getRootNode()]
        else:
            nodes = [root_node]

        hidden = []
        while nodes:
            node = nodes.pop()

            if isinstance(node, vrNodePtr.vrNodePtr):
                if not node.getActive():
                    hidden.append(node)
                else:
                    # Only check children if the parent is not hidden
                    for i in range(node.getNChildren()):
                        nodes.append(node.getChild(i))
            else:
                # v2
                if not node.isVisible():
                    hidden.append(node)
                else:
                    # Only check children if the parent is not hidden
                    for child in node.getChildren():
                        nodes.append(child)

        return hidden

    @staticmethod
    def delete_nodes(nodes, force=False):
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
        if isinstance(nodes[0], vrNodePtr.vrNodePtr):
            vrScenegraph.deleteNodes(nodes, force)

        elif isinstance(nodes[0], vrdNode):
            vrNodeService.removeNodes(nodes)

        else:
            raise VREDPy.VREDPyError("Not a node {}".format(nodes[0]))

    @staticmethod
    def set_to_b_side(nodes, b_side=True):
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
            if isinstance(node, vrNodePtr.vrNodePtr):
                vrNodeUtils.setToBSide(node, b_side)
            elif isinstance(node, vrdGeometryNode):
                node.setToBSide(b_side)
            else:
                raise VREDPy.VREDPyError("Not a geometry node {}".format(node))

    @staticmethod
    def show_nodes(nodes):
        """
        Show the nodes.

        :param nodes: The nodes to show. The elements in the list must be uniform.
        :type nodes: list<vrNodePtr> | list<vrdNode>
        """

        if not nodes:
            return

        # Check the first node to detect which api version to use to delete.
        # Assumes the list has uniform elements
        if isinstance(nodes[0], vrNodePtr.vrNodePtr):
            vrScenegraph.showNodes(nodes)

        elif isinstance(nodes[0], vrdNode):
            for node in nodes:
                node.setVisibilityFlag(True)

        else:
            raise VREDPy.VREDPyError("Not a node {}".format(nodes[0]))

    @staticmethod
    def group_nodes(nodes):
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
        vrScenegraph.selectNodes(nodes, select)
        vrScenegraph.groupSelection()
        vrScenegraph.deselectAll()

    # -------------------------------------------------------------------------------------------------------
    # Materials
    # -------------------------------------------------------------------------------------------------------

    @staticmethod
    def get_materials(items):
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
            if isinstance(item, vrdMaterial):
                mat = item
            elif isinstance(item, int):
                mat = vrMaterialService.getMaterialFromId(item)
            else:
                try:
                    mat = vrMaterialService.findMaterial(item)
                except Exception:
                    pass

            if mat:
                materials.append(mat)
            else:
                raise VREDPy.VREDPyError(
                    "Failed to convert object {} to material".format(item)
                )

        return materials

    @staticmethod
    def find_materials(using_orange_peel=None, using_texture=None):
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

        mats = vrMaterialService.getAllMaterials()

        if using_orange_peel is None and using_texture is None:
            return mats

        result = []
        for mat in mats:
            if using_orange_peel is not None:
                try:
                    clearcoat = mat.getClearcoat()
                except AttributeError:
                    # This material does not support clearcoats
                    clearcoat = None

                if not clearcoat or using_orange_peel != clearcoat.getUseOrangePeel():
                    continue

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
    # Animatino
    # -------------------------------------------------------------------------------------------------------

    @staticmethod
    def is_animation_clip(clip_node):
        """
        Return True if the clip is an Animation Clip.

        This method compatible with only VRED API v1.

        :param clip_node: The clip to check.
        :type clip_node: vrNodePtr
        """

        return clip_node.getType() == VREDPy.clip_type()

    @staticmethod
    def get_animation_clips(top_level_only=True, anim_type=VRED_TYPE_CLIP):
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

        top_level_nodes = vrAnimWidgets.getAnimClipNodes()

        if top_level_only and anim_type == VREDPy.clip_type():
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

    @staticmethod
    def get_empty_animation_clips():
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
                    if child.getType() != VREDPy.clip_type():
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
                if node_type == VREDPy.clip_type():
                    # Only add the clip if it is an Animation Clip
                    empty_clips.append(clip)
                return True
            return False

        top_level_clips = vrAnimWidgets.getAnimClipNodes()
        empty_clips = []
        for clip in top_level_clips:
            _get_empty_clips(clip, empty_clips)

        return empty_clips

    @staticmethod
    def get_empty_variant_set_groups():
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

    @staticmethod
    def get_unfold_settings(
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

        settings = vrdUVUnfoldSettings()

        settings.setIterations(iterations)
        settings.setPreventBorderIntersections(prevent_border_intersections)
        settings.setPreventTriangleFlips(prevent_triangle_flips)
        settings.setMapSize(map_size)
        settings.setRoomSpace(room_space)

        return settings

    @staticmethod
    def get_layout_settings(
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

        pre_rotate_mode = pre_rotate_mode or vrUVTypes.PreRotateMode.YAxisToV
        pre_scale_mode = pre_scale_mode or vrUVTypes.PreScaleMode.Keep3DArea
        tile_assign_mode = tile_assign_mode or vrUVTypes.TileAssignMode.Distribute
        post_scale_mode = post_scale_mode or vrUVTypes.PostScaleMode.Uniform

        settings = vrdUVLayoutSettings()

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

    @staticmethod
    def get_texture_bake_settings(
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

        renderer = renderer or vrBakeTypes.Renderer.CPURayTracing

        settings = vrdTextureBakeSettings()

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

    @staticmethod
    def get_illumination_bake_settings(
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
            or vrBakeTypes.DirectIlluminationMode.AmbientOcclusion
        )
        ambient_occlusion_weight = (
            ambient_occlusion_weight or vrBakeTypes.AmbientOcclusionWeight.Uniform
        )

        settings = vrdIlluminationBakeSettings()

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

    @staticmethod
    def get_decore_settings(
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

        decore_mode = decore_mode or vrGeometryTypes.DecoreMode.Remove
        sub_object_mode = (
            sub_object_mode or vrGeometryTypes.DecoreSubObjectMode.Triangles
        )
        transparent_object_mode = (
            transparent_object_mode
            or vrGeometryTypes.DecoreTransparentObjectMode.Ignore
        )

        settings = vrdDecoreSettings()

        settings.setResolution(resolution)
        settings.setQualitySteps(quality_steps)
        settings.setCorrectFaceNormals(correct_face_normals)
        settings.setDecoreEnabled(decore_enabled)
        settings.setDecoreMode(decore_mode)
        settings.setSubObjectMode(sub_object_mode)
        settings.setTransparentObjectMode(transparent_object_mode)

        return settings
