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
import subprocess
from os.path import dirname, abspath, join, expanduser, exists
from shutil import copyfile

from sgtk.util import prepend_path_to_env_var
from distutils.dir_util import copy_tree

CORE_SCRIPTS_DIR = r"C:\Program Files\Autodesk\VREDPro-11.0\lib\plugins\WIN64\Scripts"

def bootstrap(engine_name, context, app_path, app_args, extra_args):
    """
    Start engine acording data passed by params.
    """
    startup_path = dirname(
        abspath(sys.modules[bootstrap.__module__].__file__)
    )

    # Tell VRED to start the engine.
    os.environ['SHOTGUN_ENABLE'] = '1'

    # Tell VRED where to find the script
    resources_dir = join(dirname(dirname(dirname(__file__))), "resources")
    scripts_dir = join(resources_dir, "Shotgun")

    os.environ["VRED_SCRIPT_PLUGINS"] = "{};{}".format(scripts_dir, CORE_SCRIPTS_DIR)
    # VRED 2019 BETA SPECIFIC ENV VARIABLE - AVOID IT'S USAGE
    # environment variable VRED%YEAR%_%UPDATE%_SCRIPT_PLUGINS
    # If is BETA just VRED%YEAR%_SCRIPT_PLUGINS
    # os.environ["VRED2019_SCRIPT_PLUGINS"] = "{};{}".format(scripts_dir, CORE_SCRIPTS_DIR)
    
    app_args = (app_args or "")
    app_args += ' -insecure_python'
    if(os.environ.get('DISABLE_VRED_OPENGL', '0') == '1'):
        app_args += ' -no_opengl'

    return (app_path, app_args)