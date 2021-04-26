# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

from sgtk.platform.qt import QtCore, QtGui
from sgtk.util import is_windows, is_linux, is_macos
from tank_vendor import six


class VREDMenuGenerator(object):
    """
    Menu generation functionality for VRED.
    """

    ROOT_MENU_TEXT = u"S&hotgun"

    def __init__(self, engine):
        """
        Class constructor

        :param engine: The engine currently running.
        :type engine: :class:`tank.platform.Engine`
        """
        self._engine = engine
        self._root_menu = None
        self._menu_favourites = None

    @property
    def favourites(self):
        """
        The menu favourites, in sorted order by name.
        """

        if self._menu_favourites is None:
            self._menu_favourites = self._engine.get_setting("menu_favourites", [])
            self._menu_favourites.sort(key=lambda f: f["name"])

        return self._menu_favourites

    @property
    def root_menu(self):
        """
        Get the :class:`VREDMenu` object that is the root menu for this generator.
        """

        return self._root_menu

    def get_menubar(self):
        """
        Convenience method to return the :class:`sgtk.platform.qt.QtGui.QMainWindow`
        :class:`sgtk.platform.qt.QtGui.QMenuBar` object that generated menus will
        be added to.
        """

        return self._engine._get_dialog_parent().menuBar()

    def is_menubar_active(self):
        """
        Returns True if the main window menubar exists, is visible and enabled (in other
        words, return True if the menu bar can be used to add menus to).
        """

        menubar = self.get_menubar()
        return menubar and menubar.isVisible() and menubar.isEnabled()

    def create_menu(self, clean_menu=True):
        """
        Create the menu and add it to the VRED menu bar.

        :param clean_menu: Set to True will clean up the menu exist before creating.
        """

        if not self.is_menubar_active():
            self._engine.logger.info(
                "{}: Aborting menu creation. VRED does not have a menu bar available to add a menu to.".format(
                    self
                )
            )
            return

        self._engine.logger.debug("{}: Creating menu".format(self))

        # First, ensure that the Shotgun menu inside VRED is empty.
        # This is to ensure we can recover from context switches where
        # the engine failed to clean up after itself properly.
        if clean_menu:
            self.clean_menu()

        # Create the Shotgun root menu object.
        self._root_menu = VREDMenu(self.ROOT_MENU_TEXT, self.get_menubar())

        # Create the context submenu and add it to the top of the root menu.
        context_menu = self._create_context_menu()
        self._root_menu.add_submenu(context_menu)

        # Create menu item AppCommand objects to represent each engine command, and sort by command name.
        menu_items = [
            AppCommand(cmd_name, cmd_details)
            for cmd_name, cmd_details in self._engine.commands.items()
        ]
        menu_items.sort(key=lambda item: item.name)

        # Iterate through the menu items, mark items as favourites and add them to the root menu.
        # Favourites will appear next under the context menu, in the root menu.
        self._add_favourites_to_menu(menu_items, self._root_menu)

        # Iterate through the menu items again, this time adding any context menu commands to the context
        # submenu, while creating a dictionary mapping of apps to their app commands.
        commands_by_app = {}
        add_separator = True
        for cmd in menu_items:
            if cmd.is_context_menu_command():
                cmd.add_command_to_menu(
                    self._root_menu, context_menu, add_separator=add_separator
                )
                add_separator = False

                self._engine.logger.debug(
                    "Added context menu item '{name}'.".format(name=cmd.name)
                )

            else:
                commands_by_app.setdefault(cmd.app_name, []).append(cmd)

        # Finally, add the remaining commands to the root menu, grouped by the app they belong to.
        self._add_apps_to_menu(commands_by_app, self._root_menu)

        # Show the Shotgun menu by add it to the end of list of VRED menu bar actions.
        self._root_menu.show()

    def clean_menu(self):
        """
        Remove Shotgun root menu in VRED, if it exists.
        """

        if self._root_menu is not None:
            self._engine.logger.debug("{}: Clean up menu".format(self))

            self._root_menu.clean()
            self._root_menu = None

    def _create_context_menu(self):
        """
        Create a context menu which displays the current context.

        :returns: A Qt menu instance representing the context menu.
        :rtype: QtGui.QMenu
        """

        ctx = self._engine.context
        ctx_name = six.ensure_str(str(ctx))

        context_menu = create_qt_menu(ctx_name)
        context_menu.addAction("Jump to Shotgun", self._jump_to_sg)

        # Add the menu item only when there are filesystem locations.
        if ctx.filesystem_locations:
            context_menu.addAction("Jump to File System", self._jump_to_fs)

        return context_menu

    def _add_favourites_to_menu(self, menu_items, menu, add_separator=True):
        """
        Mark any menu item as a favourite, if defined in the engine settings, and
        add it to the menu.

        :param menu_items: List of menu item AppCommand objects.
        :param menu: The VREDMenu object to add the menu item AppCommand favourites to.
        :param add_separator: Set to True will add a separator before the first favourite command is added.
        """

        if not self.favourites:
            return

        for favourite in self.favourites:
            app_instance_name = favourite["app_instance"]
            menu_name = favourite["name"]

            try:
                favourite_cmd = next(
                    cmd
                    for cmd in menu_items
                    if cmd.app_instance_name == app_instance_name
                    and cmd.name == menu_name
                )

                # Mark this command as a favourite and add it to the menu.
                favourite_cmd.favourite = True
                favourite_cmd.add_command_to_menu(
                    menu, None, add_separator=add_separator
                )

                add_separator = False

                self._engine.logger.debug(
                    "Added menu favourite for app '{app}' with name '{name}'.".format(
                        app=app_instance_name, name=menu_name
                    )
                )

            except StopIteration:
                self._engine.logger.debug(
                    "Skipping - menu favourite not found for app '{app}' with name '{name}'.".format(
                        app=app_instance_name, name=menu_name
                    )
                )

    def _add_apps_to_menu(
        self, commands_by_app, menu, exclude_favourites=True, add_separator=True
    ):
        """
        Add all apps to the main menu, process them one by one.

        :param commands_by_app: A dictionary of app name mapping to a list of AppCommands.
        :param menu: The VREDMenu object to add the menu item AppCommands to.
        :param exclude_favourites: True will omit any single app actions that are favourite commands.
        :param add_separator: Set to True will add a separator before the first app command is added.
        """

        for app_name in sorted(commands_by_app.keys()):
            submenu = None

            if not commands_by_app[app_name]:
                continue

            elif len(commands_by_app[app_name]) > 1:
                # Create a submenu for all of the app's menu entries and add it to the menu
                submenu = create_qt_menu(app_name)

            elif exclude_favourites and commands_by_app[app_name][0].favourite:
                # Omit single app menu items if they are a favourite (they will have been added already)
                continue

            # Get the list of menu commands for this app and make sure it is in alphabetical order
            cmds = commands_by_app[app_name]
            cmds.sort(key=lambda cmd: cmd.name)

            for cmd in cmds:
                cmd.add_command_to_menu(menu, submenu, add_separator)

                self._engine.logger.debug(
                    "Added menu item for app '{app}' with name '{name}'.".format(
                        app=app_name, name=cmd.name
                    )
                )

            # Set add separator flag to False after the first item has been added
            add_separator = False

    def _jump_to_sg(self):
        """
        Jump to shotgun, launch web browser
        """
        url = self._engine.context.shotgun_url

        self._engine.logger.debug("Open URL: {}".format(url))
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def _jump_to_fs(self):
        """
        Jump from context to FS
        """
        # launch one window for each location on disk
        paths = self._engine.context.filesystem_locations

        for disk_location in paths:
            if is_linux():
                cmd = 'xdg-open "{}"'.format(disk_location)
            elif is_macos():
                cmd = 'open "{}"'.format(disk_location)
            elif is_windows():
                cmd = 'cmd.exe /C start "Folder" "{}"'.format(disk_location)
            else:
                raise Exception("Platform is not supported.")

            self._engine.logger.debug("Jump to filesystem command:  {}".format(cmd))

            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.logger.error(
                    "Failed to launch command:  '{}'!".format(cmd)
                )


class VREDMenu(object):
    """
    Class manages a custom menu action in VRED. This is primarily used to create the
    Shotgun menu in VRED.
    """

    def __init__(self, name, menu_bar):
        """
        Class Constructor

        :param name: The name for the VRED menu.
        :param menu_bar: The VRED Qt QMenuBar object that this menu resides in.
        """

        self._name = name
        self._menu_bar = menu_bar
        self._menu = create_qt_menu(self._name)

    def clean(self):
        """
        Clean up this menu by removing it from the VRED menu bar.
        """

        try:
            action_to_remove = next(
                a for a in self._menu_bar.actions() if a.text() == self._name
            )
            self._menu_bar.removeAction(action_to_remove)
        except StopIteration:
            # Menu not found, skip
            pass

    def show(self, index=-1):
        """
        Show this VRED menu by inserting it into the VRED menu bar.

        :param index: The index used to insert this menu into the menu bar location. By default, the
        menu will be added to the end of the actions list.
        """

        actions = self._menu_bar.actions()

        # If the provided index is invalid, just append to the end.
        if index < 0 or index >= len(actions):
            index = -1

        if actions is not None:
            self._menu_bar.insertMenu(actions[index], self._menu)

    def add_submenu(self, submenu, add_separator=False):
        """
        Add a submenu to this VRED menu.

        :param submenu: The submenu to add to this menu.
        :param add_separator: If True, a separator will be added before the submenu.
        """

        if add_separator:
            self._menu.addSeparator()
        self._menu.addMenu(submenu)

    def add_command(self, cmd_name, cmd_callback, add_separator=False, parent=None):
        """
        Add a command to this VRED menu.

        :param cmd_name: The name of the command.
        :param cmd_callback: The callback for the command.
        :param add_separator: If True, a separator will be added before the command.
        :param parent: A Qt QMenu object; if provided, the command will be added to the parent
        menu, and then the parent menu will be added as a submenu to this VRED menu, if it
        does not exist yet.
        """

        if parent is None:
            if add_separator:
                self._menu.addSeparator()

            self._menu.addAction(cmd_name, cmd_callback)

        else:
            if add_separator:
                parent.addSeparator()

            parent.addAction(cmd_name, cmd_callback)

            try:
                found = False
                for a in self._menu.actions():
                    if a.text() == parent.title():
                        found = True
                # next(a for a in self._menu.actions() if a.text() == parent.title())
                # Submenu already exists, nothing to do
            except StopIteration:
                # Add the parent submenu to our menu since it does not exist yet
                self.add_submenu(parent)

            if not found:
                self.add_submenu(parent)


class AppCommand(object):
    """
    Wraps around a single command that you get from engine.commands
    """

    def __init__(self, name, command_dict, is_favourite=False):
        """
        Class constructor

        :param name: Command name
        :param command_dict: Dictionary containing Command details
        """

        self.name = name
        self.favourite = is_favourite
        self.properties = command_dict["properties"]
        self.callback = command_dict["callback"]

    @property
    def app_instance_name(self):
        """
        The name of the app intance this command belongs to, as defined in the
        environment. Value will be None if not defined by the environment.
        """

        if "app" not in self.properties:
            return None

        app_instance = self.properties["app"]
        engine = app_instance.engine

        for (app_instance_name, app_instance_obj) in engine.apps.items():
            if app_instance_obj == app_instance:
                return app_instance_name

        return None

    @property
    def app_type(self):
        """
        The type of the app that this command belongs to.
        """

        return self.properties.get("type", "default")

    @property
    def app_name(self):
        """
        The name of the app that this command belongs to.
        """

        if "app" in self.properties:
            return self.properties["app"].display_name
        return "Other Items"

    def is_context_menu_command(self):
        """
        Convenience method to check if a command is a Context Menu specific item.

        :returns: True if this is a Context Menu command.
        :rtype: bool
        """

        return self.app_type == "context_menu"

    def add_command_to_menu(self, menu, submenu, add_separator=False):
        """
        Adds an app command to the menu.

        :param menu: A VRED Menu to add the command to.
        :param submenu: A Qt QMenu to add the command to first, and then added as submenu to the menu.
        :param add_separator: True will add a separator before the command in the menu.
        """

        menu.add_command(
            self.name, self.callback, add_separator=add_separator, parent=submenu
        )


def create_qt_menu(name):
    """
    Helper function to create a Qt menu with the given name.

    :param name: The menu name.
    :returns: The menu created.
    :rtype: QtGui.QMenu
    """

    menu = QtGui.QMenu()
    menu.setTitle(name)
    return menu
