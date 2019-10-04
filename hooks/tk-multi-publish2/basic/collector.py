﻿# Copyright (c) 2017 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import re

import sgtk
import vrScenegraph

HookBaseClass = sgtk.get_hook_baseclass()


class VREDSessionCollector(HookBaseClass):
    """
    Collector that operates on the vred session. Should inherit from the basic
    collector hook.
    """
    @property
    def settings(self):
        """
        Dictionary defining the settings that this collector expects to receive
        through the settings parameter in the process_current_session and
        process_file methods.

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

        # grab any base class settings
        collector_settings = super(VREDSessionCollector, self).settings or {}

        # settings specific to this collector
        vred_session_settings = {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for artist work files. Should "
                               "correspond to a template defined in "
                               "templates.yml. If configured, is made available"
                               "to publish plugins via the collected item's "
                               "properties. ",
            },
        }

        # update the base settings with these settings
        collector_settings.update(vred_session_settings)

        return collector_settings

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current scene open in a DCC and parents a subtree of items
        under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance
        """
        publisher = self.parent
        operations = publisher.engine.operations

        # get the path to the current file
        path = operations.get_current_file()

        # create an item representing the current VRED session
        item = self.collect_current_vred_session(settings, parent_item)

        # look at the render folder to find rendered images on disk
        self.collect_rendered_images(item)
        # self._collect_session_renders(item)
        self._collect_geometries(item, path)

    def collect_current_vred_session(self, settings, parent_item):
        """
        Creates an item that represents the current VRED session.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance

        :returns: Item of type vred.session
        """

        publisher = self.parent
        operations = publisher.engine.operations

        # get the path to the current file
        path = operations.get_current_file()

        # determine the display name for the item
        if path:
            file_info = publisher.util.get_file_path_components(path)
            display_name = file_info["filename"]
        else:
            display_name = "Current VRED Session"

        # create the session item for the publish hierarchy
        session_item = parent_item.create_item(
            "vred.session",
            "VRED Session",
            display_name
        )

        # get the icon path to display for this item
        icon_path = os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "vred.png"
        )
        session_item.set_icon_from_path(icon_path)

        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")
        if work_template_setting:
            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value)

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            session_item.properties["work_template"] = work_template
            self.logger.debug("Work template defined for VRED collection.")

        self.logger.info("Collected current VRED scene")

        # Need to store the path on properties to backward compatibility
        # TODO: clean LMV plugin to remove the path query
        session_item.properties["path"] = path

        return session_item

    def collect_rendered_images(self, parent_item):
        """
       Creates items for any image sequence or single image that
       can be found in the render folder.

       :param parent_item: Parent Item instance
       :return:
       """

        publisher = self.parent
        operations = publisher.engine.operations

        render_path = operations.get_render_path()
        render_folder = os.path.dirname(render_path)

        if not os.path.isdir(render_folder):
            self.logger.info("Render folder doesn't exist on disk. Skip image collection.")
            return

        # build the pattern we'll use to collect all the images on disk
        # corresponding to the current render path
        file_name, file_ext = os.path.splitext(os.path.basename(render_path))
        regex_pattern = r"{0}(?P<aov_name>-\D+)*(?P<frame>-\d+)*\{1}".format(file_name, file_ext)

        # go through all the files of the render folder to find the render images
        render_files = {}
        for f in os.listdir(render_folder):

            m = re.search(regex_pattern, f)
            if not m:
                continue

            aov_name = None if not m.group("aov_name") else m.group("aov_name")[1:]

            # image sequence case
            if m.group("frame"):
                # replace the frame number by a * character to have the sequence name without any frame number
                sequence_path = re.sub(
                    r"-\d+{0}".format(file_ext),
                    "-*{0}".format(file_ext),
                    f
                )
                if sequence_path not in render_files.keys():
                    render_files[sequence_path] = {
                        "aov_name": aov_name,
                        "is_sequence": True,
                        "render_paths": []
                    }
                    render_files[sequence_path]["render_paths"].append(f)

            # single image case
            else:
                render_files[f] = {
                    "aov_name": aov_name,
                    "is_sequence": False
                }

        for f, rd in render_files.iteritems():

            if rd["is_sequence"]:
                item = super(VREDSessionCollector, self)._collect_file(
                    parent_item,
                    os.path.join(render_folder, rd["render_paths"][0]),
                    frame_sequence=True
                )
                icon_path = os.path.join(render_folder, rd["render_paths"][0])

            else:
                item = super(VREDSessionCollector, self)._collect_file(
                    parent_item,
                    os.path.join(render_folder, f),
                    frame_sequence=False
                )
                icon_path = os.path.join(render_folder, f)

            item.set_icon_from_path(icon_path)
            if rd["aov_name"]:
                item.name = "%s (Render Pass: %s)" % (item.name, rd["aov_name"])

    def _collect_geometries(self, parent_item, parent_path):
        """
        Creates items for osb to be exported.

        :param parent_item: Parent Item instance
        :param parent_path: Parent path
        """

        # get the icon path to display for this item
        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "publish_vred_osb.png")
        
        rootNode = vrScenegraph.getRootNode()
        for n in range(0, rootNode.getNChildren()):
            childNode = rootNode.getChild(n)

            if childNode.getType() != "Geometry":
                continue

            fieldAcc = childNode.fields()
            item = super(VREDSessionCollector, self)._collect_file(parent_item, parent_path)
            item.name = childNode.getName()
            item.type = 'vred.session.geometry'
            item.display_type = 'Geometry Node'
            item.properties['node_id'] = fieldAcc.getID()
            item.set_icon_from_path(icon_path)
