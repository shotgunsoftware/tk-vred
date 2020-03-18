# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys

import sgtk
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation


class VREDLauncher(SoftwareLauncher):
    """
    Handles launching VRED executables. Automatically starts up
    a tk-vred engine with the current context in the new session
    of VRED.
    """

    # Product code names
    CODE_NAMES = {
        "Pro": dict(icon="icon_pro_256.png"),
        "Design": dict(icon="icon_design_256.png"),
    }

    # Named regex strings to insert into the executable template paths when
    # matching against supplied versions and code_names. Similar to the glob
    # strings, these allow us to alter the regex matching for any of the
    # variable components of the path in one place
    COMPONENT_REGEX_LOOKUP = {
        "version": r"[\d.]+",
        "code_name": "(?:{code_names})".format(code_names="|".join(CODE_NAMES)),
        "code_name_extra": "(?:{code_names})".format(code_names="|".join(CODE_NAMES)),
    }

    # This dictionary defines a list of executable template strings for each
    # of the supported operating systems. The templates are used for both
    # globbing and regex matches by replacing the named format placeholders
    # with an appropriate glob or regex string. As Side FX adds modifies the
    # install path on a given OS for a new release, a new template will need
    # to be added here.
    EXECUTABLE_TEMPLATES = {
        "win32": [
            # C:\Program Files\Autodesk\VREDPro-11.0\bin\WIN64\VREDPro.exe
            r"C:\Program Files\Autodesk\VRED{code_name}-{version}\bin\WIN64\VRED{code_name_extra}.exe",
        ]
    }

    @property
    def minimum_supported_version(self):
        """The minimum software version that is supported by the launcher."""
        return "11.0"

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

    def scan_software(self):
        """
        Scan the filesystem for vred executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """
        self.logger.debug("Scanning for VRED executables...")

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

    @staticmethod
    def _map_version_year(version):
        try:
            year = int(version[:2]) + 2008
            return "{0}{1}".format(year, version[2:])
        except Exception as e:
            return version

    def _find_software(self):
        """Find executables in the default install locations."""

        # all the executable templates for the current OS
        executable_templates = self.EXECUTABLE_TEMPLATES.get(sys.platform, [])

        # all the discovered executables
        sw_versions = []

        for executable_template in executable_templates:

            self.logger.debug("Processing template %s.", executable_template)

            executable_matches = self._glob_and_match(
                executable_template, self.COMPONENT_REGEX_LOOKUP
            )

            # Extract all code_names from that executable.
            for (executable_path, key_dict) in executable_matches:

                # extract the matched keys form the key_dict (default to None if
                # not included)
                version = key_dict.get("version")
                code_name = key_dict.get("code_name")
                executable_version = self._map_version_year(version)

                sw_versions.append(
                    SoftwareVersion(
                        executable_version,
                        "VRED {0}".format(code_name),
                        executable_path,
                        self._icon_from_executable(code_name),
                    )
                )

        return sw_versions
