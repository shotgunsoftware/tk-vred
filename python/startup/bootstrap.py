# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys
from os.path import dirname, abspath, join, expanduser, exists
from vred_bootstrap import compute_environment, compute_args


def bootstrap(engine_name, context, app_path, app_args, extra_args):
    """
    Start engine acording data passed by params.
    """
    startup_path = dirname(
        abspath(sys.modules[bootstrap.__module__].__file__)
    )

    env = compute_environment()
    app_args = compute_args(app_args)

    return (app_path, app_args)
