# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.
import os

import tank
import vrScenegraph
from tank import Hook
from tank import TankError

from pprint import pformat



class ScanSceneHook(Hook):
    """
    Hook to scan scene for items to publish
    """

    def execute(self, **kwargs):
        """
        Main hook entry point
        :returns:       A list of any items that were found to be published.
                        Each item in the list should be a dictionary containing
                        the following keys:
                        {
                            type:   String
                                    This should match a scene_item_type defined in
                                    one of the outputs in the configuration and is
                                    used to determine the outputs that should be
                                    published for the item

                            name:   String
                                    Name to use for the item in the UI

                            description:    String
                                            Description of the item to use in the UI

                            selected:       Bool
                                            Initial selected state of item in the UI.
                                            Items are selected by default.

                            required:       Bool
                                            Required state of item in the UI.  If True then
                                            item will not be deselectable.  Items are not
                                            required by default.

                            other_params:   Dictionary
                                            Optional dictionary that will be passed to the
                                            pre-publish and publish hooks
                        }
        """
        # Setup Data Objects
        engine = tank.platform.current_engine()
        app = self.parent

        publish_template = app.get_template('primary_publish_template')
        if publish_template is None:
            raise TankError("Configuration Error:  Could not find template specified with primary_publish_template")
        
        # Get and Check Main File
        file = self.parent.engine.get_current_file()
        if not file:
            raise TankError("Please Save your file before Publishing")
            
        # Main File
        retFileList = [
            {
                'type': 'vred_file',
                'name': os.path.basename(file),
                'description': '',
                'selected': True,
                'required': True,
                'other_params': {}
            }
        ]
        
        
        # Add Secondary Outputs - Geometry Only
        rootNode = vrScenegraph.getRootNode()
        for n in range(0,rootNode.getNChildren()):
            childNode = rootNode.getChild(n)
            if childNode.getType() == "Geometry":
                # Add node Info
                fieldAcc = childNode.fields()
                newNode = {
                    'type': 'Geometry',
                    'name': childNode.getName(),
                    'description': 'Geometry Node',
                    'selected': False,
                    'required': False,
                    'other_params': {
                            'NodeID': fieldAcc.getID() 
                        }
                }
                retFileList.append(newNode)
        
        # Return File List
        return retFileList