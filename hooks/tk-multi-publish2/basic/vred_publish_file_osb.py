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
import traceback
import sgtk
from sgtk.util.filesystem import ensure_folder_exists
import vrScenegraph
import vrFileIO

HookBaseClass = sgtk.get_hook_baseclass()


class VREDPublishOSBFilePlugin(HookBaseClass):
    @property
    def settings(self):
        # inherit the settings from the base publish plugin
        base_settings = super(VREDPublishOSBFilePlugin, self).settings or {}

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

        translator_settings = {"Translator": {"type": "dictionary", "default": None}}

        base_settings.update(translator_settings)

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

        workfile_template_setting = settings.get("Work Template")
        workfile_template = publisher.engine.get_template_by_name(
            workfile_template_setting.value
        )

        if not workfile_template:
            return False

        item.properties["work_template"] = workfile_template

        return True

    def accept(self, settings, item):
        base_accept = super(VREDPublishOSBFilePlugin, self).accept(settings, item)
        base_accept.update({"checked": False})
        base_accept.update({"visible": False})

        return base_accept

    def _translate_file(self, source_path, target_path, item):
        _rootNode = vrScenegraph.getRootNode()
        vrNodePtr = None
        for _n in range(0, _rootNode.getNChildren()):
            _childNode = _rootNode.getChild(_n)
            if _childNode.getType() == "Geometry":
                if (
                    _childNode.getName() == item.name
                    and _childNode.fields().getID() == item.properties["node_id"]
                ):
                    vrNodePtr = _childNode
                    break

        if vrNodePtr is None:
            e = "Failed to Get Node " + item.name
            self.logger.error("Error ocurred {!r}".format(e))
            raise Exception("Error ocurred {!r}".format(e))
        else:
            # Save file to publish path
            try:
                vrFileIO.saveGeometry(vrNodePtr, target_path)
            except:
                e = (
                    "Failed to save Node ( "
                    + item.name
                    + " )Geometry OSB file for "
                    + target_path
                )
                self.logger.error("Error ocurred {!r}".format(e))
                raise Exception("Error ocurred {!r}".format(e))

    def _get_target_path(self, item):
        source_path = item.properties["path"]
        work_template = item.properties.get("work_template")
        publish_template = item.properties.get("publish_template")

        if not work_template.validate(source_path):
            self.logger.warning(
                "Work file '%s' did not match work template '%s'. "
                "Publishing in place." % (source_path, work_template)
            )
            return

        fields = work_template.get_fields(source_path)
        fields["nodeName"] = item.name

        return publish_template.apply_fields(fields)

    def _copy_work_to_publish(self, settings, item):
        # Validate templates
        work_template = item.properties.get("work_template")
        if not work_template:
            self.logger.debug(
                "No work template set on the item. "
                "Skipping copy file to publish location."
            )
            return

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
            self._translate_file(source_path, target_path, item)
        except Exception as e:
            raise Exception(
                "Failed to copy work file from '%s' to '%s'.\n%s"
                % (source_path, target_path, traceback.format_exc())
            )

        self.logger.debug(
            "Copied work file '%s' to publish file '%s'." % (source_path, target_path)
        )

    def get_publish_type(self, settings, item):
        publisher = self.parent
        path = self._get_target_path(item)

        # get the publish path components
        path_info = publisher.util.get_file_path_components(path)

        # determine the publish type
        extension = path_info["extension"]

        extension = extension.lstrip(".")

        for type_def in settings["File Types"].value:
            publish_type = type_def[0]
            file_extensions = type_def[1:]

            if extension in file_extensions:
                # found a matching type in settings. use it!
                return publish_type

    def get_publish_name(self, settings, item):
        publisher = self.parent
        path = self._get_target_path(item)

        # get the publish path components
        path_info = publisher.util.get_file_path_components(path)

        # determine the publish type
        return path_info["filename"]

    def publish(self, settings, item):
        item.local_properties.publish_type = self.get_publish_type(settings, item)
        item.local_properties.publish_path = self._get_target_path(item)
        item.properties["publish_name"] = self.get_publish_name(settings, item)
        super(VREDPublishOSBFilePlugin, self).publish(settings, item)

    @property
    def item_filters(self):
        return ["vred.session.geometry"]
