# Copyright (c) 2021 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

from sgtk.platform.qt import QtCore, QtGui


class DockWidget(QtGui.QDockWidget):
    """
    Subclass :class:`sgtk.platform.qt.QtGui.QDockWidget` to customize functionality
    for docking widgets within VRED.
    """

    def __init__(self, title, main_window, widget_id, widget, closable, dock_area=None):
        """
        Constructor calls the parent constructor and then sets up and performs any
        custom functionality.
        """

        super(DockWidget, self).__init__(title, main_window)

        self._widget_id = widget_id
        self._closable = closable

        if not closable:
            # Hide the close button while the widget is docked. On some OS platforms,
            # the close button will always show when the widget is not floating (not
            # docked) -- this will be handled by overriding the closeEvent method.
            self.setFeatures(self.features() & ~QtGui.QDockWidget.DockWidgetClosable)

        self.setWidget(widget)
        self.dock_to_parent()

    @property
    def widget_id(self):
        """
        Get the unique identifier for the child widget.
        """

        return self._widget_id

    @property
    def closable(self):
        """
        Get whether or not the widget can be closed.
        """

        return self._closable

    @property
    def default_dock_area(self):
        """
        Get the default docking area.
        """

        return QtCore.Qt.RightDockWidgetArea

    def closeEvent(self, event):
        """
        Override the :class:`sgtk.platform.qt.QtGui.QDockWidget` :method:``closeEvent`` to prevent
        closing the widget when the property `closable` is False. The close button can be
        hidden while the widget is docked, but on some OS platforms, the close button will always
        show when the widget is floating (not docked).
        """

        if self.closable:
            super(DockWidget, self).closeEvent(event)

        else:
            # Ignore the close event to prevent the widget from closing, and set floating to False
            # to dock the widget to the area it was lasted docked.
            event.ignore()
            self.setFloating(False)

    def reinitialize(self, title, widget, dock_area=None):
        """
        Re-set the title and child widget, and add the dock widget to the main window.
        """

        dock_area = dock_area or self.default_dock_area
        self.setWindowTitle(title)
        self.setWidget(widget)
        self.dock_to_parent(dock_area)

    def dock_to_parent(self, dock_area=None):
        """
        Convenience method to dock the widget to its parent widget.
        """

        self.parentWidget().addDockWidget(dock_area or self.default_dock_area, self)
        # Show dock with minimum width
        self.parentWidget().resizeDocks([self], [0], QtCore.Qt.Horizontal)
