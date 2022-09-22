# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import sgtk
from sgtk.platform.qt import QtGui

HookBaseClass = sgtk.get_hook_baseclass()


class VREDUIConfig(HookBaseClass):
    """
    Hook to customize the display of the Data Validation App.

    This is just the start to customizing the app display. For now, there is only one method
    available to customize the background color of the rule itms in the view. More to follow.
    """

    def get_rule_item_background_color(self, index):
        """
        Return the color to use as the background color for a Validation Rule in the view.

        :return: The background color.
        :rtype: QtGui.QColor
        """

        return QtGui.QApplication.palette().alternateBase()