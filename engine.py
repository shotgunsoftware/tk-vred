# -*- coding: utf-8 -*-

# Copyright (c) 2015 Shotgun Software Inc.
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from tank_vendor import six


class VREDEngine(sgtk.platform.Engine):
    """A VRED engine for Shotgun Toolkit."""

    def __init__(self, tk, context, engine_instance_name, env):
        self._tk_vred = None
        self.menu = None
        self.operations = None

        super(VREDEngine, self).__init__(tk, context, engine_instance_name, env)

    def post_context_change(self, old_context, new_context):
        """
        Runs after a context change has occurred.

        :param old_context: The previous context.
        :param new_context: The current context.
        """
        self.logger.debug("%s: Post context change...", self)
        if self.context_change_allowed:
            self.menu.create()

    def pre_app_init(self):
        """
        Sets up the engine into an operational state. This method called before
        any apps are loaded.
        """
        self.logger.debug("%s: Initializing..." % (self,))

        # unicode characters returned by the shotgun api need to be converted
        # to display correctly in all of the app windows
        # tell QT to interpret C strings as utf-8
        from sgtk.platform.qt import QtCore

        utf8 = QtCore.QTextCodec.codecForName("utf-8")
        QtCore.QTextCodec.setCodecForCStrings(utf8)
        self.logger.debug("set utf-8 codec for widget text")

    def post_app_init(self):
        """
        Runs after all apps have been initialized.
        """
        from sgtk.platform.qt import QtGui

        self.logger.debug("%s: Post Initializing...", self)

        # import python/tk_vred module
        self._tk_vred = self.import_module("tk_vred")

        QtGui.QApplication.instance().aboutToQuit.connect(self.quit)

        # init menu
        self.menu = self._tk_vred.VREDMenu(engine=self)
        self.menu.create()

        # init operations
        self.operations = self._tk_vred.VREDOperations(engine=self)

    def destroy_engine(self):
        """
        Called when the engine should tear down itself and all its apps.
        """
        self.logger.debug("%s: Destroying...", self)

    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed by the engine.
        """
        return True

    def current_file_closed(self):
        """
        Called when the current file is closed.
        """
        path = self.operations.get_current_file()
        if path:
            self.execute_hook_method("file_usage_hook", "file_closed", path=path)

    def quit(self):
        try:
            self.current_file_closed()
        except Exception as e:
            self.logger.exception("Error quitting vred engine")

    def _get_dialog_parent(self):
        """
        Get the QWidget parent for all dialogs created through
        show_dialog & show_modal.
        """
        return self.get_vred_main_window()

    @staticmethod
    def get_vred_main_window():
        """
        Get the VRED main window using the object created by the plugin.
        """
        from sgtk.platform.qt import QtGui
        from shiboken2 import wrapInstance
        import vrVredUi

        if six.PY2:
            window = wrapInstance(
                long(vrVredUi.getMainWindow()), QtGui.QMainWindow  # noqa
            )
        else:
            window = wrapInstance(int(vrVredUi.getMainWindow()), QtGui.QMainWindow)

        return window

    ##########################################################################################
    # panel support

    def show_panel(self, panel_id, title, bundle, widget_class, *args, **kwargs):
        """
        Docks an app widget in a VRED panel.

        :param panel_id: Unique identifier for the panel, as obtained by register_panel().
        :param title: The title of the panel
        :param bundle: The app, engine or framework object that is associated with this window
        :param widget_class: The class of the UI to be constructed. This must derive from QWidget.

        Additional parameters specified will be passed through to the widget_class constructor.

        :returns: the created widget_class instance
        """
        from sgtk.platform.qt import QtGui, QtCore

        self.logger.debug("Begin showing panel %s", panel_id)

        # If the widget already exists, do not rebuild it but be sure to display it
        for widget in QtGui.QApplication.allWidgets():
            if widget.objectName() == panel_id:
                widget.show()
                return widget

        # As VRED doesn't have a method inside it's API to dock widget, we need to create one by hand,
        # parent it to the main window and display the app widget inside
        parent = self._get_dialog_parent()

        dock_widget = QtGui.QDockWidget(parent=parent)
        dock_widget.setObjectName(panel_id)

        widget_instance = widget_class(*args, **kwargs)
        widget_instance.setParent(dock_widget)
        self._apply_external_styleshet(bundle, widget_instance)

        dock_widget.setWidget(widget_instance)
        dock_widget.show()

        parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_widget)

        return widget_instance
