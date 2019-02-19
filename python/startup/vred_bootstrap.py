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
from os.path import dirname, abspath, join, expanduser, exists

import sgtk

# CORE_SCRIPTS_DIR = r"C:\Program Files\Autodesk\VREDPro-11.0\lib\plugins\WIN64\Scripts"


def compute_environment(engine_name=None, context=None, exec_path=None):
    """
    Return the env vars needed to launch the vred plugin.
    This will generate a dictionary of environment variables
    needed in order to launch the vred plugin.
    :returns: dictionary of env var string key/value pairs.
    """
    env = {}
    
    # Tell VRED to start the engine.
    os.environ['SHOTGUN_ENABLE'] = '1'
    
    # Tell VRED where to find the script
    resources_dir = join(dirname(dirname(dirname(__file__))), "resources")
    scripts_dir = join(resources_dir, "Shotgun")

    BASE_DIR = os.path.dirname(exec_path)

    CORE_SCRIPTS_DIR = os.path.join(BASE_DIR, "Scripts")
    os.environ["VRED_SCRIPT_PLUGINS"] = "{};{}".format(scripts_dir, CORE_SCRIPTS_DIR)
    # VRED 2019 BETA SPECIFIC ENV VARIABLE - AVOID IT'S USAGE
    # environment variable VRED%YEAR%_%UPDATE%_SCRIPT_PLUGINS
    # If is BETA just VRED%YEAR%_SCRIPT_PLUGINS
    # os.environ["VRED2019_SCRIPT_PLUGINS"] = "{};{}".format(scripts_dir, CORE_SCRIPTS_DIR)
    
    env['SHOTGUN_ENABLE'] = os.environ['SHOTGUN_ENABLE']
    env["VRED_SCRIPT_PLUGINS"] = os.environ["VRED_SCRIPT_PLUGINS"]
    
    if engine_name:
        os.environ['SGTK_ENGINE'] = engine_name
        env['SGTK_ENGINE'] = os.environ['SGTK_ENGINE']
    
    if context:
        os.environ['TANK_CONTEXT'] = context
        env['TANK_CONTEXT'] = os.environ['TANK_CONTEXT']

    if os.path.exists(os.path.join(BASE_DIR, "LMV")):
        sgtk.util.append_path_to_env_var("PATH", BASE_DIR)
        sgtk.util.append_path_to_env_var("PATH", os.path.join(BASE_DIR, "LMV"))

        env["PATH"] = os.environ["PATH"]

    return env


def compute_args(app_args):
    """
    Return the args needed to launch the vred plugin.
    This will generate a dictionary of args
    needed in order to launch the vred plugin.
    :returns: array of args.
    """
    app_args = (app_args or "")
    app_args += ' -insecure_python'
    if os.environ.get('DISABLE_VRED_OPENGL', '0') == '1':
        app_args += ' -no_opengl'
    
    return app_args