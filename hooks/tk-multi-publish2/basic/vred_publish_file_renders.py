# Copyright (c) 2017 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import pprint
import sys

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

        return base_settings

    def validate(self, settings, item):
        return True

    def accept(self, settings, item):
        base_accept = super(VREDPublishFileRendersPlugin, self).accept(settings, item)

        base_accept.update({"checked": False})

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

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        publisher = self.parent
        path = item.properties["path"]

        # allow the publish name to be supplied via the item properties. this is
        # useful for collectors that have access to templates and can determine
        # publish information about the item that doesn't require further, fuzzy
        # logic to be used here (the zero config way)
        publish_name = item.properties.get("publish_name")
        if not publish_name:
            self.logger.debug("Using path info hook to determine publish name.")

            # use the path's filename as the publish name
            path_components = publisher.util.get_file_path_components(path)
            publish_name = path_components["filename"]

        self.logger.debug("Publish name: %s" % (publish_name,))

        self.logger.info("Creating Version...")
        version_data = {
            "project": item.context.project,
            "code": publish_name,
            "description": item.description,
            "entity": self._get_version_entity(item),
            "sg_task": item.context.task
        }

        if "sg_publish_data" in item.properties:
            publish_data = item.properties["sg_publish_data"]
            version_data["published_files"] = [publish_data]

        version_data["sg_path_to_movie"] = path

        # log the version data for debugging
        self.logger.debug(
            "Populated Version data...",
            extra={
                "action_show_more_info": {
                    "label": "Version Data",
                    "tooltip": "Show the complete Version data dictionary",
                    "text": "<pre>%s</pre>" % (pprint.pformat(version_data),)
                }
            }
        )

        # Create the version
        version = publisher.shotgun.create("Version", version_data)
        self.logger.info("Version created!")

        # stash the version info in the item just in case
        item.properties["sg_version_data"] = version

        thumb = item.get_thumbnail_as_path()

        self.logger.info("Uploading content...")

        # on windows, ensure the path is utf-8 encoded to avoid issues with
        # the shotgun api
        if sys.platform.startswith("win"):
            upload_path = path.decode("utf-8")
        else:
            upload_path = path

        self.parent.shotgun.upload(
            "Version",
            version["id"],
            upload_path,
            "sg_uploaded_movie"
        )

        self.logger.info("Upload complete!")

    def _get_version_entity(self, item):
        """
        Returns the best entity to link the version to.
        """

        if item.context.entity:
            return item.context.entity
        elif item.context.project:
            return item.context.project
        else:
            return None

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once all the publish
        tasks have completed, and can for example be used to version up files.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        path = item.properties["path"]
        version = item.properties["sg_version_data"]

        self.logger.info(
            "Version uploaded for file: %s" % (path,),
            extra={
                "action_show_in_shotgun": {
                    "label": "Show Version",
                    "tooltip": "Reveal the version in Shotgun.",
                    "entity": version
                }
            }
        )
