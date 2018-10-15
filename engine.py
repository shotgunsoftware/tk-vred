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
import sys
import errno
import random

from shiboken2 import wrapInstance
from PySide2 import QtWidgets

import tank
from tank import TankError

import vrVredUi
import vrFileIO
import vrController
import vrRenderSettings
import webbrowser


class VREDEngine(tank.platform.Engine):
    """
    The VRED engine.

    The default shotgun menu actions are:
        * 'Upload Files'
        * 'File Open...'
        * 'File Save...'
        * 'Jump to Screening Room in RV'
        * 'Jump to Screening Room Web Player'
        * 'Reload and Restart'
        * 'Open Log Folder'
        * 'Shotgun Panel...'
        * 'Publish...'
        * 'Snapshot History...'
        * 'About...'
        * 'Snapshot...'
        * 'Work Area Info...'
    """
    render_path = None
    cmd_and_callback_dict = {}
    shotgun_menu_text = u'S&hotgun'

    def _can_show_menu(self):
        file_is_open = self.get_current_file()
        has_task = self.context.task
        has_asset = self.context.entity and self.context.entity.get("type") == "Asset"

        return file_is_open or (has_asset and has_task)

    def get_project_title(self):
        """Load information to infer and return the project title"""
        # Project menu title
        has_task = self.context.task
        has_asset = self.context.entity and self.context.entity.get("type") == "Asset"
        
        # Asset, Task
        if has_asset and has_task:
            title = "{}, {}".format(
                self.context.entity.get("name"),
                self.context.task.get("name")
            )
        # Asset
        elif has_asset and not has_task:
            title = self.context.entity.get("name")
        # Project
        else:
            title = self.context.project.get("name")
        return title

    def make_action(self, title, actions_store={}, custom_action=None, show=True):
        """Make an action just passing title and callbacks storage"""
        action = custom_action
        fallback = self.cmd_and_callback_dict.get(title.replace('&', ''), lambda: None)
        action = custom_action or actions_store.get(title.replace('&', ''), fallback)
        return {
            'type': 'action',
            'name': title.replace(' ', '_').replace('.', '').lower(),
            'title': title,
            'action': action,
            'show': show
        }

    def _create_shotgun_menu(self):
        """
        Creates the shotgun menu based on the loaded apps.
        To create the menu we use menu structure with next contracts:
            {
                'type': 'action|menu',
                'name': '<name or item>',
                'title': 'Reload and &Restart',
                'show': True|False,
                'action': <Python Function or Method> // Just for type=action
                'items': <Python Array with more items> // Just for type=menu
            }
            or
            {'type': 'separator', 'show':True|False},

        To enable debug create environ variable VRED_DEBUG:
            - Windows: "SET VRED_DEBUG=1"
            - UNIX: "export VRED_DEBUG=1"
        """
        try:
            window = self._window
            menubar = window.menuBar()
            menu = QtWidgets.QMenu()
            menu.setTitle(self.shotgun_menu_text)
            cmd_and_callback_dict = dict()
            for name, details in self.commands.items():
                cmd_and_callback_dict[name] = details["callback"]
            self.log_info("{}".format(cmd_and_callback_dict))
            keys_count = len(self.cmd_and_callback_dict.keys())
            if keys_count == 0:
                self.cmd_and_callback_dict = cmd_and_callback_dict
            self.log_info("Creating Menu")
            show_in_menu = self._can_show_menu()
            use_debug = os.getenv('VRED_DEBUG', False)
            self.log_info("\n\nos.environ {0}\n\n".format(os.environ))
            menu_items = [
                {
                    'type': 'menu',
                    'name': 'project_menu',
                    'title': self.get_project_title(),
                    'show': True,
                    'items': [
                        self.make_action('Jump to Shot&gun', custom_action=self.jump_to_shotgun),
                        self.make_action('Jump to File S&ystem', custom_action=self.jump_to_file_system),
                        {'type': 'separator', 'show':True},
                        self.make_action('Jump to Screening &Room Web Player', cmd_and_callback_dict),
                        self.make_action('Jump to Screening Room in RV', cmd_and_callback_dict),
                        self.make_action('Open Log Folder', cmd_and_callback_dict, show=use_debug),
                        self.make_action('Reload and &Restart', cmd_and_callback_dict, show=use_debug),
                        self.make_action('Work Area &Info...', cmd_and_callback_dict),
                    ]
                },
                {'type': 'separator', 'show':True},
                self.make_action('File &Open...', cmd_and_callback_dict),
                self.make_action('Snaps&hot...', cmd_and_callback_dict, show=show_in_menu),
                self.make_action('File &Save...', cmd_and_callback_dict, show=show_in_menu),
                self.make_action('Publish...', cmd_and_callback_dict, show=show_in_menu),
                {'type': 'separator', 'show':True},
                self.make_action('A&bout...', cmd_and_callback_dict, show=True),
                self.make_action('&Load...', cmd_and_callback_dict, show=show_in_menu),
                self.make_action('Scene Brea&kdown...', cmd_and_callback_dict, show=show_in_menu),
                {
                    'type': 'menu',
                    'name': 'scene_snapshot',
                    'title':  'Scene Snaps&hot',
                    'show': show_in_menu,
                    'items': [
                        self.make_action('Snap&shot...', cmd_and_callback_dict),
                        self.make_action('Snapshot &History...', cmd_and_callback_dict)
                    ]
                },
                self.make_action('Shotgun &Panel...', cmd_and_callback_dict, show=True),
                {
                    'type': 'menu',
                    'name': 'shotgun_workfiles',
                    'title':  'Shotgun &Workfiles',
                    'show': True,
                    'items': [
                        self.make_action('File &Open...', cmd_and_callback_dict),
                        self.make_action('File &Save...', cmd_and_callback_dict)
                    ]
                }
            ]

            self.existent = {}
            self.prepare_menu_from_structure(menu_items, menu, self.existent)
            for menubar_action in menubar.actions():
                if menubar_action.text() == u'&Help':
                    menubar.insertMenu(menubar_action, menu)
                    break

        except Exception as error:
            self.log_info('Error creating menu: {0}'.format(error))

    def prepare_menu_from_structure(self, menu_items, parentmenu, existent_elements):
        """Create menu elements and actions accorfing passed structures"""
        try:
            for item in menu_items:
                show_item = item.get('show', None)
                elm_name = item.get('name', 'elm_{0}'.format(random.randint(0, 1000)))
                if not show_item:
                    continue
                elm_type = item['type']
                elm_key = '{0}_{1}'.format(elm_type, elm_name)
                self.log_info("Checking {0}".format(elm_key))
                if not existent_elements.has_key(elm_key):
                    if elm_type == 'menu':
                        existent_elements[elm_key] = QtWidgets.QMenu()
                        existent_elements[elm_key].setTitle(item['title'])
                        self.prepare_menu_from_structure(item['items'], 
                                                         existent_elements[elm_key],
                                                         existent_elements)
                        parentmenu.addMenu(existent_elements[elm_key])
                        self.log_info("Adding Menu {0}".format(elm_key))
                    elif elm_type == 'action':
                        parentmenu.addAction(
                            item['title'],
                            item['action']
                        )
                        self.log_info("Adding Action {0}".format(elm_key))
                    elif elm_type == 'separator':
                        parentmenu.addSeparator()
        except Exception as err:
            self.log_info("{0}".format(err))

    def _rm_shotgun_menu(self):
        """
        Checks for the presence of a shotgun menu.
        Removes the shotgun menu if it exists.
        """
        # Remove the shotgun menu.
        self.log_info("Remove Shotgun Menu")

        window = self._window
        menu_bar = window.menuBar()

        for menu_elm in menu_bar.actions():
            if menu_elm.text() == self.shotgun_menu_text:
                menu_bar.removeAction(menu_elm)

    def pre_app_init(self):
        """
        Runs after the engine is set up but before any apps have been initialized.
        We use this method to set up basic things that will be needed through
        the lifecycle of the Engine, such as the logger and instance variables.
        """
        self.log_info("Pre App Initalization")
        # self._initialize_dark_look_and_feel()
        # tell QT to interpret C strings as utf-8
        utf8 = tank.platform.qt.QtCore.QTextCodec.codecForName("utf-8")
        tank.platform.qt.QtCore.QTextCodec.setCodecForCStrings(utf8)
        self.logger.debug("set utf-8 codec for widget text")

    def post_app_init(self):
        """
        Runs when all apps have initialized.
        """
        from tank.platform.qt import QtGui

        self.log_info("Post App Initalization")

        QtGui.QApplication.instance().aboutToQuit.connect(self.quit)

        self._window = self.get_vred_main_window()

        # If the app was launched to open a file, do so
        file_to_open = os.environ.get("TANK_FILE_TO_OPEN", None)
        if file_to_open:
            self.reset_scene()
            self.load_file(file_to_open)

        # Create the Shotgun menu
        self.rebuild_shotgun_menu()

    def destroy_engine(self):
        """
        Called when the engine should tear itself down.
        """
        self.log_info("Destroying engine")

    @property
    def context_change_allowed(self):
        """
        Overriding the engine base class property to allow
        context switch without a restart of this engine
        """
        # see: http://developer.shotgunsoftware.com/tk-core/platform.html?highlight=context_change_allowed#sgtk.platform.Engine.context_change_allowed
        return True

    def jump_to_shotgun(self):
        """
        Function to goto the current project page.
        """
        webbrowser.open(self.context.shotgun_url)

    def jump_to_file_system(self):
        # launch one window for each location on disk
        paths = self.context.filesystem_locations

        for disk_location in paths:
            # get the setting
            system = sys.platform

            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)

            exit_code = os.system(cmd)

            if exit_code != 0:
                self.log_error("Failed to launch '%s'!" % cmd)

    def rebuild_shotgun_menu(self):
        """
        This will remove and rebuild the menu.
        """
        try:
            self._rm_shotgun_menu()
        except Exception as error:
            self.log_info("Error Clearing Menu {0}".format(error))
        self._create_shotgun_menu()

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

    def post_context_change(self, old_context, new_context):
        """
        Called right after a context switch, let's send the new
        context to the VRED engine
        """
        self.log_info("post_context_change called with context {}".format(new_context))
        if self.context_change_allowed:
            self.rebuild_shotgun_menu()

    def get_vred_main_window(self):
        """
        Gets the main window.
        """
        window = wrapInstance(long(vrVredUi.getMainWindow()), QtWidgets.QMainWindow)

        return window

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
