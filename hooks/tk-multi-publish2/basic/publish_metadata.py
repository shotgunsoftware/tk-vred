# Copyright (c) 2023 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import json
import os

import sgtk
from sgtk.util.filesystem import ensure_folder_exists

HookBaseClass = sgtk.get_hook_baseclass()


class PublishVREDMetadataPlugin(HookBaseClass):
    """Publish VRED metadata."""

    ############################################################################
    # standard publish plugin properties

    @property
    def name(self):
        return "Publish Metadata to ShotGrid"

    @property
    def description(self):
        return "Export the VRED metadata as JSON file and publish it to ShotGrid."

    @property
    def settings(self):
        """The settings that this plugin expects to receive throughout the publish steps."""

        # inherit the settings from the base publish plugin
        base_settings = super(PublishVREDMetadataPlugin, self).settings or {}

        # settings specific to this class
        plugin_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            },
        }

        # update the base settings
        base_settings.update(plugin_settings)

        return base_settings

    @property
    def item_filters(self):
        """List of item types that this plugin is interested in."""
        return ["vred.session"]

    ############################################################################
    # specific publish plugin properties

    @property
    def vredpy(self):
        """Get the vredpy API module to communicate wtih the VRED."""
        return self.parent.engine.vredpy

    ############################################################################
    # standard publish plugin methods

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.
        A publish task will be generated for each item accepted here. Returns a
        dictionary with the following booleans:
            - accepted: Indicates if the plugin is interested in this value at
                all. Required.
            - enabled: If True, the plugin will be enabled in the UI, otherwise
                it will be disabled. Optional, True by default.
            - visible: If True, the plugin will be visible in the UI, otherwise
                it will be hidden. Optional, True by default.
            - checked: If True, the plugin will be checked in the UI, otherwise
                it will be unchecked. Optional, True by default.
        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: dictionary with boolean keys accepted, required and enabled
        """

        vredpy = self.parent.engine.vredpy

        if not hasattr(vredpy, "vrMetadataService"):
            self.logger.debug("This version of VRED does not support metadata, skipping.")
            return {"accepted": False}

        # check that we have at least one metadata in the scene
        has_metadata = self.get_metadata(settings, check=True)
        if not has_metadata:
            self.logger.debug("No metadata found in the current scene, skipping.")
            return {"accepted": False}

        return {"accepted": True, "checked": False}
        # return {"accepted": True, "checked": True}

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish. Returns a
        boolean to indicate validity.
        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if item is valid, False otherwise.
        """

        # Check for a valid publish template
        publish_template_setting = settings.get("Publish Template")
        publish_template = self.parent.engine.get_template_by_name(
            publish_template_setting.value
        )
        if not publish_template:
            # FIXME consistent error, raise or return false?
            self.logger.error("Missing publish template")
            return False

        # Store the template in the item local properties to avoid having to get the template
        # again when publshing
        item.local_properties["publish_template"] = publish_template

        # Ensure the session has been saved
        path = self.vredpy.vrFileIO.getFileIOFilePath()
        if not path:
            error_msg = "The VRED session has not been saved."
            self.logger.error(
                error_msg, extra=sgtk.platform.current_engine().open_save_as_dialog
            )
            raise Exception(error_msg)

        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        # get the publish "mode" stored inside of the root item properties
        bg_processing = item.parent.properties.get("bg_processing", False)
        in_bg_process = item.parent.properties.get("in_bg_process", False)

        if not bg_processing or (bg_processing and in_bg_process):

            publish_template = item.get_property("publish_template")

            # get the publish path of the current session and use it to retrieve some template fields
            session_publish_path = None
            publish_data = item.get_property("sg_publish_data")
            if publish_data:
                session_publish_path = publish_data.get("path", {}).get("local_path")

            if not session_publish_path:
                self.logger.error("Couldn't find the publish path of the current session")
                return

            session_publish_template = self.sgtk.template_from_path(session_publish_path)
            template_fields = session_publish_template.get_fields(session_publish_path)

            publish_path = publish_template.apply_fields(template_fields)
            item.local_properties.publish_path = publish_path

            # ensure the publish folder exists
            publish_folder = os.path.dirname(publish_path)
            ensure_folder_exists(publish_folder)

            # get the metadata and export them as json file
            scene_metadata = self.get_metadata(settings)
            with open(publish_path, "w+") as fp:
                json.dump(scene_metadata, fp)

            # finally, publish the scene
            item.local_properties.publish_type = "VRED Metadata"
            item.local_properties.publish_version = template_fields["version"]
            item.local_properties.publish_name = self.parent.util.get_publish_name(publish_path)
            item.local_properties.publish_dependencies = [session_publish_path]
            super(PublishVREDMetadataPlugin, self).publish(settings, item)

    def finalize(self, settings, item):
        """Execute the finalization pass."""
        pass

    def create_settings_widget(self, parent, items=None):
        """
        Creates a Qt widget, for the supplied parent widget (a container widget
        on the right side of the publish UI).
        :param parent: The parent to use for the widget being created.
        :param items: A list of PublishItems the selected publish tasks are parented to.
        :return: A QtGui.QWidget or subclass that displays information about
            the plugin and/or editable widgets for modifying the plugin's
            settings.
        """

        from sgtk.platform.qt import QtGui

        description_group_box = super(PublishVREDMetadataPlugin, self).create_settings_widget(parent, items)

        # Metadata preview
        metadata_group_box = QtGui.QGroupBox(parent)
        metadata_group_box.setTitle("Metadata Preview:")

        metadata_dict = self.get_metadata()
        metadata_str = json.dumps(metadata_dict, indent=4)

        metadata_label = QtGui.QLabel(metadata_str)
        metadata_label.setWordWrap(False)

        # create the layout to use within the group box
        metadata_layout = QtGui.QVBoxLayout()
        metadata_layout.addWidget(metadata_label)
        metadata_layout.addStretch()
        metadata_group_box.setLayout(metadata_layout)

        widget = QtGui.QWidget(parent)
        widget_layout = QtGui.QVBoxLayout()
        widget_layout.addWidget(description_group_box)
        widget_layout.addWidget(metadata_group_box)
        widget.setLayout(widget_layout)
        return widget


    ############################################################################
    # override parent publish plugin methods

    def _copy_work_to_publish(self, settings, item):
        """This method handles copying work files to a designated publish location."""
        pass

    def get_publish_kwargs(self, settings, item):
        """
        Get kwargs that should be passed to :meth:`tank.util.register_publish`.
        These kwargs will be used to update the kwarg dictionary that is passed
        when calling :meth:`tank.util.register_publish`, meaning that any value
        set here will supersede a value already retrieved from another
        ``property`` or ``local_property``.

        If publish_kwargs is not defined as a ``property`` or
        ``local_property``, this method will return an empty dictionary.

        :param settings: This plugin instance's configured settings
        :param item: The item to determine the publish template for

        :return: A dictionary of kwargs to be passed to
                 :meth:`tank.util.register_publish`.
        """

        publish_kwargs = item.get_property("publish_kwargs", default_value={})

        version = item.get_property("sg_version_data")
        if version:
            publish_kwargs["version_entity"] = {
                "id": version.get("id"),
                "type": version.get("type"),
                # "name": version.get("code"),
            }

        return publish_kwargs

    ############################################################################
    # specific publish plugin methods

    def get_metadata(self, settings=None, check=False):
        """
        Get the VRED metadata of the root node and all its children.
        :param settings: The plugin settings.
        :type settings: dict
        :param check: If check is True, stop as soon as we find the first metadata
        :type check: bool
        :return: The metadata, unless check is set to True, then True if there is metadata,
            else False.
        """

        def __get_metadata_recursive(node, metadata):
            """Recursive function to get the metadata of a node and its children"""

            if not node:
                return False

            print(node.getName())

            if self.vredpy.vrMetadataService.hasMetadata(node):
                node_metadata = self.vredpy.vrMetadataService.getMetadata(node)
                object_set = node_metadata.getObjectSet()
                entries = object_set.getEntries()
                node_metadata_dict = {entry.getKey(): entry.getValue() for entry in entries}
                if node_metadata_dict:
                    if check:
                        return True
                    metadata[node.getName()] = node_metadata_dict

            # Recurse on each child node
            for child_node in node.getChildren():
                has_metadata = __get_metadata_recursive(child_node, metadata)
                if check and has_metadata:
                    return True

            # No metadata for this node 
            return False


        # Get the root node to gather metadata from and all its children
        root_node = self.vredpy.vrScenegraphService.getRootNode()
        if not root_node:
            if check:
                return False
            return {}

        # Call the helper recursive function to gather all metadata
        metadata = {}
        has_metadata = __get_metadata_recursive(root_node, metadata)
        if check:
            return has_metadata
        return metadata
