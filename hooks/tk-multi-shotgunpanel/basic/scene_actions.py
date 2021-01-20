# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook that loads defines all the available actions, broken down by publish type.
"""
import os
import sys

try:
    import builtins
except ImportError:
    import __builtins__ as builtins

import sgtk

import vrFileIO

builtins.vrReferenceService = vrReferenceService

HookBaseClass = sgtk.get_hook_baseclass()


class VREDActions(HookBaseClass):
    def generate_actions(self, sg_data, actions, ui_area):
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

        :param sg_data: Shotgun data dictionary with all the standard publish fields.
        :param actions: List of action strings which have been defined in the app configuration.
        :param ui_area: String denoting the UI Area (see above).
        :returns List of dictionaries, each with keys name, params, caption and description
        """

        self.logger.debug(
            "Generate actions called for UI element {ui}"
            "Actions: {actions}"
            "Publish Data: {data}".format(ui=ui_area, actions=actions, data=sg_data)
        )

        action_instances = []
        try:
            # call base class first
            action_instances += HookBaseClass.generate_actions(
                self, sg_data, actions, ui_area
            )
        except AttributeError:
            # base class doesn't have the method, so ignore and continue
            pass

        if "import" in actions:
            action_instances.append(
                {
                    "name": "import",
                    "params": None,
                    "caption": "Import into Scene",
                    "description": "This will import the item into the current universe.",
                }
            )

        if "smart_reference" in actions:
            action_instances.append(
                {
                    "name": "smart_reference",
                    "params": None,
                    "caption": "Create Smart Reference",
                    "description": "This will import the item to the universe as a smart reference.",
                }
            )

        if "load_python" in actions:
            action_instances.append(
                {
                    "name": "load_python",
                    "params": None,
                    "caption": "Load Python Module",
                    "description": "This will allow the Python module to be imported using the VRED Python interpreter.",
                }
            )

        if "import_python" in actions:
            action_instances.append(
                {
                    "name": "import_python",
                    "params": None,
                    "caption": "Import into Scene by Executing Python",
                    "description": "This will load and execute the Python file without resetting the current scene.",
                }
            )

        if "execute_python" in actions:
            action_instances.append(
                {
                    "name": "execute_python",
                    "params": None,
                    "caption": "Create New Scene and Execute Python",
                    "description": "This will reset the current scene, then load and execute the Python file.",
                }
            )

        return action_instances

    def execute_action(self, name, params, sg_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.

        :param name: Action name string representing one of the items returned by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_data: Shotgun data dictionary with all the standard publish fields.
        :returns: No return value expected.
        """

        self.logger.debug(
            "Execute action called for action {name}"
            "Parameters: {params}"
            "Shotgun Data: {data}".format(name=name, params=params, data=sg_data)
        )

        if name == "import":
            path = self.get_publish_path(sg_data)
            vrFileIO.loadGeometry(path)

        elif name == "smart_reference":
            path = self.get_publish_path(sg_data)
            self.create_smart_reference(path)

        elif name == "load_python":
            path = self.get_publish_path(sg_data)
            module_dir = os.path.dirname(path)
            # Add the python module (if it does not already exist) to the system path to allow
            # importing it using the VRED Python interpreter.
            if module_dir not in sys.path:
                sys.path.append(module_dir)

        elif name == "import_python":
            path = self.get_publish_path(sg_data)
            (success, err_msg) = self.parent.engine.execute_python_script(
                path, reset_scene=False
            )
            if success:
                self.logger.info(
                    "Successfully executed Python script {script} for import.".format(
                        script=path
                    )
                )
            else:
                if not err_msg:
                    err_msg = "Failed to load Python file {script}.".format(script=path)
                self.logger.error(err_msg)

        elif name == "execute_python":
            path = self.get_publish_path(sg_data)
            (success, err_msg) = self.parent.engine.execute_python_script(
                path, reset_scene=True
            )
            if success:
                self.logger.info(
                    "Successfully reset scene and executed Python file {script}.".format(
                        script=path
                    )
                )
            else:
                if not err_msg:
                    err_msg = "Failed to load Python file {script}.".format(script=path)
                self.logger.error(err_msg)

        else:
            try:
                HookBaseClass.execute_action(self, name, params, sg_data)
            except AttributeError:
                # base class doesn't have the method, so ignore and continue
                pass

    def execute_multiple_actions(self, actions):
        """
        Executes the specified action on a list of items.

        The default implementation dispatches each item from ``actions`` to
        the ``execute_action`` method.

        The ``actions`` is a list of dictionaries holding all the actions to execute.
        Each entry will have the following values:

            name: Name of the action to execute
            sg_data: Publish information coming from Shotgun
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
            sg_data = single_action["sg_data"]
            params = single_action["params"]
            self.execute_action(name, params, sg_data)

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
