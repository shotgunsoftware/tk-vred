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

    def get_optimization_presets(self):
        """Return the optimization data."""

        # TODO define config as nested dicts instead of having to list out the outputs by name?

        preset_option1 = {
            "root_node": {
                "outputs": [
                    "optimize_geometries",
                    "optimize_share_geometries",
                    "optimize_merge",
                ],
                "name": "Input",
                "description": "An input node to optimization node",
                "settings": {
                    "node_name": {
                        "name": "Node",
                        "type": str,
                        "default": "Root",
                    },
                },
                "exec_func": self._save_temp_file,
            },
            "optimize_geometries": {
                "name": "Optimize Geometries",
                "description": "Optimizes the geometry structure.",
                "outputs": ["publish_optimize_geometries"],
                "exec_func": self._optimize_geometry,
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
            },
            "optimize_share_geometries": {
                "name": "Optimize/Share Geometries",
                "description": "Optimizes the geometry structure and tries to share duplicated geometries.",
                "outputs": ["publish_optimize_share_geometries"],
                "exec_func": self._share_geometries,
                "settings": {
                    "check_world_matrix": {
                        "name": "Check World Matrix",
                        "type": bool,
                        "default": False,
                    },
                },
            },
            "optimize_merge": {
                "name": "Merge/Optimize/Share Geometries",
                "description": "This is much more aggressive and changes the scenegraph structure.",
                "outputs": ["publish_optimize_merge"],
                "exec_func": self._merge_geometries,
            },
            "publish_optimize_geometries": {
                "name": "Publish File",
                "description": "Publish the current file.",
                "exec_func": self._publish_file,
                "settings": {
                    "file_name": {
                        "name": "File Name",
                        "type": str,
                        "default": "output_1.vpb",
                    },
                    "file_path": {
                        "name": "File Path",
                        "type": str,
                        "default": self.vredpy.vrFileIO.getFileIOFilePath()
                        or "C:\\Users\\oues",
                    },
                },
            },
            "publish_optimize_share_geometries": {
                "name": "Publish File",
                "description": "Publish the current file.",
                "exec_func": self._publish_file,
                "settings": {
                    "file_name": {
                        "name": "File Name",
                        "type": str,
                        "default": "output_2.vpb",
                    },
                    "file_path": {
                        "name": "File Path",
                        "type": str,
                        "default": self.vredpy.vrFileIO.getFileIOFilePath()
                        or "C:\\Users\\oues",
                    },
                },
            },
            "publish_optimize_merge": {
                "name": "Publish File",
                "description": "Publish the current file.",
                "exec_func": self._publish_file,
                "settings": {
                    "file_name": {
                        "name": "File Name",
                        "type": str,
                        "default": "output_3.vpb",
                    },
                    "file_path": {
                        "name": "File Path",
                        "type": str,
                        "default": self.vredpy.vrFileIO.getFileIOFilePath()
                        or "C:\\Users\\oues",
                    },
                },
            },
        }
        preset_option2 = {
            "root_node": {
                "outputs": [
                    "optimize_geometries",
                    "optimize_share_geometries",
                    "optimize_merge",
                ],
                "name": "Input Node",
                "description": "An input node to optimization node",
                "settings": {
                    "node_name": {
                        "name": "Name",
                        "type": str,
                        "default": "Root",
                    },
                },
                "exec_func": self._get_node,
            },
            # "write": {
            #     "name": "Save File",
            #     "description": "Save current VRED file to disk.",
            #     "exec_func": self._save_file,
            #     "settings": {
            #         "file_path": {
            #             "name": "Path",
            #             "type": str,
            #             "default": self.vredpy.vrFileIO.getFileIOFilePath(),
            #         },
            #     },
            # },
            "publish": {
                "name": "Publish File",
                "description": "Publish the current file.",
                "exec_func": self._publish_file,
                "settings": {
                    "file_path": {
                        "name": "Path",
                        "type": str,
                        "default": self.vredpy.vrFileIO.getFileIOFilePath(),
                    },
                },
            },
            "optimize_geometries": {
                "name": "Optimize Geometries",
                "description": "Optimizes the geometry structure.",
                "outputs": ["geometry_tessellate"],
                "exec_func": self._optimize_geometry,
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
            },
            "optimize_share_geometries": {
                "name": "Optimize/Share Geometries",
                "description": "Optimizes the geometry structure and tries to share duplicated geometries.",
                "outputs": ["material_remove_duplicates"],
                "exec_func": self._share_geometries,
                "settings": {
                    "check_world_matrix": {
                        "name": "Check World Matrix",
                        "type": bool,
                        "default": False,
                    },
                },
            },
            "optimize_merge": {
                "name": "Merge/Optimize/Share Geometries",
                "description": "This is much more aggressive and changes the scenegraph structure.",
                "outputs": [],
                "exec_func": self._merge_geometries,
            },
            "geometry_tessellate": {
                "name": "Tessellate",
                "description": "Tessellate the geometry.",
                "outputs": ["geometry_decore"],
                "exec_func": self._tessellate,
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
            },
            "geometry_decore": {
                "name": "Decore",
                "description": "Decore the geometry.",
                "outputs": [
                    # "write",
                    "publish",
                ],
                "exec_func": self._decore,
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
            },
            "material_remove_duplicates": {
                "name": "Remove Duplicate Materials",
                "description": "Share materials and remove duplicate",
                "outputs": [
                    "geometry_decore",
                ],
                "exec_func": self._merge_duplicate_materials,
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
            },
        }

        return {
            "Optimize Preset #1": preset_option1,
            "Optimize Preset #2": preset_option2,
        }

    @staticmethod
    def get_settings_value(settings, name, default_value=None):
        """Return the value for the sepcified settings."""

        if name not in settings:
            return default_value

        settings_data = settings[name]
        if "value" in settings_data:
            return settings_data["value"]

        return settings_data.get("default", default_value)

    def _get_node(self, input_data, settings):
        """Return the node based on the settings data."""

        node_name = self.get_settings_value(settings, "node_name")

        if not node_name:
            return  # or raise an exception?

        result = self.vredpy.get_nodes(node_name)

        # TODO standardize the node exec function return value
        return {"nodes": result}

    def _save_temp_file(self, input_data, settings):
        """Return the node based on the settings data."""

        node_name = self.get_settings_value(settings, "node_name")

        if not node_name:
            return  # or raise an exception?

        node = self.vredpy.get_nodes(node_name)[0]
        node_file_name = "{}.vpb".format(node_name)
        node_tempfile_path = os.path.join(tempfile.gettempdir(), node_file_name)
        current_file_path = self.vredpy.vrFileIO.getFileIOFilePath()

        # Save a copy of the data (to not modify the current)
        # result = self.vredpy.vrFileIO.saveGeometry(node, node_tempfile_path)

        # TODO standardize the node exec function return value
        # return {"nodes": result}
        return {
            "working_file_path": node_tempfile_path,
            "current_file_path": current_file_path,
            "node": node,
            # "result": result
        }

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

        elif "working_file_path" in input_data:
            # Load our data in from a file

            file_path = input_data["working_file_path"]
            node = input_data["node"]
            if not os.path.exists(file_path):
                # Save a copy of the data (to not modify the current)
                result = self.vredpy.vrFileIO.saveGeometry(node, file_path)
                # raise Exception("Bad file path")

            self.vredpy.vrFileIO.load(
                [file_path],
                self.vredpy.vrScenegraph.getRootNode(),
                newFile=True,
                showImportOptions=False,
            )
            # Now get our loaded file root node
            input_node = self.vredpy.vrScenegraph.getRootNode()

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

        # Forward the current path to restore at some point
        if "current_file_path" in input_data:
            result["current_file_path"] = input_data["current_file_path"]

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

        elif "working_file_path" in input_data:
            # Load our data in from a file

            file_path = input_data["working_file_path"]
            node = input_data["node"]
            if not os.path.exists(file_path):
                # Save a copy of the data (to not modify the current)
                result = self.vredpy.vrFileIO.saveGeometry(node, file_path)
                # raise Exception("Bad file path")

            self.vredpy.vrFileIO.load(
                [file_path],
                self.vredpy.vrScenegraph.getRootNode(),
                newFile=True,
                showImportOptions=False,
            )
            # Now get our loaded file root node
            input_node = self.vredpy.vrScenegraph.getRootNode()

        check_world_matrix = self.get_settings_value(
            settings, "check_world_matrix", False
        )

        result = self.vredpy.vrOptimize.shareGeometries(input_node, check_world_matrix)

        # Return the list of nodes to continue working on
        result = {"nodes": [input_node], "result": result}

        # Forward the current path to restore at some point
        if "current_file_path" in input_data:
            result["current_file_path"] = input_data["current_file_path"]

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

        elif "working_file_path" in input_data:
            # Load our data in from a file

            file_path = input_data["working_file_path"]
            node = input_data["node"]
            if not os.path.exists(file_path):
                # Save a copy of the data (to not modify the current)
                result = self.vredpy.vrFileIO.saveGeometry(node, file_path)
                # raise Exception("Bad file path")

            self.vredpy.vrFileIO.load(
                [file_path],
                self.vredpy.vrScenegraph.getRootNode(),
                newFile=True,
                showImportOptions=False,
            )
            # Now get our loaded file root node
            input_node = self.vredpy.vrScenegraph.getRootNode()

        result = self.vredpy.vrOptimize.mergeGeometry(input_node)

        # Return the list of nodes to continue working on
        result = {"nodes": [input_node], "result": result}

        # Forward the current path to restore at some point
        if "current_file_path" in input_data:
            result["current_file_path"] = input_data["current_file_path"]

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

        file_path = self.get_settings_value(settings, "file_path")
        if file_path is None:
            raise Exception("Must specify a file path!")

        file_name = self.get_settings_value(settings, "file_name")
        full_path = os.path.join(file_path, file_name)

        if root_node:
            # Saves the geometry from the root node to the filepath
            # TODO check the root node is vrNodePtr?
            self.vredpy.vrFileIO.saveGeometry(root_node, full_path)
        else:
            # Save the file
            self.vredpy.vrFileIO.save(full_path)

        # Check if our current working file is a temp file - if so, delete it.
        # NOTE should we forward the "working path" as we do wtih the current path?
        current_file_path = self.vredpy.vrFileIO.getFileIOFilePath()
        if current_file_path.startswith(tempfile.gettempdir()):
            os.remove(current_file_path)

        # NOTE a node may want a clean up op (since it would be easier maintenance for the creator to then delete it)
        if "current_file_path" in input_data:
            # Restore the original path now that we're done

            success = self.vredpy.vrFileIO.load(
                [input_data["current_file_path"]],
                self.vredpy.vrScenegraph.getRootNode(),
                newFile=True,
                showImportOptions=False,
            )

    def _publish_file(self, input_data, settings):
        """Save the current VRED file to disk."""

        # TODO get publish app api to do the publish - for now just save it

        self._save_file(input_data, settings)
