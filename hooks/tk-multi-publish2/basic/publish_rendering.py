# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class VREDSessionRenderingPublishPlugin(HookBaseClass):
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

        return """
        <p>This plugin publishes session rendering for the current session. Any
        session rendering will be exported to the path defined by this plugin's
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
        base_settings = super(VREDSessionRenderingPublishPlugin, self).settings or {}

        # settings specific to this class
        vred_publish_settings = {
            "Publish Image Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published single render image. Should"
                "correspond to a template defined in "
                "templates.yml.",
            },
            "Publish Sequence Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published render sequence. Should"
                "correspond to a template defined in "
                "templates.yml.",
            },
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
        return ["vred.session.image"]

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
        # populate the work template on the item if found
        work_template = self.sgtk.template_from_path(item.properties.path)
        if work_template:
            item.properties["work_template"] = work_template

        # populate the publish template on the item if found
        if not item.properties.get("sequence_paths"):
            publish_template_setting = settings.get("Publish Image Template")
        else:
            publish_template_setting = settings.get("Publish Sequence Template")
        publish_template = self.parent.engine.get_template_by_name(
            publish_template_setting.value
        )

        if publish_template:
            item.properties["publish_template"] = publish_template

        # do not validate the plugin if we have a different version between the rendering and the current scene
        publish_version = self.get_publish_version(settings, item)
        if (
            publish_template
            and publish_version != item.parent.properties["publish_version"]
        ):
            self.logger.warning(
                "Your rendering files don't have the same version number than your current work session."
            )
            return False

        return super(VREDSessionRenderingPublishPlugin, self).validate(settings, item)
