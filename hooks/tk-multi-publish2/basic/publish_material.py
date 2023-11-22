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
import pprint
import json

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class VREDMaterialFilePublishPlugin(HookBaseClass):
    """Plugin for creating Material publishes in ShotGrid."""

    ############################################################################
    # standard publish plugin properties

    @property
    def icon(self):
        """Path to an png icon on disk."""

        return os.path.join(self.disk_location, os.pardir, "icons", "version_up.png")

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        return """
        Publishes the VRED Material to ShotGrid.
        """

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """

        return [
            "vred.material.item",
            "vred.session.material.item",
        ]
    
    ############################################################################
    # specific publish plugin properties

    @property
    def vredpy(self):
        """Get the VRED API module."""
        return self.parent.engine.vredpy

    ############################################################################
    # staticmethods

    @staticmethod
    def has_session(item):
        """Return True if the item has a VRED Session."""

        return item.type == "vred.session.material.item"

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

        # For a session item, ensure that it has a file path for publishing
        path = item.get_property("path")
        if path is None:
            raise AttributeError("'PublishData' object has no attribute 'path'")

        # For non-session items, check that the material has the necessary metadata
        # for publishing
        material_node = item.get_property("material_node")
        if not material_node:
            raise AttributeError("'PublishData' object has no attribute 'material_node'")

        # log the accepted file and display a button to reveal it in the fs
        self.logger.info(
            "File publisher plugin accepted: %s" % (path,),
            extra={"action_show_folder": {"path": path}},
        )

        return {"accepted": True}

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.

        Returns a boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: True if item is valid, False otherwise.
        """

        success = True

        if self.has_session(item):
            # Session specific validation
            path = item.properties.get("path")
            if not path:
                path = item.properties.get("path")
                # The session still requires saving. provide a save button.
                error_msg = "The VRED session has not been saved."
                self.logger.error(error_msg, extra=self._get_save_as_action(item))
                raise Exception(error_msg)

        material_node = item.properties.get("material_node")
        if not material_node:
            error_msg = "Failed to get VRED Material Node to publish."
            self.logger.error(error_msg)
            raise Exception(error_msg)

        material = material_node.getMaterial()
        if not material:
            error_msg = "Failed to get VRED Material to publish."
            self.logger.error(error_msg)
            raise Exception(error_msg)

        material_ptr = self._get_vred_v1_material_ptr(material.getName())
        if not material_ptr:
            error_msg = "Failed to get VRED Material pointer."
            self.logger.error(error_msg)
            raise Exception(error_msg)

        publish_path = self.get_publish_path(settings, item)
        publish_file_path = self._get_vred_save_material_path(item, publish_path)
        if os.path.exists(publish_file_path):
            error_msg = (
                "VRED Material already exists. Please uncheck this plugin "
                "or save the file to a different path."
            )
            self.logger.error(error_msg)
            raise Exception(error_msg)

        publish_vred_asset_path = self._get_vred_material_asset_path(settings, item)
        if os.path.exists(publish_vred_asset_path):
            error_msg = (
                "VRED Material Asset already exists. Please uncheck this plugin "
                "or save the file to a different path."
            )
            self.logger.error(error_msg)
            raise Exception(error_msg)

        return success

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        # TODO set up for bg publish
        # # get the publish "mode" stored inside of the root item properties
        # bg_processing = item.parent.properties.get("bg_processing", False)
        # in_bg_process = item.parent.properties.get("in_bg_process", False)

        # TODO separate out publish plugins for VRED Material (.osb) and VRED Material Asset?

        publisher = self.parent

        # Get the VRED material to publish
        material_node = item.properties.get("material_node")
        material = material_node.getMaterial()
        material_name = material.getName()
        material_ptr = self._get_vred_v1_material_ptr(material_name)

        # Get publish data
        publish_type = "VRED Material"
        publish_name = self.get_publish_name(settings, item)
        publish_version = self.get_publish_version(settings, item)
        publish_version_number = self.get_publish_version_number(settings, item)
        publish_path = self.get_publish_path(settings, item)
        publish_dependencies_paths = self.get_publish_dependencies(settings, item)
        publish_user = self.get_publish_user(settings, item)
        publish_fields = self.get_publish_fields(settings, item)
        publish_kwargs = self.get_publish_kwargs(settings, item)

        # ---- save the VRED Material to publish path

        # Get the path to the where VRED will save the material (including file name)
        publish_file_path = self._get_vred_save_material_path(item, publish_path)

        # Ensure path exists before saving material, else VRED saveMaterial function will fail.
        publisher.ensure_folder_exists(publish_path)

        # Save the VRED Material to .osb file at the publish path. VRED will use the material name as the file name.
        if not self.vredpy.vrMaterialService.saveMaterials([material], publish_path):
            error_msg = f"Failed to save material {material_name} to {publish_path}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        version_data = {"id": publish_version["id"], "type": publish_version["type"]} if publish_version else None

        self.logger.info("Registering publish...")
        publish_data = {
            "tk": publisher.sgtk,
            "context": item.context,
            "comment": item.description,
            "path": publish_file_path,
            "name": publish_name,
            "created_by": publish_user,
            "version_number": publish_version_number,
            "thumbnail_path": item.get_thumbnail_as_path(),
            "published_file_type": publish_type,
            "dependency_paths": publish_dependencies_paths,
            "dependency_ids": self._get_publish_dependency_ids(item, material),
            "sg_fields": publish_fields,
            "version_entity": version_data,
        }
        publish_data.update(publish_kwargs)
        self.logger.debug(
            "Populated Publish data...",
            extra={
                "action_show_more_info": {
                    "label": "Publish Data",
                    "tooltip": "Show the complete Publish data dictionary",
                    "text": "<pre>%s</pre>" % (pprint.pformat(publish_data),),
                }
            },
        )

        # create the publish and stash it in the item properties for other plugins to use.
        item.properties.sg_publish_data = sgtk.util.register_publish(**publish_data)
        self.logger.info("Publish registered!")
        self.logger.debug(
            "ShotGrid Publish data...",
            extra={
                "action_show_more_info": {
                    "label": "ShotGrid Publish Data",
                    "tooltip": "Show the complete ShotGrid Publish Entity dictionary",
                    "text": "<pre>%s</pre>"
                    % (pprint.pformat(item.properties.sg_publish_data),),
                }
            },
        )

        # ---- publish the VRED Material Asset files

        if self._publish_vred_material_asset(settings, item, publish_data, material_ptr, material_name):
            self.logger.info("Published VRED Material Asset!")
        else:
            self.logger.error("Failed to publish VRED Material Asset.")

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once
        all the publish tasks have completed, and can for example
        be used to version up files.

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
            super(VREDMaterialFilePublishPlugin, self).finalize(settings, item)

        # bump the session file to the next version
        if not bg_processing or (bg_processing and not in_bg_process):
            if self.has_session(item):
                self._save_to_next_version(item.properties["path"], item, self.save_file)

            # Replace current vred asset with the new published asset
            vred_asset_data = item.get_property("sg_publish_vred_material_asset_data")
            self._update_material_asset(vred_asset_data)

    def _update_material_asset(self, material_data):
        """Update the VRED Material Asset."""

        # Load the material asset that was just created and published 
        path = material_data.get("path", {}).get("local_path")
        name = self.vredpy.get_material_asset_name_from_path(path)
        # This replaces the old material (old material is deleted)
        material_v1 = self.vredpy.vrAssetsModule.loadMaterialAssetByName(name, path)
        # Convert to v2 material
        material_v2 = self.vredpy.get_material_v2(material_v1)

        # Update metadata to material. This brute forces it by removing the old first, then
        # adds the new metadata
        self.vredpy.remove_shotgrid_metadata([material_v2])
        metadata = material_data.copy()
        self.vredpy.add_metadata_to_material(material_v2, metadata)

        # # Add tags to material. First remove all existing tags.
        # existing_tags = self.vredpy.vrMetadataService.getTags([material_v2])
        # self.vredpy.vrMetadataService.removeTags([material_v2], existing_tags)
        # version_number = metadata["version_number"]
        # tags = [
        #     "ShotGrid",
        #     f"v{version_number}",
        # ]
        # self.vredpy.vrMetadataService.addTags([material_v2], tags)

        # Save changes to material 
        # self.vredpy.vrAssetsModule.createMaterialAsset(material_v1, path)

    def save_file(self, path):
        """
        A callback for saving a file.

        :param path: the file path to save.
        """

        self.parent.engine.save_current_file(path)

    ############################################################################
    # Override parent publish_material plugin methods
    #

    def get_publish_version(self, settings, item, version_name=None, fields=None):
        """Get the publish version data for the supplied settings and item."""

        # Try to extract the version data from the item or one of its ancestors
        version = self._get_property_recursive(item, "sg_version_data")
        if version:
            return version

        # Try to extract from metadata
        material_node = item.get_property("material_node")
        material = material_node.getMaterial()
        metadata = self.vredpy.vrMetadataService.getMetadata(material)
        return self.vredpy.get_metadata_value(metadata, "version")

    def get_publish_version_number(self, settings, item):
        """
        Get the publish version for the supplied settings and item.

        :param settings: This plugin instance's configured settings
        :param item: The item to determine the publish version for

        Extracts the publish version via the configured work template if
        possible. Will fall back to using the path info hook.
        """

        publish_version_number = self._get_property_recursive(item, "sg_version_number")
        if publish_version_number:
            return publish_version_number
        
        material_node = item.get_property("material_node")
        material = material_node.getMaterial()
        metadata = self.vredpy.vrMetadataService.getMetadata(material)
        version_number = self.vredpy.get_metadata_value(metadata, "version_number")
        if version_number:
            return version_number + 1

        return 1

    def get_publish_name(self, settings, item):
        """
        Get the publish name for the supplied settings and item.

        :param settings: This plugin instance's configured settings
        :param item: The item to determine the publish name for

        Uses the path info hook to retrieve the publish name.
        """

        publish_name = item.get_property("publish_name")
        if publish_name:
            return publish_name

        material_node = item.get_property("material_node")
        material = material_node.getMaterial()
        metadata = self.vredpy.vrMetadataService.getMetadata(material)
        return self.vredpy.get_metadata_value(metadata, "name")


    ############################################################################
    # Helper methods
    #

    def _get_property_recursive(self, item, property_name):
        """Get the property data from the item or from an ancestor."""

        cur_item = item
        while cur_item:
            if cur_item.get_property(property_name):
                return cur_item.properties[property_name]
            cur_item = cur_item.parent
        return None

    def _set_property_recursive(self, item, property_name, value):
        """Get the property data from the item or from an ancestor."""

        cur_item = item
        while cur_item:
            cur_item.properties[property_name] = value
            cur_item = cur_item.parent

    def _get_vred_save_material_path(self, item, material_path):
        """Return the file path created when calling VRED API saveMaterials function."""

        material_name = self._get_material_name(item)
        filename = f"{material_name}.osb"
        return os.path.join(material_path, filename)

    def _get_material_name(self, item):
        """Return the filename for the publish output.""" 

        material_node = item.properties.get("material_node")
        if not material_node:
            return None

        material = material_node.getMaterial()
        if not material:
            return None

        return material.getName()

    def _get_vred_material_asset_path(self, settings, item):
        """Return the file path to the VRED Material Asset directory for the item."""

        publish_path = self.get_publish_path(settings, item)
        material_name = self._get_material_name(item)
        folder_name = f"MAT_{material_name}"
        return os.path.join(publish_path, folder_name)

    def _get_vred_v1_material_ptr(self, material_name):
        """
        """

        # FIXME cannot access v1 findMaterial built-function to create old style material pointer
        # Workaround by selecting the material and then getting the selected material using v1 material editor
        self.vredpy.vrMaterialEditor.selectMaterialByName(material_name)
        material_ptr = self.vredpy.vrMaterialEditor.getSelectedMaterials()[0]

        if not material_ptr or not material_ptr.isValid():
            return None
        return material_ptr

    def _get_save_as_action(self, item):
        """Simple helper for returning a log action to show the "File Save As" dialog"""

        def save_as(self, item):
            sgtk.platform.current_engine().open_save_as_dialog()
            if self.vredpy.vrFileIOService:
                path = self.vredpy.vrFileIOService.getFileName()
            else:
                path = self.vredpy.vrFileIO.getFileIOFilePath()
            self._set_property_recursive(item, "path", path)

        return {
            "action_button": {
                "label": "Save As...",
                "tooltip": "Save the current session",
                "callback": lambda s=self, i=item: save_as(s, i),
            }
        }

    def _get_publish_dependency_ids(self, item, material):
        """
        """

        dependency_ids = []

        publisher = self.parent

        # Add dependencies from parent
        if item.parent and "sg_publish_data" in item.parent.properties:
            dependency_ids.append(
                item.parent.properties.sg_publish_data["id"]
            )

        # NOTE how can we reference the material that was imported and modified?
        # First try to find the reference node of the main file this material was loaded from
        nodes = self.vredpy.vrNodeService.findNodes(lambda n: n.isType(self.vredpy.vrdMaterialNode) and n.getMaterial() == material)
        reference_node = self.vredpy.vrNodeService.findNodes(lambda n: n.isType(self.vredpy.vrdReferenceNode) and n.getMaterial() == material)
        if nodes:
            # We should have only found one
            if len(nodes) > 1:
                raise Exception("Found too many material nodes")
            node = nodes[0]
            # Get the reference node
            parent = node.getParent()
            if isinstance(parent, self.vredpy.vrdReferenceNode):
                ref_path = parent.getSmartPath()
                publishes = sgtk.util.find_publish(publisher.sgtk, [ref_path])
                if not publishes:
                    ref_path = parent.getSmartPath()
                    publishes = sgtk.util.find_publish(publisher.sgtk, [ref_path])
                published_source = publishes.get(ref_path)
                if published_source:
                    dependency_ids.append(published_source["id"])

        # If the material is an X-Rite material, get the measurement and check if that belongs to a published file
        # If found, this is an upstream reference
        if isinstance(material, self.vredpy.vrdXRiteMeasuredMaterial):
            source_path = material.getMeasurement()
            publishes = sgtk.util.find_publish(publisher.sgtk, [source_path])
            published_source = publishes.get(source_path)
            if published_source:
                dependency_ids.append(published_source["id"])

        return dependency_ids

    def _publish_vred_material_asset(self, settings, item, publish_data, material_ptr, material_name):
        """
        """

        # TODO add version tag to asset

        # NOTE this requires VRED to have the material assets directory to point to ShotGrid storage

        publish_path = os.path.dirname(publish_data.get("path"))

        # Ensure the Asset Manager knows about the directory
        publish_asset_dir = publish_path.replace(os.sep, "/")
        if not os.path.exists(publish_asset_dir):
            os.makedirs(publish_asset_dir)

        self.vredpy.vrAssetsModule.reloadAssetDirectory(
            os.path.dirname(publish_asset_dir)
        )

        success = self.vredpy.vrAssetsModule.createMaterialAsset(material_ptr, publish_asset_dir)
        if not success:
            # Try one more time by reloading all directories
            self.vredpy.vrAssetsModule.reloadAllAssetDirectories()
            success = self.vredpy.vrAssetsModule.createMaterialAsset(material_ptr, publish_asset_dir)

        if success:
            # Modify publish data for the VRED Material Asset
            asset_path = self._get_vred_material_asset_path(settings, item)
            thumbnail_path = os.path.join(asset_path, f"{material_name}.png")
            publish_data["path"] = asset_path
            publish_data["published_file_type"] = "VRED Material Asset"
            if os.path.exists(thumbnail_path):
                publish_data["thumbnail_path"] = thumbnail_path
            vred_material_asset_data = sgtk.util.register_publish(**publish_data)
            item.properties["sg_publish_vred_material_asset_data"] = vred_material_asset_data
        
        return success
