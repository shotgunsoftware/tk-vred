# Copyright (c) 2023 Autodesk.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk.

import os

from .base import VREDPyBase


class VREDPyMaterial(VREDPyBase):
    """VRED Python API material helper class."""

    # Constants
    # ----------------------------------------------------------------------------------------
    # This is the prefix given to VRED Material Assets
    VRED_MATERIAL_ASSET_NAME_PREFIX = "MAT_"


    def __init__(self, vred_py):
        """Initialize"""
        super(VREDPyMaterial, self).__init__(vred_py)


    # Material v1 and v2 handling
    # ----------------------------------------------------------------------------------------

    def get_material_v2(self, material_v1):
        """
        Convert the v1 material object to a v2 material object.

        :param material_v1: The v1 material object.
        :type material_v1: vrMaterialPtr

        :return: The v2 material object.
        :rtype: vrdMaterial
        """

        material_id = material_v1.getID()
        return self.vred_py.vrMaterialService.getMaterialFromId(material_id)

    def get_material_v1(self, material_v2):
        """
        Convert the v1 material object to a v2 material object.

        :param material_v1: The v1 material object.
        :type material_v1: vrMaterialPtr

        :return: The v2 material object.
        :rtype: vrdMaterial
        """

        raise NotImplementedError()

    # General Material methods
    # ----------------------------------------------------------------------------------------

    def delete_material(self, material):
        """
        Convenience method to delete a signle materials and clean up associated ShotGrid data.
        """

        self.delete_materials([material])

    def delete_materials(self, materials):
        """
        Convenience method to delete the materials and clean up associated ShotGrid data.
        """

        self.vred_py.remove_shotgrid_metadata(materials)
        self.vred_py.vrMaterialService.deleteMaterials(materials)

    # Retrieving & Searching Materials and Material Nodes
    # ----------------------------------------------------------------------------------------

    def find_material_by_metadata(self, metadata):
        """
        Find and return the material that matches the given metadata.

        This find method searches by material nodes, since the VRED API is limited to searching
        for materials by name.

        :param metadata: A list of tuples defining the metadata to search for the material by.
            The tuples contain (1) the metadata key (2) the metadata value.
        :type metadata: List[Tuple[key,value]]

        :return: The material matching the metadata.
        :rtype: vrdMaterial
        """

        def __compare_metadata(m1, m2):
            """Return True if the metadata are equal."""
            for m1_key, m1_value in m1.items():
                if isinstance(m2, dict):
                    m2_value = m2.get(m1_key)
                else:
                    m2_value = self.vred_py.get_metadata_value(m2, m1_key)

                if isinstance(m1_value, dict):
                    # Traverse nested metadata dictionaries to get to values to compare
                    if not __compare_metadata(m1_value, m2_value):
                        return False
                else:
                    # Compare the values
                    if not m1_value == m2_value:
                        return False
            return True

        def __has_metadata(node, metadata):
            """Return True if the node holds the material, else False."""
            if not node.isType(self.vred_py.vrdMaterialNode):
                return False
            material = node.getMaterial()
            if not material:
                return False
            if not self.vred_py.vrMetadataService.hasMetadata(material):
                return False

            material_metadata = self.vred_py.vrMetadataService.getMetadata(material)
            if not __compare_metadata(metadata, material_metadata):
                return False

            return True  # Material metadata matched


        material_nodes = self.vred_py.vrNodeService.findNodes(
            lambda n, m=metadata: __has_metadata(n, m),
            root=self.vred_py.vrMaterialService.getMaterialRoot(),
        )
        if not material_nodes:
            return None
        if len(material_nodes) > 1:
            print("Found more than one material node-----------------------------")
            # raise Exception("Found more than one material node")
        return material_nodes[0].getMaterial()

    def find_material_node_by_material(self, material):
        """
        Find and return the material node that holds the material.

        This method is more robust that using the VRED API findMaterialNode function, since
        findMaterialNode will search for the node based on the material name. This means that
        if there are multipl materials with the same name, this could return the incorrect
        node.
        """

        def __has_material(node, material):
            """Return True if the node holds the material, else False."""
            if not node.isType(self.vred_py.vrdMaterialNode):
                return False
            node_material = node.getMaterial()
            if not node_material:
                return False
            return node_material.getObjectId() == material.getObjectId()

        return self.vred_py.vrNodeService.findNodes(
            lambda n, m=material: __has_material(n, m),
            root=self.vred_py.vrMaterialService.getMaterialRoot(),
        )

    # Data Validation methods

    def get_materials(self, items):
        """
        Return a list of material objects.

        NOTE: this method could be improved with latest VRED API capabilitie

        :param items: The list of items to convert to materials. This list may contain
            material names (str), ids (int), or objects (vrdMaterial).
        :type items: list

        :return: The list of materials converted from the given items.
        :rtype: list<vrdMaterial>
        """

        materials = []
        if not items:
            return materials

        if not isinstance(items, (list, tuple)):
            items = [items]

        for item in items:
            if isinstance(item, dict):
                item = item.get("id")

            mat = None
            if isinstance(item, self.vred_py.vrdMaterial):
                mat = item
            elif isinstance(item, int):
                mat = self.vred_py.vrMaterialService.getMaterialFromId(item)
            else:
                try:
                    mat = self.vred_py.vrMaterialService.findMaterial(item)
                except Exception:
                    pass

            if mat:
                materials.append(mat)
            else:
                raise self.vred_py.VREDPyError(
                    "Failed to convert object {} to material".format(item)
                )

        return materials

    def find_materials(self, using_orange_peel=None, using_texture=None):
        """
        Return a list of materials matching the given parameters.

        NOTE: this method could be improved with latest VRED API capabilities

        :param using_orange_peel:
            True  - return materials that have the clearcoat property and have set to use
                    Orange Peel
            False - return materials that have the clearcoat property and have set to not
                    use Orange Peel
            None  - ignore this property (default)
        :type using_orange_peel: bool
        :param using_texture:
            True  - return materials that have the bump texture property and have set to use
                    texture
            False - return materials that have the clearcoat property and have set to not use
                    texture
            None  - ignore this property (default)
        :type using_texture: bool

        :return: The list of materials.
        :rtype: list<vrdMaterial>
        """

        mats = self.vred_py.vrMaterialService.getAllMaterials()

        if using_orange_peel is None and using_texture is None:
            return mats

        result = []
        for mat in mats:
            # Check clearcoat orange peel property, if specified.
            if using_orange_peel is not None:
                try:
                    clearcoat = mat.getClearcoat()
                except AttributeError:
                    # This material does not have the clearcoat property. Do not accept it.
                    continue

                mat_supports_orange_peel = clearcoat.supportsOrangePeel()
                if not mat_supports_orange_peel:
                    # This material does not support the clearcoat property. Do not accept it.
                    continue

                clearcoat_off = (
                    clearcoat.getType() == self.vred_py.vrdClearcoat.Type.Off
                )
                if clearcoat_off:
                    # This material has clearcoat turned off. Do not accept it.
                    continue

                mat_using_orange_peel = clearcoat.getUseOrangePeel()
                if using_orange_peel != mat_using_orange_peel:
                    # This material clearcoat value does not match the desired value. Do not accept it.
                    continue

            # Check bump texture property, if specified.
            if using_texture is not None:
                try:
                    bump_texture = mat.getBumpTexture()
                except AttributeError:
                    bump_texture = None

                if not bump_texture or using_texture != bump_texture.getUseTexture():
                    continue

            # Material accepted, add it to the results list
            result.append(mat)

        return result

    # VRED Material Asset handling
    # ----------------------------------------------------------------------------------------

    def get_material_asset_name_from_path(self, path):
        """
        Return the based VRED Material Asset name from the file path.
        """

        prefix_len = len(self.VRED_MATERIAL_ASSET_NAME_PREFIX)
        full_name = os.path.basename(path)[prefix_len:]
        base_name, _ = os.path.splitext(full_name)
        return base_name


    # ShotGrid material handling
    # ----------------------------------------------------------------------------------------

    def get_shotgrid_material_nodes(self):
        """Return the list of vrdMaterialNode objects under the ShotGrid Materials Group."""

        def __has_shotgrid_metadata(node):
            """Return True if the node holds the material, else False."""
            if not node.isType(self.vred_py.vrdMaterialNode):
                return False
            material = node.getMaterial()
            if not material:
                return False
            return self.vred_py.has_shotgrid_metadata(material)  

        material_nodes = self.vred_py.vrNodeService.findNodes(
            lambda n: __has_shotgrid_metadata(n),
            root=self.vred_py.vrMaterialService.getMaterialRoot(),
        )
        return material_nodes
