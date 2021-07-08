# Copyright (c) 2020 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import os
import subprocess
import re

import sgtk
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation
from sgtk.util import is_windows, is_macos, is_linux


class VREDLauncher(SoftwareLauncher):
    """
    Handles launching VRED executables. Automatically starts up
    a tk-vred engine with the current context in the new session
    of VRED.
    """

    # Product code names
    CODE_NAMES = {
        "VRED Pro": dict(icon="icon_pro_256.png"),
        "VRED Design": dict(icon="icon_design_256.png"),
        "VRED Presenter": dict(icon="icon_presenter_256.png"),
    }

    @property
    def minimum_supported_version(self):
        """The minimum VRED version that is supported by the launcher."""
        return "2020.0"

    @property
    def minimum_supported_presenter_version(self):
        """The minimum VRED Presenter version that is supported by the launcher."""
        return "2021.2"

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch VRED in that will automatically load
        Toolkit and the tk-vred engine when VRED starts.

        :param str exec_path: Path to VRED executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on launch.
        :returns: :class:`LaunchInformation` instance
        """
        required_env = {}

        # Command line arguments
        args += " -insecure_python"

        if os.getenv("DISABLE_VRED_OPENGL", "0") == "1":
            args += " -no_opengl"

        if os.getenv("ENABLE_VRED_CONSOLE", "0") == "1":
            args += " -console"

        # Register plugins
        plugin_dir = os.path.join(self.disk_location, "plugins", "Shotgun")
        vred_plugins_dir = os.path.join(os.path.dirname(exec_path), "Scripts")

        # be sure to not override the VRED_SCRIPT_PLUGINS environment variable if it's already declared
        if "VRED_SCRIPT_PLUGINS" in os.environ.keys():
            required_env["VRED_SCRIPT_PLUGINS"] = "{};{};{}".format(
                plugin_dir, vred_plugins_dir, os.environ["VRED_SCRIPT_PLUGINS"]
            )
        else:
            required_env["VRED_SCRIPT_PLUGINS"] = "{};{}".format(
                plugin_dir, vred_plugins_dir
            )

        # SHOTGUN_ENABLE is an extra environment variable required by VRED
        required_env["SHOTGUN_ENABLE"] = "1"

        # Prepare the launch environment with variables required by the
        # classic bootstrap approach.
        self.logger.debug("Preparing VRED Launch...")
        required_env["SGTK_ENGINE"] = self.engine_name
        required_env["SGTK_CONTEXT"] = sgtk.context.serialize(self.context)

        # Add the `file to open` to the launch environment
        if file_to_open:
            required_env["SGTK_FILE_TO_OPEN"] = file_to_open

        # Add VRED executable path as an environment variable to be used by the translators
        required_env["TK_VRED_EXECPATH"] = exec_path

        return LaunchInformation(exec_path, args, required_env)

    def scan_software(self):
        """
        Scan the filesystem for VRED executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """
        self.logger.debug("Scanning for VRED executables...")
        if is_macos():
            # No Mac version
            return []
        if is_linux():
            # TODO: Add linux support
            self.logger.debug("Linux support coming soon.")
            return []

        supported_sw_versions = []

        for sw_version in self._find_software():
            supported, reason = self._is_supported(sw_version)

            if re.search("Presenter", sw_version.product):
                supported = False

            if supported:
                supported_sw_versions.append(sw_version)
            else:
                self.logger.debug(
                    "SoftwareVersion %s is not supported: %s" % (sw_version, reason)
                )

        return supported_sw_versions

    def scan_for_presenter(self):
        """
        Scan the filesystem for VRED Presenter executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """
        self.logger.debug("Scanning for VRED Presenter...")

        supported_sw_versions = []

        for sw_version in self._find_software():
            supported, reason = self._is_supported(sw_version)

            if supported:
                supported_sw_versions.append(sw_version)
            else:
                self.logger.debug(
                    "SoftwareVersion %s is not supported: %s" % (sw_version, reason)
                )

        return supported_sw_versions

    ##########################################################################################
    # private methods

    def _icon_from_executable(self, code_name):
        """
        Find the application icon based on the code_name.

        :param code_name: Product code_name (AutoStudio, Design, ...).

        :returns: Full path to application icon as a string or None.
        """
        if code_name in self.CODE_NAMES:
            icon_name = self.CODE_NAMES.get(code_name).get("icon")
            path = os.path.join(self.disk_location, "icons", icon_name)
        else:
            path = os.path.join(self.disk_location, "icon_256.png")

        return path

    @staticmethod
    def _map_version_year(version):
        try:
            year = int(version[:2]) + 2008
            return "{0}{1}".format(year, version[2:4])
        except Exception:
            return version

    def _find_software(self):
        """
        Find executables in the Registry for Windows
        :returns: List of :class:`SoftwareVersion` instances
        """
        sw_versions = []
        if is_windows():
            # Determine a list of paths to search for VRED executables based
            # on the windows registry
            install_paths_dicts = _get_installation_paths_from_windows_registry(
                self.logger
            )

            for install_paths in install_paths_dicts:
                executable_version = self._map_version_year(install_paths["version"])
                executable_path = install_paths["path"]
                launcher_name = install_paths["_name"]
                icon_file = self._icon_from_executable(launcher_name)

                # Create The actual SoftwareVersions
                sw_versions.append(
                    SoftwareVersion(
                        executable_version,
                        launcher_name,
                        executable_path,
                        icon_file,
                    )
                )

        return sw_versions

    def _is_supported(self, sw_version):
        """
        Determine if a software version is supported or not
        :param sw_version:
        :return: boolean, message
        """
        if re.search("Presenter", sw_version.product):
            minimum_supported = self.minimum_supported_presenter_version
        else:
            minimum_supported = self.minimum_supported_version
        try:
            if int(sw_version.version.replace(".", "")) >= int(
                str(minimum_supported).replace(".", "")
            ):
                return True, ""
            else:
                return False, "Unsupported version of VRED"
        except Exception:
            return False, "Error determining VRED version"


def _get_installation_paths_from_windows_registry(logger):
    """
    Query Windows registry for VRED installations.
    :returns: List of dictionaries of paths and versions
    where VRED is installed.
    """
    # Local scope here
    from tank_vendor.shotgun_api3.lib import six

    winreg = six.moves.winreg

    logger.debug(
        "Querying Windows registry for keys "
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\Autodesk\\VRED "
        "Pro | Design | Presenter"
    )

    install_paths = []

    # VRED install keys
    base_key_names = [
        [
            "SOFTWARE\\Autodesk\\VREDPro",
            "VREDLocation",
            "\\VREDPro.exe",
            "VRED Pro",
        ],
        [
            "SOFTWARE\\Autodesk\\VREDDesign",
            "VREDLocation",
            "\\VREDDesign.exe",
            "VRED Design",
        ],
        [
            "SOFTWARE\\Autodesk\\VREDPresenter",
            "VREDLocation",
            "\\VREDPresenter.exe",
            "VRED Presenter",
        ],
    ]
    for base_key_name in base_key_names:
        sub_key_names = []
        # find all subkeys in keys
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key_name[0])
            sub_key_count = winreg.QueryInfoKey(key)[0]
            i = 0
            while i < sub_key_count:
                sub_key_names.append(winreg.EnumKey(key, i))
                i += 1
            winreg.CloseKey(key)
        except WindowsError:
            logger.debug("error opening key %s" % base_key_name[0])

        # Query the value VREDLocation on all subkeys.
        try:
            for name in sub_key_names:
                key_name = base_key_name[0] + "\\" + name
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_name)
                try:
                    base_path = winreg.QueryValueEx(key, base_key_name[1])
                    # V12.2 has a trailing backslash here
                    if base_path[0].endswith("\\"):
                        base_path_used = base_path[0].rstrip("\\")
                    else:
                        base_path_used = base_path[0]
                    full_path = base_path_used + base_key_name[2]
                    version = _get_windows_version(full_path, logger)
                    name = base_key_name[3]
                    install_paths.append(
                        {"path": full_path, "version": version, "_name": name}
                    )
                    logger.debug("Found VREDLocation value for key %s" % key_name)
                    # Add Presenter from Pro directory here
                    if name == "VRED Pro":
                        full_path = base_path_used + "\\VREDPresenter.exe"
                        name = "VRED Presenter"
                        install_paths.append(
                            {"path": full_path, "version": version, "_name": name}
                        )
                        logger.debug("Added VREDPresenter.exe from VRED Pro directory")
                except WindowsError:
                    logger.debug(
                        "Value VREDLocation not found for key %s, skipping key"
                        % key_name
                    )
                winreg.CloseKey(key)
        except WindowsError:
            logger.debug("Error opening key %s" % key_name)

    return install_paths


def _get_windows_version(full_path, logger):
    """
    Use `wmic` to determine the installed version of VRED
    """
    version = "0.0.0.0"
    try:
        version_command = subprocess.check_output(
            [
                "wmic",
                "datafile",
                "where",
                "name=" + '"' + str(full_path).replace("\\", "\\\\") + '"',
                "get",
                "Version",
                "/value",
            ]
        )

    except subprocess.CalledProcessError:
        command_string = (
            "wmic" + " "
            "datafile" + " "
            "where" + " "
            "name=" + '"' + str(full_path).replace("\\", "\\\\") + '"' + " "
            "get" + " "
            "Version" + " "
            "/value"
        )
        version_command = subprocess.check_output(command_string)

    finally:
        logger.debug("Could not determine version using `wmic`.")

    if version_command:
        version_list = re.findall(r"[\d.]", str(version_command))
        version = "".join(map(str, version_list))

    return version
