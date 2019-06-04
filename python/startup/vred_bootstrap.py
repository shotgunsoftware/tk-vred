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

    env['SHOTGUN_ENABLE'] = os.environ['SHOTGUN_ENABLE']
    env["VRED_SCRIPT_PLUGINS"] = os.environ["VRED_SCRIPT_PLUGINS"]
    
    if engine_name:
        os.environ['SGTK_ENGINE'] = engine_name
        env['SGTK_ENGINE'] = os.environ['SGTK_ENGINE']
    
    if context:
        os.environ['SGTK_CONTEXT'] = context
        env['SGTK_CONTEXT'] = os.environ['SGTK_CONTEXT']

    if os.path.exists(os.path.join(BASE_DIR, "LMV")):
        sgtk.util.append_path_to_env_var("PATH", BASE_DIR)
        sgtk.util.append_path_to_env_var("PATH", os.path.join(BASE_DIR, "LMV"))

        env["PATH"] = os.environ["PATH"]

    return env
