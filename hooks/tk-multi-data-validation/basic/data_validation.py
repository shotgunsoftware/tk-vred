# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

from functools import wraps
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


def check_vred_version_support(func):
    """
    Decorator function to check VRED version support before executing the API function.

    If the current running VRED version does not support the API function, log the original
    exception message and raise a specific exception with user friendly message (the data
    validation app will display the exception message to the user).

    :param func: The VRED API function to execute.
    :type func: function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        validation_hook_instance = args[0]
        try:
            return func(*args, **kwargs)
        except (
            validation_hook_instance.vredpy.VREDModuleNotSupported,
            validation_hook_instance.vredpy.VREDFunctionNotSupported,
        ) as vredpy_error:
            validation_hook_instance.logger.error(vredpy_error)
            raise VREDDataValidationHook.VREDDataValidationError(
                """
                This Validation Rule is not supported by the current running VRED version.
                Please update to the latest version of VRED to use this functionality.
            """
            )

    return wrapper


class VREDDataValidationHook(HookBaseClass):
    """
    Hook to integrate VRED with the Data Validation App (DVA).

    The DVA provides the user interface to visualize the data in a DCC, and handles executing
    the validation functions and applying the resolution functions to the data.

    The purpose of this hook is to define the data validation details specific to VRED, such
    that the DVA can use it in order to perform checks and fixes to the data in VRED. The main
    hook method that is essential to the DVA, and must be implemented, is:

        `get_validation_data`

    ; it is responsible for returning a dictionary of data that defines the validation
    rules for VRED. The DVA calls this hook method to set up the valdiation rules that are
    displayed in the app. Each rule may contain details in how it is displayed (e.g. validate
    and fix button names, error messages, etc.), as well as the validate and fix functions. See
    the `get_validation_data` method for more details on the validation data formatting and
    supported values.

    The second key part to this hook is to define the validation, fix and/or action functions,
    which are defined in the validation data (the data returned by `get_validation_data`). For
    any rule that defines a validate or fix function, those functions can be defined as hook
    methods in this file (or they can call other module functions). To customize any
    particular validate, fix, and/or action function, this hook `VREDDataValidationHook` can
    be subclassed and hook methods (that are the valdiate, fix, action functions) can be
    overridden.

    The last function to note, and which also must be implemented is:

        `sanitize_check_result`

    ; it is responsible for formatting the data returned by a validation "check" function,
    such that it can be processed by the DVA. See the `sanitize_check_result` hook method for
    more details.
    """

    class VREDDataValidationError(Exception):
        """Custom exception class to report VRED Data Validation specific errors."""

    def __init__(self, *args, **kwargs):
        """Initialize the hook."""

        super(VREDDataValidationHook, self).__init__(*args, **kwargs)

        # Get the VRED python api module from the engine. Use this module to access all of the VRED API
        # functions (instead of directly importing here).
        self.vredpy = self.parent.engine.vredpy

    # -------------------------------------------------------------------------------------------------------
    # Override base hook methods
    # -------------------------------------------------------------------------------------------------------

    def get_validation_data(self):
        """
        The main hook method that returns the VRED data validation rules.

        The dictionary returned by this function is formated such that it can be passed
        to the :class:`~tk-multi-data-validation:data.ValidationRule` class constructor to
        create a new validation rule object. See the ValidationRule constructor for more
        details on the supported key-values in the data dictionary.

        :return: The validation rules data set.
        :rtype: dict
        """

        return {
            "material_unused": {
                "name": "Remove Unused Materials",
                "description": "Remove Unused Materials.",
                "error_msg": "Found unused materials",
                "check_func": self._find_unused_materials,
                "fix_func": self._remove_unused_materials,
                "actions": [
                    {
                        "name": "Select All",
                        "callback": self._select_materials,
                    }
                ],
                "item_actions": [
                    {
                        "name": "Select",
                        "callback": self._select_materials,
                    }
                ],
            },
            "material_clearcoat_orangepeel": {
                "name": "Use Orange Peel for Clearcoats",
                "description": "Ensure materials with clearcoat are using orange peel.",
                "error_msg": "Found materials with clearcoat not using orange peel",
                "check_func": self._find_materials_not_using_orange_peel,
                "fix_func": self._use_clearcoat_orange_peel,
                "fix_name": "Use Orange Peel",
                "actions": [
                    {
                        "name": "Select All",
                        "callback": self._select_materials,
                    }
                ],
                "item_actions": [
                    {
                        "name": "Use Orange Peel",
                        "callback": self._use_clearcoat_orange_peel,
                    },
                    {
                        "name": "Select",
                        "callback": self._select_materials,
                    },
                ],
                "dependency_ids": ["material_unused"],
            },
            "material_bump_normal_map": {
                "name": "Use Bump and Normal Maps",
                "description": "Ensure materials with bump texture are using bump or normal maps.",
                "error_msg": "Found materials with bump texture not using bump or normal maps",
                "check_func": self._find_materials_not_using_texture,
                "fix_func": self._set_material_use_texture,
                "fix_name": "Use Bump or Normal Maps",
                "actions": [
                    {
                        "name": "Select All",
                        "callback": self._select_materials,
                    }
                ],
                "item_actions": [
                    {
                        "name": "Use Bump or Normal Maps",
                        "callback": self._set_material_use_texture,
                    },
                    {
                        "name": "Select",
                        "callback": self._select_materials,
                    },
                ],
                "dependency_ids": ["material_unused"],
            },
            "scene_graph_hidden_nodes": {
                "name": "Delete Hidden Nodes",
                "description": "Find hidden nodes in the Scene Graph and delete them.",
                "error_msg": "Found hidden nodes in the Scene Graph.",
                "check_func": self._find_hidden_nodes,
                "fix_func": self._delete_hidden_nodes,
                "fix_name": "Delete All",
                "get_kwargs": lambda: {
                    "api_version": self.vredpy.v1(),
                    "ignore_node_types": [
                        self.vredpy.switch_node_type(self.vredpy.v1())
                    ],
                },
                "actions": [
                    {
                        "name": "Select All",
                        "callback": self._select_nodes,
                    },
                ],
                "item_actions": [
                    {
                        "name": "Select",
                        "callback": self._select_nodes,
                    },
                    {
                        "name": "Delete",
                        "callback": self._delete_hidden_nodes,
                    },
                ],
            },
            "scene_graph_ref_remove": {
                "name": "Delete References",
                "description": "Find reference nodes in the Scene Graph and delete the reference nodes.",
                "error_msg": "Found reference nodes in the Scene Graph.",
                "check_func": self._find_references,
                "fix_func": self._delete_references,
                "fix_name": "Delete All",
                "actions": [
                    {
                        "name": "Select All",
                        "callback": self._select_nodes,
                    },
                ],
                "item_actions": [
                    {
                        "name": "Select",
                        "callback": self._select_nodes,
                    },
                    {
                        "name": "Delete",
                        "callback": self._delete_references,
                    },
                ],
            },
            "scene_graph_ref_unload": {
                "name": "Unload References",
                "description": "Find all loaded reference nodes in the Scene Graph and unload them.",
                "error_msg": "Found loaded reference nodes in the Scene Graph.",
                "check_func": self._find_loaded_references,
                "fix_func": self._unload_reference,
                "fix_name": "Unload All",
                "actions": [
                    {
                        "name": "Select All",
                        "callback": self._select_nodes,
                    },
                ],
                "item_actions": [
                    {
                        "name": "Select",
                        "callback": self._select_nodes,
                    },
                    {
                        "name": "Unload",
                        "callback": self._unload_reference,
                    },
                ],
            },
            "animation_clip_delete": {
                "name": "Delete Animation Clips",
                "description": "Find all animation clips and delete them. All animations in the clips will be deleted.",
                "error_msg": "Found animation clips.",
                "check_func": self._find_animation_clips,
                "fix_func": self._delete_animation_clips,
                "fix_name": "Delete All",
                "item_actions": [
                    {
                        "name": "Delete",
                        "callback": self._delete_animation_clips,
                    },
                ],
            },
            "animation_clip_empty": {
                "name": "Delete Empty Animation Clips",
                "description": "Find all empty animation clips and delete them.",
                "error_msg": "Found animation clips.",
                "check_func": self._find_empty_animation_clips,
                "fix_func": self._delete_empty_animation_clips,
                "fix_name": "Delete All",
                "item_actions": [
                    {
                        "name": "Delete",
                        "callback": self._delete_empty_animation_clips,
                    },
                ],
            },
            "animation_block_uncheck": {
                "name": "Uncheck Animation Blocks",
                "description": "Find all checked animation blocks and uncheck them.",
                "error_msg": "Found checked animations.",
                "check_func": self._find_checked_animation_blocks,
                "fix_func": self._uncheck_animation_blocks,
                "fix_name": "Uncheck All",
                "actions": [
                    # {
                    #     "name": "Group All",
                    #     "callback": self._group_animation_blocks,
                    # },
                ],
                "item_actions": [
                    {
                        "name": "Uncheck",
                        "callback": self._uncheck_animation_blocks,
                    },
                ],
            },
            "uv_mat_missing": {
                "name": "Create Missing Material UV Sets",
                "description": "Find all geometries without Material UV Set and create UVs. UVs will be created using the unfold method.",
                "error_msg": "Found geometries without Material UV Sets.",
                "check_func": self._find_geometries_without_material_uvs,
                "fix_func": self._create_material_uvs_for_geometries_without,
                "fix_name": "Create UVs",
                "actions": [
                    {
                        "name": "Select All",
                        "callback": self._select_nodes,
                    },
                ],
                "item_actions": [
                    {
                        "name": "Create UVs",
                        "callback": self._create_material_uvs_for_geometries_without,
                    },
                    {
                        "name": "Select",
                        "callback": self._select_nodes,
                    },
                ],
            },
            "uv_light_missing": {
                "name": "Create Missing Light UV Sets",
                "description": "Find all geometries without Light UV Set and create UVs. UVs will be created using the unfold method.",
                "error_msg": "Found geometries without Light UV Sets.",
                "check_func": self._find_geometries_without_light_uvs,
                "fix_func": self._create_light_uvs_for_geometries_without,
                "fix_name": "Create UVs",
                "actions": [
                    {
                        "name": "Select All",
                        "callback": self._select_nodes,
                    },
                ],
                "item_actions": [
                    {
                        "name": "Create UVs",
                        "callback": self._create_light_uvs_for_geometries_without,
                    },
                    {
                        "name": "Select",
                        "callback": self._select_nodes,
                    },
                ],
            },
            # -------------------------------------------------------------------------------------------------------
            # Data validation that is actually optimizations - nothing to "check" just fix
            # -------------------------------------------------------------------------------------------------------
            "material_remove_duplicates": {
                "name": "Merge Duplicate Materials",
                "description": "Share materials with the same properties.",
                "fix_func": self._merge_duplicate_materials,
                "fix_name": "Merge",
            },
            "optimize_geometries": {
                "name": "Optimize Geometries",
                "description": "Optimizes the geometry structure.",
                "fix_func": self._optimize_geometry,
                "fix_name": "Optimize",
                "get_kwargs": lambda: {
                    "strips": True,
                    "fans": True,
                    "stitches": False,
                },
            },
            "optimize_share_geometries": {
                "name": "Optimize/Share Geometries",
                "description": "Optimizes the geometry structure and tries to share duplicated geometries.",
                "fix_func": self._share_geometries,
                "fix_name": "Optimize",
                "get_kwargs": lambda: {"check_world_geometries": False},
            },
            "optimize_merge_geometries": {
                "name": "Merge/Optimmize/Share Geometries",
                "description": "This is much more aggressive and changes the scenegraph structure.",
                "fix_func": self._merge_geometries,
                "fix_name": "Optimize",
            },
            "geometry_tessellate": {
                "name": "Tessellate",
                "description": "Retessellates the given surfaces.",
                "fix_func": self._tessellate,
                "fix_name": "Tessellate",
            },
            "geometry_decore": {
                "name": "Decore & Correct Wrong Normal",
                "description": "Remove redundant geometry that is inside other geometry. This feature only works with OpenGL.",
                "fix_func": self._decore,
                "fix_name": "Decore",
            },
            # -------------------------------------------------------------------------------------------------------
            # Data validation that requires more information (e.g. provide path, settings, etc...)
            # -------------------------------------------------------------------------------------------------------
            "bake_texture": {
                "name": "Bake To Texture",
                "description": "Bake to texture.",
                "fix_func": self._bake_to_texture,
                "fix_name": "Bake",
            },
            "bake_repath_lightmaps": {
                "name": "Repath Lightmaps",
                "description": "Re-path existing lightmaps from a list of geometry nodes.<br/>NOTE: Need to provide a path for repathing lightmaps.",
                "fix_func": self._repath_lightmaps,
            },
            # -------------------------------------------------------------------------------------------------------
            # Data validation that don't work quite right..
            # -------------------------------------------------------------------------------------------------------
            #
            # Variant sets are deleted but still appear in the VRED UI - and will crash if interacted with.
            "variant_set_clear": {
                "name": "Clear Variant Sets",
                "description": "Find all variant sets and remove them.",
                "error_msg": "Found variant sets.",
                "check_func": self._find_variant_sets,
                "fix_func": self._delete_variant_sets,
                "fix_name": "Clear",
                "item_actions": [
                    {
                        "name": "Delete",
                        "callback": self._delete_variant_sets,
                    },
                ],
            },
            "variant_set_group_empty": {
                "name": "Delete Empty Variant Set Groups",
                "description": "Find all variant set groups and remove them.",
                "error_msg": "Found empty variant set groups.",
                "check_func": self._find_empty_variant_set_groups,
                "fix_func": self._delete_empty_variant_set_groups,
                "fix_name": "Delete All",
                "item_actions": [
                    {
                        "name": "Delete",
                        "callback": self._delete_empty_variant_set_groups,
                    },
                ],
            },
            # -------------------------------------------------------------------------------------------------------
            # Data validation that requires VRED API updates/additions
            # -------------------------------------------------------------------------------------------------------
            #
            # Requires function to delete the uv set
            #
            "uv_light_delete": {
                "name": "Delete Light UV Sets",
                "description": "Find all geometries with Light UV Sets and remove them.",
                "error_msg": "Found geometries with Light UV Sets.",
                "check_func": self._find_geometries_with_light_uvs,
                # "fix_func": delete_light_uvs,
                "fix_name": "Delete UVs",
                "actions": [
                    {
                        "name": "Select All",
                        "callback": self._select_nodes,
                    },
                ],
                "item_actions": [
                    # {
                    #     "name": "Delete UVs",
                    #     "callback": delete_light_uvs,
                    # },
                    {
                        "name": "Select",
                        "callback": self._select_nodes,
                    },
                ],
            },
            "uv_mat_delete": {
                "name": "Delete Material UV Sets",
                "description": "Find all geometries with Material UV Sets and remove them.<br/>NOTE: VRED API method not available to delete UV Sets.",
                "error_msg": "Found geometries with Material UV Sets.",
                "check_func": self._find_geometries_with_material_uvs,
                # "fix_func": delete_material_uvs,
                # "fix_name": "Delete UVs",
                "actions": [
                    {
                        "name": "Select All",
                        "callback": self._select_nodes,
                    },
                ],
                "item_actions": [
                    # {
                    #     "name": "Delete UVs",
                    #     "callback": delete_material_uvs,
                    # },
                    {
                        "name": "Select",
                        "callback": self._select_nodes,
                    },
                ],
            },
        }

    def sanitize_check_result(self, result):
        """
        Sanitize the value returned by any validate function to conform to the standard format.

        Convert the incoming list of VRED objects (that are errors) to conform to the standard
        format that the Data Validation App requires:

            is_valid:
                type: bool
                description: True if the validate function succeed with the current data, else
                             False.

            errors:
                type: list
                description: The list of error objects (found by the validate function). None
                             or empty list if the current data is valid.
                items:
                    type: dict
                    key-values:
                        id:
                            type: str | int
                            description: A unique identifier for the error object.
                            optional: False
                        name:
                            type: str
                            description: The display name for the error object.
                            optional: False
                        type:
                            type: str
                            description: The display name of the error object type.
                            optional: True

        This method will be called by the Data Validation App after any validate function is
        called, in order to receive the validate result in the required format.

        :param result: The result returned by a validation rule ``check_func``. This is
            typically (but not guaranteed) a list of VRED objects.
        :type result: list

        :return: The result of a ``check_func`` in the Data Validation standardized format.
        :rtype: dict
        """

        return {
            "is_valid": not result,
            "errors": self._sanitize_vred_objects(result),
        }

    # -------------------------------------------------------------------------------------------------------
    # Protected hook methods
    # -------------------------------------------------------------------------------------------------------

    def _sanitize_vred_objects(self, objects):
        """
        Sanitize the VRED objects.

        This method formats the list of VRED API (v1 or v2) objects such that they are
        compatible with the DVA. Each object will be formatted as a dictionary with
        keys-values:

            id:
                type: str | int
                description: The VRED object's unique ID.

            name:
                type: str | int
                description: The VRED object display name (this may be the same as the ID).

            type:
                type: str
                description: (optional) The VRED object type display name.

        :return: The list of sanitized VRED objects.
        :rtype: list<dict>
        """

        if not objects:
            return []

        object_results = []
        for obj in objects:
            object_id = self.vredpy.get_id(obj)

            if hasattr(obj, "getName"):
                object_name = obj.getName()
            else:
                # Fallback to use the id as the name
                object_name = object_id

            object_results.append(
                {
                    "id": object_id,
                    "name": object_name,
                    "type": self.vredpy.get_type_as_str(obj),
                }
            )

        return object_results

    # -------------------------------------------------------------------------------------------------------
    # Select Methods (action functions)
    # -------------------------------------------------------------------------------------------------------

    def _select_nodes(self, errors=None):
        """
        Select the given nodes in the scene graph.

        This method is used as an individual fix and/or action function for a validation rule -
        it must include the `errors` key-value argument with default value None.

        :param errors: The nodes to select. If None, current selection does not change.
        :type errors: list.
        """

        nodes = self.vredpy.get_nodes(errors)
        if nodes:
            select = True
            self.vredpy.vrScenegraph.selectNodes(nodes, select)

    def _select_materials(self, errors=None):
        """
        Select the given materials.

        This method is used as an individual fix and/or action function for a validation rule -
        it must include the `errors` key-value argument with default value None.

        :param errors: The materials to select. If None, current selection does not change.
        :type errors: list
        """

        mats = self.vredpy.get_materials(errors)
        if mats:
            self.vredpy.vrMaterialService.setMaterialSelection(mats)

    # -------------------------------------------------------------------------------------------------------
    # Validation & Fix Methods (check and fix functions)
    # -------------------------------------------------------------------------------------------------------

    @check_vred_version_support
    def _find_unused_materials(self):
        """
        Find all unused materials.

        Format the data before returning to be compatible with the Data Validation App.

        :return: The unused materials.
        :rtype: dict
        """

        return self.vredpy.vrMaterialService.findUnusedMaterials()

    @check_vred_version_support
    def _remove_unused_materials(self, errors=None):
        """
        Remove all unused materials.

        :param errors: A list of unused materials to remove.
        :type errors: list
        """

        self.vredpy.vrMaterialService.removeUnusedMaterials()

    @check_vred_version_support
    def _find_hidden_nodes(
        self, node=None, ignore_node_types=None, ignore_nodes=None, api_version=None
    ):
        """
        Find all hidden nodes in the scene graph.

        Format the data before returning to be compatible with the Data Validation App.

        :param node: (optional) If None all nodes will be checked, else only nodes in the node
            subtree will be checked.
        :type node: vrNodePtr | vrdNode
        :param ignore_node_types: A list of node types to exclude from the result. All children
            of these types of nodes will also be ignored (regardless of the child node type).
            This list of types must correspond to the `api_version`.
        :type ignore_node_types: list<str> (for v1) | list<class> (for v2)
        :param ignore_nodes: A list of nodes by name to exclude from the result. Unlike the
            `ignore_node_types` list, the children of these nodes will not be ignored.
        :type ignore_nodes: list<str>
        :param api_version: The VRED API version to use for finding hidden nodes. Defaults to v1.
        :type api_version: str (v1|v2)

        :return: The hidden nodes.
        :rtype: dict
        """

        api_version = api_version or self.vredpy.v1()
        ignore_node_types = ignore_node_types or []
        hidden_nodes = self.vredpy.get_hidden_nodes(
            root_node=node, ignore_node_types=ignore_node_types, api_version=api_version
        )

        if ignore_nodes:
            return [node for node in hidden_nodes if node.getName() not in ignore_nodes]

        return hidden_nodes

    @check_vred_version_support
    def _show_nodes(
        self,
        errors=None,
        node=None,
        ignore_node_types=None,
        ignore_nodes=None,
        api_version=None,
    ):
        """
        Show the given hidden nodes, or show all hidden nodes if nodes not specified.

        This method is used as an individual fix and/or action function for a validation rule -
        it must include the `errors` key-value argument with default value None.

        :param errors: The nodes to show. If None, all hidden nodes will be shown.
        :type errors: list
        :param node: (optional) If None all nodes will be checked, else only nodes in the node
            subtree will be checked. This param is ignored if the errors param is not None.
            This param is ignored if the errors param is specified.
        :type node: vrNodePtr | vrdNode
        :param ignore_node_types: A list of node types to exclude from the result. All children
            of these types of nodes will also be ignored (regardless of the child node type).
            This list of types must correspond to the `api_version`. If errors specified, this
            param is itself ignored.
        :type ignore_node_types: list<str> (for v1) | list<class> (for v2)
        :param ignore_nodes: A list of nodes by name to exclude from the result. Unlike the
            `ignore_node_types` list, the children of these nodes will not be ignored. If
            errors specified, this param itself is ignored.
        :type ignore_nodes: list<str>
        :param api_version: The VRED API version to use for finding hidden nodes. Defaults to
            v1. If errors specified, this param itself is ignored.
        :type api_version: str (v1|v2)
        """

        if errors is None:
            hidden_nodes = self._find_hidden_nodes(
                node, ignore_node_types, ignore_nodes, api_version
            )
        else:
            hidden_nodes = self.vredpy.get_nodes(errors)

        self.vredpy.show_nodes(hidden_nodes)

    @check_vred_version_support
    def _delete_hidden_nodes(
        self,
        errors=None,
        node=None,
        ignore_node_types=None,
        ignore_nodes=None,
        api_version=None,
    ):
        """
        Delete the given hidden nodes, or delete all hidden nodes if nodes not specified.

        This method is used as an individual fix and/or action function for a validation rule -
        it must include the `errors` key-value argument with default value None.

        :param errors: The nodes to delete. If None, all hidden nodes will be deleted.
        :type errors: list
        :param node: (optional) If None all nodes will be checked, else only nodes in the node
            subtree will be checked. This param is ignored if the errors param is not None.
            This param is ignored if the errors param is specified.
        :type node: vrNodePtr | vrdNode
        :param ignore_node_types: A list of node types to exclude from the result. All children
            of these types of nodes will also be ignored (regardless of the child node type).
            This list of types must correspond to the `api_version`. If errors specified, this
            param is itself ignored.
        :type ignore_node_types: list<str> (for v1) | list<class> (for v2)
        :param ignore_nodes: A list of nodes by name to exclude from the result. Unlike the
            `ignore_node_types` list, the children of these nodes will not be ignored. If
            errors specified, this param itself is ignored.
        :type ignore_nodes: list<str>
        :param api_version: The VRED API version to use for finding hidden nodes. Defaults to
            v1. If errors specified, this param itself is ignored.
        :type api_version: str (v1|v2)
        """

        if errors is None:
            hidden_nodes = self._find_hidden_nodes(
                node, ignore_node_types, ignore_nodes, api_version
            )
        else:
            hidden_nodes = self.vredpy.get_nodes(errors)

        self.vredpy.delete_nodes(hidden_nodes)

    @check_vred_version_support
    def _set_hidden_nodes_to_b_side(
        self,
        errors=None,
        node=None,
        ignore_node_types=None,
        ignore_nodes=None,
        api_version=None,
    ):
        """
        Set all given nodes to B-Side, or set all hidden nodes if nodes not sepcified.

        This method is used as an individual fix and/or action function for a validation rule -
        it must include the `errors` key-value argument with default value None.

        :param errors: The nodes to set to B-Side. If None, all hidden nodes set to B-Side.
        :type errors: list
        :param node: (optional) If None all nodes will be checked, else only nodes in the node
            subtree will be checked. This param is ignored if the errors param is not None.
            This param is ignored if the errors param is specified.
        :type node: vrNodePtr | vrdNode
        :param ignore_node_types: A list of node types to exclude from the result. All children
            of these types of nodes will also be ignored (regardless of the child node type).
            This list of types must correspond to the `api_version`. If errors specified, this
            param is itself ignored.
        :type ignore_node_types: list<str> (for v1) | list<class> (for v2)
        :param ignore_nodes: A list of nodes by name to exclude from the result. Unlike the
            `ignore_node_types` list, the children of these nodes will not be ignored. If
            errors specified, this param itself is ignored.
        :type ignore_nodes: list<str>
        :param api_version: The VRED API version to use for finding hidden nodes. Defaults to
            v1. If errors specified, this param itself is ignored.
        :type api_version: str (v1|v2)
        """

        if errors is None:
            hidden_nodes = self._find_hidden_nodes(
                node, ignore_node_types, ignore_nodes, api_version
            )
        else:
            hidden_nodes = self.vredpy.get_nodes(errors)

        self.vredpy.set_to_b_side(hidden_nodes, b_side=True)

    @check_vred_version_support
    def _find_references(self):
        """
        Find all references in the scene graph.

        Format the data before returning to be compatible with the Data Validation App.

        :return: The references.
        :rtype: dict
        """

        return self.vredpy.vrReferenceService.getSceneReferences()

    @check_vred_version_support
    def _delete_references(self, errors=None):
        """
        Find all references in the scene graph and delete the reference nodes.

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The references to delete. If None, delete all references.
        :type errors: list
        """

        if errors is None:
            ref_nodes = self.vredpy.vrReferenceService.getSceneReferences()
        else:
            ref_nodes = self.vredpy.get_nodes(errors, api_version=self.vredpy.v2())

        self.vredpy.vrNodeService.removeNodes(ref_nodes)

    @check_vred_version_support
    def _find_loaded_references(self):
        """
        Find references that are loaded, in the scene graph.

        Format the data before returning to be compatible with the Data Validation App.

        :return: The loaded references.
        :rtype: dict
        """

        return [
            r
            for r in self.vredpy.vrReferenceService.getSceneReferences()
            if r.isLoaded()
        ]

    @check_vred_version_support
    def _unload_reference(self, errors=None):
        """
        Unload the references.

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The references to unload. If None, unload all references.
        :type errors: list
        """

        if errors is None:
            refs = self.vredpy.vrReferenceService.getSceneReferences()
        else:
            refs = self.vredpy.get_nodes(errors, api_version=self.vredpy.v2())

        for ref in refs:
            if ref.isLoaded():
                ref.unload()

    @check_vred_version_support
    def _find_variant_sets(self):
        """
        Find all variant sets.

        Format the data before returning to be compatible with the Data Validation App.

        :return: The variant sets.
        :rtype: dict
        """

        return self.vredpy.vrVariantSets.getVariantSets()

    @check_vred_version_support
    def _delete_variant_sets(self, errors=None):
        """
        Delete the given variant sets.

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The variant sets to delete. If None, delete all variant sets.
        :type errors: list
        """

        if errors is None:
            vsets = self.vredpy.vrVariantSets.getVariantSets()
        else:
            vsets = errors

        if not isinstance(vsets, (list, tuple)):
            vsets = [vsets]

        for vset in vsets:
            self.vredpy.vrVariantSets.deleteVariantSet(vset)

    @check_vred_version_support
    def _find_animation_clips(self, top_level_only=False):
        """
        Find all animation clips.

        Format the data before returning to be compatible with the Data Validation App.

        :param top_level_only: True will only find the top level animation clips, else False
            will find all animation clips (including nested/child clips).
        :type top_level_only: bool

        :return: The animation clips.
        :rtype: dict
        """

        return self.vredpy.get_animation_clips(top_level_only=top_level_only)

    @check_vred_version_support
    def _delete_animation_clips(self, errors=None, top_level_only=False):
        """
        Delete the animation clip nodes.

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The clips to delete. If None, delete all clips.
        :type errors: list
        :param top_level_only: True will only find the top level animation clips, else False
            will find all animation clips (including nested/child clips). This param is
            ignored if the errors param is specified.
        :type top_level_only: bool
        """

        if errors is None:
            clip_nodes = self.vredpy.get_animation_clips(top_level_only=top_level_only)
        else:
            clip_nodes = self.vredpy.get_nodes(errors)

        self.vredpy.delete_nodes(clip_nodes)

    @check_vred_version_support
    def _find_empty_animation_clips(self):
        """
        Find all empty animation clips nodes.

        Format the data before returning to be compatible with the Data Validation App.

        :return: The empty animation clips.
        :rtype: dict
        """

        return self.vredpy.get_empty_animation_clips()

    @check_vred_version_support
    def _delete_empty_animation_clips(self, errors=None):
        """
        Delete empty animation clip nodes.

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The animation clips to delete. If none, delete all empty clips.
        :type errors: list
        """

        if errors is None:
            clip_nodes = self.vredpy.get_empty_animation_clips()
        else:
            clip_nodes = self.vredpy.get_nodes(errors)

        self.vredpy.delete_nodes(clip_nodes)

    @check_vred_version_support
    def _find_checked_animation_blocks(self, include_hidden=True):
        """
        Find all checked animation blocks nodes.

        Format the data before returning to be compatible with the Data Validation App.

        :param include_hidden: True will find animation blocks that are hidden, else False
            will ignore hidden blocks.
        :type include_hidden: bool

        :return: The checked animation blocks.
        :rtype: dict
        """

        return [
            block
            for block in self.vredpy.vrAnimWidgets.getAnimBlockNodes(include_hidden)
            if block.getActive()
        ]

    @check_vred_version_support
    def _uncheck_animation_blocks(self, errors=None, include_hidden=True):
        """
        Find all checked animation blocks and uncheck them.

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The animation blocks to delete. If None, uncheck all animation blocks.
        :type errors: list
        :param include_hidden: True will find animation blocks that are hidden, else False
            will ignore hidden blocks. This param is ignored if the errors param is specified.
        :type include_hidden: bool
        """

        if errors is None:
            checked_blocks = [
                block
                for block in self.vredpy.vrAnimWidgets.getAnimBlockNodes(include_hidden)
                if block.getActive()
            ]
        else:
            checked_blocks = self.vredpy.get_nodes(errors)

        for block in checked_blocks:
            block.setActive(False)

    @check_vred_version_support
    def _find_geometries_without_material_uvs(self):
        """
        Find geometries without Material UV Sets.

        Format the data before returning to be compatible with the Data Validation App.

        :return: The geometry without material UV sets.
        :rtype: dict
        """

        return self.vredpy.get_geometry_nodes(has_mat_uvs=False)

    @check_vred_version_support
    def _create_material_uvs_for_geometries_without(
        self, errors=None, nodes=None, unfold_settings=None, layout_settings=None
    ):
        """
        Find geometries without Material UV Sets and create UVs for them.

        The UVs are created using the unfold operation which does the following:

            Compute unfolded UV coordinates for the given geometry nodes.

            For each geometry, its coordinates are unfolded and packed into UV space according
            to the provided layout settings. Unfolding is done with Unfold3D. Any existing UV
            coordinates are overwritten. The input geometry does not need to have UVs. UVs are
            created from scratch based on the 3D data of the geometry. Degenerate triangles are
            removed from the input geometry.

            To run unfold on a shell geometry, pass the shell geometry node to this function,
            do not include the surface nodes in the list. When passing surface nodes to unfold,
            the surfaces are unfolded individually.

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The geometry to unfold. If None, unfold the given nodes.
        :type errors: list
        :param nodes: Ignored if errors is not None. The geometry to unfold. If None, unfold
            all nodes.
        :type nodes: List[vrdGeometryNode]
        :param unfold_settings: The settings used to unfold the UVs.
        :type unfold_settings: vrdUVUnfoldSettings
        :param layout_settings: The settings used to pack the unfolded UV islands into UV space.
        :type layout_settings: vrdUVLayoutSettings
        """

        if errors is None:
            nodes = self.vredpy.get_geometry_nodes(has_mat_uvs=False)
        else:
            if nodes is None:
                nodes = self.vredpy.get_nodes(errors, api_version=self.vredpy.v2())

        unfold_settings = unfold_settings or self.vredpy.get_unfold_settings()
        layout_settings = layout_settings or self.vredpy.get_layout_settings()

        self.vredpy.vrUVService.unfold(
            nodes,
            unfold_settings,
            layout_settings,
            uvSet=self.vredpy.vrUVTypes.MaterialUVSet,
        )

    @check_vred_version_support
    def _find_geometries_with_material_uvs(self):
        """
        Find geometries with Material UV Sets.

        Format the data before returning to be compatible with the Data Validation App.

        :return: The geometry with material UV sets.
        :rtype: dict
        """

        return self.vredpy.get_geometry_nodes(has_mat_uvs=True)

    @check_vred_version_support
    def _find_geometries_without_light_uvs(self):
        """
        Find geometries without Light UV Sets.

        Format the data before returning to be compatible with the Data Validation App.

        :return: The geometry without light UV sets.
        :rtype: dict
        """

        return self.vredpy.get_geometry_nodes(has_light_uvs=False)

    @check_vred_version_support
    def _find_geometries_with_light_uvs(self):
        """
        Find geometries with Light UV Sets.

        Format the data before returning to be compatible with the Data Validation App.

        :return: The geometry with light UV sets.
        :rtype: dict
        """

        return self.vredpy.get_geometry_nodes(has_light_uvs=True)

    @check_vred_version_support
    def _create_light_uvs_for_geometries_without(
        self, errors=None, nodes=None, unfold_settings=None, layout_settings=None
    ):
        """
        Find geometries without Light UV Sets and create UVs for them.

        The UVs are created using the unfold operation which does the following:

            Compute unfolded UV coordinates for the given geometry nodes.

            For each geometry, its coordinates are unfolded and packed into UV space according
            to the provided layout settings. Unfolding is done with Unfold3D. Any existing UV
            coordinates are overwritten. The input geometry does not need to have UVs. UVs are
            created from scratch based on the 3D data of the geometry. Degenerate triangles are
            removed from the input geometry.

            To run unfold on a shell geometry, pass the shell geometry node to this function,
            do not include the surface nodes in the list. When passing surface nodes to unfold,
            the surfaces are unfolded individually.

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The geometry to unfold. If None, unfold the given nodes.
        :type errors: list
        :param nodes: Ignored if errors is not None. The geometry to unfold. If None, unfold
            all nodes.
        :type nodes: List[vrdGeometryNode]
        :param unfold_settings: The settings used to unfold the UVs.
        :type unfold_settings: vrdUVUnfoldSettings
        :param layout_settings: The settings used to pack the unfolded UV islands into UV space.
        :type layout_settings: vrdUVLayoutSettings
        """

        if errors is None:
            nodes = self.vredpy.get_geometry_nodes(has_light_uvs=False)
        else:
            if nodes is None:
                nodes = self.vredpy.get_nodes(errors, api_version=self.vredpy.v2())

        unfold_settings = unfold_settings or self.vredpy.get_unfold_settings()
        layout_settings = layout_settings or self.vredpy.get_layout_settings()

        self.vredpy.vrUVService.unfold(
            nodes,
            unfold_settings,
            layout_settings,
            uvSet=self.vredpy.vrUVTypes.LightmapUVSet,
        )

    @check_vred_version_support
    def _find_materials_not_using_orange_peel(self):
        """
        Find all materials with the clearcoat property and using orange peel.

        Format the data before returning to be compatible with the Data Validation App.

        :return: The materials not using orange peel.
        :rtype: dict
        """

        return self.vredpy.find_materials(using_orange_peel=False)

    @check_vred_version_support
    def _use_clearcoat_orange_peel(self, errors=None):
        """
        For materials with the clearcoat property, use orange peel.

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The materials to set to use orange peel. If None, set all materials to
            use orange peel.
        :type errors: list
        """

        if errors is None:
            mats = self.vredpy.find_materials(using_orange_peel=False)
        else:
            mats = self.vredpy.get_materials(errors)

        for mat in mats:
            try:
                clearcoat = mat.getClearcoat()
            except AttributeError:
                clearcoat = None

            if clearcoat:
                clearcoat.setUseOrangePeel(True)

    @check_vred_version_support
    def _find_materials_not_using_texture(self):
        """
        Find all materials with the bump map property and using texture.

        Format the data before returning to be compatible with the Data Validation App.

        :return: The materials not using textures.
        :rtype: dict
        """

        return self.vredpy.find_materials(using_texture=False)

    @check_vred_version_support
    def _set_material_use_texture(self, errors=None):
        """
        For materials with the bump texture property, set the material to use texture.

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The materials to set to use texture. If None, set all materials to use
            texture.
        :type errors: list
        """

        if errors is None:
            mats = self.vredpy.find_materials(using_texture=False)
        else:
            mats = self.vredpy.get_materials(errors)

        for mat in mats:
            try:
                bump_texture = mat.getBumpTexture()
            except AttributeError:
                bump_texture = None

            if bump_texture:
                bump_texture.setUseTexture(True)

    @check_vred_version_support
    def _group_animation_blocks(self):
        """Group all animation block nodes."""

        block_nodes = self.vredpy.vrAnimWidgets.getAnimBlockNodes(True)
        if block_nodes:
            self.vredpy.group_nodes(block_nodes)

    @check_vred_version_support
    def _bake_to_texture(
        self,
        errors=None,
        nodes=None,
        illumination_bake_settings=None,
        texture_bake_settings=None,
        replace_texture_bake=True,
    ):
        """
        Start the texture bake calculation for one lightmap per geometry node with the given settings.

        This method bakes only a single lightmap per node. invisible geometries are ignored.

        Either a base or a separate lightmap can be baked, depending on the illumination mode,
        see vrdIlluminationBakeSettings.setDirectIlluminationMode(value).

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The geometry to bake. If None, bake the geometry in the node's subtree.
        :type errors: list
        :param nodes: Ignored if errors param is not None. The geometry nodes to bake.
        :type root_node: list<vrdGeometryNode>. If errors and nodes are None, then bake all nodes.
        :param illumination_bake_settings: The illumination bake settings.
        :type illumination_bake_settings: vrdIlluminationBakeSettings
        :param texture_bake_settings: The texture bake settings.
        :type texture_bake_settings: vrdIlluminationBakeSettings
        :param replace_texture_bake: Specify what to do with an already existing separate
            lightmap on the node when baking a base lightmap. If True, the previous texture
            baking is replaced by the new base lightmap, the separate lightmap is deleted. If
            False, the separate lightmap is kept. When baking a separate lightmap this option
            is ignored, i.e. it creates or updates the separate lightmap and keeps the base
            lightmap.
        :type replace_texture_bake: bool
        """

        if errors is None:
            nodes = self.vredpy.get_nodes(errors, api_version=self.vredpy.v2())
        else:
            if nodes is None:
                root = self.vredpy.vrNodeService.getRootNode()
                nodes = self.vredpy.get_geometry_nodes(root_node=root)

        illumination_bake_settings = (
            illumination_bake_settings or self.vredpy.get_illumination_bake_settings()
        )
        texture_bake_settings = (
            texture_bake_settings or self.vredpy.get_texture_bake_settings()
        )

        self.vredpy.vrBakeService.bakeToTexture(
            nodes,
            illumination_bake_settings,
            texture_bake_settings,
            replace_texture_bake,
        )

    @check_vred_version_support
    def _repath_lightmaps(self, errors=None, path=None):
        """
        Re-paths existing lightmaps from a list of geometry nodes.

        This function takes the current directory paths of the lightmaps and exchanges it with
        a new one. An existing lightmap name is used to construct the file name. If the name
        was deleted, the old file name of the texture path is used instead. The new lightmaps
        will be loaded and replace the current ones.

        Re-pathing from a base and separate lightmap to a base only, deletes the separate
        lightmap.

        Re-pathing from a base and separate lightmap to a separate only, keeps the old base
        lightmap unchanged.

        Re-pathing from a single base lightmap will also search the new location for a
        corresponding separate lightmap based on its naming scheme.

        Re-pathing from a single separate lightmap will also search the new location for a
        corresponding base lightmap based on its naming scheme.

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The geometry to re-path. If None, re-path all geometry.
        :type errors: list
        :param path: The path to the folder which will replace the current one.
        :type path: str
        """

        if not path:
            raise self.VREDDataValidationError("Path required to re-path lightmaps.")

        if errors is None:
            geometry_nodes = [self.vredpy.vrNodeService.getRootNode()]
        else:
            geometry_nodes = self.vredpy.get_nodes(errors)

        self.vredpy.vrBakeService.repathLightmaps(geometry_nodes, path)

    @check_vred_version_support
    def _find_empty_variant_set_groups(self):
        """
        Find all empty variant set groups.

        Format the data before returning to be compatible with the Data Validation App.

        :return: The empty variant set groups.
        :rtype: dict
        """

        return self.vredpy.get_empty_variant_set_groups()

    @check_vred_version_support
    def _delete_empty_variant_set_groups(self, errors=None):
        """
        Delete the empty variant set groups.

        This method is used as a fix/action function for a validation rule - it must include
        the `errors` key-value argument with default value None.

        :param errors: The groups to delete. If None, delete all groups.
        :type errors: list
        """

        if errors is None:
            empty_groups = self.vredpy.get_empty_variant_set_groups()
        else:
            empty_groups = errors

        if not isinstance(empty_groups, (list, tuple)):
            empty_groups = [empty_groups]

        for group_name in empty_groups:
            self.vredpy.vrVariantSets.deleteVariantSetGroup(group_name)

    # -------------------------------------------------------------------------------------------------------
    # Optimize methods
    #   TODO
    # -------------------------------------------------------------------------------------------------------

    def _optimize_geometry(
        self, root_node=None, strips=True, fans=True, stitches=False
    ):
        """
        Optimize geometry to speed up rendering.

        Stripes and fans are optimized primitives that can be rendered much faster by your
        graphics hardware.

        :param root_node: The root node of the subgraph to be optimized. Defaults to the scene
            graph root node.
        :type root_node: vrNodePtr
        :param strips: Turn strips on or off in optimization. Default is True.
        :type strips: bool
        :param fans: Turn fans on or off in optimization. Default is True.
        :type fans: bool
        :param stitches: Turn stitches on or off in optimization. Default is False.
        :type stitches: bool
        """

        root_node = root_node or self.vredpy.vrNodeService.getRootNode()
        self.vredpy.vrOptimize.optimizeGeometry(root_node, strips, fans, stitches)

    def _share_geometries(self, root_node=None, check_world_matrix=False):
        """
        Share equal geometry nodes.

        :param root_node: The root node of the subgraph to be optimized. Defaults to the scene
            graph root node.
        :type root_node: vrNodePtr
        :param check_world_matrix: If True, only share the geometry when the world matrix of
        both nodes is equal.
        :type check_world_matrix: bool
        """

        root_node = root_node or self.vredpy.vrNodeService.getRootNode()
        self.vredpy.vrOptimize.shareGeometries(root_node, check_world_matrix)

    def _merge_geometries(self, root_node=None):
        """
        Merges geometry nodes.

        :param root_node: The root node of the subgraph to be optimized. Defaults to the scene
            graph root node.
        :type root_node: vrNodePtr
        """

        root_node = root_node or self.vredpy.vrNodeService.getRootNode()
        self.vredpy.vrOptimize.mergeGeometry(root_node)

    def _tessellate(
        self,
        nodes=None,
        chordal_deviation=0.0,
        normal_tolerance=0.0,
        max_chord_len=1.0,
        enable_stitching=True,
        stitching_tolerance=1.0,
        preserve_uvs=False,
    ):
        """
        Retessellate the geometry surfaces.

        :param nodes: The nodes to tessellate. If None, the root node is used.
        :type nodes: List[vrNodePtr]
        :param chordal_deviaition: The chordal deviation limit.
        :type chordal_deviaition: float
        :param normal_tolerance: The normal tolerance.
        :type normal_tolerance: float
        :param max_chord: The maximum length of a chord.
        :type max_chord: float
        :param enable_stitching: Sets stitching to either on or off.
        :type enable_stitching: bool
        :param stitching_tolerance: The maximum radius to use for stitching.
        :type stitching_tolerance: float
        :param preserve_uvs: Preserve existing UV layouts (Optional). Default is off. Enable
            option if you retessellate surfaces for which you've already setup UVs in VRED.
        :type preserve_uvs: bool
        """

        nodes = nodes or [self.vredpy.vrNodeService.getRootNode()]

        self.vredpy.vrGeometryEditor.tessellateSurfaces(
            nodes,
            chordal_deviation,
            normal_tolerance,
            max_chord_len,
            enable_stitching,
            stitching_tolerance,
            preserve_uvs,
        )

    def _decore(self, nodes=None, treat_as_combine_object=True, settings=None):
        """
        Decores the given objects with the given settings.

        :param nodes: The nodes to decore. Defaults to the root node.
        :type nodes: List[vrdNode]
        :param treat_as_combine_object: Defines if the given nodes are treated as combined objects or separately.
        :type treat_as_combine_object: bool
        :param settings: Settings for decoring objects.
        :type settings: vrdDecoreSettings
        """

        nodes = nodes or [self.vredpy.vrNodeService.getRootNode()]
        settings = settings or self.vredpy.get_decore_settings()

        self.vredpy.vrDecoreService.decore(nodes, treat_as_combine_object, settings)

    def _merge_duplicate_materials(self):
        """Optimize the scene by merging duplicate materials."""
        self.vredpy.vrMaterialService.mergeDuplicateMaterials()
