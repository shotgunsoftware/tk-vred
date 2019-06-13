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
    
    env['SHOTGUN_ENABLE'] = os.environ['SHOTGUN_ENABLE']

    return env
