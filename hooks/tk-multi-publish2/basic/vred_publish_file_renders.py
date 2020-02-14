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
import shutil

import traceback
from sgtk.util.filesystem import copy_file, ensure_folder_exists
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class VREDPublishFileRendersPlugin(HookBaseClass):
    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        return """
        <p>This plugin publishes renders for the current session. Any
        session render will be exported to the path defined by this plugin's
        configured "Publish Template" setting.</p>
        """

    @property
    def settings(self):
        # inherit the settings from the base publish plugin
        base_settings = super(VREDPublishFileRendersPlugin, self).settings or {}

        # settings specific to this class
        publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            }
        }

        base_settings.update(publish_settings)

        workfile_settings = {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            }
        }

        base_settings.update(workfile_settings)

        return base_settings

    def validate(self, settings, item):
        publisher = self.parent

        publish_template_setting = settings.get("Publish Template")
        publish_template = publisher.engine.get_template_by_name(
            publish_template_setting.value
        )

        if not publish_template:
            return False

        item.properties["publish_template"] = publish_template
        return True

    def accept(self, settings, item):
        base_accept = super(VREDPublishFileRendersPlugin, self).accept(settings, item)

        base_accept.update({"checked": False})
        base_accept.update({"visible": False})

        return base_accept

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["vred.session.renders"]

    def _get_target_path(self, item):
        publisher = self.parent
        source_path = item.properties["path"]
        publish_template = item.properties.get("publish_template")
        scene_name = os.path.basename(os.path.dirname(source_path))
        context_fields = publisher.context.as_template_fields(
            publish_template, validate=True
        )
        context_fields.update({"scene_name": scene_name})
        target_path = publish_template.apply_fields(context_fields)
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        target_path = os.path.sep.join([target_path, scene_name + ".png"])
        return target_path

    def _copy_work_to_publish(self, settings, item):
        publish_template = item.properties.get("publish_template")
        if not publish_template:
            self.logger.debug(
                "No publish template set on the item. "
                "Skipping copying file to publish location."
            )
            return

        # Source path
        source_path = item.properties["path"]
        target_path = self._get_target_path(item)

        try:
            publish_folder = os.path.dirname(target_path)
            ensure_folder_exists(publish_folder)
            shutil.copyfile(source_path, target_path)
        except Exception as e:
            raise Exception(
                "Failed to copy work file from '%s' to '%s'.\n%s"
                % (source_path, target_path, traceback.format_exc())
            )

        self.logger.debug(
            "Copied work file '%s' to publish file '%s'." % (source_path, target_path)
        )

    def publish(self, settings, item):
        item.local_properties.publish_path = self._get_target_path(item)
        super(VREDPublishFileRendersPlugin, self).publish(settings, item)
