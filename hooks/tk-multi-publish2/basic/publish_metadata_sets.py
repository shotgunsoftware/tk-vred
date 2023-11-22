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


class PublishVREDMetadataSetPlugin(HookBaseClass):
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
        base_settings = super(PublishVREDMetadataSetPlugin, self).settings or {}

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
        return ["vred.session.metadata_set.item"]

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

        if not hasattr(self.vredpy, "vrMetadataService"):
            self.logger.debug("This version of VRED does not support metadata, skipping.")
            return {"accepted": False}

        return {"accepted": True, "checked": True}

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

        # NOTE do we need this other than just for resolving templates via path?
        # Ensure the session has been saved
        path = self.vredpy.vrFileIO.getFileIOFilePath()
        if not path:
            error_msg = "The VRED session has not been saved."
            self.logger.error(
                error_msg, extra=sgtk.platform.current_engine().open_save_as_dialog
            )
            raise Exception(error_msg)

        if not item.get_property("metadata_set"):
            error_msg = "Metdata Set not found"
            self.logger.error(error_msg)
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
            metadata_set = item.get_property("metadata_set")
            if not metadata_set:
                self.logger.error("Missing Metadata Set to publish.")
                return

            path = item.get_property("path")
            if not path:
                self.logger.error("Missing path to publish Metadata Set to.")
                return

            publisher = self.parent

            # convert the metadata set to dictionary
            metadata_set_data = self.metadata_set_to_dict(metadata_set)
            metadata_set_name = self.get_publish_name(settings, item)

            # check if metadata set asset already exists and version up, or create new (sub) asset
            # 1. Find existing asset of type 'Trim Set' that is a sub asset of the main asset
            metadata_set_asset = self._get_metadata_set_asset(settings, item)
            if metadata_set_asset:
                # Asset exists
                version_number = len(metadata_set_asset.get("sg_published_files", [])) + 1
            else:
                # Create asset
                asset_data = {
                    "sg_asset_type": metadata_set_data.get("SG_asset_type"),
                    "parents": [item.context.entity],
                    "code": self.get_publish_name(settings, item),
                    "project": item.context.project,
                }
                metadata_set_asset = publisher.shotgun.create("Asset", asset_data)
                version_number = 1

            # FIXME get from context?
            session_publish_template = self.sgtk.template_from_path(path)
            template_fields = session_publish_template.get_fields(path)
            template_fields["name"] = self.get_publish_name(settings, item)
            template_fields["version"] = version_number
            template_fields["sg_asset_type"] = metadata_set_data.get("SG_asset_type")
            template_fields["Asset"] = metadata_set_name

            publish_template = item.get_property("publish_template")
            publish_path = publish_template.apply_fields(template_fields)
            item.local_properties.publish_path = publish_path

            # ensure the publish folder exists
            publish_folder = os.path.dirname(publish_path)
            ensure_folder_exists(publish_folder)

            # dump the metadata in a json file to publish
            with open(publish_path, "w+") as fp:
                json.dump(metadata_set_data, fp)
            
            # finally, publish the metadata set
            publish_type = "VRED Metadata Set"
            publish_name = self.get_publish_name(settings, item)
            publish_version = version_number
            publish_dependencies_paths = self.get_publish_dependencies(settings, item)
            publish_user = self.get_publish_user(settings, item)
            publish_fields = self.get_publish_fields(settings, item)
            publish_kwargs = self.get_publish_kwargs(settings, item)
            publish_dependencies_ids = []

            # Metadata set context
            metadata_set_context = sgtk.Context(
                item.context.sgtk,
                project=item.context.project,
                entity=metadata_set_asset,
                step=item.context.step,
                task=item.context.task,
                user=item.context.user,
                additional_entities=item.context.additional_entities,
                source_entity=item.context.source_entity,
            )

            # TODO upstream dependencies point to material published files

            publish_data = {
                "tk": publisher.sgtk,
                "context": metadata_set_context,
                "comment": item.description,
                "path": publish_path,
                "name": publish_name,
                "created_by": publish_user,
                "version_number": publish_version,
                "thumbnail_path": item.get_thumbnail_as_path(),
                "published_file_type": publish_type,
                "dependency_paths": publish_dependencies_paths,
                "dependency_ids": publish_dependencies_ids,
                "sg_fields": publish_fields,
            }

            # add extra kwargs
            publish_data.update(publish_kwargs)
            result = sgtk.util.register_publish(**publish_data)

    def _get_metadata_set_asset(self, settings, item):
        """Return the ShotGrid Asset matching the VRED Metadata Set."""

        metadata_set_name = self.get_publish_name(settings, item)
        parent_asset = item.context.entity
        return self.parent.shotgun.find_one(
            "Asset",
            filters=[
                ["code", "is", metadata_set_name],
                ["parents", "is", parent_asset],
            ],
            fields=[
                "sg_published_files",
            ],
        )

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

        item = items[0]

        description_group_box = super(PublishVREDMetadataSetPlugin, self).create_settings_widget(parent, items)

        # Metadata preview
        metadata_group_box = QtGui.QGroupBox(parent)
        metadata_group_box.setTitle("Metadata Preview:")

        metadata_set = item.get_property("metadata_set")
        metadata_dict = self.metadata_set_to_dict(metadata_set)
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

    def get_publish_name(self, settings, item):
        """
        Get the publish name for the supplied settings and item.

        :param settings: This plugin instance's configured settings
        :param item: The item to determine the publish name for

        Uses the path info hook to retrieve the publish name.
        """

        metadata_set = item.get_property("metadata_set")
        if not metadata_set:
            return
        return metadata_set.getName()

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
            }

        return publish_kwargs

    ############################################################################
    # specific publish plugin methods

    def metadata_set_to_dict(self, metadata_set):
        """
        Return the VRED Metadata Set as a dictionary.

        :param metadata_set: The VRED Metadata Set.
        :type settings: vrdMetadataSet

        :return: The metadata set represented as a dictionary.
        :rtype: dict
        """

        result = {}
        entries = metadata_set.getEntries()
        for entry in entries:
            result[entry.getKey()] = entry.getValue()
        return result
