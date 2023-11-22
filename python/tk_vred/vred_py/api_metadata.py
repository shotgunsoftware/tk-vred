# Copyright (c) 2023 Autodesk.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk.

import json
from .base import VREDPyBase


class VREDPyMetadata(VREDPyBase):
    """VRED Python API metadata helper class."""

    # Constants
    # ----------------------------------------------------------------------------------------
    SHOTGRID_METADATA_SET_NAME = "ShotGrid"
    SHOTGRID_METADATA_KEY_PREFIX = "SG_"


    def __init__(self, vred_py):
        """Initialize"""
        super(VREDPyMetadata, self).__init__(vred_py)


    # ShotGrid Metadata
    # ----------------------------------------------------------------------------------------

    def get_shotgrid_metadata_key(self, key_name):
        """
        Conveneicne function to get the ShotGrid metadata key.
        """

        return f"{self.SHOTGRID_METADATA_KEY_PREFIX}{key_name}"

    # TODO decide on consistent function naming to include 'shotgrid' or not
    def get_metadata_value(self, metadata, key):
        """
        Convenience function to get the ShotGrid metadata.
        """

        if not metadata:
            return
        sg_key = self.get_shotgrid_metadata_key(key)
        value = metadata.getValue(sg_key)
        try:
            return json.loads(value)
        except (json.decoder.JSONDecodeError, TypeError):
            # Not a json value, just return the value as is.
            return value

    def remove_shotgrid_metadata(self, objects):
        """Remove the ShotGrid metadata from the list of objects"""

        sets_to_delete = []
        for obj in objects:
            metadata = self.vred_py.vrMetadataService.getMetadata(obj)
            metadata_sets = metadata.getSets()
            for metadata_set in metadata_sets:
                if metadata_set.getName() == self.SHOTGRID_METADATA_SET_NAME:
                    sets_to_delete.append(metadata_set)

        self.vred_py.vrMetadataService.deleteSets(sets_to_delete)
    
    def has_shotgrid_metadata(self, obj):
        """Return True if the object has ShotGrid metadata."""

        metadata = self.vred_py.vrMetadataService.getMetadata(obj)
        metadata_sets = metadata.getSets()
        for metadata_set in metadata_sets:
            if metadata_set.getName() == self.SHOTGRID_METADATA_SET_NAME:
                return True
        return False

    # Metadata for Materials
    # ----------------------------------------------------------------------------------------

    def add_metadata_to_material(self, material, sg_publish_data):
        """Convenience method to add metadata to single material."""

        self.add_metadata_to_materials([material], sg_publish_data)

    def add_metadata_to_materials(self, materials, sg_publish_data):
        """Add metadata to materials that is necessary for referencing materials."""


        # Add metadata to each materail within the ShotGrid set
        for material in materials:
            sg_metadata_set = None
            if self.vred_py.vrMetadataService.hasMetadata(material):
                # Check if it has SG metadata
                metadata = self.vred_py.vrMetadataService.getMetadata(material)
                if metadata.hasSet(self.SHOTGRID_METADATA_SET_NAME):
                    sg_metadata_set = next((s for s in metadata.getSets() if s.getName() == self.SHOTGRID_METADATA_SET_NAME), None)

            # Create the set if it does not exist
            if sg_metadata_set is None:
                sg_metadata_set = self.vred_py.vrMetadataService.createSet(self.SHOTGRID_METADATA_SET_NAME, [material])
            
            # Add the SG published file metadata to the material
            for key, value in sg_publish_data.items():
                if value is None:
                    continue
                sg_key = f"{self.SHOTGRID_METADATA_KEY_PREFIX}{key}"
                success = sg_metadata_set.setValue(sg_key, value)
                # TODO better handling of setting values of unknown data types
                if not success:
                    if isinstance(value, dict):
                        # Store it as json
                        value = json.dumps(value)
                    else:
                        value = str(value)
                    success = sg_metadata_set.setValue(sg_key, value)
                    if not success:
                        print("FAILED TO SET METADATA", sg_key, value, type(value))
                        

            # NOTE should we lock this?
            # sg_metadata_set.setLocked(True)
