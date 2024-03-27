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


class VREDPyReference(VREDPyBase):
    """VRED Python API reference helper class."""

    def __init__(self, vred_py):
        """Initialize"""
        super(VREDPyReference, self).__init__(vred_py)

    def get_reference_by_id(self, reference_id):
        """
        Get the reference object by its id.

        :param reference_id: The id of the reference to get.
        :type reference_id: int

        :return: The reference object.
        :rtype: vrdReference
        """

        references = self.vred_py.vrReferenceService.getSceneReferences()
        for reference in references:
            if reference.getObjectId() == reference_id:
                return reference
        return None
