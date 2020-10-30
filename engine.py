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

try:
    import builtins

    builtins.vrFileIOService = vrFileIOService
except ImportError:
    import __builtin__

    try:
        __builtin__.vrFileIOService = vrFileIOService
    except NameError:
        vrFileIOService = False

import vrController
import vrFileDialog
import vrFileIO
import vrRenderSettings


class VREDEngine(sgtk.platform.Engine):
    """
    A VRED engine for Shotgun Toolkit.
    """

    def __init__(self, tk, context, engine_instance_name, env):
        """
        Class Constructor
        """
        self._tk_vred = None
        self._menu_generator = None
        self._dock_widget = None

        super(VREDEngine, self).__init__(tk, context, engine_instance_name, env)

    def post_context_change(self, old_context, new_context):
        """
        Runs after a context change has occurred.

        :param old_context: The previous context.
        :param new_context: The current context.
        """

        self.logger.debug("{}: Post context change...".format(self))

        # Rebuild the menu on context change.
        self.menu_generator.create_menu()

    def pre_app_init(self):
        """
        Sets up the engine into an operational state. This method called before
        any apps are loaded.
        """

        self.logger.debug("{}: Initializing...".format(self))

        # unicode characters returned by the shotgun api need to be converted
        # to display correctly in all of the app windows
        # tell QT to interpret C strings as utf-8
        from sgtk.platform.qt import QtCore, QtGui

        utf8 = QtCore.QTextCodec.codecForName("utf-8")
        QtCore.QTextCodec.setCodecForCStrings(utf8)
        self.logger.debug("set utf-8 codec for widget text")

        # import python/tk_vred module
        self._tk_vred = self.import_module("tk_vred")

        # check for version compatibility
        vred_version = int(vrController.getVredVersionYear())
        self.logger.debug("Running VRED version {}".format(vred_version))
        if vred_version > self.get_setting("compatibility_dialog_min_version", 2021):
            msg = (
                "The Shotgun Pipeline Toolkit has not yet been fully tested with VRED {version}. "
                "You can continue to use the Toolkit but you may experience bugs or "
                "instability.  Please report any issues you see to support@shotgunsoftware.com".format(
                    version=vred_version
                )
            )
            self.logger.warning(msg)
            QtGui.QMessageBox.warning(
                self._get_dialog_parent(),
                "Warning - Shotgun Pipeline Toolkit!",
                msg,
            )

    def post_app_init(self):
        """
        Runs after all apps have been initialized.
        """

        self.logger.debug("{}: Post Initializing...".format(self))

        # Init menu
        self.menu_generator.create_menu(clean_menu=False)

        # Run a series of app instance commands at startup.
        self._run_app_instance_commands()

    def destroy_engine(self):
        """
        Called when the engine should tear down itself and all its apps.
        """
        self.logger.debug("{}: Destroying...".format(self))

        # Clean up the menu and clear the menu generator
        self.menu_generator.clean_menu()
        self._menu_generator = None

        self._dock_widget = None

        # Close all Shotgun app dialogs that are still opened since
        # some apps do threads cleanup in their onClose event handler
        # Note that this function is called when the engine is restarted (through "Reload Engine and Apps")

        # Important: Copy the list of dialogs still opened since the call to close() will modify created_qt_dialogs
        dialogs_still_opened = self.created_qt_dialogs[:]

        for dialog in dialogs_still_opened:
            dialog.close()

    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed by the engine.
        """
        return True

    @property
    def menu_generator(self):
        """
        Menu generator to help the engine manage the Shotgun menu in VRED.
        """
        if self._menu_generator is None:
            self._menu_generator = self._tk_vred.VREDMenuGenerator(engine=self)

        return self._menu_generator

    def _get_dialog_parent(self):
        """
        Get the QWidget parent for all dialogs created through show_dialog & show_modal.
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
        from sgtk.platform.qt import QtGui, QtCore

        self.logger.debug("Begin showing panel {}".format(panel_id))

        # If the widget already exists, do not rebuild it but be sure to display it
        for widget in QtGui.QApplication.allWidgets():
            if widget.objectName() == panel_id:
                self.add_dock_widget(title, widget, QtCore.Qt.RightDockWidgetArea)
                return widget

        if not self.has_ui:
            self.log_error(
                "Sorry, this environment does not support UI display! Cannot show "
                "the requested window '{}'.".format(title)
            )
            return None

        # Create a dialog with the panel widget -- the dialog itself is not needed
        # to display the docked widget but it is responsible for cleaning up the widget.
        # The dialog also applies desired styling to the widget.
        dialog, widget = self._create_dialog_with_widget(
            title, bundle, widget_class, *args, **kwargs
        )

        self.add_dock_widget(title, widget, QtCore.Qt.RightDockWidgetArea)

        # Return the widget created by the method, _create_dialog_with_widget, since this will
        # have the widget_class type expected by the caller. This widget represents the panel
        # so it should have the object name set to the panel_id
        widget.setObjectName(panel_id)
        return widget

    def add_dock_widget(self, title, widget, dock_area):
        """
        Create a dock widget managed by the VRED engine, if one has not yet been created. Set the
        widget to show in the dock widget and add it to the VRED dock area.

        :param title: The title of the dock widget window.
        :param widget: The QWidget to show in the dock widget.
        :param dock_area: The dock widget area (e.g. QtCore.Qt.RightDockWidgetArea).
        """
        from sgtk.platform.qt import QtGui

        if self._dock_widget is None:
            self._dock_widget = QtGui.QDockWidget()

        self._dock_widget.setWindowTitle(title)
        self._dock_widget.setWidget(widget)

        # VRED does not have a Python API method to dock a widget, so we need to create a dock widget
        # and dock it to the VRED main window.
        parent = self._get_dialog_parent()
        parent.addDockWidget(dock_area, self._dock_widget)

        self._dock_widget.show()

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
            if vrFileIOService:
                filename = vrFileIOService.getFileName()
            else:
                filename = vrFileIO.getFileIOFilePath()
            path = vrFileDialog.getSaveFileName(
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

        vrFileIO.save(file_path)

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
            file_path = vrFileIO.getFileIOFilePath()
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

        vrRenderSettings.setRenderFilename(render_path)
