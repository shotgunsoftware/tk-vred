# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.


class VREDPyBase:
    def __init__(self, vred_py):
        """Initialize the VREDPy base helper class."""

        self.__vred_py = vred_py

    @property
    def vred_py(self):
        """Get the VREDPy module to access the VRED api."""
        return self.__vred_py
