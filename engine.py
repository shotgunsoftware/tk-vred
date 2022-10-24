# Copyright (c) 2020 Autodesk Inc.
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk Inc.

import logging
import os
import re

import sgtk
from tank_vendor import six


class VREDEngine(sgtk.platform.Engine):
    """A VRED engine for ShotGrid Toolkit."""

    def __init__(self, tk, context, engine_instance_name, env):
        """Class Constructor"""

        self._tk_vred = None
        self._menu_generator = None
        self.vred_version = None
        self._dock_widgets = {}
        self._tabbed_dock_widgets = {}
        self._vredpy = None

        super(VREDEngine, self).__init__(tk, context, engine_instance_name, env)

    @property
    def has_ui(self):
        """
        Detect and return if VRED is running in interactive/non-interactive mode
        """
        # for now, we don't have a method in VRED to get the execution mode
        # so, we're assuming that if we can't access to the menubar, we're running VRED in non-ui mode
        menubar = self._get_dialog_parent().menuBar()
        if menubar and menubar.isVisible() and menubar.isEnabled():
            return True
        else:
            return False

    @property
    def vredpy(self):
        """Return the VRED Python API helper module."""
        if not self._vredpy:
            # Create the VREDPy object on first access, if we have access to the tk_vred module
            if self._tk_vred:
                self._vredpy = self._tk_vred.VREDPy()
        return self._vredpy

    def post_context_change(self, old_context, new_context):
        """
        Runs after a context change has occurred.

        :param old_context: The previous context.
        :param new_context: The current context.
        """

        self.logger.debug("{}: Post context change...".format(self))

        # Rebuild the menu on context change.
        if self.has_ui:
            self.menu_generator.create_menu()

    def pre_app_init(self):
        """
        Sets up the engine into an operational state. This method called before
        any apps are loaded.
        """

        self.logger.debug("{}: Initializing...".format(self))

        # unicode characters returned by the ShotGrid api need to be converted
        # to display correctly in all of the app windows
        # tell QT to interpret C strings as utf-8
        from sgtk.platform.qt import QtCore, QtGui

        utf8 = QtCore.QTextCodec.codecForName("utf-8")
        QtCore.QTextCodec.setCodecForCStrings(utf8)
        self.logger.debug("set utf-8 codec for widget text")

        # Temporarily monkey patch QToolButton and QMenu to resolve a Qt 5.15.0 bug (seems that it will fixed in 5.15.1)
        # where QToolButton menu will open only on primary screen.
        if self.has_ui:
            self._monkey_patch_qtoolbutton()
            self._monkey_patch_qmenu()

        # import python/tk_vred module
        self._tk_vred = self.import_module("tk_vred")

        # check for version compatibility
        self.vred_version = os.getenv("TK_VRED_VERSION", None)
        self.logger.debug("Running VRED version {}".format(self.vred_version))
        if (
            self._version_check(
                self.vred_version,
                str(self.get_setting("compatibility_dialog_min_version")),
            )
            > 0
        ):
            msg = (
                "The ShotGrid Pipeline Toolkit has not yet been fully tested with VRED {version}. "
                "You can continue to use the Toolkit but you may experience bugs or "
                "instability.  Please report any issues you see to {support_url}".format(
                    version=self.vred_version, support_url=sgtk.support_url
                )
            )
            self.logger.warning(msg)
            if self.has_ui:
                QtGui.QMessageBox.warning(
                    self._get_dialog_parent(),
                    "Warning - ShotGrid Pipeline Toolkit!",
                    msg,
                )
        elif self._version_check(self.vred_version, "2021.0") < 0 and self.get_setting(
            "compatibility_dialog_old_version"
        ):
            msg = (
                "The ShotGrid Pipeline Toolkit is not fully capable with VRED {version}. "
                "You should consider upgrading to a more recent version of VRED. "
                "Please report any issues you see to {support_url}".format(
                    version=self.vred_version, support_url=sgtk.support_url
                )
            )
            self.logger.warning(msg)
            if self.has_ui:
                QtGui.QMessageBox.warning(
                    self._get_dialog_parent(),
                    "Warning - ShotGrid Pipeline Toolkit!",
                    msg,
                )

    def post_app_init(self):
        """
        Runs after all apps have been initialized.
        """

        self.logger.debug("{}: Post Initializing...".format(self))

        # Init menu
        if self.has_ui:
            self.menu_generator.create_menu(clean_menu=False)

        # Run a series of app instance commands at startup.
        self._run_app_instance_commands()

        # Hide the Shotgun entry from the VRED Scripts menu
        if self.has_ui:
            self._hide_menu_in_scripts()

    def destroy_engine(self):
        """
        Called when the engine should tear down itself and all its apps.
        """
        self.logger.debug("{}: Destroying...".format(self))

        # Clean up the menu and clear the menu generator
        if self.has_ui:
            self.menu_generator.clean_menu()
            self._menu_generator = None

        for widget in self._dock_widgets.values():
            widget.deleteLater()
            widget = None
        self._dock_widgets.clear()
        self._tabbed_dock_widgets.clear()

        # Close all ShotGrid app dialogs that are still opened since
        # some apps do threads cleanup in their onClose event handler
        # Note that this function is called when the engine is restarted (through "Reload Engine and Apps")

        # Important: Copy the list of dialogs still opened since the call to close() will modify created_qt_dialogs
        dialogs_still_opened = self.created_qt_dialogs[:]

        for dialog in dialogs_still_opened:
            dialog.close()

    @property
    def context_change_allowed(self):
        """Specifies that context changes are allowed by the engine."""
        return True

    @property
    def menu_generator(self):
        """Menu generator to help the engine manage the ShotGrid menu in VRED."""
        if self._menu_generator is None:
            self._menu_generator = self._tk_vred.VREDMenuGenerator(engine=self)

        return self._menu_generator

    def _get_dialog_parent(self):
        """Get the QWidget parent for all dialogs created through show_dialog & show_modal."""
        from sgtk.platform.qt import QtGui
        from shiboken2 import wrapInstance

        if self.vredpy:
            vrVredUi = self.vredpy.vrVredUi
        else:
            import vrVredUi

        if six.PY2:
            window = wrapInstance(
                long(vrVredUi.getMainWindow()), QtGui.QMainWindow  # noqa
            )
        else:
            window = wrapInstance(int(vrVredUi.getMainWindow()), QtGui.QMainWindow)

        return window

    def _hide_menu_in_scripts(self):
        """
        Remove the entry in the VRED Scripts menu.

        If running in VRED Design also remove the Scripts menu itself.
        """
        main_window = self._get_dialog_parent()
        menu_actions = main_window.menuBar().actions()
        scripts_action = next(
            (
                menu_action
                for menu_action in menu_actions
                if menu_action.text() == "Scripts"
            ),
            None,
        )
        if scripts_action:
            shotgun_action = next(
                (
                    submenu_action
                    for submenu_action in scripts_action.menu().actions()
                    if submenu_action.text() == "Shotgun"
                ),
                None,
            )

            # Remove the Shotgun entry from the Scripts menu
            if shotgun_action:
                shotgun_action.setVisible(False)
            # Also remove the Scripts menu in VRED Design
            if os.getenv("TK_VRED_EXECPATH").endswith("VREDDesign.exe"):
                scripts_action.setVisible(False)

    def _version_check(self, version1, version2):
        """
        Compare version strings and return 1 if version1 is greater than version2,
            0 if they are equal and -1 if version1 is less than version2
        :param version1: A version string to compare against version2 e.g. 2022.2
        :param version2: A version string to compare against version1 e.g. 2021.3.1
        :return: 1, 0, -1 as per above.
        """
        # This will split both the versions by the '.' character
        arr1 = version1.split(".")
        arr2 = version2.split(".")
        n = len(arr1)
        m = len(arr2)

        # Converts to integer from string
        arr1 = [int(i) for i in arr1]
        arr2 = [int(i) for i in arr2]

        # Compares which list is bigger and fills
        # the smaller list with zero (for unequal delimeters)
        if n > m:
            for i in range(m, n):
                arr2.append(0)
        elif m > n:
            for i in range(n, m):
                arr1.append(0)

        # Returns 1 if version1 is greater
        # Returns -1 if version2 is greater
        # Returns 0 if they are equal
        for i in range(len(arr1)):
            if arr1[i] > arr2[i]:
                return 1
            elif arr2[i] > arr1[i]:
                return -1
        return 0

    def _run_app_instance_commands(self):
        """
        Runs the series of app instance commands listed in the 'run_at_startup' setting
        of the environment configuration yaml file.
        """

        # Build a dictionary mapping app instance names to dictionaries of commands they registered with the engine.
        app_instance_commands = {}
        for (command_name, value) in self.commands.items():
            app_instance = value["properties"].get("app")
            if app_instance:
                # Add entry 'command name: command function' to the command dictionary of this app instance.
                command_dict = app_instance_commands.setdefault(
                    app_instance.instance_name, {}
                )
                command_dict[command_name] = value["callback"]

        commands_to_run = []
        # Run the series of app instance commands listed in the 'run_at_startup' setting.
        for app_setting_dict in self.get_setting("run_at_startup", []):

            app_instance_name = app_setting_dict["app_instance"]
            # Menu name of the command to run or '' to run all commands of the given app instance.
            setting_command_name = app_setting_dict["name"]

            # Retrieve the command dictionary of the given app instance.
            command_dict = app_instance_commands.get(app_instance_name)

            if command_dict is None:
                self.logger.warning(
                    "{engine_name} configuration setting 'run_at_startup' requests app '{app_name}' that is not installed.".format(
                        engine_name=self.name, app_name=app_instance_name
                    )
                )
            else:
                if not setting_command_name:
                    # Run all commands of the given app instance.
                    for (command_name, command_function) in command_dict.items():
                        self.logger.debug(
                            "{engine_name} startup running app '{app_name}' command '{cmd_name}'.".format(
                                engine_name=self.name,
                                app_name=app_instance_name,
                                cmd_name=command_name,
                            )
                        )
                        commands_to_run.append(command_function)
                else:
                    # Run the command whose name is listed in the 'run_at_startup' setting.
                    command_function = command_dict.get(setting_command_name)
                    if command_function:
                        self.logger.debug(
                            "{engine_name} startup running app '{app_name}' command '{cmd_name}'.".format(
                                engine_name=self.name,
                                app_name=app_instance_name,
                                cmd_name=setting_command_name,
                            )
                        )
                        commands_to_run.append(command_function)
                    else:
                        known_commands = ", ".join(
                            "'{}'".format(name) for name in command_dict
                        )
                        self.logger.warning(
                            "{engine_name} configuration setting 'run_at_startup' requests app '{app_name}' unknown command '{cmd_name}'. "
                            "Known commands: {known_cmds}".format(
                                engine_name=self.name,
                                app_name=app_instance_name,
                                cmd_name=setting_command_name,
                                known_cmds=known_commands,
                            )
                        )

        # no commands to run. just bail
        if not commands_to_run:
            return

        # finally, run the commands
        for command in commands_to_run:
            command()

    def _monkey_patch_qtoolbutton(self):
        """
        Temporary method to monkey patch the QToolButton to fix opening a QToolButton
        menu on the correct screen (Qt 5.15.0 bug QTBUG-84462).
        """

        from sgtk.platform.qt import QtGui

        class QToolButtonPatch(QtGui.QToolButton):
            """
            A QToolButton object with the exception of modifying the setMenu and
            addAction methods.
            """

            # Define QToolButtonPatch class field for menu that will be created to
            # hold any actions added to the QToolButtonPatch, without a menu object.
            _patch_menu = None

            def setMenu(self, menu):
                """
                Override the setMenu method to link the QToolButton to the menu. The menu
                will need to know which QToolButton it is being opened from on the showEvent
                inorder to repositiong itself correctly to the button.
                :param menu: A QMenu object to set for this button.
                """
                menu.patch_toolbutton = self
                super(QToolButtonPatch, self).setMenu(menu)

            def addAction(self, action):
                """
                Override the addAction method to create a QMenu object here, that will hold
                any button menu actions. Normally, the QMenu object would be created on show,
                in the C++ source QToolButton::popupTimerDone(), but since we've monkey patched
                the QMenu object, we need to create it on the Python side to make sure we use our
                QMenuPatch object instead of QMenu.
                :param action: The QAction object to add to our QToolButton menu.
                """

                if self.menu() is None:
                    self._patch_menu = QtGui.QMenu()
                    self.setMenu(self._patch_menu)

                self.menu().addAction(action)

        # All QToolButtons will now be a QToolButtonPatch.
        QtGui.QToolButton = QToolButtonPatch

    def _monkey_patch_qmenu(self):
        """
        Temporary method to monkey patch the QMenu to fix opening a QToolButton menu on
        the correct screen (Qt 5.15.0 bug QTBUG-84462).
        """

        from sgtk.platform.qt import QtCore, QtGui

        class QMenuPatch(QtGui.QMenu):
            """
            A QMenu object with the exception of modifying the showEvent method.
            """

            def showEvent(self, event):
                """
                Override the showEvent method in order to reposition the menu correctly.
                """

                # Only apply menu position patch for menus that are shown from QToolButtons.
                fix_menu_pos = hasattr(self, "patch_toolbutton") and isinstance(
                    self.patch_toolbutton, QtGui.QToolButton
                )

                if fix_menu_pos:
                    # Get the orientation for the menu.
                    horizontal = True
                    if isinstance(self.patch_toolbutton.parentWidget(), QtGui.QToolBar):
                        if (
                            self.patch_toolbutton.parentWidget().orientation()
                            == QtCore.Qt.Vertical
                        ):
                            horizontal = False

                    # Get the correct position for the menu.
                    initial_pos = self.position_menu(
                        horizontal, self.sizeHint(), self.patch_toolbutton
                    )

                    # Save the geometry of the menu, we will need to re-set the geometry after
                    # the menu is shown to make sure the menu size is correct.
                    rect = QtCore.QRect(initial_pos, self.size())

                    # Move the menu to the correct position before the show event.
                    self.move(initial_pos)

                super(QMenuPatch, self).showEvent(event)

                if fix_menu_pos:
                    # Help correct the size of the menu.
                    self.setGeometry(rect)

            def position_menu(self, horizontal, size_hint, toolbutton):
                """
                This method is copied from the C++ source qtoolbutton.cpp in Qt 5.15.1 fix version.
                :param horizontal: The orientation of the QToolBar that the menu is shown for. This
                should be True if the menu is not in a QToolBar.
                :param size_hint: The QSize size hint for this menu.
                :param toolbutton: The QToolButtonPatch object that this menu is shown for. Used to
                positiong the menu correctly.
                """

                point = QtCore.QPoint()

                rect = toolbutton.rect()
                desktop = QtGui.QApplication.desktop()
                screen = desktop.availableGeometry(
                    toolbutton.mapToGlobal(rect.center())
                )

                if horizontal:
                    if toolbutton.isRightToLeft():
                        if (
                            toolbutton.mapToGlobal(QtCore.QPoint(0, rect.bottom())).y()
                            + size_hint.height()
                            <= screen.bottom()
                        ):
                            point = toolbutton.mapToGlobal(rect.bottomRight())

                        else:
                            point = toolbutton.mapToGlobal(
                                rect.topRight() - QtCore.QPoint(0, size_hint.height())
                            )

                        point.setX(point.x() - size_hint.width())

                    else:
                        if (
                            toolbutton.mapToGlobal(QtCore.QPoint(0, rect.bottom())).y()
                            + size_hint.height()
                            <= screen.bottom()
                        ):
                            point = toolbutton.mapToGlobal(rect.bottomLeft())

                        else:
                            point = toolbutton.mapToGlobal(
                                rect.topLeft() - QtCore.QPoint(0, size_hint.height())
                            )

                else:
                    if toolbutton.isRightToLeft():

                        if (
                            toolbutton.mapToGlobal(QtCore.QPoint(rect.left(), 0)).x()
                            - size_hint.width()
                            <= screen.x()
                        ):
                            point = toolbutton.mapToGlobal(rect.topRight())

                        else:
                            point = toolbutton.mapToGlobal(rect.topLeft())
                            point.setX(point.x() - size_hint.width())

                    else:
                        if (
                            toolbutton.mapToGlobal(QtCore.QPoint(rect.right(), 0)).x()
                            + size_hint.width()
                            <= screen.right()
                        ):
                            point = toolbutton.mapToGlobal(rect.topRight())

                        else:
                            point = toolbutton.mapToGlobal(
                                rect.topLeft() - QtCore.QPoint(size_hint.width(), 0)
                            )

                point.setX(
                    max(
                        screen.left(),
                        min(point.x(), screen.right() - size_hint.width()),
                    )
                )
                point.setY(point.y() + 1)
                return point

        # All QMenus will now be a QMenuPatch
        QtGui.QMenu = QMenuPatch

    #####################################################################################
    # Logging

    def _emit_log_message(self, handler, record):
        """
        Called by the engine to log messages in VRED Terminal.
        All log messages from the toolkit logging namespace will be passed to this method.

        :param handler: Log handler that this message was dispatched from.
                        Its default format is "[levelname basename] message".
        :type handler: :class:`~python.logging.LogHandler`
        :param record: Standard python logging record.
        :type record: :class:`~python.logging.LogRecord`
        """

        # For Python2, make sure the msg passed to VRED C++ API is indeed a Python
        # string (and not unicode, which may be the case if any string concatenation
        # was performed on the msg).
        msg = str(handler.format(record))

        # The VREDPy may not have been initialized yet when this method is called, fall back
        # to import the vrController module
        if self.vredpy:
            vrController = self.vredpy.vrController
        else:
            import vrController

        if record.levelno < logging.WARNING:
            vrController.vrLogInfo(msg)
        elif record.levelno < logging.ERROR:
            vrController.vrLogWarning(msg)
        else:
            vrController.vrLogError(msg)

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

        from sgtk.platform.qt import QtCore, QtGui

        self.logger.debug("Begin showing panel {}".format(panel_id))

        if not self.has_ui:
            self.log_error(
                "Sorry, this environment does not support UI display! Cannot show "
                "the requested window '{}'.".format(title)
            )
            return None

        # Reuse the widget instance, if it already exists. Only reuse the widget
        # instance if it is found in the docked widgets - widgets found by
        # traversing all the application widgets may point to stale widgets and
        # attempting to reuse them may cause errors (e.g. there have been issues
        # with reusing Shotgun Panel App by finding it from QApplication.allWidgets())
        widget_instance = None
        for dock_widget_panel_id, dock_widget in self._dock_widgets.items():
            if dock_widget_panel_id == panel_id:
                widget_instance = dock_widget.widget()
                parent = self._get_dialog_parent()
                widget_instance.setParent(parent)
                break

        if not widget_instance:
            _, widget_instance = self._create_dialog_with_widget(
                title, bundle, widget_class, *args, **kwargs
            )

        dock_properties = self.get_setting("docked_apps", {}).get(bundle.name, {})
        dock_area = dock_properties.get("pos", QtCore.Qt.RightDockWidgetArea)
        tabbed = dock_properties.get("tabbed", True)
        self.show_dock_widget(
            panel_id, title, widget_instance, dock_area=dock_area, tabbed=tabbed
        )

        # Return the widget created by the method, _create_dialog_with_widget, since this will
        # have the widget_class type expected by the caller. This widget represents the panel
        # so it should have the object name set to the panel_id
        widget_instance.setObjectName(panel_id)
        return widget_instance

    def show_dock_widget(self, panel_id, title, widget, dock_area=None, tabbed=False):
        """
        Create a dock widget managed by the VRED engine, if one has not yet been created. Set the
        widget to show in the dock widget and add it to the VRED dock area.

        :param title: The title of the dock widget window.
        :param widget: The QWidget to show in the dock widget.
        :param dock_area: The dock widget area (e.g. QtCore.Qt.RightDockWidgetArea).
        """

        dock_widget = self._dock_widgets.get(panel_id, None)
        if dock_widget is None:
            dock_widget = self._tk_vred.DockWidget(
                title,
                self._get_dialog_parent(),
                panel_id,
                widget,
                self.menu_generator.root_menu
                is not None,  # closable if there is a menu to reopen it
                dock_area,
                tabbed,
            )
            dock_widget.setMinimumWidth(400)

            # Keep track of the dock widget
            self._dock_widgets[panel_id] = dock_widget

            # Get the dock widget to tabify this dock widget with
            tabify_widget = (
                self.get_tabify_widget(dock_widget, dock_area) if tabbed else None
            )

            if tabbed:
                # Keep track of it by dock position in order to tabify with other dock widgets
                self._tabbed_dock_widgets.setdefault(dock_area, []).append(dock_widget)

            dock_widget.dock_to_parent(tabify_widget)
        else:
            tabify_widget = (
                self.get_tabify_widget(dock_widget, dock_area) if tabbed else None
            )
            dock_widget.reinitialize(title, widget, tabify_widget)

        dock_widget.show()

    def get_tabify_widget(self, dock_widget, dock_area):
        """
        Return the dock widget to tabify the given dock widget with.

        :return: The dock widget to tabify the given dock widget.
        :rtype: DockWidget
        """

        tabify_widget = None
        tabbed_widets_in_pos = self._tabbed_dock_widgets.get(dock_area, [])
        index = len(tabbed_widets_in_pos) - 1

        while tabify_widget is None and index >= 0:
            if tabbed_widets_in_pos[index] != dock_widget:
                tabify_widget = tabbed_widets_in_pos[index]
            index -= 1

        return tabify_widget

    #####################################################################################
    # VRED File IO

    def has_unsaved_changes(self):
        """
        Return True if the current scene has unsaved changes, otherwise False.
        The VRED API does not currently have an endpoint to check for unsaved changes,
        so to determine whether or not there are changes, check if the VRED window title
        contains a '*' character (this indicates that there are changes in the scene).
        """

        window_title_string = self._get_dialog_parent().windowTitle()
        return re.findall(r"\*", window_title_string)

    def save_or_discard_changes(self, override_cursor=None):
        """
        Check if the current VRED scene has any changes. Open a dialog to as the user
        to save their changes, if any, or proceed with discarding any changes.

        :param override_cursor: A Qt cursor type that will be used to set an override
                                cursor when opening QMessageBox.
        :type override_cursor: :class:`sgtk.platform.qt.QtGui.QCursor`
        :returns: True indicating the user has successfully saved or discarded their
                  current changes, if any, else False indicates the user failed to
                  resolve their unsaved changes.
        :rtype: bool
        """
        from sgtk.platform.qt import QtGui

        resolved = not self.has_unsaved_changes()
        has_overriden_cursor = False

        while not resolved:
            if override_cursor and not has_overriden_cursor:
                has_overriden_cursor = True
                QtGui.QApplication.setOverrideCursor(override_cursor)

            answer = QtGui.QMessageBox.question(
                None,
                "Save your scene?",
                "Your scene has unsaved changes. Save before proceeding?",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel,
            )

            if answer == QtGui.QMessageBox.Cancel:
                # User has indicated to abort the operation
                break

            if answer == QtGui.QMessageBox.No:
                # User has indicated to discard changes
                resolved = True

            elif answer == QtGui.QMessageBox.Yes:
                # User has indicated they want to save changes before proceeding
                self.open_save_as_dialog()
                resolved = not self.has_unsaved_changes()

        if has_overriden_cursor:
            QtGui.QApplication.restoreOverrideCursor()

        return resolved

    def open_save_as_dialog(self):
        """
        Open the tk-multi-workfiles2 app's file save dialog. Fallback to using VRED save
        dialog UI if workfiles is not available.
        """

        open_dialog_func = None
        kwargs = {}
        workfiles = self.apps.get("tk-multi-workfiles2", None)

        if workfiles:
            if hasattr(workfiles, "show_file_save_dlg"):
                open_dialog_func = workfiles.show_file_save_dlg
                kwargs["use_modal_dialog"] = True

        if open_dialog_func:
            open_dialog_func(**kwargs)

        else:
            # Fallback to using VRED's save dialog. Pass flag to not confirm overwrite, the
            # save dialog will already ask this.
            if self.vredpy.vrFileIOService:
                filename = self.vredpy.vrFileIOService.getFileName()
            else:
                filename = self.vredpy.vrFileIO.getFileIOFilePath()
            path = self.vredpy.vrFileDialog.getSaveFileName(
                caption="Save As",
                filename=filename,
                filter=["VRED Project Binary (*.vpb)"],
                confirmOverwrite=False,
            )
            self.save_current_file(path, False)

    def save_current_file(self, file_path, set_render_path=True):
        """
        Save the current project as a file.

        :param file_path: the name of the project file.
        """

        if not file_path:
            self.logger.debug(
                "{engine_name} no file path given for save -- aborting".format(
                    engine_name=self.name
                )
            )
            return

        self.logger.debug(
            "{engine_name} calling VRED save for file '{path}'".format(
                engine_name=self.name, path=file_path
            )
        )

        self.vredpy.vrFileIO.save(file_path)

        if not os.path.exists(six.ensure_str(str(file_path))):
            msg = "VRED Failed to save file {}".format(file_path)
            self.logger.error(msg)
            raise Exception(msg)

        if set_render_path:
            self.set_render_path(file_path)

    def set_render_path(self, file_path=None):
        """
        Prepare render path when the file is selected or saved.

        :param file_path: the name of the file.
        """

        render_template_settings = self.get_setting("render_template")
        render_template = self.get_template_by_name(render_template_settings)
        if not render_template:
            self.logger.debug(
                "{engine_name} failed to set render path: template not found from 'render_template' engine settings: {settings}".format(
                    engine_name=self.name, settings=render_template_settings
                )
            )
            return

        if file_path is None:
            file_path = self.vredpy.vrFileIO.getFileIOFilePath()
            if file_path is None:
                self.logger.debug(
                    "{engine_name} failed to set render path: current scene path not found".format(
                        engine_name=self.name
                    )
                )
                return

        work_template = self.sgtk.template_from_path(file_path)
        if not work_template:
            self.logger.debug(
                "{engine_name} failed to set render path: template matching scene path '{path}' not found".format(
                    engine_name=self.name, path=file_path
                )
            )
            return

        # Update the template fields with the context ones to be sure to have all the required fields.
        template_fields = work_template.get_fields(file_path)
        context_fields = self.context.as_template_fields(render_template)
        for k in context_fields:
            if k not in template_fields.keys():
                template_fields[k] = context_fields[k]

        missing_keys = render_template.missing_keys(template_fields, skip_defaults=True)
        if missing_keys:
            self.logger.debug(
                "{engine_name} failed to set render path: render template missing keys {keys}".format(
                    engine_name=self.name, keys=missing_keys
                )
            )
            return

        render_path = render_template.apply_fields(template_fields)

        # Be sure the render folder is created.
        render_folder = os.path.dirname(render_path)
        if not os.path.isdir(render_folder):
            os.makedirs(render_folder)

        self.logger.debug(
            "{engine_name} calling VRED to set render path '{path}'".format(
                engine_name=self.name, path=render_path
            )
        )

        self.vredpy.vrRenderSettings.setRenderFilename(render_path)
