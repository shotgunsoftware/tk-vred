# Copyright (c) 2021 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import json
import os

import sgtk


HookBaseClass = sgtk.get_hook_baseclass()


class VredActions(HookBaseClass):
    """Hook that loads defines all the available actions, broken down by publish type."""

    def __init__(self, *args, **kwargs):
        """Initialize the hook."""

        super(VredActions, self).__init__(*args, **kwargs)

        self.vredpy = self.parent.engine.vredpy

    ##############################################################################################################
    # public interface - to be overridden by deriving classes

    def generate_actions(self, sg_publish_data, actions, ui_area):
        """
        Returns a list of action instances for a particular publish.
        This method is called each time a user clicks a publish somewhere in the UI.
        The data returned from this hook will be used to populate the actions menu for a publish.

        The mapping between Publish types and actions are kept in a different place
        (in the configuration) so at the point when this hook is called, the loader app
        has already established *which* actions are appropriate for this object.

        The hook should return at least one action for each item passed in via the
        actions parameter.

        This method needs to return detailed data for those actions, in the form of a list
        of dictionaries, each with name, params, caption and description keys.

        Because you are operating on a particular publish, you may tailor the output
        (caption, tooltip etc) to contain custom information suitable for this publish.

        The ui_area parameter is a string and indicates where the publish is to be shown.
        - If it will be shown in the main browsing area, "main" is passed.
        - If it will be shown in the details area, "details" is passed.
        - If it will be shown in the history area, "history" is passed.

        Please note that it is perfectly possible to create more than one action "instance" for
        an action! You can for example do scene introspection - if the action passed in
        is "character_attachment" you may for example scan the scene, figure out all the nodes
        where this object can be attached and return a list of action instances:
        "attach to left hand", "attach to right hand" etc. In this case, when more than
        one object is returned for an action, use the params key to pass additional
        data into the run_action hook.

        :param sg_publish_data: ShotGrid data dictionary with all the standard publish fields.
        :param actions: List of action strings which have been defined in the app configuration.
        :param ui_area: String denoting the UI Area (see above).
        :returns List of dictionaries, each with keys name, params, caption and description
        """

        self.logger.debug(
            "Generate actions called for UI element {ui}"
            "Actions: {actions}"
            "Publish Data: {data}".format(
                ui=ui_area, actions=actions, data=sg_publish_data
            )
        )

        action_instances = []
        try:
            # call base class first
            action_instances += HookBaseClass.generate_actions(
                self, sg_publish_data, actions, ui_area
            )
        except AttributeError:
            # base class doesn't have the method, so ignore and continue
            pass

        if "smart_reference" in actions:
            action_instances.append(
                {
                    "name": "smart_reference",
                    "params": None,
                    "caption": "Create Smart Reference",
                    "description": "This will import the item to the universe as a smart reference.",
                }
            )

        if "import" in actions:
            action_instances.append(
                {
                    "name": "import",
                    "params": None,
                    "caption": "Import into Scene",
                    "description": "This will import the item into the current VRED Scene.",
                }
            )

        if "import_with_options" in actions:
            if (
                self.parent.engine._version_check(
                    self.parent.engine.vred_version, "2022.1"
                )
                >= 0
            ):
                action_instances.append(
                    {
                        "name": "import_with_options",
                        "params": None,
                        "caption": "Open Import Dialog to change options...",
                        "description": "This will open the Import Options Dialog.",
                    }
                )
            else:
                self.logger.debug(
                    "Not able to add import_with_options to Loader actions. "
                    "This capability requires VRED 2022.1 or later."
                )

        if "import_sceneplate" in actions:
            action_instances.append(
                {
                    "name": "import_sceneplate",
                    "params": None,
                    "caption": "Import image(s) into scene as a sceneplate",
                    "description": "This will import the image(s) into the current VRED Scene.",
                }
            )

        if "import_metadata" in actions:
            action_instances.append(
                {
                    "name": "import_metadata",
                    "params": None,
                    "caption": "Load Metadata",
                    "description": "Load the metadata into VRED from the file.",
                }
            )

        if "import_metadata_set" in actions:
            action_instances.append(
                {
                    "name": "import_metadata_set",
                    "params": None,
                    "caption": "Apply Metadata Set",
                    "description": "Load the Metdata Set into VRED from the file.",
                }
            )

        if "import_material" in actions:
            action_instances.append(
                {
                    "name": "import_material",
                    "params": None,
                    "caption": "Load Material",
                    "description": "Load the material into VRED from the file.",
                }
            )

        if "import_material_asset" in actions:
            action_instances.append(
                {
                    "name": "import_material_asset",
                    "params": None,
                    "caption": "Load Material Asset",
                    "description": "Load the VRED Material Asset.",
                }
            )

        if "apply_to_nodes" in actions:
            action_instances.append(
                {
                    "name": "apply_to_nodes",
                    "params": None,
                    "caption": "Apply to Selected Nodes",
                    "description": "Apply the material to the selected nodes.",
                }
            )

        if "apply_to_scene" in actions:
            action_instances.append(
                {
                    "name": "apply_to_scene",
                    "params": None,
                    "caption": "Apply to Scene by Name",
                    "description": "Apply the material to the scene by name.",
                }
            )

        if "open_file_system" in actions:
            action_instances.append(
                {
                    "name": "open_file_system",
                    "params": None,
                    "caption": "Open in Explorer",
                    "description": "Show in the local file system.",
                }
            )
        
        # NOTE requires bulk operations
        # if "export_to_library" in actions:
        #     action_instances.append(
        #         {
        #             "name": "export_to_library",
        #             "params": {"bulk_operation": True},
        #             "caption": "Export to Material Library",
        #             "description": "Create a Material Library with selected item or add to existing.",
        #         }
        #     )

        return action_instances

    def execute_action(self, name, params, sg_publish_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.

        :param name: Action name string representing one of the items returned by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_publish_data: ShotGrid data dictionary with all the standard publish fields.
        :returns: No return value expected.
        """

        self.logger.debug(
            "Execute action called for action {name}"
            "Parameters: {params}"
            "Publish Data: {data}".format(
                name=name, params=params, data=sg_publish_data
            )
        )

        path = self.get_publish_path(sg_publish_data)

        if name == "smart_reference":
            self.create_smart_reference(path)

        elif name == "import":
            self.import_file(path)

        elif name == "import_with_options":
            self.open_import_dialog(path)

        elif name == "import_sceneplate":
            image_path = self.get_publish_path(sg_publish_data)
            self.import_sceneplate(image_path)

        elif name == "import_metadata":
            self._import_metadata(path, sg_publish_data)

        elif name == "import_metadata_set":
            self._import_metadata_set(path, sg_publish_data)

        # Material actions
        elif name == "import_material":
            self._import_material(path, sg_publish_data)
        elif name == "import_material_asset":
            self._import_material(path, sg_publish_data)
        elif name == "apply_to_nodes":
            self._apply_material_to_selected_nodes(path)
        elif name == "apply_to_scene":
            self._apply_material_to_scene_by_name(path)
        elif name == "open_file_system":
            self._open_in_explorer(path)

    def execute_multiple_actions(self, actions):
        """
        Executes the specified action on a list of items.

        The default implementation dispatches each item from ``actions`` to
        the ``execute_action`` method.

        The ``actions`` is a list of dictionaries holding all the actions to execute.
        Each entry will have the following values:

            name: Name of the action to execute
            sg_publish_data: Publish information coming from ShotGrid
            params: Parameters passed down from the generate_actions hook.

        .. note::
            This is the default entry point for the hook. It reuses the ``execute_action``
            method for backward compatibility with hooks written for the previous
            version of the loader.

        .. note::
            The hook will stop applying the actions on the selection if an error
            is raised midway through.

        :param list actions: Action dictionaries.
        """
        for single_action in actions:
            name = single_action["name"]
            sg_publish_data = single_action["sg_publish_data"]
            params = single_action["params"]
            self.execute_action(name, params, sg_publish_data)

    def import_sceneplate(self, image_path):
        """
        Executes the import of the image(s) and the creation
        of the VRED sceneplate

        :param str image_path: Path to image file from the sg_published_data
        """

        self.logger.debug(
            "Import sceneplate for image file '{path}'".format(path=image_path)
        )

        # Get the Sceneplate Root object
        vredSceneplateRoot = self.vredpy.vrSceneplateService.getRootNode()

        # Extract the filename for the name of the Sceneplate
        nodeName = os.path.basename(image_path)

        # Load in the image
        imageObject = self.vredpy.vrImageService.loadImage(image_path)

        # Create the actual Sceneplate node
        newSceneplateNode = self.vredpy.vrSceneplateService.createNode(
            vredSceneplateRoot,
            self.vredpy.vrSceneplateTypes.NodeType.Frontplate,
            nodeName,
        )
        newSceneplate = self.vredpy.vrdSceneplateNode(newSceneplateNode)

        # Set the type to image
        newSceneplate.setContentType(self.vredpy.vrSceneplateTypes.ContentType.Image)

        # Assign the image to the Sceneplate
        newSceneplate.setImage(imageObject)

    def create_smart_reference(self, path):
        """
        Create a smart reference for the given path

        :param path: Path to the file to import as smart reference
        """

        self.logger.debug("Creating smart reference for path {}".format(path))

        # extract the node name from the reference path
        ref_name = os.path.splitext(os.path.basename(path))[0]

        # create the smart ref, load it and finally change the node name to reflect the ref path
        ref_node = self.vredpy.vrReferenceService.createSmart()
        ref_node.setSmartPath(path)
        ref_node.load()
        ref_node.setName(ref_name)

    def import_file(self, path):
        """
        :param path: Path of file to import
        """

        parent = self.vredpy.vrScenegraph.getRootNode()
        self.vredpy.vrFileIOService.importFiles([path], parent)

    def open_import_dialog(self, path):
        """
        :param path: Path to the file to display import options for
        """

        self.vredpy.vrGUIService.openImportDialog([path])

    def _import_metadata(self, path, sg_publish_data=None):
        """Import the VRED Metadata."""

        if not hasattr(self.vredpy, "vrMetadataService"):
            error_msg = "Failed to import VRED Metadata - the current running version of VRED does not support metadata."
            self.logger.error(error_msg)
            raise Exception(error_msg)

        if not os.path.isfile(path):
            error_msg = "Failed to import VRED Metadata - metadata file path invalid."
            self.logger.error(error_msg)
            raise Exception(error_msg)

        with open(path, "r+") as fp:
            metadata = json.load(fp)
            for node_name, node_metadata in metadata.items():
                node = self.vredpy.vrNodeService.findNode(node_name)
                if not node:
                    error_msg = f"Failed to import VRED Metadata - node '{node_name}' not found ."
                    self.logger.error(error_msg)
                    continue
                metadata = self.vredpy.vrMetadataService.getMetadata(node)
                object_set = metadata.getObjectSet()
                for key, value in node_metadata.items():
                    object_set.setValue(key, value)

    def _import_metadata_set(self, path, sg_publish_data=None):
        """Import the VRED Metadata Set."""

        # TODO do not load if metadata set already exists

        if not hasattr(self.vredpy, "vrMetadataService"):
            error_msg = "Failed to import VRED Metadata Set - the current running version of VRED does not support metadata."
            self.logger.error(error_msg)
            raise Exception(error_msg)

        if not os.path.isfile(path):
            error_msg = "Failed to import VRED Metadata Set - metadata file path invalid."
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        metadata_set_name = sg_publish_data.get("name")
        if not metadata_set_name:
            error_msg = "Failed to import VRED Metadata Set - missing name."
            self.logger.error(error_msg)
            raise Exception(error_msg)

        existing_sets = self.vredpy.vrMetadataService.findSets(metadata_set_name)
        if existing_sets:
            # TODO ask to delete first or not continue
            self.vredpy.vrMetadataService.deleteSets(existing_sets)
            # warning_msg = "Metadata Set already exists."
            # self.logger.warning(warning_msg)
            # raise Exception(warning_msg)

        # TODO assign metadata set to objects
        objects = [] 
        metadata_set = self.vredpy.vrMetadataService.createSet(metadata_set_name, objects)

        metadata = None
        with open(path, "r+") as fp:
            metadata = json.load(fp)

        if not metadata:
            warning_msg = "No metadata found."
            self.logger.warning(warning_msg)
            raise Exception(warning_msg)

        # 
        # FIXME clean this up
        #

        # Load all materials first
        materials = metadata.get("SG_materials", [])
        filters = []
        entity_type = None
        for material in materials:
            material_data = json.loads(material)
            project_data = material_data["project"]
            entity_type = material_data["type"]
            filters.append(
                {
                    "filter_operator": "and",
                    "filters": [
                        ["id", "is", material_data["id"]],
                        ["project", "is", project_data],
                    ],
                }
            )
                    
        if filters:
            filter_value = [{
                "filter_operator": "any",
                "filters": filters,
            }]
            materials = self.parent.shotgun.find(
                entity_type,
                filter_value,
                fields=["code", "path"],
            )
            for material_publish_data in materials:
                path = self.get_publish_path(material_publish_data)
                self._import_material(path, material_publish_data)

        # Load metadata sets and apply metadata to nodes
        for set_key, set_value in metadata.items():
            metadata_set.setValue(set_key, set_value)
            node = self.vredpy.vrNodeService.findNode(set_key)
            if node and node.isValid():
                metadata = self.vredpy.vrMetadataService.getMetadata(node)
                object_set = metadata.getObjectSet()
                values = json.loads(set_value)
                for key, value in values.items():
                    object_set.setValue(key, value)
                    # TODO apply the metadata to the node, e.g. apply material, texture, color, etc...
                    if key == "material":
                        if isinstance(value, dict):
                            material = self.vredpy.find_material_by_metadata(value)
                        else:
                            material = self.vredpy.vrMaterialService.findMaterial(value)
                        if material:
                            node.applyMaterial(material)

    def _import_material(self, path, sg_publish_data=None):
        """Import the VRED Material."""

        # TODO check if already imported/loaded

        # First try to import the material as a VRED Material Asset
        material = self._import_material_asset(path)

        if material and material.isValid():
            # Convert v1 vrMaterialPtr to v2 vrdMaterial
            material_v2 = self.vredpy.get_material_v2(material)
            materials = [material_v2]
        else:
            # NOTE this is a reason to use material assets - guarantees one material per asset/file
            # Import materials from file path
            if not os.path.isfile(path):
                return
            materials = self.vredpy.vrMaterialService.loadMaterials([path])

        # Create metadata for material (for Scene Breakdown2 referencing), if data given
        if sg_publish_data:
            self.vredpy.add_metadata_to_materials(materials, sg_publish_data)

        return materials

    def _import_material_asset(self, path):
        """Load the VRED Material Asset."""

        if not path:
            return

        name = self.vredpy.get_material_asset_name_from_path(path)
        return self.vredpy.vrAssetsModule.loadMaterialAssetByName(name, path)

    def _apply_material_to_selected_nodes(self, path):
        """ """

        # TODO move to vrepdy

        nodes = self.vredpy.vrScenegraphService.getSelectedNodes()
        if not nodes:
            return

        materials = self._import_material(path)
        if not materials:
            return

        material = materials[0]
        self.vredpy.vrMaterialService.applyMaterialToNodes(material, nodes)

    def _apply_material_to_scene_by_name(self, path):
        """ """

        # TODO move to vrepdy

        # Update nodes to use the new material
        materials = self._import_material(path)
        materials_to_remove = []
        for material in materials:
            existing_materials = self.vredpy.vrMaterialService.findMaterials(
                material.getName()
            )
            if not existing_materials:
                continue
            for existing_material in existing_materials:
                nodes = self.vredpy.vrMaterialService.findNodesWithMaterial(
                    existing_material
                )
                if not nodes:
                    continue
                self.vredpy.vrMaterialService.applyMaterialToNodes(material, nodes)
            materials_to_remove.extend(existing_materials)

        # Remove the old materials
        self.vredpy.vrMaterialService.deleteMaterials(materials_to_remove)

    def _open_in_explorer(self, path):
        """ """

        # Taken from workfiles
        if not sgtk.util.is_windows():
            return

        if os.path.isfile(path):
            path = os.path.dirname(path)
        cmd = 'cmd.exe /C start "Folder" "%s"' % path

        exit_code = os.system(cmd)
        if exit_code != 0:
            # Log error
            pass
    