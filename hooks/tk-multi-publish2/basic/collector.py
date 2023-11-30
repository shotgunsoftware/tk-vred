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
import tempfile

import sgtk
from sgtk.platform.qt import QtGui

import vrRenderSettings

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
            "Background Processing": {
                "type": "bool",
                "default": False,
                "description": "Boolean to turn on/off the background publishing process.",
            },
        }

        # update the base settings with these settings
        collector_settings.update(vred_session_settings)

        return collector_settings

    @property
    def vredpy(self):
        """Get the VRED api module."""
        return self.parent.engine.vredpy

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current scene open in a DCC and parents a subtree of items
        under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance
        """
        # create an item representing the current VRED session
        item = self.collect_current_vred_session(settings, parent_item)

        # Collect the materail items for Material context
        self.collect_materials(item)

        # look at the render folder to find rendered images on disk
        self.collect_rendered_images(item)

    def collect_current_vred_session(self, settings, parent_item):
        """
        Creates an item that represents the current VRED session.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance

        :returns: Item of type vred.session
        """

        publisher = self.parent
        vredpy = publisher.engine.vredpy

        # store the Batch Processing settings in the root item properties
        bg_processing = settings.get("Background Processing")
        if bg_processing:
            parent_item.properties["bg_processing"] = bg_processing.value

        # get the path to the current file
        path = self.vredpy.vrFileIO.getFileIOFilePath()

        # determine the display name for the item
        if path:
            file_info = publisher.util.get_file_path_components(path)
            display_name = file_info["filename"]
        else:
            display_name = "Current VRED Session"

        # create the session item for the publish hierarchy
        session_item = parent_item.create_item(
            "vred.session", "VRED Session", display_name
        )

        # get the icon path to display for this item
        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "vred.png")
        session_item.set_icon_from_path(icon_path)

        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")
        if work_template_setting:
            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value
            )

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            session_item.properties["work_template"] = work_template
            self.logger.debug("Work template defined for VRED collection.")

        # TODO do the same for the object metadata / publish_metadata plugin
        # Find metadata sets
        asset_name = session_item.context.entity.get("name")
        all_metadata_sets = vredpy.vrMetadataService.getAllSets()
        metadata_sets = []
        for metadata_set in all_metadata_sets:
            parent_asset = metadata_set.getValue("SG_parent_asset")
            if parent_asset == asset_name:
                metadata_sets.append(metadata_set)
        if metadata_sets:
            metadata_set_group_item = session_item.create_item(
                "vred.session.metadata_set", "Metadata Sets", asset_name,
            )
            for metadata_set in metadata_sets:
                metadata_set_item = metadata_set_group_item.create_item(
                    "vred.session.metadata_set.item", "Metadata Set", metadata_set.getName(),
                )
                metadata_set_item.properties["metadata_set"] = metadata_set
                # NOTE do we need this?
                metadata_set_item.properties["path"] = path
            
        self.logger.info("Collected current VRED scene")

        # Need to store the path on properties to backward compatibility
        # TODO: clean LMV plugin to remove the path query
        session_item.properties["path"] = path

        # Set a default thumbnail as the current VRED viewport
        session_item.thumbnail = self._get_thumbnail_pixmap()

        return session_item

    def collect_rendered_images(self, parent_item):
        """
        Creates items for any image sequence or single image that
        can be found in the render folder.

        :param parent_item: Parent Item instance
        :return:
        """

        render_path = self.vredpy.vrRenderSettings.getRenderFilename()
        render_folder = os.path.dirname(render_path)

        if not os.path.isdir(render_folder):
            self.logger.info(
                "Render folder doesn't exist on disk. Skip image collection."
            )
            return

        # build the pattern we'll use to collect all the images on disk
        # corresponding to the current render path
        file_name, file_ext = os.path.splitext(os.path.basename(render_path))
        regex_pattern = r"{0}(?P<render_pass>-\D+)*(?P<frame>-\d+)*\{1}".format(
            file_name, file_ext
        )

        # go through all the files of the render folder to find the render images
        render_files = {}
        for f in os.listdir(render_folder):

            m = re.search(regex_pattern, f)
            if not m:
                continue

            render_pass = (
                None if not m.group("render_pass") else m.group("render_pass")[1:]
            )

            # image sequence case
            if m.group("frame"):
                # replace the frame number by a * character to have the sequence name without any frame number
                sequence_path = re.sub(
                    r"-\d+{0}".format(file_ext), "-*{0}".format(file_ext), f
                )
                if sequence_path not in render_files.keys():
                    render_files[sequence_path] = {
                        "render_pass": render_pass,
                        "is_sequence": True,
                        "render_paths": [],
                    }
                render_files[sequence_path]["render_paths"].append(
                    os.path.join(render_folder, f)
                )

            # single image case
            else:
                render_files[f] = {"render_pass": render_pass, "is_sequence": False}

        for f, rd in render_files.items():

            self.logger.info("Processing render sequence path: {}".format(f))

            if rd["is_sequence"]:
                item = super(VREDSessionCollector, self)._collect_file(
                    parent_item, rd["render_paths"][0], frame_sequence=True
                )
                icon_path = rd["render_paths"][0]
                item.properties["sequence_paths"] = rd["render_paths"]

            else:
                item = super(VREDSessionCollector, self)._collect_file(
                    parent_item, os.path.join(render_folder, f), frame_sequence=False
                )
                icon_path = os.path.join(render_folder, f)

            # fill in some item properties manually
            item.type = "vred.session.image"
            item.type_display = "VRED Rendering"
            item.properties["publish_type"] = "Rendered Image"
            item.set_icon_from_path(icon_path)

            if rd["render_pass"]:
                item.name = "%s (Render Pass: %s)" % (item.name, rd["render_pass"])

    def collect_materials(self, session_item):
        """
        Creates an item that represents the current VRED session materials.

        :param settings: Configured settings for this collector
        :type settings: dict
        :param parent_item: The VRED session item instance
        :type parent_item: :class:`PublishItem`

        :returns: Item of type vred.session.material
        """

        # TODO bg publishing

        publisher = self.parent
        vredpy = publisher.engine.vredpy

        material_nodes = vredpy.get_shotgrid_material_nodes()
        if not material_nodes:
            return None

        # Get info from the VRED session item
        path = session_item.properties["path"]
        work_template = session_item.properties["work_template"]

        # Create the material group item
        material_group_item = session_item.create_item(
            "vred.session.material", "VRED", "Materials"
        )
        material_icon_path = os.path.join(self.disk_location, os.pardir, "icons", "material.png")
        material_group_item.set_icon_from_path(material_icon_path)

        # Create the material items (under the group)
        for material_node in material_nodes:
            material = material_node.getMaterial()
            material_name = material.getName()
            material_node_item = material_group_item.create_item(
                "vred.session.material.item", "VRED Material", material_name
            )
            material_node_item.properties["material_node"] = material_node
            material_node_item.properties["path"] = path
            material_node_item.properties["work_template"] = work_template
            material_node_item.set_icon_from_path(material_icon_path)

        return material_group_item
    def _get_thumbnail_pixmap(self):
        """
        Generate a thumbnail from the current VRED viewport.

        :return: A thumbnail of the current VRED viewport.
        :rtype: QtGui.QPixmap
        """

        pixmap = None
        thumbnail_path = None

        try:
            thumbnail_path = tempfile.NamedTemporaryFile(
                suffix=".jpg", prefix="sgtk_thumb", delete=False
            ).name
            self.vredpy.vrMovieExport.createSnapshotFastInit(800, 600)
            self.vredpy.vrMovieExport.createSnapshotFast(thumbnail_path)
            self.vredpy.vrMovieExport.createSnapshotFastTerminate()
            pixmap = QtGui.QPixmap(thumbnail_path)
        except Exception as e:
            self.logger.error(f"Failed to set default thumbnail: {e}")
        finally:
            try:
                os.remove(thumbnail_path)
            except:
                pass

        return pixmap
