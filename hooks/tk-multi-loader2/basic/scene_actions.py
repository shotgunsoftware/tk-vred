# Copyright (c) 2020 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

"""
Hook that loads defines all the available actions, broken down by publish type.
"""
import os

try:
    import builtins
except ImportError:
    try:
        import __builtins__ as builtins
    except ImportError:
        import __builtin__ as builtins

import sgtk

from vrKernelServices import vrSceneplateTypes
from vrKernelServices import vrdSceneplateNode
import vrFileIO

builtins.vrReferenceService = vrReferenceService

HookBaseClass = sgtk.get_hook_baseclass()


class VredActions(HookBaseClass):

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

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
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
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
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
            vrFileIO.loadGeometry(path)

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
            sg_publish_data: Publish information coming from Shotgun
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
        vredSceneplateRoot = vrSceneplateService.getRootNode()
        # Extract the filename for the name of the Sceneplate
        nodeName = os.path.basename(image_path)
        # Load in the image
        imageObject = vrImageService.loadImage(image_path)
        # Create the actual Sceneplate node
        newSceneplateNode = vrSceneplateService.createNode(
            vredSceneplateRoot, vrSceneplateTypes.NodeType.Frontplate, nodeName
        )
        newSceneplate = vrdSceneplateNode(newSceneplateNode)
        # Set the type to image
        newSceneplate.setContentType(vrSceneplateTypes.ContentType.Image)
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
        ref_node = vrReferenceService.createSmart()
        ref_node.setSmartPath(path)
        ref_node.load()
        ref_node.setName(ref_name)
