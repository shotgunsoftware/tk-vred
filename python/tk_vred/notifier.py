# Copyright (c) 2024 Autodesk Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk Inc.

from sgtk.platform.qt import QtCore


class VREDNotifier(QtCore.QObject):
    """Class to define Qt signals for VRED events."""

    # Signal emitted when files have finished importing in VRED. The signal
    # carries the result of the import operation (0 for failure, 1 for success)
    file_import_finished = QtCore.Signal()
