# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

from enum import Enum
from functools import wraps
import os
import tempfile

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
            raise VREDOptimizationHook.VREDOptimizationError(
                """
                This optimization is not supported by the current running VRED version.
                Please update to the latest version of VRED to use this functionality.
            """
            )

    return wrapper


class VREDOptimizationHook(HookBaseClass):
    """Hook to integrate VRED with the Optimize App."""

    class VREDOptimizationError(Exception):
        """Custom exception class to report VRED Data Validation specific errors."""

    def __init__(self, *args, **kwargs):
        """Initialize the hook."""

        super(VREDOptimizationHook, self).__init__(*args, **kwargs)

        # Get the VRED python api module from the engine. Use this module to access all of the VRED API
        # functions (instead of directly importing here).
        self.vredpy = self.parent.engine.vredpy

    # -------------------------------------------------------------------------------------------------------
    # Override base hook methods
    # -------------------------------------------------------------------------------------------------------

    def get_optimization_nodes(self):
        """Return the list of available nodes to add to an optimization graph."""

        # TODO add input/output restrictions/limits

        return {
            #
            # Input nodes
            #
            "scene_graph_node": {
                "name": "Scene Graph Node",
                "description": "This node will get the VRED node from the scene graph and pass it to its output nodes.",
                "settings": {
                    "node_name": {
                        "name": "Node",
                        "type": str,
                        "default": "Root",
                    },
                },
                "exec_func": self._get_node_name,
                "pre_output_exec_func": self._save_temp_file,
                "post_output_exec_func": self._remove_temp_file,
                "allowed_inputs": False,  # No inputs accepted
                "allowed_outputs": True,  # Accepts any number of outputs
            },
            "current_file": {
                "name": "Current File",
                "type": "input",
                "description": "This node will get a handle to the current file in VRED and pass it to its output nodes.",
                "pre_output_exec_func": self._save_temp_file,
                "post_output_exec_func": self._remove_temp_file,
                "allowed_inputs": False,  # No inputs accepted
                "allowed_outputs": True,  # Accepts any number of outputs
            },
            "file": {
                "name": "File",
                "type": "input",
                "description": "This node will get a handle to the specified file and pass it to its output nodes.",
                "settings": {
                    "file_path": {
                        "name": "File Path",
                        "type": str,
                    },
                },
                "exec_func": self._load_file,
                "post_exec_func": self._load_file,
                "pre_output_exec_func": self._save_temp_file,
                "post_output_exec_func": self._remove_temp_file,
                "allowed_inputs": False,  # No inputs accepted
                "allowed_outputs": True,  # Accepts any number of outputs
            },
            #
            # (Final?) Output nodes
            #
            "publish_file": {
                "name": "Publish File",
                "type": "output",
                "description": "Publish the file using ShotGrid.",
                "settings": {
                    "file_name": {
                        "name": "File Name",
                        "type": str,
                        "default": "publish_output.vpb",
                    },
                    "file_path": {
                        "name": "File Path",
                        "type": str,
                        "default": os.path.dirname(
                            self.vredpy.vrFileIO.getFileIOFilePath()
                        )
                        or "C:\\Users\\oues",
                    },
                },
                "exec_func": self._publish_file,
                "allowed_inputs": 1,  # Accepts exactly 1 input (NOTE could it accept multiple input nodes to merge/save into one file?)
                "allowed_outputs": False,
            },
            "save_file": {
                "name": "Save File",
                "type": "output",
                "description": "Save the file to local disk.",
                "settings": {
                    "file_name": {
                        "name": "File Name",
                        "type": str,
                        "default": "output_2.vpb",
                    },
                    "file_path": {
                        "name": "File Path",
                        "type": str,
                        "default": os.path.dirname(
                            self.vredpy.vrFileIO.getFileIOFilePath()
                        )
                        or "C:\\Users\\oues",
                    },
                },
                "exec_func": self._save_file,
                "allowed_inputs": 1,
                "allowed_outputs": False,
            },
            #
            # Optimization nodes
            #
            "optimize_geometries": {
                "name": "Optimize Geometries",
                "type": "optimize",
                "description": "Optimizes the geometry structure.",
                "settings": {
                    "strips": {
                        "name": "Strips",
                        "type": bool,
                        "default": True,
                    },
                    "fans": {
                        "name": "Fans",
                        "type": bool,
                        "default": True,
                    },
                    "stitches": {
                        "name": "Stitches",
                        "type": bool,
                        "default": False,
                    },
                },
                "exec_func": self._optimize_geometry,
                "allowed_inputs": 1,  # Accepts exactly 1 input (NOTE could it accept multiple input nodes to merge/save into one file?)
                "allowed_outputs": True,  # No outputs
            },
            "optimize_share_geometries": {
                "name": "Optimize/Share Geometries",
                "description": "Optimizes the geometry structure and tries to share duplicated geometries.",
                "settings": {
                    "check_world_matrix": {
                        "name": "Check World Matrix",
                        "type": bool,
                        "default": False,
                    },
                },
                "exec_func": self._share_geometries,
            },
            "optimize_merge": {
                "name": "Merge/Optimize/Share Geometries",
                "description": "This is much more aggressive and changes the scenegraph structure.",
                "exec_func": self._merge_geometries,
            },
            "geometry_tessellate": {
                "name": "Tessellate",
                "description": "Tessellate the geometry.",
                "settings": {
                    "chordal_deviation": {
                        "name": "Chordal Deviation",
                        "type": bool,
                        "default": False,
                    },
                    "normal_tolerance": {
                        "name": "Normal Tolerance",
                        "type": float,
                        "default": 10.0,
                        "decimals": 2,
                    },
                    "max_chord_len": {
                        "name": "Max Chord Length",
                        "type": int,
                        "default": 200,
                    },
                    "enable_stitching": {
                        "name": "Stitching",
                        "type": bool,
                        "default": True,
                    },
                    "stitching_tolerance": {
                        "name": "Stitching Tolerance",
                        "type": float,
                        "default": 0.1,
                    },
                    "preserve_uvs": {
                        "name": "Preserve UVs",
                        "type": bool,
                        "default": False,
                    },
                },
                "exec_func": self._tessellate,
            },
            "geometry_decore": {
                "name": "Decore",
                "description": "Decore the geometry.",
                "settings": {
                    "resolution": {
                        "name": "Resolution",
                        "type": int,
                        "default": 1024,
                    },
                    "quality_steps": {
                        "name": "Quality Steps",
                        "type": int,
                        "default": 8,
                    },
                    "correct_face_normals": {
                        "name": "Correct Face Normals",
                        "type": bool,
                        "default": False,
                    },
                    "decore_enabled": {
                        "name": "Enable Decore",
                        "type": bool,
                        "default": False,
                    },
                    "decore_mode": {
                        "name": "Decore Mode",
                        "type": Enum,
                        "default": self.vredpy.vrGeometryTypes.DecoreMode.Remove,
                        "choices": [
                            ("Remove", self.vredpy.vrGeometryTypes.DecoreMode.Remove),
                            (
                                "Set To B Side",
                                self.vredpy.vrGeometryTypes.DecoreMode.SetToBSide,
                            ),
                        ],
                    },
                    "sub_object_mode": {
                        "name": "Sub Object Mode",
                        "type": Enum,
                        "default": self.vredpy.vrGeometryTypes.DecoreSubObjectMode.Triangles,
                        "choices": [
                            (
                                "None",
                                self.vredpy.vrGeometryTypes.DecoreSubObjectMode.None_,
                            ),
                            (
                                "Components",
                                self.vredpy.vrGeometryTypes.DecoreSubObjectMode.Components,
                            ),
                            (
                                "Triangles",
                                self.vredpy.vrGeometryTypes.DecoreSubObjectMode.Triangles,
                            ),
                            (
                                "Components and Triangles",
                                self.vredpy.vrGeometryTypes.DecoreSubObjectMode.ComponentsAndTriangles,
                            ),
                        ],
                    },
                    "transparent_object_mode": {
                        "name": "Transparent Object Mode",
                        "type": Enum,
                        "default": "Ignore",
                        "default": self.vredpy.vrGeometryTypes.DecoreTransparentObjectMode.Ignore,
                        "choices": [
                            (
                                "Ignore",
                                self.vredpy.vrGeometryTypes.DecoreTransparentObjectMode.Ignore,
                            ),
                            (
                                "Treat as Transparent",
                                self.vredpy.vrGeometryTypes.DecoreTransparentObjectMode.TreatAsTransparent,
                            ),
                            (
                                "Treat As Opaque",
                                self.vredpy.vrGeometryTypes.DecoreTransparentObjectMode.TreatAsOpaque,
                            ),
                        ],
                    },
                    "treat_as_combine_object": {
                        "name": "Treat as Combine Object",
                        "type": bool,
                        "default": True,
                    },
                },
                "exec_func": self._decore,
            },
            "material_remove_duplicates": {
                "name": "Remove Duplicate Materials",
                "description": "Share materials and remove duplicate",
                "settings": {
                    "merge_options": {
                        "name": "Merge Options",
                        "type": Enum,
                        "default": self.vredpy.vrMaterialTypes.MergeOptions.Default,
                        "choices": [
                            (
                                "Default",
                                self.vredpy.vrMaterialTypes.MergeOptions.Default,
                            ),
                            (
                                "Ignore Name",
                                self.vredpy.vrMaterialTypes.MergeOptions.IgnoreName,
                            ),
                            (
                                "Include Switch Materials",
                                self.vredpy.vrMaterialTypes.MergeOptions.IncludeSwitchMaterials,
                            ),
                        ],
                    },
                },
                "exec_func": self._merge_duplicate_materials,
            },
        }

    def get_optimization_presets(self):
        """Return the optimization preset graph data."""

        return [
            {
                "name": "Optimize Preset #1",
                "data": {
                    "root": {
                        "node_id": "scene_graph_node",
                        "output_node_ids": [
                            "optimize_node1",
                            "optimize_node2",
                            "optimize_node3",
                        ],
                    },
                    "optimize_node1": {
                        "node_id": "optimize_geometries",
                        "output_node_ids": ["publish_node1"],
                    },
                    "optimize_node2": {
                        "node_id": "optimize_share_geometries",
                        "output_node_ids": ["publish_node2"],
                    },
                    "optimize_node3": {
                        "node_id": "optimize_merge",
                        "output_node_ids": ["publish_node3"],
                    },
                    "publish_node1": {
                        "node_id": "publish_file",
                    },
                    "publish_node2": {
                        "node_id": "publish_file",
                    },
                    "publish_node3": {
                        "node_id": "publish_file",
                    },
                },
            },
            {
                "name": "Optimize Preset #2",
                "data": {
                    "root": {
                        "node_id": "scene_graph_node",
                        "output_node_ids": [
                            "optimize_node1",
                            "optimize_node2",
                            "optimize_node3",
                        ],
                    },
                    "optimize_node1": {
                        "node_id": "optimize_geometries",
                        "output_node_ids": ["optimize_node5"],
                    },
                    "optimize_node2": {
                        "node_id": "optimize_share_geometries",
                        "output_node_ids": ["optimize_node4"],
                    },
                    "optimize_node3": {
                        "node_id": "optimize_merge",
                    },
                    "optimize_node4": {
                        "node_id": "material_remove_duplicates",
                        "output_node_ids": ["optimize_node6"],
                    },
                    "optimize_node5": {
                        "node_id": "geometry_tessellate",
                        "output_node_ids": ["optimize_node6"],
                    },
                    "optimize_node6": {
                        "node_id": "geometry_decore",
                        "output_node_ids": ["publish_node1"],
                    },
                    "publish_node1": {
                        "node_id": "publish_file",
                    },
                },
            },
            {
                "name": "Optimize Preset #3",
                "data": {
                    "root": {
                        "node_id": "file",
                        "output_node_ids": [
                            "o1",
                        ],
                    },
                    "o1": {
                        "node_id": "optimize_geometries",
                        "output_node_ids": [
                            "p1",
                        ],
                    },
                    "p1": {
                        "node_id": "publish_file",
                    },
                },
            },
        ]

    @staticmethod
    def get_settings_value(settings, name, default_value=None):
        """Return the value for the sepcified settings."""

        if name not in settings:
            return default_value

        settings_data = settings[name]
        if "value" in settings_data:
            return settings_data["value"]

        return settings_data.get("default", default_value)

    def _get_node_name(self, input_data, settings):
        """Return the node based on the settings data."""

        node_name = self.get_settings_value(settings, "node_name")

        # TODO standardize the node exec function return value

        return {"node_name": node_name}

    def _load_file(self, input_data, settings):
        """Load the file."""

        result = {}

        # First check if the file path is in the input data to restore
        file_path = input_data.get("_load_file_restore_file_path")

        # If not found, check the settings for user input
        if not file_path:
            file_path = self.get_settings_value(settings, "file_path")

            # Get the current file path (if there is one) to restore at a later point
            current_file_path = self.vredpy.vrFileIO.getFileIOFilePath()
            if current_file_path:
                result["_load_file_restore_file_path"] = current_file_path

        if not file_path:
            raise self.VREDOptimizationError("Missing required file path to load.")

        # Load the file
        success = self.vredpy.vrFileIO.load(
            [file_path],
            self.vredpy.vrScenegraph.getRootNode(),
            newFile=True,
            showImportOptions=False,
        )
        if not success:
            raise self.VREDOptimizationError(f"Failed to load file '{file_path}.")

        # result["node_name"] = self.vredpy.vrScenegraph.getRootNode().getName()
        return result

    def _save_temp_file(self, input_data, output_node):
        """Return the node based on the settings data."""

        node_name = input_data.get("node_name")

        if node_name:
            try:
                node = self.vredpy.get_nodes(node_name)[0]
            except IndexError:
                raise self.VREDOptimizationError(f"Failed to find node '{node_name}'")
        else:
            node = self.vredpy.vrScenegraph.getRootNode()

        # Get the current file path
        current_file_path = self.vredpy.vrFileIO.getFileIOFilePath()
        # If the current file has not been saved yet, raise an exception, or prompt user? Should this be checked before optimze steps even begin?
        if not current_file_path:
            raise VREDOptimizationHook.VREDOptimizationError(
                "Current file must be saved before proceeding."
            )

        node_name = node.getName()
        tempfile_name = f"{output_node.id}_{node_name}.vpb"
        tempfile_path = os.path.join(tempfile.gettempdir(), tempfile_name)

        # Save a copy of the data (to not modify the current)
        save_success = self.vredpy.vrFileIO.saveGeometry(node, tempfile_path)
        if not save_success:
            raise self.VREDOptimizationError("Failed to save temporary working file.")

        # Load the copy to work on
        load_success = self.vredpy.vrFileIO.load(
            [tempfile_path],
            self.vredpy.vrScenegraph.getRootNode(),
            newFile=True,
            showImportOptions=False,
        )
        if not load_success:
            raise self.VREDOptimizationError("Failed to load temporary working file.")

        # Get the new root node from the file just loaded
        root_node = self.vredpy.vrScenegraph.getRootNode()

        return {
            "temp_file_path": tempfile_path,
            "_save_temp_file_restore_file_path": current_file_path,
            "nodes": [root_node],
        }

    def _remove_temp_file(self, input_data, output_node):
        """Clean up function for save temp file."""

        success = True

        # Restore (load back) the original file
        if "_save_temp_file_restore_file_path" in input_data:
            file_path = input_data["_save_temp_file_restore_file_path"]
            success = self.vredpy.vrFileIO.load(
                [file_path],
                self.vredpy.vrScenegraph.getRootNode(),
                newFile=True,
                showImportOptions=False,
            )

        # Remove (temp) file
        if "temp_file_path" in input_data:
            file_path = input_data["temp_file_path"]
            if os.path.exists(file_path):
                os.remove(file_path)

        return success

    def _optimize_geometry(self, input_data, settings):
        """
        Optimize geometry to speed up rendering.

        :param input_node: Data to use for this optimization function.
        :type input_node: vrNodePtr
        :param settings: Settings option values to apply to the optimization function.
        :type settings: dict
        """

        input_data = input_data or {}

        if "nodes" in input_data:
            # Working straight off the current file (this may modify the current data)

            input_nodes = input_data["nodes"]
            if not input_nodes:
                raise VREDOptimizationHook.VREDOptimizationError(
                    "Missing required input node."
                )

            # This optimize method only expect a single node
            input_node = input_nodes[0]

            if not input_node:
                raise VREDOptimizationHook.VREDOptimizationError(
                    "Missing required input node."
                )

            if not isinstance(input_node, self.vredpy.vrNodePtr.vrNodePtr):
                raise VREDOptimizationHook.VREDOptimizationError(
                    "Input node must be of type vrNodePtr."
                )

        # Turn strips on or off in optimization. Default is True.
        strips = self.get_settings_value(settings, "strips", True)
        # Turn fans on or off in optimization. Default is True.
        fans = self.get_settings_value(settings, "fans", True)
        # Turn stitches on or off in optimization. Default is False.
        stitches = self.get_settings_value(settings, "stitches", False)

        success = self.vredpy.vrOptimize.optimizeGeometry(
            input_node, strips, fans, stitches
        )

        # Return the list of nodes to continue working on
        result = {"nodes": [input_node], "result": success}

        return result

    def _share_geometries(self, input_data, settings):
        """
        Share equal geometry nodes.

        :param input_node: The root node of the subgraph to be optimized. Defaults to the scene
            graph root node.
        :type input_node: vrNodePtr
        :param check_world_matrix: If True, only share the geometry when the world matrix of
        both nodes is equal.
        :type check_world_matrix: bool
        """

        input_data = input_data or {}

        if "nodes" in input_data:
            # Working straight off the current file (this may modify the current data)

            input_nodes = input_data["nodes"]
            if not input_nodes:
                raise VREDOptimizationHook.VREDOptimizationError(
                    "Missing required input node."
                )

            # This optimize method only expect a single node
            input_node = input_nodes[0]

            if not input_node:
                raise VREDOptimizationHook.VREDOptimizationError(
                    "Missing required input node."
                )

            if not isinstance(input_node, self.vredpy.vrNodePtr.vrNodePtr):
                raise VREDOptimizationHook.VREDOptimizationError(
                    "Input node must be of type vrNodePtr."
                )

        # elif "working_file_path" in input_data:
        #     # Load our data in from a file

        #     file_path = input_data["working_file_path"]
        #     node = input_data["node"]
        #     if not os.path.exists(file_path):
        #         # Save a copy of the data (to not modify the current)
        #         result = self.vredpy.vrFileIO.saveGeometry(node, file_path)
        #         # raise Exception("Bad file path")

        #     self.vredpy.vrFileIO.load(
        #         [file_path],
        #         self.vredpy.vrScenegraph.getRootNode(),
        #         newFile=True,
        #         showImportOptions=False,
        #     )
        #     # Now get our loaded file root node
        #     input_node = self.vredpy.vrScenegraph.getRootNode()

        check_world_matrix = self.get_settings_value(
            settings, "check_world_matrix", False
        )

        result = self.vredpy.vrOptimize.shareGeometries(input_node, check_world_matrix)

        # Return the list of nodes to continue working on
        result = {"nodes": [input_node], "result": result}

        return result

    def _merge_geometries(self, input_data, settings):
        """
        Merges geometry nodes.

        :param input_node: The root node of the subgraph to be optimized. Defaults to the scene
            graph root node.
        :type input_node: vrNodePtr
        """

        input_data = input_data or {}

        if "nodes" in input_data:
            # Working straight off the current file (this may modify the current data)

            input_nodes = input_data["nodes"]
            if not input_nodes:
                raise VREDOptimizationHook.VREDOptimizationError(
                    "Missing required input node."
                )

            # This optimize method only expect a single node
            input_node = input_nodes[0]

            if not input_node:
                raise VREDOptimizationHook.VREDOptimizationError(
                    "Missing required input node."
                )

            if not isinstance(input_node, self.vredpy.vrNodePtr.vrNodePtr):
                raise VREDOptimizationHook.VREDOptimizationError(
                    "Input node must be of type vrNodePtr."
                )

        # elif "working_file_path" in input_data:
        #     # Load our data in from a file

        #     file_path = input_data["working_file_path"]
        #     node = input_data["node"]
        #     if not os.path.exists(file_path):
        #         # Save a copy of the data (to not modify the current)
        #         result = self.vredpy.vrFileIO.saveGeometry(node, file_path)
        #         # raise Exception("Bad file path")

        #     self.vredpy.vrFileIO.load(
        #         [file_path],
        #         self.vredpy.vrScenegraph.getRootNode(),
        #         newFile=True,
        #         showImportOptions=False,
        #     )
        #     # Now get our loaded file root node
        #     input_node = self.vredpy.vrScenegraph.getRootNode()

        result = self.vredpy.vrOptimize.mergeGeometry(input_node)

        # Return the list of nodes to continue working on
        result = {"nodes": [input_node], "result": result}

        return result

    def _tessellate(self, input_data, settings):
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

        input_data = input_data or {}
        input_nodes = input_data.get("nodes")

        chordal_deviation = self.get_settings_value(
            settings, "chordal_deviation", 0.075
        )
        normal_tolerance = self.get_settings_value(settings, "normal_tolerance", 10.0)
        max_chord_len = self.get_settings_value(settings, "max_chord_len", 200)
        enable_stitching = self.get_settings_value(settings, "enable_stitching", True)
        stitching_tolerance = self.get_settings_value(
            settings, "stitching_tolerance", 0.1
        )
        preserve_uvs = self.get_settings_value(settings, "preserve_uvs", False)

        result = self.vredpy.vrGeometryEditor.tessellateSurfaces(
            input_nodes,
            chordal_deviation,
            normal_tolerance,
            max_chord_len,
            enable_stitching,
            stitching_tolerance,
            preserve_uvs,
        )

        return {"nodes": input_nodes, "result": result}

    def _decore(self, input_data, settings):
        """
        Decores the given objects with the given settings.

        :param nodes: The nodes to decore. Defaults to the root node.
        :type nodes: List[vrdNode]
        :param treat_as_combine_object: Defines if the given nodes are treated as combined objects or separately.
        :type treat_as_combine_object: bool
        :param settings: Settings for decoring objects.
        :type settings: vrdDecoreSettings
        """

        input_data = input_data or {}
        input_nodes = input_data.get("nodes")

        decore_settings = self.vredpy.get_decore_settings()
        # TODO update default settings with user settings
        decore_settings.setResolution(
            self.get_settings_value(
                settings, "resolution", decore_settings.getResolution()
            )
        )
        decore_settings.setQualitySteps(
            self.get_settings_value(
                settings, "quality_steps", decore_settings.getQualitySteps()
            )
        )
        decore_settings.setCorrectFaceNormals(
            self.get_settings_value(
                settings,
                "correct_face_normals",
                decore_settings.getCorrectFaceNormals(),
            )
        )
        decore_settings.setDecoreEnabled(
            self.get_settings_value(
                settings, "decore_enabled", decore_settings.getDecoreEnabled()
            )
        )

        decore_mode = self.get_settings_value(
            settings, "decore_mode", decore_settings.getDecoreMode()
        )
        if isinstance(decore_mode, int):
            decore_mode = self.vredpy.vrGeometryTypes.DecoreMode(decore_mode)
        decore_settings.setDecoreMode(decore_mode)

        sub_object_mode = self.get_settings_value(
            settings, "sub_object_mode", decore_settings.getSubObjectMode()
        )
        if isinstance(sub_object_mode, int):
            sub_object_mode = self.vredpy.vrGeometryTypes.DecoreSubObjectMode(
                sub_object_mode
            )
        decore_settings.setSubObjectMode(sub_object_mode)

        transparent_object_mode = self.get_settings_value(
            settings,
            "transparent_object_mode",
            decore_settings.getTransparentObjectMode(),
        )
        if isinstance(transparent_object_mode, int):
            transparent_object_mode = (
                self.vredpy.vrGeometryTypes.DecoreTransparentObjectMode(
                    transparent_object_mode
                )
            )
        decore_settings.setTransparentObjectMode(transparent_object_mode)

        treat_as_combine_object = self.get_settings_value(
            settings, "treat_as_combine_object", True
        )

        result = self.vredpy.vrDecoreService.decore(
            input_nodes, treat_as_combine_object, decore_settings
        )

        return {"nodes": input_nodes, "result": result}

    def _merge_duplicate_materials(self, input_data, settings):
        """Optimize the scene by merging duplicate materials."""

        merge_options = self.get_settings_value(
            settings, "merge_options", self.vredpy.vrMaterialTypes.MergeOptions.Default
        )
        if isinstance(merge_options, int):
            merge_options = self.vredpy.vrMaterialTypes.MergeOptions(merge_options)

        result = self.vredpy.vrMaterialService.mergeDuplicateMaterials(merge_options)

        return {"result": result}

    def _save_file(self, input_data, settings):
        """Save the current VRED file to disk."""

        input_data = input_data or {}
        input_nodes = input_data.get("nodes", [])

        root_node = input_nodes[0] if input_nodes else None
        # NOTE debug - save geoemtry for specific node sometimes fails..?
        root_node = None

        file_path = self.get_settings_value(settings, "file_path")
        if file_path is None:
            raise Exception("Must specify a file path!")

        file_name = self.get_settings_value(settings, "file_name")
        full_path = os.path.join(file_path, file_name)

        if root_node:
            # Saves the geometry from the root node to the filepath
            # TODO check the root node is vrNodePtr?
            success = self.vredpy.vrFileIO.saveGeometry(root_node, full_path)
        else:
            # Save the file
            success = self.vredpy.vrFileIO.save(full_path)

        if not success:
            raise self.VREDOptimizationError(f"Failed to save output file {full_path}")

        return success

    def _publish_file(self, input_data, settings):
        """Save the current VRED file to disk."""

        # TODO get publish app api to do the publish - for now just save it

        return self._save_file(input_data, settings)
