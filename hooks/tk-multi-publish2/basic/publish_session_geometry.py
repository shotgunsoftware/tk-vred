# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class VREDSessionGeometryPublishPlugin(HookBaseClass):
    """
    Plugin for publishing VRED geometry nodes.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/basic/publish_session.py"

    """

    # NOTE: The plugin icon and name are defined by the base file plugin.

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        return """
        <p>This plugin publishes VRED geometry nodes for the current session. Any
        session geometry nodes will be exported to the path defined by this plugin's
        configured "Publish Template" setting.</p>
        """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """
        # inherit the settings from the base publish plugin
        base_settings = super(VREDSessionGeometryPublishPlugin, self).settings or {}

        # settings specific to this class
        vred_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            }
        }

        # update the base settings
        base_settings.update(vred_publish_settings)

        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["vred.session.geometry"]

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

        # if a publish template is configured, disable context change. This
        # is a temporary measure until the publisher handles context switching
        # natively.
        if settings.get("Publish Template").value:
            item.context_change_allowed = False

        path = _session_path()

        if not path:
            # the session has not been saved before (no path determined).
            # provide a save button. the session will need to be saved before
            # validation will succeed.
            self.logger.warn(
                "The VRED session has not been saved.", extra=_get_save_as_action()
            )

        self.logger.info(
            "VRED '%s' plugin accepted the current VRED session." % (self.name,)
        )
        return {"accepted": True, "checked": False}

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

        publisher = self.parent
        path = _session_path()

        # ---- ensure the session has been saved

        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The VRED session has not been saved."
            self.logger.error(error_msg, extra=_get_save_as_action())
            raise Exception(error_msg)

        # ---- check the session against any attached work template

        # get the path in a normalized state. no trailing separator,
        # separators are appropriate for current os, no double separators,
        # etc.
        path = sgtk.util.ShotgunPath.normalize(path)

        # if the session item has a known work template, see if the path
        # matches. if not, warn the user and provide a way to save the file to
        # a different path
        work_template = item.parent.properties.get("work_template")
        if not work_template or not work_template.validate(path):
            self.logger.warning(
                "The current session does not match the configured work "
                "file template.",
                extra={
                    "action_button": {
                        "label": "Save File",
                        "tooltip": "Save the current VRED session to a "
                        "different file name",
                        # will launch wf2 if configured
                        "callback": _get_save_as_action(),
                    }
                },
            )
            return False
        else:
            self.logger.debug("Work template configured and matches session file.")

        # ---- populate the necessary properties and call base class validation

        # populate the publish template on the item if found
        publish_template_setting = settings.get("Publish Template")
        publish_template = publisher.engine.get_template_by_name(
            publish_template_setting.value
        )
        if publish_template:
            item.properties["publish_template"] = publish_template

        # set the session path on the item for use by the base plugin validation
        # step. NOTE: this path could change prior to the publish phase.
        item.properties["path"] = path

        # if we don't have a publish path, we can't publish
        publish_path = self.get_publish_path(settings, item)
        if not publish_path:
            self.logger.warning(
                "Couldn't find a valid publish path for the geometry file."
            )
            return False

        # run the base class validation
        return super(VREDSessionGeometryPublishPlugin, self).validate(settings, item)

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        publisher = self.parent
        operations = publisher.engine.operations

        # be sure the geometry node is still in the current scene
        geometry_node = operations.get_geometry_node_by_id(item.properties.node_id)
        if not geometry_node:
            self.logger.error(
                "Couldn't find node %s in the current VRED session." % item.name
            )
            return

        # get the path to create and publish
        publish_path = self.get_publish_path(settings, item)

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        self.parent.ensure_folder_exists(publish_folder)

        # save the geometry at the right place
        try:
            operations.export_geometry(geometry_node, publish_path)
        except Exception as e:
            self.logger.error("Failed to export geometry: %s" % str(e))
            return

        # change the value of the item path property in order to have the right publish name and file type
        item.properties["path"] = publish_path

        # Now that the path has been generated, hand it off to the
        super(VREDSessionGeometryPublishPlugin, self).publish(settings, item)

    def get_publish_path(self, settings, item):
        """
        Get a publish path for the supplied settings and item.

        :param settings: This plugin instance's configured settings
        :param item: The item to determine the publish path for

        :return: A string representing the output path to supply when
            registering a publish for the supplied item

        Extracts the publish path via the configured work and publish templates
        if possible.
        """

        # publish type explicitly set or defined on the item
        publish_path = item.get_property("publish_path")
        if publish_path:
            return publish_path

        # fall back to template/path logic
        path = item.properties.path

        work_template = item.parent.properties.get("work_template")
        publish_template = self.get_publish_template(settings, item)

        work_fields = []
        publish_path = None

        # We need both work and publish template to be defined for template
        # support to be enabled.
        if work_template and publish_template:
            if work_template.validate(path):
                work_fields = work_template.get_fields(path)

            if "extra_template_fields" in item.properties:
                work_fields.update(item.properties.extra_template_fields)

            missing_keys = publish_template.missing_keys(work_fields)

            if missing_keys:
                self.logger.warning(
                    "Not enough keys to apply work fields (%s) to "
                    "publish template (%s)" % (work_fields, publish_template)
                )
            else:
                publish_path = publish_template.apply_fields(work_fields)
                self.logger.debug(
                    "Used publish template to determine the publish path: %s"
                    % (publish_path,)
                )
        else:
            self.logger.debug("publish_template: %s" % publish_template)
            self.logger.debug("work_template: %s" % work_template)

        if not publish_path:
            return None
            publish_path = path
            self.logger.debug("Could not validate a publish template.")

        # store the publish path
        item.properties["publish_path"] = publish_path

        return publish_path


def _session_path():
    """
    Return the path to the current session
    :return:
    """
    engine = sgtk.platform.current_engine()
    operations = engine.operations

    return operations.get_current_file()


def _get_save_as_action():
    """
    Simple helper for returning a log action dict for saving the session
    """

    engine = sgtk.platform.current_engine()
    operations = engine.operations

    # default save callback
    callback = operations.open_save_as_dialog

    # if workfiles2 is configured, use that for file save
    if "tk-multi-workfiles2" in engine.apps:
        app = engine.apps["tk-multi-workfiles2"]
        if hasattr(app, "show_file_save_dlg"):
            callback = app.show_file_save_dlg

    return {
        "action_button": {
            "label": "Save As...",
            "tooltip": "Save the current session",
            "callback": callback,
        }
    }
