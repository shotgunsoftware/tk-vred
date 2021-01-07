# Copyright (c) 2020 Shotgun Software Inc.
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

import vrController
import vrFileIO
import vrOptimize
import vrScenegraph


if __name__ == "__main__":

    fbx_path = sys.argv[0]

    # get the root node
    root_node = vrScenegraph.getRootNode()

    # convert all the surface nodes to mesh
    # convert_surface_node_to_mesh(root_node)
    vrOptimize.removeNURBS(root_node)

    # export the file as fbx
    if not os.path.exists(os.path.dirname(fbx_path)):
        os.makedirs(os.path.dirname(fbx_path))
    vrFileIO.saveGeometry(root_node, fbx_path)

    # finally terminate VRED
    vrController.terminateVred()
