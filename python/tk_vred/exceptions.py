# Copyright (c) 2021 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.


class VREDEngineException(Exception):
    """
    Base class for custom tk-vred exceptions.
    """


class FileNotFound(VREDEngineException):
    """
    Raised when VRED Engine cannot proceed due to an invalid file path.
    """
