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

from collections import OrderedDict
import os
import sys

from sgtk.platform.qt import QtGui
from sgtk.platform.qt import QtCore


class VREDMenu(object):
    ROOT_MENU_TEXT = u'S&hotgun'

    def __init__(self, engine):
        """Initialize attributes."""
        # engine instance
        self._engine = engine

        self.logger = self._engine.logger

    def create(self):
        self.logger.info("Creating Shotgun Menu")

        # Destroy root menu if exists
        if self.exists:
            self.destroy()

        # Create root menu
        window = self._engine.get_vred_main_window()
        menubar = window.menuBar()
        root_menu = QtGui.QMenu()
        root_menu.setTitle(self.ROOT_MENU_TEXT)

        # Get all options
        options = [(caption, data) for caption, data in self._engine.commands.items()]
        if options:
            options.sort(key=lambda option: option[0])

        # Context submenu
        root_menu.addMenu(self._create_context_submenu(options))
        root_menu.addSeparator()

        # Favourites
        favourites = self._create_favourites(options)
        [root_menu.addAction(caption, callback) for caption, callback in favourites]
        if favourites:
            root_menu.addSeparator()

        # Apps
        apps = self._create_apps(options)
        for caption, callback, submenu in apps:
            if submenu:
                root_menu.addMenu(submenu)
            else:
                root_menu.addAction(caption, callback)

        # Add root menu
        for action in menubar.actions():
            if action.text() == u'&Help':
                menubar.insertMenu(action, root_menu)
                break

    def _create_context_submenu(self, options):
        submenu = QtGui.QMenu()
        submenu.setTitle(self.context_name)

        submenu.addAction("Jump to Shotgun", self.jump_to_sg)
        submenu.addAction("Jump to File System", self.jump_to_fs)
        submenu.addSeparator()

        options = [(caption, data) for caption, data in options
                   if data.get("properties").get("type") == "context_menu"]

        for caption, data in options:
            callback = data.get("callback")
            submenu.addAction(caption, callback)

        return submenu

    def _create_favourites(self, options):
        favourites = []

        for favourite in self._engine.get_setting("menu_favourites"):
            app_instance = favourite["app_instance"]
            name = favourite["name"]

            for caption, data in options:
                if data.get("properties").get("type") == "context_menu":
                    continue

                if 'app' in data.get("properties"):
                    app_name = data.get("properties").get("app").name

                    if caption == name and app_name == app_instance:
                        callback = data.get("callback")
                        favourites.append((caption, callback))

        return favourites

    def _create_apps(self, options):
        # Apps to display in the bottom of the menu
        bottom_apps = OrderedDict()
        bottom_apps[('tk-multi-autoabout', 'About Shotgun Pipeline Toolkit')] = []

        favourites = [(favourite["app_instance"], favourite["name"])
                      for favourite in self._engine.get_setting("menu_favourites")]

        options = [(caption, data) for caption, data in options
                   if data.get("properties").get("type") != "context_menu"]

        groups = OrderedDict()
        for caption, data in options:
            callback = data.get("callback")
            app_name = None
            app_display_name = None
            if 'app' in data.get("properties"):
                app_name = data.get("properties").get("app").name
                app_display_name = data.get("properties").get("app").display_name

            k = (app_name, app_display_name)

            if k in bottom_apps:
                bottom_apps[k].append((caption, callback))
            else:
                if k not in groups:
                    groups[k] = []

                groups[k].append((caption, callback))

        raw_options = []

        for (app_name, app_display_name), options in groups.items():
            first_option = options[0]
            caption = first_option[0]
            callback = first_option[1]
            options_number = len(options)

            raw_option = None
            if options_number == 1 and (app_name, caption) not in favourites:
                # apps.append()
                raw_option = (caption, caption, callback, None)

            elif options_number > 1:
                submenu = QtGui.QMenu()
                submenu.setTitle(app_display_name)
                for caption, callback in options:
                    submenu.addAction(caption, callback)

                raw_option = (app_display_name, None, None, submenu)

            if raw_option:
                raw_options.append(raw_option)

        raw_options.sort(key=lambda option: option[0])

        apps = [(caption, callback, submenu) for _, caption, callback, submenu in raw_options]

        for (app_name, app_display_name), options in bottom_apps.items():
            first_option = options[0]
            caption = first_option[0]
            callback = first_option[1]
            options_number = len(options)

            if options_number == 1 and (app_name, caption) not in favourites:
                apps.append((caption, callback, None))
            elif options_number > 1:
                submenu = QtGui.QMenu()
                submenu.setTitle(app_display_name)
                for caption, callback in options:
                    submenu.addAction(caption, callback)

                apps.append((None, None, submenu))

        return apps

    @property
    def exists(self):
        window = self._engine.get_vred_main_window()
        menu_bar = window.menuBar()
        options = [option for option in menu_bar.actions() if option.text() == self.ROOT_MENU_TEXT]

        if options:
            return True

        return False

    def destroy(self):
        self.logger.info("Destroying Shotgun Menu")

        window = self._engine.get_vred_main_window()
        menu_bar = window.menuBar()
        option = [option for option in menu_bar.actions() if option.text() == self.ROOT_MENU_TEXT][0]
        menu_bar.removeAction(option)

    @property
    def context_name(self):
        """Returns the context name used by the context submenu caption."""
        return str(self._engine.context).decode("utf-8")

    def jump_to_sg(self):
        """
        Jump to shotgun, launch web browser
        """
        url = self._engine.context.shotgun_url
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def jump_to_fs(self):
        """
        Jump from context to FS
        """
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

            self._engine.logger.debug("Jump to filesystem command: {}".format(cmd))

            exit_code = os.system(cmd)

            if exit_code != 0:
                self.logger.error("Failed to launch '%s'!", cmd)

