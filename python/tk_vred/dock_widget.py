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
from tank_vendor import six


class DockWidget(QtGui.QDockWidget):
    """
    Subclass :class:`sgtk.platform.qt.QtGui.QDockWidget` to customize functionality
    for docking widgets within VRED.
    """

    POSITIONS = {
        "right": QtCore.Qt.RightDockWidgetArea,
        "left": QtCore.Qt.LeftDockWidgetArea,
        "top": QtCore.Qt.TopDockWidgetArea,
        "bottom": QtCore.Qt.BottomDockWidgetArea,
    }

    def __init__(
        self,
        title,
        main_window,
        widget_id,
        widget,
        closable,
        dock_area=None,
        tabbed=False,
    ):
        """
        Constructor calls the parent constructor and then sets up and performs any
        custom functionality.
        """

        super(DockWidget, self).__init__(title, main_window)

        self._widget_id = widget_id
        self._closable = closable
        self._tabbed = tabbed

        if dock_area is None:
            self._dock_area = QtCore.Qt.RightDockWidgetArea
        elif isinstance(dock_area, six.string_types):
            self._dock_area = self.POSITIONS.get(
                dock_area, QtCore.Qt.RightDockWidgetArea
            )
        else:
            self._dock_area = dock_area

        if not closable:
            # Hide the close button while the widget is docked. On some OS platforms,
            # the close button will always show when the widget is not floating (not
            # docked) -- this will be handled by overriding the closeEvent method.
            self.setFeatures(self.features() & ~QtGui.QDockWidget.DockWidgetClosable)

        self.setWidget(widget)

    def __eq__(self, other):
        """
        Override the equality operator to compare dock widgets.

        A dock widget is equal to another dock widget if they have the same widget id.
        """

        if isinstance(other, DockWidget):
            return self.widget_id == other.widget_id
        return False

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
    def dock_area(self):
        """
        Get or set the docking area for this widget.
        """

        return self._dock_area

    @dock_area.setter
    def dock_area(self, value):
        self._dock_area = value

    @property
    def tabbed(self):
        """
        Get or set the flag indicating if the widget is tabbed when docked.
        """

        return self._tabbed

    @tabbed.setter
    def tabbed(self, value):
        self._tabbed = value

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

    def reinitialize(self, title, widget, tabify_widget=None):
        """
        Re-set the title and child widget, and add the dock widget to the main window.

        :param title: the title to display on the dock widget
        :type title: str
        :param widget: the widget to set for this dock widget
        :type widget: QtGui.QWidget
        :param tabify_widget: (optional) the widget to put in a tab group with this dock widget
        :type tabify_widget: DockWidget
        """

        self.setWindowTitle(title)
        self.setWidget(widget)
        self.dock_to_parent(tabify_widget)

    def dock_to_parent(self, tabify_widget=None):
        """
        Convenience method to dock the widget to its parent widget.

        :param tabify_widget: (optional) the widget to put in a tab group with this dock widget
        :type tabify_widget: DockWidget
        """

        if tabify_widget and self.tabbed:
            self.parentWidget().tabifyDockWidget(tabify_widget, self)
        else:
            self.parentWidget().addDockWidget(self.dock_area, self)

        # Show dock with minimum width
        self.parentWidget().resizeDocks([self], [0], QtCore.Qt.Horizontal)
