# Copyright (c) 2023 Autodesk.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk.

from .base import VREDPyBase


class VREDPyMaterial(VREDPyBase):
    """VRED Python API material helper class."""

    def __init__(self, vred_py):
        """Initialize"""
        super(VREDPyMaterial, self).__init__(vred_py)

    def get_materials(self, items):
        """
        Return a list of material objects.

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
