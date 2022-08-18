# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

from distutils.log import error
from tkinter import W
import sgtk


try:
    import builtins
except ImportError:
    try:
        import __builtins__ as builtins
    except ImportError:
        import __builtin__ as builtins

# VRED API v2 imports
builtins.vrDecoreService = vrDecoreService
builtins.vrNodeService = vrNodeService
builtins.vrMaterialService = vrMaterialService
builtins.vrBakeService = vrBakeService
builtins.vrReferenceService = vrReferenceService
from vrKernelServices import vrdDecoreSettings, vrGeometryTypes, vrdMaterial, vrdNode

# VRED API v1 imports
import vrOptimize
import vrScenegraph
import vrGeometryEditor
import vrNodePtr
import vrNodeUtils

HookBaseClass = sgtk.get_hook_baseclass()


class SceneDataValidationHook(HookBaseClass):
    """
    Hook to define Alias scene validation functionality.
    """

    def get_validation_data(self):
        """
        Return the validation rule data set to validate an Alias scene.

        This method will retrieve the default validation rules returned by
        :meth:`AliasSceneDataValidator.get_validation_data`. To customize the default
        validation rules, override this hook method to modify the returned data dictionary.

        The dictionary returned by this function should be formated such that it can be passed
        to the :class:`~tk-multi-data-validation:data.ValidationRule` class constructor to
        create a new validation rule object.

        :return: The validation rules data set.
        :rtype: dict
        """

        return {
            "optimize_geometries": {
                "name": "Optimize Geometries",
                "description": "Optimizes the geometry structure.",
                "fix_func": optimize_geometries,
            },
            "optimize_share_geometries": {
                "name": "Optimize/Share Geometries",
                "description": "Optimizes the geometry structure and tries to share duplicated geometries.",
                "fix_func": share_geometries,
            },
            "optimize_merge_geometries": {
                "name": "Merge/Optimmize/Share Geometries",
                "description": "This is much more aggressive and changes the scenegraph structure.",
                "fix_func": merge_geometries,
            },
            "geometry_tessellate": {
                "name": "Tessellate",
                "description": "Retessellates the given surfaces.",
                "fix_func": tessellate,
            },
            "geometry_decore": {
                "name": "Decore & Correct Wrong Normal",
                "description": "Remove redundant geometry that is inside other geometry. This feature only works with OpenGL",
                "check_func": check_decore,
                "fix_func": decore,
            },
            "material_remove_duplicates": {
                "name": "Merge Duplicate Materials",
                "description": "Share materials with the same properties.",
                "fix_func": merge_duplicate_materials,
            },
            "material_unused": {
                "name": "Remove Unused Materials",
                "description": "Remove Unused Materials",
                "error_msg": "Found unused materials",
                "check_func": find_unused_materials,
                "fix_func": remove_unused_materials,
                "actions": [
                    {
                        "name": "Select All",
                        "callback": select_materials,
                    }
                ],
                "item_actions": [
                    {
                        "name": "Select",
                        "callback": select_materials,
                    }
                ],
            },
            "bake_repath_lightmaps": {
                "name": "Repath Lightmaps",
                "description": "Re-path existing lightmaps from a list of geometry nodes.",
                "fix_func": repath_lightmaps,
            },
            "scene_graph_hidden_nodes": {
                "name": "Delete Hidden Nodes",
                "description": "Find hidden nodes in the Scene Graph and delete them.",
                "error_msg": "Found hidden nodes in the Scene Graph.",
                "check_func": find_hidden_nodes,
                "fix_func": delete_hidden_nodes,
                "fix_name": "Delete All",
                "actions": [
                    {
                        "name": "Show All",
                        "callback": show_hidden_nodes,
                    },
                    {
                        "name": "Set All To B Side",
                        "callback": set_hidden_nodes_to_b_side,
                    },
                    {
                        "name": "Select All",
                        "callback": select_nodes,
                    },
                ],
                "item_actions": [
                    {
                        "name": "Select",
                        "callback": select_nodes,
                    },
                    {
                        "name": "Show",
                        "callback": show_hidden_nodes,
                    },
                    {
                        "name": "Set To B Side",
                        "callback": set_hidden_nodes_to_b_side,
                    },
                    {
                        "name": "Delete",
                        "callback": delete_hidden_nodes,
                    },
                ],
            },
            "scene_graph_ref_remove": {
                "name": "Delete References",
                "description": "Find reference nodes in the Scene Graph and delete the reference nodes.",
                "error_msg": "Found reference nodes in the Scene Graph.",
                "check_func": find_references,
                "fix_func": delete_references,
                "fix_name": "Delete All",
                "actions": [
                    {
                        "name": "Select All",
                        "callback": select_nodes,
                    },
                ],
                "item_actions": [
                    {
                        "name": "Select",
                        "callback": select_nodes,
                    },
                    {
                        "name": "Delete",
                        "callback": delete_references,
                    },
                ],
            },
        }


# -------------------------------------------------------------------------------------------------------
# Helper classes & functions
# -------------------------------------------------------------------------------------------------------


class VREDDataValidationError(Exception):
    """Custom exception class for VRED Data Validation errors."""


def get_nodes(items):
    """Return a list of node objects."""

    nodes = []

    if not items:
        return nodes

    if not isinstance(items, (list, tuple)):
        items = [items]

    for item in items:
        node = None
        if isinstance(item, vrNodePtr.vrNodePtr):
            node = item
        elif isinstance(item, int):
            node = vrNodePtr.toNode(item)
        else:
            try:
                node = vrScenegraph.findNode(item)
            except Exception:
                pass

        if node:
            nodes.append(node)
        else:
            self.logger.error("Failed to get node object from {}".format(node))

    return nodes


def get_hidden_nodes():
    """Return a list of the hidden nodes in the scene graph."""

    # def getHidden(node, hidden):
    #     if not node.getActive():
    #         hidden.append(node)

    #     for i in range(0, node.getNChildren()):
    #         getHidden(node.getChild(i), hidden)

    hidden = []
    # nodes = vrScenegraph.getAllNodes()
    nodes = [vrScenegraph.getRootNode()]

    while nodes:
        node = nodes.pop()
        if not node.getActive():
            hidden.append(node)

        for i in range(node.getNChildren()):
            nodes.append(node.getChild(i))

    return hidden


# -------------------------------------------------------------------------------------------------------
# Validation helper functions
# -------------------------------------------------------------------------------------------------------


def get_check_result(error_items):
    """Return the result in a format consumable by the ValidationRule class."""

    return {"is_valid": not error_items, "errors": sanitize_vrd_objects(error_items)}


def sanitize_vrd_objects(objects):
    """
    Sanitize the VRED objects (objects of type vrdObject) before returning from a validation check function.

    :return: The list of sanitized vrdObjects.
    :rtype: list<dict>
    """

    object_results = []

    for obj in objects:
        if isinstance(obj, vrdNode) or hasattr(obj, "getObjectId"):
            # v2 API vrdObject
            object_id = obj.getObjectId()
        elif isinstance(obj, vrNodePtr.vrNodePtr) or hasattr(obj, "getID"):
            # v1 API vrNodePtr
            # Use the name as the ID since the name is used to find objects
            # object_id = obj.getName()
            object_id = obj.getID()
        else:
            raise VREDDataValidationError("Failed to get object ID from {}", obj)

        if hasattr(obj, "getName"):
            object_name = obj.getName()
        else:
            # Fallback to use the id as the name
            object_name = object_id

        object_results.append(
            {
                "id": object_id,
                "name": object_name,
                "type": get_vrd_object_type(obj),
            }
        )

    return object_results


def get_vrd_object_type(obj):
    """ """

    if hasattr(obj, "getType"):
        return obj.getType()

    if obj.isType(vrdMaterial):
        return "Material"

    if obj.isType(vrdReferenceNode):
        return "Reference"

    print("Unknown vrd type", obj)
    return "Unknown"


# -------------------------------------------------------------------------------------------------------
# Action functions
# -------------------------------------------------------------------------------------------------------


def select_nodes(errors=None):
    """Select the given nodes in the scene graph."""

    nodes = get_nodes(errors)
    if not nodes:
        return

    select = True
    vrScenegraph.selectNodes(nodes, select)


def select_materials(errors=None):
    """Select the given materials."""

    if not errors:
        return

    if not isinstance(errors, (list, tuple)):
        errors = [errors]

    materials = []
    for item in errors:
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
            self.logger.error("Failed to get vrdMaterial object from {}", item)

    vrMaterialService.setMaterialSelection(materials)


# -------------------------------------------------------------------------------------------------------
# Check & Fix functions
# -------------------------------------------------------------------------------------------------------


def optimize_geometries():
    """ """

    root_node = vrScenegraph.getRootNode()
    vrOptimize.optimizeGeometries(root_node)


def share_geometries():
    """ """

    root_node = vrScenegraph.getRootNode()
    vrOptimize.shareGeometries(root_node)


def merge_geometries():
    """ """

    root_node = vrScenegraph.getRootNode()
    vrOptimize.mergeGeometries(root_node)


def tessellate():
    """ """

    root_node = vrScenegraph.getRootNode()
    vrGeometryEditor.tessellateSurfaces(root_node)


def check_decore():
    nodes_to_decore = vrNodeService.findNodes("GeometryToDecore")
    return get_check_result(nodes_to_decore)


def decore():
    """ """

    settings = vrdDecoreSettings()
    settings.setResolution(1024)
    settings.setQualitySteps(8)
    settings.setCorrectFaceNormals(True)
    settings.setDecoreEnabled(True)
    settings.setDecoreMode(vrGeometryTypes.DecoreMode.Remove)
    settings.setSubObjectMode(vrGeometryTypes.DecoreSubObjectMode.Triangles)
    settings.setTransparentObjectMode(
        vrGeometryTypes.DecoreTransparentObjectMode.Ignore
    )
    treat_as_combine_object = True
    nodes_to_decore = vrNodeService.findNodes("GeometryToDecore")
    vrDecoreService.decore(nodes_to_decore, treat_as_combine_object, settings)


def merge_duplicate_materials():
    """ """

    vrMaterialService.mergeDuplicateMaterials()


def find_unused_materials():
    """Find any unused materials."""

    unused_mats = vrMaterialService.findUnusedMaterials()
    return get_check_result(unused_mats)


def remove_unused_materials():
    """Remove all unused materials."""
    vrMaterialService.removeUnusedMaterials()


def repath_lightmaps():
    """ """

    # FIXME pass correct lsit of geometry ndoes
    root_node = vrScenegraph.getRootNode()
    nodes_to_repath = [root_node]
    vrBakeService.repathLightmaps(nodes_to_repath)


def find_hidden_nodes():
    """Find hidden nodes in the scene graph."""

    hidden_nodes = get_hidden_nodes()
    return get_check_result(hidden_nodes)


def show_hidden_nodes(errors=None):
    """Find hidden nodes in the scene graph and show them (unhide)."""

    if errors is None:
        hidden_nodes = get_hidden_nodes()
    else:
        hidden_nodes = get_nodes(errors)

    vrScenegraph.showNodes(hidden_nodes)


def delete_hidden_nodes(errors=None):
    """Find hidden nodes in the scene graph and delete them."""

    if errors is None:
        hidden_nodes = get_hidden_nodes()
    else:
        hidden_nodes = get_nodes(errors)

    force = False
    vrScenegraph.deleteNodes(hidden_nodes, force)


def set_hidden_nodes_to_b_side(errors=None):
    """Find all hidden nodes and set them to the B Side."""

    if errors is None:
        hidden_nodes = get_hidden_nodes()
    else:
        hidden_nodes = get_nodes(errors)

    for node in hidden_nodes:
        if isinstance(node, vrNodePtr.vrNodePtr):
            vrNodeUtils.setToBSide(node, True)
        elif isinstance(node, vrdGeometryNode):
            node.setToBSide(True)
        else:
            raise VREDDataValidationError("Unsupported node type {}".format(node))


def find_references():
    """Find references in the scene graph."""

    ref_nodes = vrReferenceService.getSceneReferences()
    return get_check_result(ref_nodes)


def delete_references(errors=None):
    """Find references in the scene graph and delete them."""

    if not errors:
        ref_nodes = vrReferenceService.getSceneReferences()
    else:
        ref_nodes = get_nodes(errors)

    vrNodeService.removeNodes(ref_nodes)
