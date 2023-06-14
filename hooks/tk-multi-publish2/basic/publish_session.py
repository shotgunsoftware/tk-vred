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

import vrFileIO

HookBaseClass = sgtk.get_hook_baseclass()


class VREDSessionPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an open VRED session.

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

        loader_url = "https://developer.shotgridsoftware.com/a4c0a4f1/?title=Loader"

        return """
            Publishes the file to ShotGrid. A <b>Publish</b> entry will be
            created in ShotGrid which will include a reference to the file's current
            path on disk. If a publish template is configured, a copy of the
            current session will be copied to the publish template path which
            will be the file that is published. Other users will be able to access
            the published file via the <b><a href='%s'>Loader</a></b> so long as
            they have access to the file's location on disk.

            If the session has not been saved, validation will fail and a button
            will be provided in the logging output to save the file.

            <h3>File versioning</h3>
            If the filename contains a version number, the process will bump the
            file to the next version after publishing.

            The <code>version</code> field of the resulting <b>Publish</b> in
            Shotgrid will also reflect the version number identified in the filename.
            The basic worklfow recognizes the following version formats by default:

            <ul>
            <li><code>filename.v###.ext</code></li>
            <li><code>filename_v###.ext</code></li>
            <li><code>filename-v###.ext</code></li>
            </ul>

            After publishing, if a version number is detected in the work file, the
            work file will automatically be saved to the next incremental version
            number. For example, <code>filename.v001.ext</code> will be published
            and copied to <code>filename.v002.ext</code>

            If the next incremental version of the file already exists on disk, the
            validation step will produce a warning, and a button will be provided in
            the logging output which will allow saving the session to the next
            available version number prior to publishing.

            <br><br><i>NOTE: any amount of version number padding is supported. for
            non-template based workflows.</i>

            <h3>Overwriting an existing publish</h3>
            In non-template workflows, a file can be published multiple times,
            however only the most recent publish will be available to other users.
            Warnings will be provided during validation if there are previous
            publishes.
            """ % (
            loader_url,
        )

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
        base_settings = super(VREDSessionPublishPlugin, self).settings or {}

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
        return ["vred.session"]

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

        path = vrFileIO.getFileIOFilePath()

        if not path:
            # the session has not been saved before (no path determined).
            # provide a save button. the session will need to be saved before
            # validation will succeed.
            self.logger.warn(
                "The VRED session has not been saved.",
                extra=_get_save_as_action(),
            )

        self.logger.info(
            "VRED '%s' plugin accepted the current VRED session." % (self.name,)
        )
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

        path = vrFileIO.getFileIOFilePath()

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
        work_template = item.properties.get("work_template")
        if work_template:
            if not work_template.validate(path):
                error_msg = "The current session does not match the configured work file template."
                self.logger.warning(
                    error_msg,
                    extra={
                        "action_button": {
                            "label": "Save File",
                            "tooltip": "Save the current VRED session to a "
                            "different file name",
                            "callback": sgtk.platform.current_engine().open_save_as_dialog,
                        }
                    },
                )
                raise Exception(error_msg)
            else:
                self.logger.debug("Work template configured and matches session file.")
        else:
            self.logger.debug("No work template configured.")

        # ---- see if the version can be bumped post-publish

        # check to see if the next version of the work file already exists on
        # disk. if so, warn the user and provide the ability to jump to save
        # to that version now
        (next_version_path, version) = self._get_next_version_info(path, item)
        if next_version_path and os.path.exists(next_version_path):

            # determine the next available version_number. just keep asking for
            # the next one until we get one that doesn't exist.
            while os.path.exists(next_version_path):
                (next_version_path, version) = self._get_next_version_info(
                    next_version_path, item
                )

            error_msg = "The next version of this file already exists on disk."
            self.logger.error(
                error_msg,
                extra={
                    "action_button": {
                        "label": "Save to v%s" % (version,),
                        "tooltip": "Save to the next available version number, "
                        "v%s" % (version,),
                        "callback": lambda: self.save_file(next_version_path),
                    }
                },
            )
            raise Exception(error_msg)

        # ---- populate the necessary properties and call base class validation

        # populate the publish template on the item if found
        publish_template_setting = settings.get("Publish Template")
        publish_template = self.parent.engine.get_template_by_name(
            publish_template_setting.value
        )
        if publish_template:
            item.properties["publish_template"] = publish_template

        # set the session path on the item for use by the base plugin validation
        # step. NOTE: this path could change prior to the publish phase.
        item.properties["path"] = path

        # store the item publish version
        item.properties["publish_version"] = self.get_publish_version(settings, item)

        # run the base class validation
        return super(VREDSessionPublishPlugin, self).validate(settings, item)

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

        # get the path in a normalized state. no trailing separator, separators
        # are appropriate for current os, no double separators, etc.
        session_path = vrFileIO.getFileIOFilePath()
        path = sgtk.util.ShotgunPath.normalize(session_path)

        # ensure the session is saved
        if not bg_processing or (bg_processing and not in_bg_process):
            self.save_file(path)

            # only store the session name if we are using the background publish mode
            if bg_processing and "session_path" not in item.parent.properties:
                item.parent.properties["session_path"] = path
                item.parent.properties[
                    "session_name"
                ] = "VRED Session - {task_name}, {entity_type} {entity_name} - {file_name}".format(
                    task_name=item.context.task["name"],
                    entity_type=item.context.entity["type"],
                    entity_name=item.context.entity["name"],
                    file_name=os.path.basename(path),
                )

        # update the item with the saved session path
        item.properties["path"] = path

        if not bg_processing or (bg_processing and in_bg_process):

            # let the base class register the publish
            super(VREDSessionPublishPlugin, self).publish(settings, item)

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once all the publish
        tasks have completed, and can for example be used to version up files.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        # get the publish "mode" stored inside of the root item properties
        bg_processing = item.parent.properties.get("bg_processing", False)
        in_bg_process = item.parent.properties.get("in_bg_process", False)

        if not bg_processing or (bg_processing and in_bg_process):
            # do the base class finalization
            super(VREDSessionPublishPlugin, self).finalize(settings, item)

        # bump the session file to the next version
        if not bg_processing or (bg_processing and not in_bg_process):
            self._save_to_next_version(item.properties["path"], item, self.save_file)

    def save_file(self, path):
        """
        A callback for saving a file.

        :param path: the file path to save.
        """

        self.parent.engine.save_current_file(path)


def _get_save_as_action():
    """Simple helper for returning a log action to show the "File Save As" dialog"""
    return {
        "action_button": {
            "label": "Save As...",
            "tooltip": "Save the current session",
            "callback": sgtk.platform.current_engine().open_save_as_dialog,
        }
    }
