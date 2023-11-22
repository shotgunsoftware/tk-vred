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
import json

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class VREDMaterialsCollector(HookBaseClass):
    """Collector for VRED Materials."""

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
        collector_settings = super(VREDMaterialsCollector, self).settings or {}

        # settings specific to this collector
        vred_session_settings = {
            "Background Processing": {
                "type": "bool",
                "default": False,
                "description": "Boolean to turn on/off the background publishing process.",
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

        # TODO bg publishing

        return self.collect_materials(parent_item)

    def collect_materials(self, parent_item):
        """
        Creates an item that represents the current VRED session materials.

        :param settings: Configured settings for this collector
        :type settings: dict
        :param parent_item: The VRED session item instance
        :type parent_item: :class:`PublishItem`

        :returns: Item of type vred.session.material
        """

        publisher = self.parent
        vredpy = publisher.engine.vredpy

        material_nodes = vredpy.get_shotgrid_material_nodes()
        if not material_nodes:
            return None

        # Create the material group item
        material_group_item = parent_item.create_item(
            "vred.material", "VRED", "Materials"
        )
        material_icon_path = os.path.join(self.disk_location, os.pardir, "icons", "material.png")
        material_group_item.set_icon_from_path(material_icon_path)

        # Create the material items (under the group)
        for material_node in material_nodes:
            material = material_node.getMaterial()
            material_node_item = material_group_item.create_item(
                "vred.material.item", "VRED Material", material.getName()
            )
            material_node_item.set_icon_from_path(material_icon_path)

            # Get the material data from the VRED metadata
            material = material_node.getMaterial()
            metadata = vredpy.vrMetadataService.getMetadata(material)
            path = vredpy.get_metadata_value(metadata, "path")["local_path"]
            material_task = vredpy.get_metadata_value(metadata, "task")
            material_entity = vredpy.get_metadata_value(metadata, "entity")

            material_node_item.properties["material_node"] = material_node
            material_node_item.properties["material_entity"] = material_entity
            material_node_item.properties["material_task"] = material_task
            material_node_item.properties["path"] = path

        return material_group_item

