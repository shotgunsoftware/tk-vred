# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Menu handling for Alias
"""

import os
import random
import sys
import webbrowser

from sgtk.platform.qt import QtGui


class VREDMenu(object):
    """VRED menu handler."""

    def __init__(self, engine):
        """Initialize attributes."""
        # engine instance
        self._engine = engine

        self.logger = self._engine.logger

    def _can_show_menu(self):
        file_is_open = self._engine.get_current_file()
        has_task = self._engine.context.task
        has_asset = self._engine.context.entity and self._engine.context.entity.get("type") != "Project"

        return file_is_open or (has_asset and has_task)

    def get_project_title(self):
        """Load information to infer and return the project title"""
        # Project menu title
        has_task = self._engine.context.task
        has_asset = self._engine.context.entity and self._engine.context.entity.get("type") != "Project"

        # Asset, Task
        if has_asset and has_task:
            title = "{}, {}".format(
                self._engine.context.entity.get("name"),
                self._engine.context.task.get("name")
            )
        # Asset
        elif has_asset and not has_task:
            title = self._engine.context.entity.get("name")
        # Project
        else:
            title = self._engine.context.project.get("name")
        return title

    def make_action(self, title, actions_store={}, custom_action=None, show=True):
        """Make an action just passing title and callbacks storage"""
        fallback = self._engine.cmd_and_callback_dict.get(title.replace('&', ''), lambda: None)
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
            window = self._engine.get_vred_main_window()
            menubar = window.menuBar()
            menu = QtGui.QMenu()
            menu.setTitle(self._engine.shotgun_menu_text)
            cmd_and_callback_dict = dict()

            for name, details in self._engine.commands.items():
                cmd_and_callback_dict[name] = details["callback"]

            self.logger.info("{}".format(cmd_and_callback_dict))
            keys_count = len(self._engine.cmd_and_callback_dict.keys())

            if keys_count == 0:
                self._engine.cmd_and_callback_dict = cmd_and_callback_dict

            self.logger.info("Creating Menu")
            show_in_menu = self._can_show_menu()

            use_debug = os.getenv('VRED_DEBUG', False)

            menu_items = [
                {
                    'type': 'menu',
                    'name': 'project_menu',
                    'title': self.get_project_title(),
                    'show': True,
                    'items': [
                        self.make_action('Jump to Shot&gun', custom_action=self.jump_to_shotgun),
                        self.make_action('Jump to File S&ystem', custom_action=self.jump_to_file_system),
                        {'type': 'separator', 'show': True},
                        self.make_action('Open Log Folder', cmd_and_callback_dict, show=use_debug),
                        self.make_action('Reload and &Restart', cmd_and_callback_dict, show=use_debug),
                        self.make_action('Work Area &Info...', cmd_and_callback_dict),
                    ]
                },
                {'type': 'separator', 'show': True},
                self.make_action('File &Open...', cmd_and_callback_dict),
                self.make_action('Snaps&hot...', cmd_and_callback_dict, show=show_in_menu),
                self.make_action('File &Save...', cmd_and_callback_dict, show=show_in_menu),
                self.make_action('Publish...', cmd_and_callback_dict, show=show_in_menu),
                {'type': 'separator', 'show': True},
                self.make_action('A&bout...', cmd_and_callback_dict, show=True),
                self.make_action('&Load...', cmd_and_callback_dict, show=show_in_menu),
                self.make_action('Scene Brea&kdown...', cmd_and_callback_dict, show=show_in_menu),
                {
                    'type': 'menu',
                    'name': 'scene_snapshot',
                    'title': 'Scene Snaps&hot',
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
                    'title': 'Shotgun &Workfiles',
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
            self.logger.info('Error creating menu: {0}'.format(error))

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
                self.logger.info("Checking {0}".format(elm_key))
                if not existent_elements.has_key(elm_key):
                    if elm_type == 'menu':
                        existent_elements[elm_key] = QtGui.QMenu()
                        existent_elements[elm_key].setTitle(item['title'])
                        self.prepare_menu_from_structure(item['items'],
                                                         existent_elements[elm_key],
                                                         existent_elements)
                        parentmenu.addMenu(existent_elements[elm_key])
                        self.logger.info("Adding Menu {0}".format(elm_key))
                    elif elm_type == 'action':
                        parentmenu.addAction(
                            item['title'],
                            item['action']
                        )
                        self.logger.info("Adding Action {0}".format(elm_key))
                    elif elm_type == 'separator':
                        parentmenu.addSeparator()
        except Exception as err:
            self.logger.info("{0}".format(err))

    def _rm_shotgun_menu(self):
        """
        Checks for the presence of a shotgun menu.
        Removes the shotgun menu if it exists.
        """
        # Remove the shotgun menu.
        self.logger.info("Remove Shotgun Menu")

        window = self._engine.get_vred_main_window()
        menu_bar = window.menuBar()

        for menu_elm in menu_bar.actions():
            if menu_elm.text() == self._engine.shotgun_menu_text:
                menu_bar.removeAction(menu_elm)

    def jump_to_shotgun(self):
        """
        Function to goto the current project page.
        """
        webbrowser.open(self._engine.context.shotgun_url)

    def jump_to_file_system(self):
        # launch one window for each location on disk
        paths = self._engine.context.filesystem_locations

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
                self.logger.error("Failed to launch '%s'!" % cmd)

    def rebuild_shotgun_menu(self):
        """
        This will remove and rebuild the menu.
        """
        try:
            self._rm_shotgun_menu()
        except Exception as error:
            self.logger.info("Error Clearing Menu {0}".format(error))
        self._create_shotgun_menu()
