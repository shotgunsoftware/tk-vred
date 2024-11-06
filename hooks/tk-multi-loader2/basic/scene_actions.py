# Copyright (c) 2021 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import os
import sgtk
from sgtk.platform.qt import QtCore, QtGui


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

        :param sg_publish_data: Flow Production Tracking data dictionary with all the standard publish fields.
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

        if "import_as_env" in actions:
            action_instances.append(
                {
                    "name": "import_as_env",
                    "params": None,
                    "caption": "Import as Environment",
                    "description": "This will create an enviornment node and add it to the VRED scenegraph under Environments.",
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

        return action_instances

    def execute_action(self, name, params, sg_publish_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.

        :param name: Action name string representing one of the items returned by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_publish_data: Flow Production Tracking data dictionary with all the standard publish fields.
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

        elif name == "import_as_env":
            self.import_envs([path])

        elif name == "import_with_options":
            self.open_import_dialog(path)

        elif name == "import_sceneplate":
            image_path = self.get_publish_path(sg_publish_data)
            self.import_sceneplate(image_path)

    def execute_multiple_actions(self, actions):
        """
        Executes the specified action on a list of items.

        The default implementation dispatches each item from ``actions`` to
        the ``execute_action`` method.

        The ``actions`` is a list of dictionaries holding all the actions to execute.
        Each entry will have the following values:

            name: Name of the action to execute
            sg_publish_data: Publish information coming from Flow Production Tracking
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

        batch_actions = {
            "import": {
                "paths": [],
                "func": self.import_files,
            },
            "import_as_env": {
                "paths": [],
                "func": self.import_envs,
            },
            "import_with_options": {
                "paths": [],
                "func": self.open_import_batch_dialog,
            },
        }

        for action in actions:
            name = action["name"]
            sg_publish_data = action["sg_publish_data"]
            if name in batch_actions:
                # This action must be executed in a single batch function
                path = self.get_publish_path(sg_publish_data)
                batch_actions[name]["paths"].append(path)
            else:
                # This action can be executed in multiple single functions
                params = action["params"]
                self.execute_action(name, params, sg_publish_data)

        # Execute batch functions now that the data has been gatheredt
        for batch_action in batch_actions.values():
            paths = batch_action["paths"]
            if not paths:
                continue  # No data, do not execute function
            batch_action["func"](paths)

    def import_sceneplate(self, image_path):
        """
        Executes the import of the image(s) and the creation
        of the VRED sceneplate

        :param str image_path: Path to image file from the sg_published_data
        """

        self.logger.debug(
            "Import sceneplate for image file '{path}'".format(path=image_path)
        )

        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
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
            newSceneplate.setContentType(
                self.vredpy.vrSceneplateTypes.ContentType.Image
            )

            # Assign the image to the Sceneplate
            newSceneplate.setImage(imageObject)
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def create_smart_reference(self, path):
        """
        Create a smart reference for the given path

        :param path: Path to the file to import as smart reference
        """

        self.logger.debug("Creating smart reference for path {}".format(path))

        # extract the node name from the reference path
        ref_name = os.path.splitext(os.path.basename(path))[0]

        # create the smart ref, load it and finally change the node name to reflect the ref path
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            ref_node = self.vredpy.vrReferenceService.createSmart()
            ref_node.setSmartPath(path)
            ref_node.load()
            ref_node.setName(ref_name)
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def import_envs(self, paths):
        """
        Import the list of files into VRED as environments.

        :param paths: The file paths to import
        :type paths: List[str]
        """

        def __on_envs_imported(env_group_node):
            """
            Callback triggered after the environments have been imported.

            Move all nodes in the given group node, to the Environments node in
            the VRED scenegraph. Delete the temporary group node.

            :param env_group_node: The temporary group node that contains the
                imported environments.
            """

            if not env_group_node:
                return

            # Ensure we have a vrdNode object
            if isinstance(env_group_node, self.vredpy.vrNodePtr.vrNodePtr):
                env_group_node = self.vredpy.vrNodeService.getNodeFromId(
                    env_group_node.getID()
                )

            # Post process the imported environments:
            #
            # Move all imported environment materials to the default environment
            # switch material. Ensure this does not auto-create a node in the
            # scenegraph.
            # Ensure that the imported environment nodes are added to the
            # default environment switch node in the scenegraph (this should be
            # done automatically by moving the materials to the default
            # environment switch material).
            # If it is desirable to set the imported environment to geometry,
            # assign the default environment switch material to the geometries
            #
            # This is the manual process that
            # vrAssetsModule.loadEnvironmentAssetByName performs. We could use
            # this if it is guaranteed that the envrionment is a VRED Asset.
            for env_node in env_group_node.children:
                m = self.vredpy.vrMaterialService.findMaterial(env_node.getName())
                env_material = self.vredpy.vrdEnvironmentMaterial(m)
                self.vredpy.vrMaterialService.addToDefaultEnvironmentSwitch(
                    env_material
                )

            # Remove the temporary group node and update the scenegraph
            self.vredpy.vrNodeService.removeNodes([env_group_node])
            self.vredpy.vrScenegraph.updateScenegraph(True)

        # Create a temporary group node to place the imported environments. The
        # environments are imported async, so this is how we can find them after
        # the import is finished.
        root_node = self.vredpy.vrScenegraph.getRootNode()
        unique_name = self.vredpy.vrNodeService.getUniqueName(
            "FPTR_Imported_Envs", root_node
        )
        temp_group_node = self.vredpy.vrScenegraph.createNode(
            "Group", unique_name, root_node
        )

        # Set the environment import option to 'merge'. Save the current option
        # and restore it after the import is done.
        settings = self.vredpy.vrdProjectMergeSettings()
        restore_option = settings.getEnvironmentImportOption()
        settings.setEnvironmentImportOption(3)
        # Import will be done async, set up signal/slot to post process the
        # imported environments. This signal is disconnected after it is
        # triggered.
        if self.parent.engine.notifier:
            self.__connect_once(
                self.parent.engine.notifier.file_import_finished,
                lambda: __on_envs_imported(temp_group_node),
            )
        else:
            self.logger.error(
                "Failed to connect environment import finished signal/slot. Environments may not be imported correctly."
            )

        # Import the environments from the given paths
        try:
            self.parent.engine.import_files(paths, root_node=temp_group_node)
        finally:
            settings.setEnvironmentImportOption(restore_option)

    def import_files(self, paths):
        """
        Import the list of files into VRED.

        :param paths: The file paths to import
        :type paths: List[str]
        """

        self.parent.engine.import_files(paths)

    def import_file(self, path):
        """
        Import the file into VRED.

        :param path: Path of file to import
        :type path: str
        """

        self.import_files([path])

    def open_import_batch_dialog(self, paths):
        """
        Import the list of file into VRED using the import dialog.

        :param paths: The list of files to import.
        :type paths: List[str]
        """

        self.vredpy.vrGUIService.openImportDialog(paths)

    def open_import_dialog(self, path):
        """
        Import the file into VRED using the import dialog.

        :param path: Path to the file to import.
        :type path: str
        """

        self.open_import_batch_dialog([path])

    # --------------------------------------------------------------------------
    # Private methods

    def __connect_once(self, signal, slot):
        """
        Connect the signal to the slot, but only trigger once.

        :param signal: The signal to connect.
        :param slot: The slot to connect.
        """

        def wrapper(*args, **kwargs):
            slot(*args, **kwargs)
            signal.disconnect(wrapper)

        signal.connect(wrapper)
