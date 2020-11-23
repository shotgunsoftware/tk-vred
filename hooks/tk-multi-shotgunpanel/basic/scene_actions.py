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

import re

import sgtk
from sgtk import util
from sgtk.platform.qt import QtCore, QtGui
from tank_vendor.six.moves import urllib

import vrFileIO
import vrScenegraph

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

        if "load_for_review" in actions:
            action_instances.append(
                {
                    "name": "load_for_review",
                    "params": None,
                    "caption": "Load for Review",
                    "description": "This will reset and load the item into the current universe.",
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
        :returns: Dictionary representing an Entity if action requires a context change in the panel,
                  otherwise no return value expected.
        """

        self.logger.debug(
            "Execute action called for action {name}"
            "Parameters: {params}"
            "Shotgun Data: {data}".format(name=name, params=params, data=sg_data)
        )

        result = None

        if name == "import":
            path = self.get_publish_path(sg_data)
            vrFileIO.loadGeometry(path)

        elif name == "load_for_review":
            result = self._load_for_review(sg_data)

        else:
            try:
                result = HookBaseClass.execute_action(self, name, params, sg_data)
            except AttributeError:
                # base class doesn't have the method, so ignore and continue
                pass

        return result

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

    def execute_entity_doubleclicked_action(self, sg_data):
        """
        This action is triggered when an entity is double-clicked.
        Perform any specific actions and return a tuple represetnting
        the entity that the panel will navigate to.

        :param sg_data: Dictionary containing data for the entity that
                        was double-clicked.
        :return: A tuple ('entity_type', 'entity_id')
        """

        return self._load_for_review(sg_data, confirm_action=True)

    def _load_for_review(self, sg_data, confirm_action=False):
        """
        Find an associated published file from the entity defined by the `sg_data`,
        and load it into VRED.
        """

        # The current entity. This entity dictionary will be the return value to
        # trigger a context change in SG Panel to this entity.
        entity = {"type": sg_data["type"], "id": sg_data["id"]}

        # Load for review action only supports Version entity type
        if sg_data["type"] != "Version":
            return entity

        # Ask the user if they want to proceed with loading the Version for review.
        if confirm_action:
            answer = QtGui.QMessageBox.question(
                None,
                "Load for Review?",
                "Do you want to load this {} for review?".format(sg_data["type"]),
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel,
            )

            if answer == QtGui.QMessageBox.Cancel:
                # Abort this action altogether.
                return None

            if answer == QtGui.QMessageBox.No:
                # Continue this action but do not load for review.
                return entity

        # Check for unsaved changes and do not load new scene until changes are resolved.
        engine = self.parent.engine
        resolved = engine.save_or_discard_changes()
        if not resolved:
            return None

        # OK to proceed with loading the Version for review
        published_file_entity_type = sgtk.util.get_published_file_entity_type(self.sgtk)
        accepted_published_file_types = engine.get_setting(
            "accepted_published_file_types", []
        )
        published_files = self.parent.engine.shotgun.find(
            published_file_entity_type,
            [
                ["version", "is", entity],
                [
                    "published_file_type.PublishedFileType.code",
                    "in",
                    accepted_published_file_types,
                ],
            ],
            fields=["id", "path"],
            order=[{"field_name": "version_number", "direction": "desc"}],
        )

        if not published_files:
            raise Exception("Version has no published files to load for review.")

        if len(published_files) != 1:
            raise Exception(
                "Failed to load Version for review with VRED because there is more than one PublishedFile entity with the same PublishedFileType associated for this Version"
            )

        # Load the Version's "latest" PublishedFile, the one with the highest version.
        published_file = published_files[0]
        if published_file:
            path = _get_published_file_path(published_file)
            if not path:
                raise Exception(
                    "Unable to determine the path on disk for published file with id '{}'.".format(
                        published_file["id"]
                    )
                )

            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            vrFileIO.load(
                [path],
                vrScenegraph.getRootNode(),
                newFile=True,
                showImportOptions=False,
            )
            QtGui.QApplication.restoreOverrideCursor()

        return entity


def _get_published_file_path(published_file):
    """
    Return the path on disk for the given published file.
    """

    if published_file is None:
        return None

    path = published_file.get("path", None)
    if path is None:
        return ""

    # Return the local path right away, if we have it
    if path.get("local_path", None) is not None:
        return path["local_path"]

    # This published file came from a zero config publish, it will
    # have a file URL rather than a local path.
    path_on_disk = path.get("url", None)
    if path_on_disk is not None:
        # We might have something like a %20, which needs to be
        # unquoted into a space, as an example.
        if "%" in path_on_disk:
            path_on_disk = urllib.parse.unquote(path_on_disk)

        # If this came from a file url via a zero-config style publish
        # then we'll need to remove that from the head in order to end
        # up with the local disk path to the file.
        #
        # On Windows, we will have a path like file:///E:/path/to/file.jpg
        # and we need to ditch all three of the slashes at the head. On
        # other operating systems it will just be file:///path/to/file.jpg
        # and we will want to keep the leading slash.
        if util.is_windows():
            pattern = r"^file:///"
        else:
            pattern = r"^file://"

        path_on_disk = re.sub(pattern, "", path_on_disk)

    return path_on_disk
