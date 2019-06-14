# -*- coding: utf-8 -*-

# Copyright (c) 2015 Shotgun Software Inc.
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

from shiboken2 import wrapInstance

import sgtk
from sgtk import TankError

import vrVredUi
import vrFileIO
import vrController
import vrRenderSettings


class VREDEngine(sgtk.platform.Engine):
    """A VRED engine for Shotgun Toolkit."""
    def __init__(self, tk, context, engine_instance_name, env):
        self._tk_vred = None
        self.menu = None
        self.render_path = None
        self.cmd_and_callback_dict = {}

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

    def get_current_file(self):
        """
        Get the current file.
        """
        return vrFileIO.getFileIOFilePath()

    def load_file(self, file_path):
        """
        Load a new file into VRED. This will reset the workspace.
        """
        decision = self.execute_hook_method("file_usage_hook", "file_attempt_open", path=file_path)
        if decision:
            self.log_info("Load File: {}".format(file_path))
            vrFileIO.load(file_path)
            self.prepare_render_path(file_path)
        else:
            # The user chose not to open the file
            pass
    
    def import_file(self, file_path):
        """
        Import a file into VRED. This will reset not the workspace.
        """
        decision = self.execute_hook_method("file_usage_hook", "file_attempt_open", path=file_path)
        if decision:
            self.log_info("Import File: {}".format(file_path))
            vrFileIO.loadGeometry(file_path)
            self.prepare_render_path(file_path)
        else:
            # The user chose not to open the file
            pass

    def reset_scene(self):
        """
        Resets the Scene in VRED.
        """
        self.log_info("Reset Scene")
        self.current_file_closed()
        vrController.newScene()

    def log_info(self, message):
        """
        Log debugging information.
        """
        self.logger.info(message)

    def log_debug(self, message):
        """
        Log a debug message
        """
        self.logger.debug(message)

    def log_error(self, message):
        """
        Log Error debugging information.
        """
        self.logger.error(message)

    def save_current_file(self, file_path):
        """
        Tell VRED to save the out the current project as a file.
        """
        # Save the actual file
        self.log_info("Save File: {}".format(file_path))

        vrFileIO.save(file_path)
        if not os.path.exists(file_path.decode('utf-8')):
            msg = "VRED Failed to save file {}".format(file_path)
            self.log_error(msg)
            raise TankError(msg)

        allowed_to_open = self.execute_hook_method("file_usage_hook", "file_attempt_open", path=file_path)
        if not allowed_to_open:
            raise TankError("Can't save file: a lock for this path already exists")

        self.prepare_render_path(file_path)

    def current_file_closed(self):
        """
        Called when the current file is closed.
        """
        path = self.get_current_file()
        if path:
            self.execute_hook_method("file_usage_hook", "file_closed", path=path)

    def quit(self):
        self.current_file_closed()

    def get_render_path(self, file_path):
        """
        Get render path when the file is selected or saved
        """
        self.log_info('Generating render path')
        try:
            template = self.get_template_by_name(self.get_setting('render_template'))
            context_fields = self.context.as_template_fields(template, validate=True)
            scene_name = file_path.split(os.path.sep)[-1].replace('.vpb', '')
            context_fields.update({'scene_name': scene_name})
            path = template.apply_fields(context_fields)
            self.log_info('Path value: {0}'.format(path))
            if not os.path.exists(path):
                os.makedirs(path)
            path = os.path.sep.join([path, scene_name+'.png'])
            self.log_info('\nFull path value: {0}\n'.format(path))
        except Exception as err:
            self.log_info("\n\nError generating render path: {0}\n\n".format(err))
            path = None

        return path

    def prepare_render_path(self, file_path):
        """
        Prepare render path when the file selected or saved
        """
        path = self.get_render_path(file_path)

        if path:
            self.render_path = path
            vrRenderSettings.setRenderFilename(self.render_path)

    def save_before_publish(self, path):
        """
        Save the scene before publish in order to get the latest changes
        """
        self.save_current_file(path)

    def save_after_publish(self, path):
        """
        Save the scene after publish in order to get a new version in the workfiles folder
        """
        self.save_current_file(path)

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

        window = wrapInstance(long(vrVredUi.getMainWindow()), QtGui.QMainWindow)

        return window
